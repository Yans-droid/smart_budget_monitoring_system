from models.pr_po_data import PrPoData
from models.item_mapping import ItemMapping
from utils.db import db
from utils.sanitize import to_int_or_none
from datetime import datetime, timedelta
from sqlalchemy import func
from models.mapping_log import MappingLog
from models.planning_detail import PlanningDetail


class ItemMappingService:

    @staticmethod
    def get_all():
        mappings = ItemMapping.query.order_by(
            ItemMapping.priority.asc()
        ).all()
        return {
            "success": True,
            "data": [m.to_dict() for m in mappings]
        }, 200

    @staticmethod
    def get_by_id(mapping_id):
        mapping = db.session.get(ItemMapping, mapping_id)
        if not mapping:
            return {"success": False, "message": "Item mapping tidak ditemukan"}, 404
        return {"success": True, "data": mapping.to_dict()}, 200

    @staticmethod
    def create(data):
        keyword = data.get("keyword")
        planning_item = data.get("planning_item")
        # Konversi empty string ke None — form React kirim '' kalau tidak dipilih
        kategori_id = to_int_or_none(data.get("kategori_id"))
        priority = data.get("priority", 1)

        if not keyword:
            return {"success": False, "message": "keyword wajib diisi"}, 400
        if not planning_item:
            return {"success": False, "message": "planning_item wajib diisi"}, 400

        mapping = ItemMapping(
            keyword=keyword,
            planning_item=planning_item,
            kategori_id=kategori_id,
            priority=priority,
            is_active=data.get("is_active", True)
        )

        try:
            db.session.add(mapping)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"Gagal menyimpan: {str(e)}"}, 500

        return {
            "success": True,
            "message": "Item mapping berhasil dibuat",
            "data": mapping.to_dict()
        }, 201

    @staticmethod
    def update(mapping_id, data):
        mapping = db.session.get(ItemMapping, mapping_id)
        if not mapping:
            return {"success": False, "message": "Item mapping tidak ditemukan"}, 404

        if "keyword" in data:
            mapping.keyword = data["keyword"]
        if "planning_item" in data:
            mapping.planning_item = data["planning_item"]
        if "kategori_id" in data:
            # Sanitasi: konversi empty string ke None
            mapping.kategori_id = to_int_or_none(data["kategori_id"])
        if "priority" in data:
            mapping.priority = data["priority"]
        if "is_active" in data:
            mapping.is_active = data["is_active"]

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"Gagal update: {str(e)}"}, 500

        return {
            "success": True,
            "message": "Item mapping berhasil diupdate",
            "data": mapping.to_dict()
        }, 200

    @staticmethod
    def delete(mapping_id):
        mapping = db.session.get(ItemMapping, mapping_id)
        if not mapping:
            return {"success": False, "message": "Item mapping tidak ditemukan"}, 404

        db.session.delete(mapping)
        db.session.commit()

        return {"success": True, "message": "Item mapping berhasil dihapus"}, 200

    @staticmethod
    def find_mapping(keyword, kategori_id=None):
        """
        Cari planning_item yang cocok berdasarkan keyword.
        Matching dilakukan dengan mengecek apakah deskripsi PR (keyword)
        MENGANDUNG keyword dari ItemMapping di DB.
        """
        from sqlalchemy import literal, func
        
        query = ItemMapping.query.filter(
            ItemMapping.is_active == True,
            literal(keyword).ilike(func.concat('%', ItemMapping.keyword, '%'))
        )

        if kategori_id:
            query = query.filter(ItemMapping.kategori_id == kategori_id)

        result = query.order_by(ItemMapping.priority.asc()).first()

        if not result:
            return None

        return result.planning_item

    @staticmethod
    def suggest_new_rules(min_occurrence=3, months_back=12):
        """
        Cari pola dari mapping_log: description yang sama persis,
        dipetakan ke planning_detail_id yang sama, berulang >= min_occurrence kali,
        dalam `months_back` bulan terakhir. Cuma menyarankan, TIDAK auto-insert
        ke item_mapping.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=months_back * 30)

        results = db.session.query(
            PrPoData.description,
            MappingLog.planning_detail_hasil_id,
            func.count(MappingLog.id).label('jumlah')
        ).join(
            MappingLog, MappingLog.pr_po_data_id == PrPoData.id
        ).filter(
            MappingLog.is_selected == True,
            MappingLog.planning_detail_hasil_id.isnot(None),  # otomatis exclude OOP (poin 4)
            MappingLog.created_at >= cutoff_date               # exclude data lama (poin 2)
        ).group_by(
            PrPoData.description, MappingLog.planning_detail_hasil_id
        ).having(
            func.count(MappingLog.id) >= min_occurrence
        ).order_by(
            func.count(MappingLog.id).desc()                    # urutkan by jumlah (poin 3)
        ).all()

        suggestions = []
        for desc, detail_id, jumlah in results:
            # Skip kalau rule untuk keyword ini SUDAH ada (aktif ATAU sudah di-dismiss)
            existing_rule = ItemMapping.query.filter_by(keyword=desc).first()
            if existing_rule:
                continue
            detail = db.session.get(PlanningDetail, detail_id)
            suggestions.append({
                "description": desc,
                "planning_detail_id": detail_id,
                "planning_item": detail.item if detail else None,
                "jumlah_kemunculan": jumlah
            })
        return suggestions

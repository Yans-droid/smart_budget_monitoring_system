from models.item_mapping import ItemMapping
from utils.db import db


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
        kategori_id = data.get("kategori_id")
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
            is_active=True
        )

        db.session.add(mapping)
        db.session.commit()

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
            mapping.kategori_id = data["kategori_id"]
        if "priority" in data:
            mapping.priority = data["priority"]
        if "is_active" in data:
            mapping.is_active = data["is_active"]

        db.session.commit()

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

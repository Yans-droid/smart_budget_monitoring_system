from models.pr_po_data import PrPoData
from utils.db import db


class PrService:
    """
    CRUD dan query umum untuk PrPoData.
    """

    @staticmethod
    def get_all(upload_id=None, status_ai=None, tracking_stage=None, page=1, per_page=50):
        query = PrPoData.query

        if upload_id:
            query = query.filter(PrPoData.upload_id == upload_id)
        if status_ai:
            query = query.filter(PrPoData.status_ai == status_ai)
            
        if tracking_stage == "GR":
            query = query.filter(PrPoData.gr_legal_number.isnot(None))
        elif tracking_stage == "PO":
            query = query.filter(PrPoData.po_doc_num.isnot(None), PrPoData.gr_legal_number.is_(None))
        elif tracking_stage == "PR":
            query = query.filter(PrPoData.pr_doc_num.isnot(None), PrPoData.po_doc_num.is_(None), PrPoData.gr_legal_number.is_(None))

        pagination = query.order_by(PrPoData.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            "success": True,
            "data": [pr.to_dict() for pr in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages
        }, 200

    @staticmethod
    def get_by_id(pr_id: int):
        pr = db.session.get(PrPoData, pr_id)
        if not pr:
            return {"success": False, "message": "PR tidak ditemukan"}, 404
        return {"success": True, "data": pr.to_dict()}, 200

    @staticmethod
    def update_kategori(pr_id: int, kategori_id: int, user_id: int):
        """Manual override kategori oleh reviewer."""
        from datetime import datetime

        pr = db.session.get(PrPoData, pr_id)
        if not pr:
            return {"success": False, "message": "PR tidak ditemukan"}, 404

        pr.kategori_id_koreksi = kategori_id
        pr.direview_oleh = user_id
        pr.direview_at = datetime.utcnow()
        pr.perlu_review = False

        db.session.commit()

        return {
            "success": True,
            "message": "Kategori PR berhasil diupdate",
            "data": pr.to_dict()
        }, 200

    @staticmethod
    def get_summary_by_upload(upload_id: int):
        """Ringkasan status AI per upload."""
        from sqlalchemy import func

        rows = (
            db.session.query(PrPoData.status_ai, func.count(PrPoData.id))
            .filter(PrPoData.upload_id == upload_id)
            .group_by(PrPoData.status_ai)
            .all()
        )

        summary = {status: count for status, count in rows}

        return {
            "success": True,
            "upload_id": upload_id,
            "summary": summary
        }, 200

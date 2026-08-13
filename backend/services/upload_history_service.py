from datetime import datetime

from models.upload_history import UploadHistory
from utils.db import db
class UploadHistoryService:

    @staticmethod
    def get_all_upload_histories():
        return UploadHistory.query.order_by(
            UploadHistory.created_at.desc()
        ).all()

    @staticmethod
    def get_upload_history_by_id(upload_id):
        return db.session.get(UploadHistory, upload_id)

    @staticmethod
    def create_upload_history(data):

        user_id = data.get("user_id")
        original_filename = data.get("original_filename")
        stored_filename = data.get("stored_filename")
        total_data = data.get("total_data", 0)

        # validasi
        if not user_id:
            return {
                "success": False,
                "message": "user_id wajib diisi"
            }, 400

        if not original_filename:
            return {
                "success": False,
                "message": "original_filename wajib diisi"
            }, 400

        upload = UploadHistory(
            user_id=user_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            total_data=total_data,
            status="UPLOADING",
            uploaded_at=datetime.utcnow()
        )

        db.session.add(upload)
        db.session.commit()

        return {
            "success": True,
            "message": "Upload history berhasil dibuat",
            "data": upload.to_dict()
        }, 201

    @staticmethod
    def update_upload_history(upload_id, data):
        upload = db.session.get(UploadHistory, upload_id)

        if not upload:
            return {
                "success": False,
                "message": "Upload history tidak ditemukan"
            }, 404

        if "status" in data:
            allowed = ("UPLOADING", "SUCCESS", "FAILED")
            if data["status"] not in allowed:
                return {
                    "success": False,
                    "message": (
                        f"Status harus salah satu dari: "
                        f"{', '.join(allowed)}"
                    )
                }, 400
            upload.status = data["status"]

        if "total_data" in data:
            upload.total_data = data["total_data"]

        if "filename" in data:
            upload.filename = data["filename"]

        db.session.commit()

        return {
            "success": True,
            "message": "Upload history berhasil diupdate",
            "data": upload.to_dict()
        }, 200

    @staticmethod
    def delete_upload_history(upload_id):
        upload = db.session.get(UploadHistory, upload_id)

        from models.pr_po_data import PrPoData
        from models.mapping_log import MappingLog
        from models.klasifikasi_log import KlasifikasiLog
        
        if not upload:
            return {
                "success": False,
                "message": "Upload history tidak ditemukan"
            }, 404

        try:
            # Ambil semua id PR terkait
            pr_ids = [row.id for row in db.session.query(PrPoData.id).filter_by(upload_id=upload.id).all()]
            
            if pr_ids:
                # Hapus turunan pr_po_data secara berurutan
                db.session.query(MappingLog).filter(MappingLog.pr_po_data_id.in_(pr_ids)).delete(synchronize_session=False)
                db.session.query(KlasifikasiLog).filter(KlasifikasiLog.pr_po_data_id.in_(pr_ids)).delete(synchronize_session=False)
                
                # Hapus pr_po_data
                db.session.query(PrPoData).filter(PrPoData.upload_id == upload.id).delete(synchronize_session=False)

            # Terakhir hapus upload_history
            db.session.delete(upload)
            db.session.commit()
            
            return {
                "success": True,
                "message": "Upload history beserta data PR terkait berhasil dihapus permanen"
            }, 200
        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Gagal menghapus data: {str(e)}"
            }, 500
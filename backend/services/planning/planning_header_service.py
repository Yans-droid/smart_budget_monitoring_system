from models.planning_header import PlanningHeader
from utils.db import db

class PlanningHeaderService:
    @staticmethod
    def create_planning_header(data):
        periode = data.get('periode')
        user_id = data.get('user_id')
        filename = data.get('filename')
       
        if not periode:
            return {
                "success": False,
                "message":"periode wajib diisi"
            }, 400
        if not user_id:
            return {
                "success": False,
                "message": "user id wajib diisi"
            }, 400
        if not filename:
            return {
                "success": False,
                "message": "filename wajib diisi"
            }, 400

        planning = PlanningHeader(
            periode=periode,
            user_id=user_id,
            filename=filename,
            status="UPLOADING",
        )

        db.session.add(planning)
        db.session.flush()


        return {
            "success": True,
            "message": "Planning header berhasil dibuat",
            "data": planning.to_dict()
        }, 201


    @staticmethod
    def update_status(planning_header_id, status, commit=False):
        planning = db.session.get(PlanningHeader, planning_header_id)
        if not planning:
            return {
                "success": False,
                "message": "Planning header tidak ditemukan"
            }, 404

        allowed_status = (
            "UPLOADING",
            "SUCCES",
            "FAILED",
        )

        if status not in allowed_status:
            return {
                "success": False,
                "message": f"Status harus salah satu dari: {', '.join(allowed_status)}"
            }, 400

        planning.status = status

        if commit:
            db.session.commit()

        return {
            "success": True,
            "message": "Planning header berhasil diupdate",
            "data": planning.to_dict()
        }, 200

    @staticmethod
    def delete_planning_header(planning_header_id):
        from models.pr_po_data import PrPoData
        from models.planning_detail import PlanningDetail
        
        planning = db.session.get(PlanningHeader, planning_header_id)
        if not planning:
            return {
                "success": False,
                "message": "Planning header tidak ditemukan"
            }, 404

        # 1. Temukan semua ID planning_detail yang terkait
        detail_ids = db.session.query(PlanningDetail.id).filter(
            PlanningDetail.planning_header_id == planning_header_id
        ).all()
        detail_ids = [d[0] for d in detail_ids]

        # 2. Update pr_po_data yang mengacu ke detail-detail tersebut
        if detail_ids:
            prs = db.session.query(PrPoData).filter(
                PrPoData.planning_detail_id.in_(detail_ids)
            ).all()
            for pr in prs:
                pr.planning_detail_id = None
                pr.budget_status = None
                # Kembalikan status ke WAITING atau DONE (bergantung workflow), 
                # WAITING paling aman agar diproses ulang dari awal pipeline
                pr.status_ai = "WAITING"

        # 3. Hapus header (karena cascade="all, delete-orphan", detailnya juga akan terhapus)
        db.session.delete(planning)
        db.session.commit()

        return {
            "success": True,
            "message": "Planning berhasil dihapus"
        }, 200

from models.planning_detail import PlanningDetail
from utils.db import db

class PlanningDetailService:
    @staticmethod
    def create_planning_detail(data):
        planning_header_id = data.get("planning_header_id")
        kategori_id = data.get("kategori_id")
        month = data.get("month")
        item = data.get("item")
        planning_amount = data.get("planning_amount")
        remarks = data.get("remarks")

        if not planning_header_id:
            return {
                "success": False,
                "message": "planning header id wajib diisi"
            }, 400
        if not kategori_id:
            return {
                "success": False,
                "message": "kategori id wajib diisi"
            }, 400
        if not item:
            return {
                "success": False,
                "message": "item wajib diisi"
            }, 400
        if not planning_amount:
            return {
                "success": False,
                "message": "planning amount wajib diisi"
            }, 400
        
        planning_detail = PlanningDetail(
            planning_header_id=planning_header_id,
            kategori_id=kategori_id,
            month=month,
            item=item,
            planning_amount=planning_amount,
            remarks=remarks
        )
        
        db.session.add(planning_detail)
        
        return {
            "success": True,
            "message": "Planning detail berhasil dibuat",
            "data": planning_detail.to_dict()
        }, 201

    @staticmethod
    def get_by_header(planning_header_id):
        return PlanningDetail.query.filter_by(
            planning_header_id=planning_header_id
        ).all()

    @staticmethod
    def delete_by_header(planning_header_id):
        PlanningDetail.query.filter_by(
            planning_header_id=planning_header_id
        ).delete()
        db.session.commit()

        return {
            "success": True,
            "message": "Planning detail berhasil dihapus"
        }, 200

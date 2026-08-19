from datetime import datetime
from models.planning_header import PlanningHeader
from models.planning_detail import PlanningDetail
from utils.db import db
from utils.sanitize import to_int_or_none


class PlanningServices:

    @staticmethod
    def create_planning_header(data):

        periode = data.get('periode')
        user_id = data.get('user_id')
        filename = data.get('filename')
       
        if not periode:
            return{
                "success": False,
                "message":"periode wajib diisi"
            },400
        if not user_id:
            return{
                "success": False,
                "message": "user id wajib diisi"
            },400
        if not filename:
            return{
                "success": False,
                "message": "filename wajib diisi"
            },400


        planning = PlanningHeader(
            periode=periode,
            user_id=user_id,
            filename=filename,
            status="UPLOADING",
        )

        db.session.add(planning)
        db.session.commit()

        return{
            "success": True,
            "message": "Planning header berhasil dibuat",
            "data": planning.to_dict()
        },201


            
    @staticmethod
    def create_planning_detail(data):

        planning_header_id = to_int_or_none(data.get("planning_header_id"))
        kategori_id = to_int_or_none(data.get("kategori_id"))
        item = data.get("item")
        planning_amount = data.get("planning_amount")
        remarks = data.get("remarks")

        if not planning_header_id:
            return{
                "success": False,
                "message": "planning header id wajib diisi"
            },400
        
        if not kategori_id:
            return{
                "success": False,
                "message": "kategori id wajib diisi"
            },400
        if not item:
            return{
                "success": False,
                "message": "item wajib diisi"
            },400
        if not planning_amount:
            return{
                "success": False,
                "message": "planning amount wajib diisi"
            },400
        
        planning_detail = PlanningDetail(
            planning_header_id=planning_header_id,
            kategori_id=kategori_id,
            item=item,
            planning_amount=planning_amount,
            remarks=remarks
        )
        
        db.session.add(planning_detail)
        db.session.commit()
        
        return{
            "success": True,
            "message": "Planning detail berhasil dibuat",
            "data": planning_detail.to_dict()
        },201
        
    @staticmethod
    def upload_planning(file,user_id):
        file=request.files.get("file")
        user_id=request.form.get("user_id")
        
        
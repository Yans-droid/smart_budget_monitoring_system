from flask import Blueprint, request, jsonify
from services.planning.planning_upload_service import PlanningUploadService
from services.planning.planning_header_service import PlanningHeaderService
from services.planning.planning_detail_service import PlanningDetailService
from models.planning_header import PlanningHeader
from models.planning_detail import PlanningDetail
from utils.db import db

planning_bp = Blueprint("planning", __name__)


# ------------------------------------------------------------------
# Upload Planning Excel
# POST /api/v1/planning/upload
# ------------------------------------------------------------------
@planning_bp.route("/upload", methods=["POST"])
def upload_planning():
    file = request.files.get("file")
    user_id = request.form.get("user_id", 1)
    periode = request.form.get("periode")

    result, status = PlanningUploadService.upload_planning(
        file=file,
        user_id=user_id,
        periode=periode
    )
    return jsonify(result), status


# ------------------------------------------------------------------
# List semua PlanningHeader
# GET /api/v1/planning/?periode=&status=&page=&per_page=
# ------------------------------------------------------------------
@planning_bp.route("/", methods=["GET"])
def get_all_planning():
    periode = request.args.get("periode")
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = PlanningHeader.query

    if periode:
        query = query.filter(PlanningHeader.periode == periode)
    if status:
        query = query.filter(PlanningHeader.status == status)

    pagination = query.order_by(PlanningHeader.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "success": True,
        "data": [h.to_dict() for h in pagination.items],
        "total": pagination.total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages
    }), 200


# ------------------------------------------------------------------
# Detail satu PlanningHeader
# GET /api/v1/planning/<id>
# ------------------------------------------------------------------
@planning_bp.route("/<int:header_id>", methods=["GET"])
def get_planning_by_id(header_id):
    header = db.session.get(PlanningHeader, header_id)
    if not header:
        return jsonify({"success": False, "message": "Planning tidak ditemukan"}), 404

    return jsonify({
        "success": True,
        "data": header.to_dict()
    }), 200


# ------------------------------------------------------------------
# Delete satu PlanningHeader
# DELETE /api/v1/planning/<id>
# ------------------------------------------------------------------
@planning_bp.route("/<int:header_id>", methods=["DELETE"])
def delete_planning(header_id):
    result, status = PlanningHeaderService.delete_planning_header(header_id)
    return jsonify(result), status


# ------------------------------------------------------------------
# Detail list planning (per bulan & item)
# GET /api/v1/planning/<id>/details?month=&kategori_id=
# ------------------------------------------------------------------
@planning_bp.route("/<int:header_id>/details", methods=["GET"])
def get_planning_details(header_id):
    header = db.session.get(PlanningHeader, header_id)
    if not header:
        return jsonify({"success": False, "message": "Planning tidak ditemukan"}), 404

    month = request.args.get("month")
    kategori_id = request.args.get("kategori_id", type=int)

    query = PlanningDetail.query.filter_by(planning_header_id=header_id)

    if month:
        query = query.filter(PlanningDetail.month == month)
    if kategori_id:
        query = query.filter(PlanningDetail.kategori_id == kategori_id)

    details = query.order_by(PlanningDetail.month.asc(), PlanningDetail.item.asc()).all()

    return jsonify({
        "success": True,
        "planning_header": header.to_dict(),
        "total": len(details),
        "data": [d.to_dict() for d in details]
    }), 200
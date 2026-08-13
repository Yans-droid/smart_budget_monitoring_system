from flask import Blueprint, request, jsonify
from services.pr.pr_upload_service import PrUploadService
from services.pr.pr_service import PrService
from services.pipeline_service import PipelineService

pr_bp = Blueprint("pr", __name__)


# ------------------------------------------------------------------
# Upload Excel PR
# POST /api/v1/pr/upload
# ------------------------------------------------------------------
@pr_bp.route("/upload", methods=["POST"])
def upload_pr():
    file = request.files.get("file")
    user_id = request.form.get("user_id", 1)
    periode = request.form.get("periode")

    # Validasi input dasar
    if not file:
        return jsonify({"success": False, "message": "File wajib diisi"}), 400
    if not periode or not str(periode).strip():
        return jsonify({"success": False, "message": "Periode wajib diisi"}), 400
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "user_id harus berupa angka"}), 400

    result, status = PrUploadService.upload(
        file=file,
        user_id=user_id,
        periode=periode
    )
    return jsonify(result), status


# ------------------------------------------------------------------
# List PR (dengan filter & paginasi)
# GET /api/v1/pr/?upload_id=&status_ai=&page=&per_page=
# ------------------------------------------------------------------
@pr_bp.route("/", methods=["GET"])
def get_all():
    upload_id = request.args.get("upload_id", type=int)
    status_ai = request.args.get("status_ai")
    tracking_stage = request.args.get("tracking_stage")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    result, status = PrService.get_all(
        upload_id=upload_id,
        status_ai=status_ai,
        tracking_stage=tracking_stage,
        page=page,
        per_page=per_page
    )
    return jsonify(result), status


# ------------------------------------------------------------------
# Detail satu PR
# GET /api/v1/pr/<pr_id>
# ------------------------------------------------------------------
@pr_bp.route("/<int:pr_id>", methods=["GET"])
def get_by_id(pr_id):
    result, status = PrService.get_by_id(pr_id)
    return jsonify(result), status


# ------------------------------------------------------------------
# Manual override kategori (review)
# PUT /api/v1/pr/<pr_id>/kategori
# Body: { "kategori_id": 5, "user_id": 1 }
# ------------------------------------------------------------------
@pr_bp.route("/<int:pr_id>/kategori", methods=["PUT"])
def update_kategori(pr_id):
    data = request.get_json()
    kategori_id = data.get("kategori_id")
    user_id = data.get("user_id")

    if not kategori_id:
        return jsonify({"success": False, "message": "kategori_id wajib diisi"}), 400
    if not user_id:
        return jsonify({"success": False, "message": "user_id wajib diisi"}), 400

    result, status = PrService.update_kategori(pr_id, kategori_id, user_id)
    return jsonify(result), status


# ------------------------------------------------------------------
# Ringkasan status AI per upload
# GET /api/v1/pr/summary/<upload_id>
# ------------------------------------------------------------------
@pr_bp.route("/summary/<int:upload_id>", methods=["GET"])
def get_summary(upload_id):
    result, status = PrService.get_summary_by_upload(upload_id)
    return jsonify(result), status


# ------------------------------------------------------------------
# Trigger Batch Pipeline untuk Sprint 6
# POST /api/v1/pr/process_pipeline
# Body: { "periode": "2026" }
# ------------------------------------------------------------------
@pr_bp.route("/process_pipeline", methods=["POST"])
def process_pipeline():
    data = request.get_json()
    periode = data.get("periode") if data else None
    
    if not periode:
        return jsonify({"success": False, "message": "periode wajib diisi"}), 400
        
    result = PipelineService.process_all_waiting(periode)
    return jsonify(result), 200

# ------------------------------------------------------------------
# Retry Mapping Only (Untuk status NEED_MAPPING)
# POST /api/v1/pr/retry_mapping
# Body: { "periode": "2026" }
# ------------------------------------------------------------------
@pr_bp.route("/retry_mapping", methods=["POST"])
def retry_mapping():
    data = request.get_json()
    periode = data.get("periode") if data else None
    
    if not periode:
        return jsonify({"success": False, "message": "periode wajib diisi"}), 400
        
    result = PipelineService.retry_mapping_only(periode)
    return jsonify(result), 200

# ------------------------------------------------------------------
# Get Dashboard Summary Sprint 6
# GET /api/v1/pr/dashboard_summary?periode=2026
# ------------------------------------------------------------------
@pr_bp.route("/dashboard_summary", methods=["GET"])
def get_dashboard_summary():
    periode = request.args.get("periode")
    if not periode:
        return jsonify({"success": False, "message": "periode wajib diisi"}), 400
        
    result = PipelineService.get_dashboard_summary(periode)
    return jsonify(result), 200

@pr_bp.route("/dashboard_summary_monthly", methods=["GET"])
def get_dashboard_summary_monthly():
    periode = request.args.get("periode")
    if not periode:
        return jsonify({"success": False, "message": "periode wajib diisi"}), 400

    result = PipelineService.get_dashboard_summary_monthly(periode)
    return jsonify(result), 200

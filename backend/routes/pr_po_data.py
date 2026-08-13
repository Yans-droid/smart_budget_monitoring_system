from flask import Blueprint, jsonify, request

from services.pr_po_data_service import PrPoDataService

pr_po_data_bp = Blueprint(
    "pr_po_data",
    __name__
)


# GET / — semua data PR/PO (dengan paginasi & filter)
@pr_po_data_bp.route("/", methods=["GET"])
def get_all():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    upload_id = request.args.get("upload_id", type=int)
    status_ai = request.args.get("status_ai")
    perlu_review = request.args.get("perlu_review")
    budget_status = request.args.get("budget_status")
    search = request.args.get("search")              # server-side text search
    kategori_kode = request.args.get("kategori_kode")  # filter by category code
    metode = request.args.get("metode")              # filter by classification method

    # parse boolean
    if perlu_review is not None:
        perlu_review = perlu_review.lower() in ("true", "1", "yes")

    result = PrPoDataService.get_all(
        upload_id=upload_id,
        status_ai=status_ai,
        perlu_review=perlu_review,
        budget_status=budget_status,
        search=search,
        kategori_kode=kategori_kode,
        metode=metode,
        page=page,
        per_page=per_page
    )

    return jsonify({
        "success": True,
        **result
    }), 200


# GET /review-queue — data yang perlu review manual
@pr_po_data_bp.route("/review-queue", methods=["GET"])
def get_review_queue():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    result = PrPoDataService.get_review_queue(
        page=page,
        per_page=per_page
    )

    return jsonify({
        "success": True,
        **result
    }), 200


# GET /monthly-summary — data grafik bulanan
@pr_po_data_bp.route("/monthly-summary", methods=["GET"])
def get_monthly_summary():
    periode = request.args.get("periode")
    kode = request.args.get("kode")

    result = PrPoDataService.get_monthly_summary(
        periode=periode,
        kode=kode
    )

    return jsonify({
        "success": True,
        "data": result
    }), 200


# GET /upload/<upload_id> — data by upload batch
@pr_po_data_bp.route(
    "/upload/<int:upload_id>", methods=["GET"]
)
def get_by_upload(upload_id):
    records = PrPoDataService.get_by_upload_id(upload_id)

    return jsonify({
        "success": True,
        "total": len(records),
        "data": [r.to_dict() for r in records]
    }), 200


# GET /<id> — data by id
@pr_po_data_bp.route("/<int:data_id>", methods=["GET"])
def get_by_id(data_id):
    record = PrPoDataService.get_by_id(data_id)

    if record is None:
        return jsonify({
            "success": False,
            "message": "Data PR/PO tidak ditemukan"
        }), 404

    return jsonify({
        "success": True,
        "data": record.to_dict()
    }), 200


# POST / — simpan satu data PR/PO
@pr_po_data_bp.route("/", methods=["POST"])
def create():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body wajib diisi"
        }), 400

    result, status = PrPoDataService.create(data)
    return jsonify(result), status


# POST /bulk — simpan banyak data PR/PO sekaligus
@pr_po_data_bp.route("/bulk", methods=["POST"])
def create_bulk():
    data = request.get_json()

    if not data or not data.get("items"):
        return jsonify({
            "success": False,
            "message": "Field 'items' (array) wajib diisi"
        }), 400

    upload_id = data.get("upload_id")

    result, status = PrPoDataService.create_bulk(
        data["items"],
        upload_id=upload_id
    )

    return jsonify(result), status


# PUT /<id> — update data PR/PO
@pr_po_data_bp.route("/<int:data_id>", methods=["PUT"])
def update(data_id):
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body wajib diisi"
        }), 400

    result, status = PrPoDataService.update(data_id, data)
    return jsonify(result), status


# PUT /<id>/review — review & koreksi manual
@pr_po_data_bp.route(
    "/<int:data_id>/review", methods=["PUT"]
)
def review(data_id):
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body wajib diisi"
        }), 400

    result, status = PrPoDataService.review(data_id, data)
    return jsonify(result), status

# PUT /<id>/approve — setujui klasifikasi AI langsung tanpa ubah kategori
@pr_po_data_bp.route(
    "/<int:data_id>/approve", methods=["PUT"]
)
def approve(data_id):
    """
    Quick approve: setujui hasil klasifikasi AI apa adanya.
    Hanya set perlu_review=False dan catat siapa yang approve.
    Tidak mengubah kategori.
    """
    from utils.db import db
    from models.pr_po_data import PrPoData
    from datetime import datetime

    data = request.get_json() or {}
    direview_oleh = data.get("direview_oleh")

    record = db.session.get(PrPoData, data_id)
    if not record:
        return jsonify({"success": False, "message": "Data tidak ditemukan"}), 404

    record.perlu_review = False
    record.direview_oleh = direview_oleh
    record.direview_at = datetime.utcnow()
    # Metode tetap dipertahankan (REGEX / SVM / RULE_BASE)
    # Hanya jika admin benar-benar ganti kategori lewat Simpan Perubahan -> barulah jadi MANUAL

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Klasifikasi disetujui",
        "data": record.to_dict()
    }), 200


# DELETE /<id> — hapus data PR/PO individual
@pr_po_data_bp.route("/<int:data_id>", methods=["DELETE"])
def delete_pr(data_id):
    from utils.db import db
    from models.pr_po_data import PrPoData
    
    from models.mapping_log import MappingLog
    from models.klasifikasi_log import KlasifikasiLog

    pr = db.session.get(PrPoData, data_id)
    if not pr:
        return jsonify({"success": False, "message": "Data tidak ditemukan"}), 404
        
    try:
        # Hapus log turunan terlebih dahulu (Sequential hard delete)
        MappingLog.query.filter_by(pr_po_data_id=pr.id).delete()
        KlasifikasiLog.query.filter_by(pr_po_data_id=pr.id).delete()
        
        # Hapus data utamanya
        db.session.delete(pr)
        db.session.commit()
        return jsonify({"success": True, "message": "Berhasil menghapus data PR"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Gagal menghapus data: {str(e)}"}), 500

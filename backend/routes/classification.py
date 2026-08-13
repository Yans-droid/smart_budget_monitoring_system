from flask import Blueprint, request, jsonify

from services.classification_service import ClassificationService

classification_bp = Blueprint(
    "classification",
    __name__
)


@classification_bp.route("/classify", methods=["POST"])
def classify():
    """
    Klasifikasi satu teks.
    Body: { "text": "KALIBRASI TOHNICHI TORQUE WRENCH" }
    """
    data = request.get_json()

    if not data or not data.get("text"):
        return jsonify({
            "success": False,
            "message": "Field 'text' wajib diisi"
        }), 400

    result = ClassificationService.classify_single(data["text"])

    return jsonify({
        "success": True,
        "data": result
    }), 200


@classification_bp.route("/classify/bulk", methods=["POST"])
def classify_bulk():
    """
    Klasifikasi banyak teks sekaligus (tanpa simpan ke DB).
    Body: { "items": ["teks 1", "teks 2", ...] }
    """
    data = request.get_json()

    if not data or not data.get("items"):
        return jsonify({
            "success": False,
            "message": "Field 'items' (array of text) wajib diisi"
        }), 400

    items = data["items"]
    results = []

    for text in items:
        result = ClassificationService.classify_single(text)
        result["text"] = text
        results.append(result)

    return jsonify({
        "success": True,
        "total": len(results),
        "data": results
    }), 200


@classification_bp.route(
    "/classify/pr-po/<int:pr_po_data_id>",
    methods=["POST"]
)
def classify_pr_po(pr_po_data_id):
    """
    Klasifikasi satu record PrPoData dan simpan hasilnya.
    """
    result, status = ClassificationService.classify_and_save(
        pr_po_data_id
    )
    return jsonify(result), status


@classification_bp.route(
    "/classify/upload/<int:upload_id>",
    methods=["POST"]
)
def classify_upload(upload_id):
    """
    Klasifikasi semua record PrPoData dari satu upload batch.
    """
    result, status = ClassificationService.classify_by_upload_id(
        upload_id
    )
    return jsonify(result), status
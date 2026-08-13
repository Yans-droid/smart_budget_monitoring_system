from flask import Blueprint, jsonify, request

from services.upload_history_service import UploadHistoryService

upload_history_bp = Blueprint(
    "upload_history",
    __name__
)


# GET / — semua upload history
@upload_history_bp.route("/", methods=["GET"])
def get_upload_histories():

    upload_histories = UploadHistoryService.get_all_upload_histories()

    return jsonify({
        "success": True,
        "total": len(upload_histories),
        "data": [
            upload.to_dict()
            for upload in upload_histories
        ]
    }), 200


# GET /<id> — upload history by id
@upload_history_bp.route(
    "/<int:upload_history_id>", methods=["GET"]
)
def get_upload_history(upload_history_id):

    upload = UploadHistoryService.get_upload_history_by_id(
        upload_history_id
    )

    if upload is None:
        return jsonify({
            "success": False,
            "message": "Upload history tidak ditemukan"
        }), 404

    return jsonify({
        "success": True,
        "data": upload.to_dict()
    }), 200


# POST / — buat upload history baru
@upload_history_bp.route("/", methods=["POST"])
def create_upload_history():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body wajib diisi"
        }), 400

    result, status_code = UploadHistoryService.create_upload_history(
        data
    )

    return jsonify(result), status_code


# PUT /<id> — update upload history
@upload_history_bp.route(
    "/<int:upload_history_id>", methods=["PUT"]
)
def update_upload_history(upload_history_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body wajib diisi"
        }), 400

    result, status = UploadHistoryService.update_upload_history(
        upload_history_id,
        data
    )

    return jsonify(result), status


# DELETE /<id> — hapus upload history
@upload_history_bp.route(
    "/<int:upload_history_id>", methods=["DELETE"]
)
def delete_upload_history(upload_history_id):

    result, status = UploadHistoryService.delete_upload_history(
        upload_history_id
    )

    return jsonify(result), status
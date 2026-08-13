from flask import Blueprint, jsonify, request

from services.kategori_service import KategoriService

kategori_bp = Blueprint(
    "kategori",
    __name__
)


# GET / — semua kategori
@kategori_bp.route("/", methods=["GET"])
def get_kategoris():
    kategoris = KategoriService.get_all()

    return jsonify({
        "success": True,
        "total": len(kategoris),
        "data": [k.to_dict() for k in kategoris]
    }), 200


# GET /<id> — kategori by id
@kategori_bp.route("/<int:kategori_id>", methods=["GET"])
def get_kategori(kategori_id):
    kategori = KategoriService.get_by_id(kategori_id)

    if kategori is None:
        return jsonify({
            "success": False,
            "message": "Kategori tidak ditemukan"
        }), 404

    return jsonify({
        "success": True,
        "data": kategori.to_dict()
    }), 200


# GET /kode/<kode> — kategori by kode
@kategori_bp.route("/kode/<string:kode>", methods=["GET"])
def get_kategori_by_kode(kode):
    kategori = KategoriService.get_by_kode(kode)

    if kategori is None:
        return jsonify({
            "success": False,
            "message": f"Kategori dengan kode '{kode}' tidak ditemukan"
        }), 404

    return jsonify({
        "success": True,
        "data": kategori.to_dict()
    }), 200


# POST / — buat kategori baru
@kategori_bp.route("/", methods=["POST"])
def create_kategori():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body wajib diisi"
        }), 400

    result, status = KategoriService.create(data)
    return jsonify(result), status


# PUT /<id> — update kategori
@kategori_bp.route("/<int:kategori_id>", methods=["PUT"])
def update_kategori(kategori_id):
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body wajib diisi"
        }), 400

    result, status = KategoriService.update(kategori_id, data)
    return jsonify(result), status


# DELETE /<id> — hapus kategori
@kategori_bp.route("/<int:kategori_id>", methods=["DELETE"])
def delete_kategori(kategori_id):

    result, status = KategoriService.delete(kategori_id)
    return jsonify(result), status

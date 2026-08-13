from flask import Blueprint, jsonify, request

from services.user_service import UserService

user_bp = Blueprint(
    "user",
    __name__
)


# POST /login — autentikasi user
@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body wajib diisi"
        }), 400

    username = data.get("username")
    password = data.get("password")

    result, status = UserService.authenticate(username, password)
    return jsonify(result), status


# GET / — semua user
@user_bp.route("/", methods=["GET"])
def get_users():

    users = UserService.get_all_users()

    return jsonify({
        "success": True,
        "total": len(users),
        "data": [user.to_dict() for user in users]
    }), 200


# GET /<id> — user by id
@user_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):

    user = UserService.get_by_id(user_id)

    if user is None:
        return jsonify({
            "success": False,
            "message": "User tidak ditemukan"
        }), 404

    return jsonify({
        "success": True,
        "data": user.to_dict()
    }), 200


# POST / — buat user baru
@user_bp.route("/", methods=["POST"])
def create_user():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body wajib diisi"
        }), 400

    result, status = UserService.create_user(data)
    return jsonify(result), status


# PUT /<id> — update user
@user_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body wajib diisi"
        }), 400

    result, status = UserService.update_user(user_id, data)
    return jsonify(result), status


# DELETE /<id> — hapus user
@user_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):

    result, status = UserService.delete_user(user_id)
    return jsonify(result), status
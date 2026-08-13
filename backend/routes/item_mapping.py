from flask import Blueprint, request, jsonify
from services.mapping.item_mapping_service import ItemMappingService

item_mapping_bp = Blueprint("item_mapping", __name__)


@item_mapping_bp.route("/", methods=["GET"])
def get_all():
    result, status = ItemMappingService.get_all()
    return jsonify(result), status


@item_mapping_bp.route("/<int:mapping_id>", methods=["GET"])
def get_by_id(mapping_id):
    result, status = ItemMappingService.get_by_id(mapping_id)
    return jsonify(result), status


@item_mapping_bp.route("/", methods=["POST"])
def create():
    data = request.get_json()
    result, status = ItemMappingService.create(data)
    return jsonify(result), status


@item_mapping_bp.route("/<int:mapping_id>", methods=["PUT"])
def update(mapping_id):
    data = request.get_json()
    result, status = ItemMappingService.update(mapping_id, data)
    return jsonify(result), status


@item_mapping_bp.route("/<int:mapping_id>", methods=["DELETE"])
def delete(mapping_id):
    result, status = ItemMappingService.delete(mapping_id)
    return jsonify(result), status

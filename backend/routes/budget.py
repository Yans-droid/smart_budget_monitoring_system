from flask import Blueprint, jsonify, request

from services.budget_service import BudgetService

budget_bp = Blueprint(
    "budget",
    __name__
)


# GET /summary — ringkasan dashboard
@budget_bp.route("/summary", methods=["GET"])
def get_summary():
    periode = request.args.get("periode")

    summary = BudgetService.get_summary(periode=periode)

    return jsonify({
        "success": True,
        "data": summary
    }), 200


# GET / — semua budget
@budget_bp.route("/", methods=["GET"])
def get_all_budgets():
    periode = request.args.get("periode")

    budgets = BudgetService.get_all_budgets(periode=periode)

    return jsonify({
        "success": True,
        "total": len(budgets),
        "data": [b.to_dict() for b in budgets]
    }), 200


# GET /<id> — budget by id
@budget_bp.route("/<int:budget_id>", methods=["GET"])
def get_budget_by_id(budget_id):

    budget = BudgetService.get_budget_by_id(budget_id)

    if budget is None:
        return jsonify({
            "success": False,
            "message": "Budget tidak ditemukan"
        }), 404

    return jsonify({
        "success": True,
        "data": budget.to_dict()
    }), 200


# POST / — buat budget baru
@budget_bp.route("/", methods=["POST"])
def create_budget():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body wajib diisi"
        }), 400

    result, status = BudgetService.create_budget(data)
    return jsonify(result), status


# PUT /<id> — update budget
@budget_bp.route("/<int:budget_id>", methods=["PUT"])
def update_budget(budget_id):
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body wajib diisi"
        }), 400

    result, status = BudgetService.update_budget(budget_id, data)
    return jsonify(result), status


# DELETE /<id> — hapus budget
@budget_bp.route("/<int:budget_id>", methods=["DELETE"])
def delete_budget(budget_id):

    result, status = BudgetService.delete_budget(budget_id)
    return jsonify(result), status

# DELETE /periode/<periode> — hapus semua budget untuk satu periode
@budget_bp.route("/periode/<periode>", methods=["DELETE"])
def delete_budget_by_periode(periode):
    result, status = BudgetService.delete_by_periode(periode)
    return jsonify(result), status
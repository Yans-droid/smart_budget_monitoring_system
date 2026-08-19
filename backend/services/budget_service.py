from decimal import Decimal

from sqlalchemy import func, extract

from models.budget import Budget
from models.kategori import Kategori
from models.pr_po_data import PrPoData
from utils.db import db
from utils.sanitize import to_int_or_none


class BudgetService:

    @staticmethod
    def get_budget_by_id(budget_id):
        return db.session.get(Budget, budget_id)

    @staticmethod
    def get_all_budgets(periode=None):
        query = Budget.query

        if periode:
            query = query.filter_by(periode=periode)

        return query.order_by(Budget.id).all()

    @staticmethod
    def create_budget(data):
        kategori_id = to_int_or_none(data.get("kategori_id"))
        periode = data.get("periode")
        nominal = data.get("nominal")
        created_by = to_int_or_none(data.get("created_by"))
        upload_id = to_int_or_none(data.get("upload_id"))

        if not kategori_id:
            return {
                "success": False,
                "message": "kategori_id wajib diisi"
            }, 400

        if not periode:
            return {
                "success": False,
                "message": "periode wajib diisi"
            }, 400

        if nominal is None:
            return {
                "success": False,
                "message": "nominal wajib diisi"
            }, 400

        # cek kategori ada
        kategori = db.session.get(Kategori, kategori_id)
        if not kategori:
            return {
                "success": False,
                "message": "Kategori tidak ditemukan"
            }, 404

        # cek duplikat (kategori + periode unik)
        existing = Budget.query.filter_by(
            kategori_id=kategori_id,
            periode=periode
        ).first()
        if existing:
            existing.nominal = Decimal(str(nominal))
            existing.upload_id = upload_id
            db.session.commit()
            return {
                "success": True,
                "message": "Budget berhasil diupdate",
                "data": existing.to_dict()
            }, 200

        budget = Budget(
            kategori_id=kategori_id,
            periode=periode,
            nominal=Decimal(str(nominal)),
            created_by=created_by,
            upload_id=upload_id
        )

        db.session.add(budget)
        db.session.commit()

        return {
            "success": True,
            "message": "Budget berhasil dibuat",
            "data": budget.to_dict()
        }, 201

    @staticmethod
    def update_budget(budget_id, data):
        budget = db.session.get(Budget, budget_id)
        if not budget:
            return {
                "success": False,
                "message": "Budget tidak ditemukan"
            }, 404

        if "nominal" in data:
            budget.nominal = Decimal(str(data["nominal"]))

        if "periode" in data:
            budget.periode = data["periode"]

        if "kategori_id" in data:
            kat_id = to_int_or_none(data["kategori_id"])
            if not kat_id:
                return {
                    "success": False,
                    "message": "kategori_id tidak valid"
                }, 400
            kategori = db.session.get(Kategori, kat_id)
            if not kategori:
                return {
                    "success": False,
                    "message": "Kategori tidak ditemukan"
                }, 404
            budget.kategori_id = kat_id

        db.session.commit()

        return {
            "success": True,
            "message": "Budget berhasil diupdate",
            "data": budget.to_dict()
        }, 200

    @staticmethod
    def delete_budget(budget_id):
        budget = db.session.get(Budget, budget_id)
        if not budget:
            return {
                "success": False,
                "message": "Budget tidak ditemukan"
            }, 404

        db.session.delete(budget)
        db.session.commit()

        return {
            "success": True,
            "message": "Budget berhasil dihapus"
        }, 200

    @staticmethod
    def delete_by_periode(periode):
        if not periode:
            return {
                "success": False,
                "message": "Periode tidak valid"
            }, 400

        budgets = Budget.query.filter_by(periode=periode).all()
        if not budgets:
            return {
                "success": False,
                "message": "Tidak ada budget pada periode tersebut"
            }, 404

        for b in budgets:
            db.session.delete(b)
        db.session.commit()

        return {
            "success": True,
            "message": f"Berhasil menghapus {len(budgets)} budget untuk periode {periode}"
        }, 200

    @staticmethod
    def get_summary(periode=None):
        """
        Ringkasan budget untuk dashboard.
        Mengembalikan total budget vs actual per tipe (CAPEX/OPEX)
        dan per kategori (E-1, E-9, I-1, dll).
        """
        kategoris = Kategori.query.all()
        
        # Ambil semua budget di periode ini
        budget_query = (
            db.session.query(
                Kategori.kode,
                Budget.nominal
            )
            .join(Kategori, Budget.kategori_id == Kategori.id)
        )
        if periode:
            budget_query = budget_query.filter(
                Budget.periode == periode
            )

        budget_rows = budget_query.all()
        budget_map = {row.kode: float(row.nominal) for row in budget_rows}

        # Hitung actual (total_price) dari pr_po_data
        # yang sudah berhasil diklasifikasi (status_ai = DONE)
        actual_query = (
            db.session.query(
                Kategori.kode,
                func.coalesce(
                    func.sum(PrPoData.total_price), 0
                ).label("actual")
            )
            .join(Kategori, PrPoData.kategori_id == Kategori.id)
            .filter(PrPoData.status_ai == "DONE")
        )
        if periode:
            actual_query = actual_query.filter(
                extract('year', PrPoData.request_date) == int(periode)
            )

        actual_rows = actual_query.group_by(Kategori.kode).all()
        actual_map = {row.kode: float(row.actual) for row in actual_rows}

        # Bangun summary per kategori
        items = []

        for kat in kategoris:
            if kat.kode in budget_map or kat.kode in actual_map:
                budget_val = budget_map.get(kat.kode, 0)
                actual_val = actual_map.get(kat.kode, 0)
                saldo = budget_val - actual_val

                items.append({
                    "kode": kat.kode,
                    "nama": kat.nama,
                    "tipe_formulir": kat.tipe_formulir,
                    "budget": budget_val,
                    "actual": actual_val,
                    "saldo": saldo,
                    "is_over": saldo < 0,
                })

        # Summary per tipe
        capex_item = next((i for i in items if i["kode"] == "CAPEX"), None)
        opex_item = next((i for i in items if i["kode"] == "OPEX"), None)
        
        capex_budget = capex_item["budget"] if capex_item else sum(
            i["budget"] for i in items
            if i["tipe_formulir"] == "CAPEX" and i["kode"] != "CAPEX"
        )
        capex_actual = sum(
            i["actual"] for i in items
            if i["tipe_formulir"] == "CAPEX"
        )
        
        opex_budget = opex_item["budget"] if opex_item else sum(
            i["budget"] for i in items
            if i["tipe_formulir"] == "OPEX" and i["kode"] != "OPEX"
        )
        opex_actual = sum(
            i["actual"] for i in items
            if i["tipe_formulir"] == "OPEX"
        )

        total_budget = capex_budget + opex_budget
        total_actual = capex_actual + opex_actual

        over_count = sum(1 for i in items if i["is_over"])

        return {
            "periode": periode,
            "total_budget": total_budget,
            "total_actual": total_actual,
            "total_saldo": total_budget - total_actual,
            "over_count": over_count,
            "capex": {
                "budget": capex_budget,
                "actual": capex_actual,
                "saldo": capex_budget - capex_actual,
            },
            "opex": {
                "budget": opex_budget,
                "actual": opex_actual,
                "saldo": opex_budget - opex_actual,
            },
            "items": items,
        }
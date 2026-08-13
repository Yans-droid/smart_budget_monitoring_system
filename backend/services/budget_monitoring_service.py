from decimal import Decimal
from models.pr_po_data import PrPoData
from models.planning_detail import PlanningDetail
from utils.db import db
from sqlalchemy import func

class BudgetMonitoringService:

    @staticmethod
    def recalculate_planning_status(planning_detail_id):
        """
        Hitung ulang status_realisasi pada PlanningDetail berdasarkan
        semua PR yang di-mapping ke item tersebut.

          OPEN   — belum ada PR yang mapping ke item ini
          PROSES — ada minimal satu PR yang belum selesai (po_status / gr_legal_number masih NULL)
          CLOSED — semua PR yang mapping sudah punya GR & PO
        """
        if not planning_detail_id:
            return

        detail = db.session.get(PlanningDetail, planning_detail_id)
        if not detail:
            return

        linked_prs = PrPoData.query.filter_by(planning_detail_id=planning_detail_id).all()

        if not linked_prs:
            detail.status_realisasi = 'OPEN'
        elif any(pr.procurement_status not in ('GOODS_RECEIVED', 'COMPLETED') for pr in linked_prs):
            detail.status_realisasi = 'PROSES'
        else:
            detail.status_realisasi = 'CLOSED'
        # commit dilakukan oleh caller

    @staticmethod
    def calculate_budget_consumption(pr_po_data: PrPoData) -> dict:
        """
        Menghitung konsumsi anggaran untuk PR/PO yang sudah di-MATCHED ke sebuah planning_detail.
        Rumus:
        Remaining = Planning Amount - Used Amount
        """
        if not pr_po_data.planning_detail_id:
            return {"success": False, "message": "PR belum di-MATCHED ke planning_detail"}

        planning_detail = db.session.get(PlanningDetail, pr_po_data.planning_detail_id)
        if not planning_detail:
            return {"success": False, "message": "Planning detail tidak ditemukan"}

        # Hitung Used Amount: Jumlah semua PR/PO yang ON_PLAN atau OVER_PLAN
        # (sudah fix memotong budget) untuk planning_detail ini
        used_amount = (
            db.session.query(func.coalesce(func.sum(PrPoData.total_price), 0))
            .filter(
                PrPoData.planning_detail_id == planning_detail.id,
                PrPoData.budget_status.in_(["ON_PLAN", "OVER_PLAN"]),
                PrPoData.id != pr_po_data.id  # Kecualikan PR yang sedang diproses
            )
            .scalar()
        ) or Decimal("0")

        planning_amount = planning_detail.planning_amount or Decimal("0")
        current_pr_amount = pr_po_data.total_price or Decimal("0")

        remaining_before_pr = planning_amount - Decimal(str(used_amount))
        remaining_after_pr = remaining_before_pr - Decimal(str(current_pr_amount))

        # Tentukan status akhir
        if remaining_after_pr < 0:
            final_status = "OVER_PLAN"
        else:
            final_status = "ON_PLAN"  # Tepat 0 atau masih ada sisa = On plan

        pr_po_data.budget_status = final_status

        # Update status_realisasi planning_detail setiap kali ada PR yang di-map
        BudgetMonitoringService.recalculate_planning_status(pr_po_data.planning_detail_id)

        db.session.commit()

        return {
            "success": True,
            "planning_amount": float(planning_amount),
            "used_amount": float(used_amount),
            "current_pr_amount": float(current_pr_amount),
            "remaining_before": float(remaining_before_pr),
            "remaining_after": float(remaining_after_pr),
            "final_status": final_status
        }

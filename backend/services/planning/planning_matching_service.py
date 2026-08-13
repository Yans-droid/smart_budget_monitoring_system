"""
Planning Matching Engine — Sprint 4
=====================================

Flow:
    PR Upload (PrPoData)
        │  description + kategori_id + periode + month
        ▼
    match_pr_to_planning_item()
        │  ItemMappingService.find_mapping → planning_item
        │  Jika tidak ditemukan → OOP
        ▼
    find_active_planning()
        │  Cari PlanningDetail (exact match: periode, month, kategori, item)
        │  Jika tidak ada → OOP
        ▼
    calculate_budget_consumption()
        │  planning_amount, used_amount, remaining_amount
        ▼
    generate_status()
        │  PLANNING / OVER_PLAN / OOP
        ▼
    Result
"""

from decimal import Decimal
from models.pr_po_data import PrPoData
from models.planning_detail import PlanningDetail
from models.planning_header import PlanningHeader
from services.mapping.item_mapping_service import ItemMappingService
from utils.db import db
from sqlalchemy import func


class PlanningMatchingService:

    # ------------------------------------------------------------------
    # Method 1: PR Description → Planning Item (via ItemMapping)
    # ------------------------------------------------------------------
    @staticmethod
    def match_pr_to_planning_item(description: str, kategori_id=None) -> str | None:
        """
        Ubah deskripsi PR menjadi planning_item menggunakan item_mapping.
        Return planning_item (str) atau None jika tidak ada mapping.
        """
        if not description:
            return None

        return ItemMappingService.find_mapping(
            keyword=description,
            kategori_id=kategori_id
        )

    # ------------------------------------------------------------------
    # Method 2: Cari PlanningDetail yang aktif (exact match, index-friendly)
    # ------------------------------------------------------------------
    @staticmethod
    def find_active_planning(
        planning_item: str,
        periode: str,
        month: str,
        kategori_id=None
    ) -> PlanningDetail | None:
        """
        Cari PlanningDetail yang cocok secara exact match (=) berdasarkan:
        - planning_item (item)
        - periode (dari PlanningHeader)
        - month
        - kategori_id (opsional)

        Menggunakan = bukan LIKE agar query memanfaatkan index database.
        """
        query = (
            db.session.query(PlanningDetail)
            .join(PlanningHeader, PlanningDetail.planning_header_id == PlanningHeader.id)
            .filter(
                PlanningHeader.periode == periode,
                PlanningHeader.status == "SUCCES",
                PlanningDetail.month == month,
                PlanningDetail.item == planning_item
            )
        )

        if kategori_id:
            query = query.filter(PlanningDetail.kategori_id == kategori_id)

        return query.first()

    # ------------------------------------------------------------------
    # Method 3: Hitung Budget Consumption
    # ------------------------------------------------------------------
    @staticmethod
    def calculate_budget_consumption(
        planning_detail: PlanningDetail,
        current_pr_amount: Decimal
    ) -> dict:
        """
        Hitung konsumsi anggaran berdasarkan PlanningDetail.

        used_amount = total_price PR lain yang sudah matched ke planning_detail ini
                      (berdasarkan kategori + item + month yang sama, status DONE)
        remaining_amount = planning_amount - used_amount
        """
        # Sum total PR yang sudah digunakan untuk planning_detail ini
        used_amount = (
            db.session.query(func.coalesce(func.sum(PrPoData.total_price), 0))
            .filter(
                PrPoData.kategori_id == planning_detail.kategori_id,
                PrPoData.status_ai == "DONE"
            )
            .scalar()
        ) or Decimal("0")

        planning_amount = planning_detail.planning_amount or Decimal("0")
        remaining_amount = planning_amount - Decimal(str(used_amount))
        after_this_pr = remaining_amount - Decimal(str(current_pr_amount))

        return {
            "planning_detail_id": planning_detail.id,
            "planning_amount": float(planning_amount),
            "used_amount": float(used_amount),
            "remaining_amount": float(remaining_amount),
            "current_pr_amount": float(current_pr_amount),
            "remaining_after_pr": float(after_this_pr)
        }

    # ------------------------------------------------------------------
    # Method 4: Generate Status Akhir
    # ------------------------------------------------------------------
    @staticmethod
    def generate_status(
        planning_item: str | None,
        planning_detail: PlanningDetail | None,
        budget: dict | None
    ) -> str:
        """
        Tentukan status akhir berdasarkan hasil matching dan budget.

        - OOP       : tidak ada mapping ATAU tidak ada planning aktif
        - OVER_PLAN : ada planning, tapi sisa anggaran tidak cukup
        - PLANNING  : ada planning dan anggaran masih mencukupi
        """
        if not planning_item or not planning_detail:
            return "OOP"

        if budget and budget["remaining_after_pr"] < 0:
            return "OVER_PLAN"

        return "PLANNING"

    # ------------------------------------------------------------------
    # Full Flow: Proses satu PrPoData
    # ------------------------------------------------------------------
    @staticmethod
    def process_pr(pr: PrPoData, periode: str) -> dict:
        """
        Jalankan full matching engine untuk satu PR.
        """
        pr_amount = pr.total_price or Decimal("0")

        # Step 1: Description → Planning Item
        planning_item = PlanningMatchingService.match_pr_to_planning_item(
            description=pr.description,
            kategori_id=pr.kategori_id
        )

        # Extract month dari request_date — format Indonesia sesuai DB (Jan, Agu, Okt, dst)
        _MONTH_ID = {
            "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "Mei", "06": "Jun",
            "07": "Jul", "08": "Agu", "09": "Sep", "10": "Okt", "11": "Nov", "12": "Des"
        }
        month = None
        if pr.request_date:
            month = _MONTH_ID.get(pr.request_date.strftime("%m"))

        # Step 2: Cari Planning Detail aktif
        planning_detail = None
        if planning_item and month:
            planning_detail = PlanningMatchingService.find_active_planning(
                planning_item=planning_item,
                periode=periode,
                month=month,
                kategori_id=pr.kategori_id
            )

        # Step 3: Hitung budget consumption
        budget = None
        if planning_detail:
            budget = PlanningMatchingService.calculate_budget_consumption(
                planning_detail=planning_detail,
                current_pr_amount=pr_amount
            )

        # Step 4: Generate status
        status = PlanningMatchingService.generate_status(
            planning_item=planning_item,
            planning_detail=planning_detail,
            budget=budget
        )

        return {
            "pr_id": pr.id,
            "pr_doc_num": pr.pr_doc_num,
            "description": pr.description,
            "kategori_id": pr.kategori_id,
            "month": month,
            "periode": periode,
            "planning_item": planning_item,
            "planning_detail_id": planning_detail.id if planning_detail else None,
            "budget": budget,
            "final_status": status
        }

    # ------------------------------------------------------------------
    # Batch: Proses banyak PR sekaligus
    # ------------------------------------------------------------------
    @staticmethod
    def run_batch(pr_ids: list, periode: str) -> dict:
        """
        Jalankan matching engine untuk batch PR ID.
        """
        pr_list = PrPoData.query.filter(PrPoData.id.in_(pr_ids)).all()

        results = []
        summary = {"PLANNING": 0, "OVER_PLAN": 0, "OOP": 0}

        for pr in pr_list:
            result = PlanningMatchingService.process_pr(pr, periode)
            results.append(result)
            summary[result["final_status"]] = summary.get(result["final_status"], 0) + 1

        return {
            "success": True,
            "periode": periode,
            "total_pr": len(pr_list),
            "summary": summary,
            "results": results
        }, 200

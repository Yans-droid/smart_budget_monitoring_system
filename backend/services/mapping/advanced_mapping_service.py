import re
import time
from rapidfuzz import fuzz, process
from rapidfuzz.utils import default_process
from utils.db import db
from models.item_mapping import ItemMapping
from models.planning_detail import PlanningDetail
from models.planning_header import PlanningHeader
from models.mapping_log import MappingLog
from models.pr_po_data import PrPoData


class AdvancedMappingService:

    @staticmethod
    def extract_periode(pr_doc_num):
        """
        Ekstrak TAHUN dari pr_doc_num format SAI/PR/YYMM####
        Contoh: SAI/PR/26010001 -> '2026'
        Karena planning_header.periode disimpan sebagai tahun penuh.
        """
        if not pr_doc_num:
            return None

        match = re.search(r"SAI/PR/(\d{2})(\d{2})", pr_doc_num)
        if match:
            yy = match.group(1)
            return f"20{yy}"
        return None

    @staticmethod
    def extract_code(text):
        """Ambil kode/part number: angka di dalam kurung, atau kode alfanumerik di akhir teks."""
        if not text:
            return None
        # Pola 1: angka/kode di dalam kurung, misal "(0117020)" atau "(003)"
        match = re.search(r'\(([A-Za-z0-9\-]+)\)', text)
        if match:
            return match.group(1).upper()
        # Pola 2: kode di akhir teks tanpa kurung, misal "MSTP6-20"
        match = re.search(r'\b([A-Z]{2,}\d+[\-A-Z0-9]*)\b', text.upper())
        if match:
            return match.group(1)
        return None

    @staticmethod
    def run_mapping(pr: PrPoData):
        start_time = time.time()

        # 1. Ekstrak tahun dari pr_doc_num
        periode = AdvancedMappingService.extract_periode(pr.pr_doc_num)
        if not periode:
            pr.status_ai = "NEED_MAPPING"
            db.session.commit()
            return {"success": False, "message": "Gagal ekstrak periode dari pr_doc_num", "status": "NEED_MAPPING"}

        # Cari planning_header yang sesuai
        header = PlanningHeader.query.filter_by(periode=periode, status="SUCCES").first()
        if not header:
            pr.status_ai = "NEED_MAPPING"
            db.session.commit()
            return {"success": False, "message": f"Tidak ada planning aktif untuk periode {periode}", "status": "NEED_MAPPING"}

        # 2. Ekstrak bulan dari request_date menggunakan format English abbreviated (%b)
        #    Contoh: datetime(2026, 8, 1) -> 'Aug'
        month = pr.request_date.strftime("%b") if pr.request_date else None
        print(f"DEBUG [PR#{pr.id}] request_date={pr.request_date} -> month='{month}'")
        print(f"DEBUG [PR#{pr.id}] periode='{periode}' header_id={header.id} kategori_id={pr.kategori_id}")

        if not month:
            pr.status_ai = "NEED_MAPPING"
            db.session.commit()
            return {"success": False, "message": "Tidak bisa ekstrak bulan dari request_date", "status": "NEED_MAPPING"}

        # Cek nilai month yang ada di DB untuk header ini
        existing_months = [pd.month for pd in PlanningDetail.query.filter_by(planning_header_id=header.id).all()]
        print(f"DEBUG [PR#{pr.id}] months di DB untuk header {header.id}: {list(set(existing_months))}")

        # 3. Coba item_mapping (rule-based)
        description = pr.description or ""
        comment_text = pr.comment_text or ""
        search_text = f"{description} {comment_text}"

        rules = ItemMapping.query.filter_by(is_active=True).order_by(ItemMapping.priority.asc()).all()
        valid_rules = [r for r in rules if r.kategori_id == pr.kategori_id or r.kategori_id is None]

        matched_planning_item = None
        for rule in valid_rules:
            if re.search(rule.keyword, search_text, re.IGNORECASE):
                matched_planning_item = rule.planning_item
                break

        print(f"DEBUG [PR#{pr.id}] desc='{description[:60]}' -> matched_planning_item='{matched_planning_item}'")

        # 4. Kalau rule ketemu -> cari planning_detail persis (+ filter bulan)
        if matched_planning_item:
            exact_detail = PlanningDetail.query.filter_by(
                planning_header_id=header.id,
                item=matched_planning_item,
                month=month
            ).first()
            print(f"DEBUG [PR#{pr.id}] exact_detail (rule) = {exact_detail}")

            if exact_detail:
                # Sinkronkan kategori PR mengikuti kategori resmi dari Planning,
                # karena rule keyword ini sudah jadi otoritas final
                if pr.kategori_id != exact_detail.kategori_id:
                    pr.kategori_id_koreksi = pr.kategori_id
                pr.kategori_id = exact_detail.kategori_id
                pr.planning_detail_id = exact_detail.id
                pr.status_ai = "DONE"

                proc_time = time.time() - start_time
                log = MappingLog(
                    pr_po_data_id=pr.id,
                    method="ITEM_MAPPING_RULE",
                    planning_detail_hasil_id=exact_detail.id,
                    confidence_score=1.0,
                    is_selected=True,
                    processing_time=proc_time
                )
                db.session.add(log)
                db.session.commit()
                return {"success": True, "message": "Mapped via Rule", "status": "DONE"}

        # Bersihkan log FUZZY lama untuk PR ini jika ada
        MappingLog.query.filter_by(pr_po_data_id=pr.id, method="FUZZY_MATCH").delete()

        # 5. Fuzzy matching — Coba bulan yang sama dulu
        candidates = PlanningDetail.query.filter_by(
            planning_header_id=header.id,
            kategori_id=pr.kategori_id,
            month=month
        ).all()

        pr_reg_num = AdvancedMappingService.extract_code(description)
        print(f"DEBUG [PR#{pr.id}] Code diekstrak: {pr_reg_num}")

        # Fungsi helper untuk fuzzy match + adjustment score
        def get_adjusted_fuzzy_results(choices_dict, limit=15):
            raw_results = process.extract(
                description,
                choices_dict,
                scorer=fuzz.token_set_ratio,
                processor=default_process,
                limit=limit
            )
            adjusted = []
            for item_name, score, detail_id in raw_results:
                new_score = score
                # Jika PR punya reg num, dan item kandidat juga punya reg num yang sama persis
                if pr_reg_num:
                    cand_reg = AdvancedMappingService.extract_code(item_name)
                    if cand_reg == pr_reg_num:
                        # Kasih bobot prioritas besar
                        new_score = min(100.0, score + 40.0)
                adjusted.append((item_name, new_score, detail_id))
            # Sort ulang berdasarkan score baru
            adjusted.sort(key=lambda x: x[1], reverse=True)
            return adjusted[:5]

        final_results = []
        cross_month = False

        if candidates:
            choices = {c.id: c.item for c in candidates}
            results = get_adjusted_fuzzy_results(choices)
            # Jika skor tertinggi lumayan bagus (>= 65), gunakan hasil ini
            if results and results[0][1] >= 65.0:
                final_results = results

        # Fallback: jika tidak ada kandidat di bulan yang sama, ATAU skor terbaik sangat rendah (< 65)
        # Cari di seluruh bulan tapi HILANGKAN DUPLIKAT NAMA
        if not final_results:
            cross_month = True
            all_candidates = PlanningDetail.query.filter_by(
                planning_header_id=header.id,
                kategori_id=pr.kategori_id
            ).all()

            unique_choices = {}
            seen_items = set()
            for c in all_candidates:
                normalized_name = c.item.strip().upper()
                if normalized_name not in seen_items:
                    seen_items.add(normalized_name)
                    unique_choices[c.id] = c.item

            if unique_choices:
                final_results = get_adjusted_fuzzy_results(unique_choices)

        print(f"DEBUG [PR#{pr.id}] fuzzy candidates (cross_month={cross_month}), top score: {final_results[0][1] if final_results else 0}")

        if not final_results:
            pr.status_ai = "OUT_OF_PLAN"
            pr.perlu_review = True
            db.session.commit()
            return {"success": False, "message": "Tidak ada kandidat di kategori ini", "status": "OUT_OF_PLAN"}

        proc_time = time.time() - start_time
        rank = 1
        for res in final_results:
            item_name, score, detail_id = res
            conf = score / 100.0
            log = MappingLog(
                pr_po_data_id=pr.id,
                method="FUZZY_MATCH",
                planning_detail_hasil_id=detail_id,
                confidence_score=conf,
                rank_no=rank,
                is_selected=False,
                processing_time=proc_time
            )
            db.session.add(log)
            rank += 1

        pr.status_ai = "NEED_MAPPING"
        pr.perlu_review = True
        db.session.commit()
        return {"success": True, "message": "Mapped via Fuzzy (Needs Review)", "status": "NEED_MAPPING"}


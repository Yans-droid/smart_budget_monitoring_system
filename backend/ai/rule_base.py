import re

CAPEX_RULES = [
    r"\bNEW\s+MACHINE\b",
    r"\bNEW\s+EQUIPMENT\b",
    r"\bINVESTMENT\b",
    r"\bINSTALLATION\b",
    r"\bPURCHASE\b",
    r"\bPROJECT\b",
    r"\bASSET\b",
]

OPEX_RULES = [
    r"\bMAINTENANCE\b",
    r"\bREPAIR\b",
    r"\bSPARE\s+PARTS?\b",
    r"\bCONSUMABLE\b",
    r"\bSERVICE\b",
]


def detect_budget_type(text):
    """
    Layer 2 — fallback kalau Layer 1 (regex_predict) gagal menentukan
    Form. Cuma menentukan CAPEX/OPEX berdasar keyword, BUKAN jenis
    barang — jenis barang (tools, kunci, dst) urusannya regex_predict
    di Layer 1, bukan di sini.
    """
    text_up = text.upper()

    capex_score = sum(1 for r in CAPEX_RULES if re.search(r, text_up))
    opex_score = sum(1 for r in OPEX_RULES if re.search(r, text_up))

    if capex_score > opex_score:
        return "CAPEX"
    if opex_score > capex_score:
        return "OPEX"

    return None  # skor sama atau 0 → lanjut ke SVM
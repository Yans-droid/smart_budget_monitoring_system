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


INVENTORY_KEYWORDS = [
    r"\bKUNCI\s+L\b",
    r"\bKUNCI\s+SHOCK\b",
    r"\bTOOLBOX\b",
    r"\bTOOL\s+SET\b",
    r"\bTOOL\s+BOX\b",
    r"\bPEMOTONG\s+KERTAS\b",
]

REPAIR_INDICATORS = [
    r"\bREPAIR\b",
    r"\bSERVICE\b",
    r"\bPERBAIKAN\b",
    r"\bBENERIN\b",
]

def regex_predict(text):
    text_up = text.upper()

    if re.search(r'\bI[- ]?1\b', text_up):
        return "I-1"
    if re.search(r'\bE[- ]?1\b', text_up):
        return "E-1"
    if re.search(r'\bE[- ]?9\b', text_up):
        return "E-9"

    # Kalau ada indikasi ini jasa perbaikan, JANGAN masuk I-1
    # walau nama barangnya match keyword inventory
    is_repair = any(re.search(p, text_up) for p in REPAIR_INDICATORS)
    if not is_repair:
        for pattern in INVENTORY_KEYWORDS:
            if re.search(pattern, text_up):
                return "I-1"

    return None

def detect_budget_type(text):
    text_up = text.upper()

    capex_score = sum(1 for r in CAPEX_RULES if re.search(r, text_up))
    opex_score  = sum(1 for r in OPEX_RULES  if re.search(r, text_up))

    if capex_score > opex_score:
        return "CAPEX"
    if opex_score > capex_score:
        return "OPEX"

    return None  # skor sama atau 0 → lanjut ke ML
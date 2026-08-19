import re
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
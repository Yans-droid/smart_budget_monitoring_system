import pickle
import logging
import os
from utils.regex_rules import regex_predict, detect_budget_type
from utils.preprocess import clean_text

logger = logging.getLogger(__name__)

# Resolve path model relatif terhadap file ini agar tidak bergantung pada CWD
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODEL_PATH = os.path.join(_BASE, 'model', 'svm_model.pkl')

with open(_MODEL_PATH, 'rb') as f:
    _data = pickle.load(f)

model = _data['model']
tfidf = _data['tfidf']

CONFIDENCE_THRESHOLD = 0.7


def predict_category(text: str) -> tuple[str, str]:
    if not text or not text.strip():
        return 'UNKNOWN', 'Invalid Input'

    # Coba rule-based terlebih dahulu
    rule_result = regex_predict(text)
    if rule_result:
        logger.info(f'Regex match: {rule_result}')
        return rule_result, 'Rule Base'

    # Deteksi tipe budget (CAPEX / OPEX)
    budget_type = detect_budget_type(text)
    logger.info(f'Budget type detected: {budget_type}')

    if budget_type == 'CAPEX':
        return 'CAPEX', 'Rule Base'

    # Fallback ke ML model
    cleaned = clean_text(text)
    vector  = tfidf.transform([cleaned])
    prediction = model.predict(vector)[0]
    proba      = model.predict_proba(vector)[0]
    confidence = max(proba)

    if confidence < CONFIDENCE_THRESHOLD:
        logger.warning(f'Low confidence ({confidence:.2f}) for: {text[:50]}')
        return 'UNKNOWN', 'Low Confidence'

    logger.info(f'SVM prediction: {prediction} ({confidence:.2f})')
    return prediction, 'SVM Model'
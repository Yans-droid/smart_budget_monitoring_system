import re

def clean_text(text):

    text = text.lower()

    # hapus simbol
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

    # hapus spasi berlebih
    text = re.sub(r'\s+', ' ', text).strip()

    return text
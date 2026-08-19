"""
utils/sanitize.py
-----------------
Helper terpusat: konversi nilai FK integer dari request JSON.
Form React mengirim '' (empty string) saat select tidak dipilih,
tapi kolom BigInteger MySQL tidak bisa menerima string kosong.
"""


def to_int_or_none(value):
    """
    Konversi value ke int jika valid, atau None jika kosong/null.
    Aman untuk FK integer dari form React.

    to_int_or_none('')    → None
    to_int_or_none(None)  → None
    to_int_or_none('5')   → 5
    to_int_or_none(5)     → 5
    to_int_or_none(0)     → None   (0 bukan FK valid)
    """
    if value in (None, '', 0, '0'):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

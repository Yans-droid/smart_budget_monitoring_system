import os
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g

# Ambil dari environment variable, JANGAN hardcode secret di kode.
# Set di .env: JWT_SECRET_KEY=<string random panjang>
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-ganti-ini-di-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_HOURS = 8  # token berlaku 8 jam, sesuai jam kerja


def generate_token(user):
    """
    Bikin JWT buat user yang berhasil login.
    Payload sengaja minimal: cuma id, username, role — jangan simpan
    data sensitif (password hash, dll) di dalam token, karena payload
    JWT bisa dibaca siapa aja (cuma signature-nya yang diverifikasi).
    """
    payload = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRES_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token):
    """
    Decode + verifikasi token. Return payload dict kalau valid,
    None kalau invalid/expired.
    """
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def _extract_token_from_header():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def token_required(f):
    """
    Wajibkan request bawa token valid di header Authorization: Bearer <token>.
    User yang login ditaruh di g.current_user (dict: user_id, username, role)
    biar bisa diakses di dalam route/service tanpa perlu query ulang.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token_from_header()
        if not token:
            return jsonify({"success": False, "message": "Token tidak ditemukan, silakan login"}), 401

        payload = decode_token(token)
        if not payload:
            return jsonify({"success": False, "message": "Token tidak valid atau kadaluarsa, silakan login ulang"}), 401

        g.current_user = payload
        return f(*args, **kwargs)
    return decorated


def role_required(*allowed_roles):
    """
    Wajibkan token valid DAN role user termasuk salah satu dari allowed_roles.
    Selalu jalanin token_required duluan (auth dulu, baru otorisasi),
    jadi dua-duanya bisa langsung dipasang bertumpuk atau pakai ini sendirian
    (sudah termasuk cek token).

    Pemakaian: @role_required('admin')
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if g.current_user["role"] not in allowed_roles:
                return jsonify({
                    "success": False,
                    "message": f"Akses ditolak — butuh role: {', '.join(allowed_roles)}"
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
from flask import Blueprint, request, jsonify
from services.upload_service import UploadService

upload_bp = Blueprint(
    "upload",
    __name__
)

@upload_bp.route("/", methods=["POST"])
def upload_excel():
    # 1. Ambil file dari request.files
    file = request.files.get("file")
    print(file )
    
    # Optional: ambil user_id dari request form atau token (dummy user=1 sementara jika tidak ada)
    user_id = request.form.get("user_id", 1)
    
    if not user_id:
        user_id = 1 # Fallback untuk testing jika auth tidak aktif

    # 3. Kirim file ke UploadService (Validasi 1 dan 2 sudah ditangani di service)
    result, status_code = UploadService.upload_excel(file, user_id=user_id)

    # 4. Return response
    return jsonify(result), status_code

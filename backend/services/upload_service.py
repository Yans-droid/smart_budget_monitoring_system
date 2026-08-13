import os
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime
import pandas as pd
from services.upload_history_service import UploadHistoryService
class UploadService:

    @staticmethod
    def upload_excel(file, user_id):
        if not file:
            return {
                "success": False,
                "message": "File wajib diisi"
            }, 400

        filename = secure_filename(file.filename)
        if not filename:
            return {
                "success": False,
                "message": "Nama file tidak valid"
            }, 400

        ext = filename.rsplit('.', 1)[-1].lower()
        ALLOWED_EXTENSIONS = {'xls', 'xlsx'}
        if ext not in ALLOWED_EXTENSIONS:
            return {
                "success": False,
                "message": "Ekstensi file tidak diizinkan (gunakan .xls atau .xlsx)"
            }, 400

        # Simpan ke file temp sementara (aman untuk Docker/Cloud)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
        file.save(tmp.name)
        filepath = tmp.name
        tmp.close()

        history, status_code = UploadHistoryService.create_upload_history({
            "user_id": user_id,
            "original_filename": filename,
            "stored_filename": os.path.basename(filepath),
            "total_data": 0
        })
        if not history["success"]:
            os.unlink(filepath)  # Hapus file temp jika history gagal dibuat
            return history, status_code
        upload_id = history["data"]["id"]

        try:
            df = pd.read_excel(filepath)
            df.columns = [
                str(col).strip().lower().replace(" ", "_").replace("-", "_")
                for col in df.columns
            ]
        except Exception as e:
            return {
                "success": False,
                "message": f"File Excel tidak dapat dibaca: {str(e)}"
            }, 400
        finally:
            # Selalu hapus file temp setelah dibaca
            try:
                os.unlink(filepath)
            except Exception:
                pass

        return {
            "success": True,
            "message": "Excel berhasil dibaca",
            "upload_id": upload_id
        }, 200
    

    

    


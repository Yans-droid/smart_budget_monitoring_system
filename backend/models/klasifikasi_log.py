from utils.db import db


class KlasifikasiLog(db.Model):
    __tablename__ = "klasifikasi_log"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    pr_po_data_id = db.Column(
        db.BigInteger,
        db.ForeignKey("pr_po_data.id")
    )

    layer = db.Column(
        db.SmallInteger,
        comment="1=Rule Base, 2=Regex, 3=SVM"
    )

    method = db.Column(
        db.Enum(
            "RULE_BASE",
            "REGEX",
            "SVM"
        )
    )

    berhasil = db.Column(
        db.Boolean
    )

    kategori_hasil_id = db.Column(
        db.BigInteger,
        db.ForeignKey("kategori.id")
    )

    confidence_score = db.Column(
        db.Numeric(5, 4)
    )

    processing_time = db.Column(
        db.Numeric(10, 4),
        comment="Waktu proses dalam detik"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    # --- Relationships ---

    pr_po_data = db.relationship(
        "PrPoData",
        backref="klasifikasi_logs"
    )

    kategori_hasil = db.relationship(
        "Kategori",
        backref="klasifikasi_logs"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "pr_po_data_id": self.pr_po_data_id,
            "layer": self.layer,
            "method": self.method,
            "berhasil": self.berhasil,
            "kategori_hasil_id": self.kategori_hasil_id,
            "kategori_kode": (
                self.kategori_hasil.kode
                if self.kategori_hasil else None
            ),
            "confidence_score": (
                float(self.confidence_score)
                if self.confidence_score else None
            ),
            "processing_time": (
                float(self.processing_time)
                if self.processing_time else None
            ),
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            ),
        }

    def __repr__(self):
        return (
            f"<KlasifikasiLog {self.id} "
            f"layer={self.layer} "
            f"method={self.method}>"
        )

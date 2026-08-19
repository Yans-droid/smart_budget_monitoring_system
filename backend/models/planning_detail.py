from utils.db import db


class PlanningDetail(db.Model):
    __tablename__ = "planning_detail"

    id = db.Column(
        db.BigInteger,
        primary_key=True
    )
    planning_header_id = db.Column(
        db.BigInteger,
        db.ForeignKey("planning_header.id"),
        nullable=False
    )
    kategori_id = db.Column(
        db.BigInteger,
        db.ForeignKey("kategori.id"),
        nullable=True
    )
    month = db.Column(
        db.String(20),
        nullable=True,
        comment="Bulan planning, contoh: Jan, Feb, Mar"
    )
    item = db.Column(
        db.String(255),
        nullable=False
    )
    planning_amount = db.Column(
        db.Numeric(18, 2),
        nullable=False
    )
    remarks = db.Column(
        db.String(255)
    )
    status_realisasi = db.Column(
        db.Enum('OPEN', 'PROSES', 'CLOSED', 'CANCELLED'),
        nullable=False,
        default='OPEN',
        comment="Agregat status realisasi dari semua PR yang di-mapping ke item ini"
    )
    created_at = db.Column(
        db.TIMESTAMP,
        default=db.func.current_timestamp()
    )
    updated_at = db.Column(
        db.TIMESTAMP,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    kategori = db.relationship(
        "Kategori",
        backref="planning_details"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "planning_header_id": self.planning_header_id,
            "kategori_id": self.kategori_id,
            "kategori_kode": self.kategori.kode if self.kategori else None,
            "kategori_nama": self.kategori.nama if self.kategori else None,
            "kategori_tipe_formulir": self.kategori.tipe_formulir if self.kategori else None,
            "month": self.month,
            "item": self.item,
            "planning_amount": float(self.planning_amount) if self.planning_amount else 0,
            "remarks": self.remarks,
            "status_realisasi": self.status_realisasi or 'OPEN',
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
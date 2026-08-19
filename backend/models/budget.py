from utils.db import db

class Budget(db.Model):
    __tablename__ = "budget"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )
    kategori_id = db.Column(
        db.BigInteger,
        db.ForeignKey("kategori.id"),
        index=True
    )
    periode =db.Column(
        db.String(30)
    )
    nominal = db.Column(
        db.Numeric(18,2),
        nullable=False
    )
    created_by = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id")
    )

    upload_id = db.Column(
        db.BigInteger,
        db.ForeignKey("upload_history.id"),
    )
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    kategori= db.relationship(
        "Kategori",
        backref="budgets"
    )
    user = db.relationship(
        "User",
        backref="budgets"
    )
    upload_history = db.relationship(
        "UploadHistory",
        backref="budgets"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "kategori_id": self.kategori_id,
            "periode": self.periode,
            "nominal": self.nominal,
            "created_by": self.created_by,
            "upload_id": self.upload_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
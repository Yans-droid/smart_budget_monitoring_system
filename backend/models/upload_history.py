from utils.db import db


class UploadHistory(db.Model):
    __tablename__ = "upload_history"

    id = db.Column(
        db.BigInteger,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.BigInteger,
        db.ForeignKey("users.id"),
        nullable=False
    )

    original_filename = db.Column(
        db.String(255),
        nullable=False
    )

    stored_filename = db.Column(
        db.String(255),
        nullable=False,
        unique=True
    )

    total_data = db.Column(
        db.Integer
    )

    status = db.Column(
        db.Enum(
            "UPLOADING",
            "SUCCESS",
            "FAILED"
        ),
        default="UPLOADING"
    )

    uploaded_at = db.Column(
        db.DateTime
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    user = db.relationship(
        "User",
        backref="uploads"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "original_filename": self.original_filename,
            "stored_filename": self.stored_filename,
            "total_data": self.total_data,
            "status": self.status,
            "uploaded_at": self.uploaded_at,
            "created_at": self.created_at
        }
from datetime import datetime
from sqlalchemy.sql import func
from utils.db import db

class ItemMapping(db.Model):
    __tablename__ = "item_mapping"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    kategori_id = db.Column(db.BigInteger, db.ForeignKey('kategori.id'), nullable=True)
    keyword = db.Column(db.String(255), nullable=False)
    planning_item = db.Column(db.String(255), nullable=False)
    priority = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    kategori = db.relationship('Kategori', backref='item_mappings')

    def to_dict(self):
        return {
            "id": self.id,
            "kategori_id": self.kategori_id,
            "keyword": self.keyword,
            "planning_item": self.planning_item,
            "priority": self.priority,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
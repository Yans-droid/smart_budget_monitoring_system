from utils.db import db

class MappingLog(db.Model):
    __tablename__ = "mapping_log"
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    pr_po_data_id = db.Column(
        db.BigInteger,
        db.ForeignKey("pr_po_data.id", ondelete="CASCADE"),
        nullable=False
    )
    method = db.Column(
        db.Enum('ITEM_MAPPING_RULE', 'FUZZY_MATCH', 'MANUAL'),
        nullable=False
    )
    planning_detail_hasil_id = db.Column(
        db.BigInteger,
        db.ForeignKey("planning_detail.id", ondelete="SET NULL"),
        nullable=True
    )
    confidence_score = db.Column(db.Numeric(5, 4), nullable=True)
    rank_no = db.Column(db.Integer, nullable=True)
    is_selected = db.Column(db.Boolean, default=False)
    processing_time = db.Column(db.Numeric(10, 4), nullable=True)
    created_at = db.Column(
        db.DateTime(),
        server_default=db.func.current_timestamp()
    )

    pr_po_data = db.relationship("PrPoData", backref=db.backref("mapping_logs", cascade="all, delete-orphan"))
    planning_detail = db.relationship("PlanningDetail")

    def to_dict(self):
        return {
            "id": self.id,
            "pr_po_data_id": self.pr_po_data_id,
            "method": self.method,
            "planning_detail_hasil_id": self.planning_detail_hasil_id,
            "confidence_score": float(self.confidence_score) if self.confidence_score is not None else None,
            "rank_no": self.rank_no,
            "is_selected": self.is_selected,
            "processing_time": float(self.processing_time) if self.processing_time is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

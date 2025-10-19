from datetime import datetime
from config import db


class UserReview(db.Model):
    __tablename__ = "user_reviews"

    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reviewed_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reviewer = db.relationship("User", foreign_keys=[reviewer_id], backref="given_reviews")
    reviewed_user = db.relationship("User", foreign_keys=[reviewed_user_id], backref="received_reviews")

    __table_args__ = (
        db.UniqueConstraint("reviewer_id", "reviewed_user_id", name="unique_user_review"),
    )

    def __repr__(self):
        return f"<UserReview {self.id} - {self.reviewer_id} → {self.reviewed_user_id}>"

    def to_dict(self):
        """Trả về dữ liệu ở dạng dictionary, có thêm thông tin thời gian."""
        time_ago = self._time_ago()
        return {
            "id": self.id,
            "reviewer_id": self.reviewer_id,
            "reviewed_user_id": self.reviewed_user_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "time_ago": time_ago,
        }

    def _time_ago(self):
        """Tính khoảng thời gian 'x phút/giờ/ngày trước'."""
        now = datetime.utcnow()
        delta = now - (self.updated_at or self.created_at)

        if delta.days > 0:
            return f"{delta.days} ngày trước"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours} giờ trước"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes} phút trước"
        return "Vừa xong"

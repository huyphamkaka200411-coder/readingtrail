
from config import db
from datetime import datetime, timezone
from pytz import timezone as pytz_timezone


class BookReview(db.Model):
    __tablename__ = 'book_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    book = db.relationship('Book', backref='reviews')
    user = db.relationship('User', backref='reviews')
    
    # Unique constraint to prevent duplicate reviews from same user
    __table_args__ = (db.UniqueConstraint('book_id', 'user_id', name='unique_book_user_review'),)
    
    def __repr__(self):
        return f'<BookReview {self.id} for book {self.book_id} by user {self.user_id}>'
    

    def to_dict(self):
        # Ensure created_at is timezone-aware
        if self.created_at.tzinfo is None:
            created_at_utc = self.created_at.replace(tzinfo=timezone.utc)
        else:
            created_at_utc = self.created_at.astimezone(timezone.utc)

        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        time_diff = now_utc - created_at_utc

        # Format time ago
        if time_diff.days > 0:
            time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif time_diff.seconds > 60:
            minutes = time_diff.seconds // 60
            time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            time_ago = "Just now"

        # Convert to Vietnam timezone
        vn_tz = pytz_timezone('Asia/Ho_Chi_Minh')
        local_time = created_at_utc.astimezone(vn_tz)

        return {
            'id': self.id,
            'book_id': self.book_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'review_text': self.review_text,
            'created_at': created_at_utc.isoformat(),
            'formatted_time': local_time.strftime('%d/%m/%Y %H:%M'),
            'time_ago': time_ago,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'username': self.user.username if self.user else 'Unknown',
            'user_full_name': self.user.get_full_name() if self.user else 'Unknown User'
        }
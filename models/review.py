from datetime import datetime
from config import db


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
        from pytz import timezone
        from datetime import datetime as dt
        
        # Calculate time ago
        now = dt.utcnow()
        time_diff = now - self.created_at
        
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
        
        vn_tz = timezone('Asia/Ho_Chi_Minh')
        local_time = self.created_at.replace(tzinfo=timezone('UTC')).astimezone(vn_tz)
        
        return {
            'id': self.id,
            'book_id': self.book_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'review_text': self.review_text,
            'created_at': self.created_at.isoformat(),
            'formatted_time': local_time.strftime('%d/%m/%Y %H:%M'),
            'time_ago': time_ago,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'username': self.user.username if self.user else 'Unknown',
            'user_full_name': self.user.get_full_name() if self.user else 'Unknown User'
        }
from datetime import datetime
from config import db


class Discussion(db.Model):
    __tablename__ = 'discussions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=True)  # Optional for book-specific discussions
    
    # Relationships
    user = db.relationship('User', backref='discussions')
    book = db.relationship('Book', backref='discussions')
    
    def __repr__(self):
        return f'<Discussion {self.id} by {self.username}>'
    
    def to_dict(self):
        from pytz import timezone
        vn_tz = timezone('Asia/Ho_Chi_Minh')
        local_time = self.created_at.replace(tzinfo=timezone('UTC')).astimezone(vn_tz)
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'message': self.message,
            'timestamp': self.created_at.isoformat(),
            'formatted_time': local_time.strftime('%d/%m/%Y %H:%M'),
            'book_id': self.book_id
        }


class PrivateMessage(db.Model):
    __tablename__ = 'private_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=True)  # Optional context
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')
    book = db.relationship('Book', backref='private_messages')
    
    def __repr__(self):
        return f'<PrivateMessage {self.id} from {self.sender_id} to {self.recipient_id}>'
    
    def to_dict(self):
        from pytz import timezone
        import datetime
        vn_tz = timezone('Asia/Ho_Chi_Minh')
        local_time = self.timestamp.replace(tzinfo=timezone('UTC')).astimezone(vn_tz)
        
        # Calculate time ago
        now = datetime.datetime.utcnow().replace(tzinfo=timezone('UTC'))
        time_diff = now - self.timestamp.replace(tzinfo=timezone('UTC'))
        
        if time_diff.days > 0:
            time_ago = f"{time_diff.days}d ago"
        elif time_diff.seconds > 3600:
            time_ago = f"{time_diff.seconds // 3600}h ago"
        elif time_diff.seconds > 60:
            time_ago = f"{time_diff.seconds // 60}m ago"
        else:
            time_ago = "just now"
        
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'formatted_time': local_time.strftime('%d/%m/%Y %H:%M'),
            'time_ago': time_ago,
            'is_read': self.is_read,
            'book_id': self.book_id
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'borrow_request', 'borrow_approved', 'borrow_rejected', etc.
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=True)
    related_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    book = db.relationship('Book', backref='notifications')
    related_user = db.relationship('User', foreign_keys=[related_user_id])
    
    def __repr__(self):
        return f'<Notification {self.id} for {self.user_id}>'
    
    def to_dict(self):
        from pytz import timezone
        vn_tz = timezone('Asia/Ho_Chi_Minh')
        local_time = self.created_at.replace(tzinfo=timezone('UTC')).astimezone(vn_tz)
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'formatted_time': local_time.strftime('%d/%m/%Y %H:%M'),
            'book_id': self.book_id,
            'related_user_id': self.related_user_id
        }
class Follow(db.Model):
    __tablename__ = 'follows'

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    follower = db.relationship('User', foreign_keys=[follower_id], backref='following')
    followed = db.relationship('User', foreign_keys=[followed_id], backref='followers')

    def __repr__(self):
        return f'<Follow {self.follower_id} → {self.followed_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'follower_id': self.follower_id,
            'followed_id': self.followed_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

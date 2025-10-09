from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from config import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    borrowed_books = db.relationship('BorrowedBook', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def is_online(self):
        """Check if user is considered online (active within last 5 minutes)"""
        if not self.last_activity:
            return False
        return (datetime.utcnow() - self.last_activity).total_seconds() < 300  # 5 minutes
    
    def update_activity(self):
        """Update user's last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def __repr__(self):
        return f'<User {self.username}>'
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
    
    def get_total_points(self):
        """Calculate total points from all achievements"""
        from models.achievement import Achievement, UserAchievement
        total = db.session.query(db.func.sum(Achievement.points)).join(
            UserAchievement, Achievement.id == UserAchievement.achievement_id
        ).filter(UserAchievement.user_id == self.id).scalar()
        return total if total else 0
    
    def get_rank_info(self):
        """Get user's rank based on total points"""
        total_points = self.get_total_points()
        
        # Define rank system
        ranks = [
            {'name': 'Newbie', 'min_points': 0, 'color': '#95a5a6', 'icon': 'fa-seedling'},
            {'name': 'Reader', 'min_points': 50, 'color': '#3498db', 'icon': 'fa-book'},
            {'name': 'Bookworm', 'min_points': 150, 'color': '#9b59b6', 'icon': 'fa-book-open'},
            {'name': 'Scholar', 'min_points': 300, 'color': '#e67e22', 'icon': 'fa-graduation-cap'},
            {'name': 'Expert', 'min_points': 500, 'color': '#f39c12', 'icon': 'fa-star'},
            {'name': 'Master', 'min_points': 750, 'color': '#e74c3c', 'icon': 'fa-crown'},
            {'name': 'Grandmaster', 'min_points': 1000, 'color': '#1abc9c', 'icon': 'fa-gem'},
            {'name': 'Legend', 'min_points': 1500, 'color': '#fd79a8', 'icon': 'fa-trophy'}
        ]
        
        # Find current rank
        current_rank = ranks[0]
        for rank in ranks:
            if total_points >= rank['min_points']:
                current_rank = rank
            else:
                break
        
        # Find next rank
        next_rank = None
        for rank in ranks:
            if total_points < rank['min_points']:
                next_rank = rank
                break
        
        # Calculate progress
        points_needed = 0
        progress_percentage = 0
        if next_rank:
            points_needed = next_rank['min_points'] - total_points
            progress_percentage = ((total_points - current_rank['min_points']) / 
                                 (next_rank['min_points'] - current_rank['min_points'])) * 100
        
        return {
            'current_rank': current_rank,
            'next_rank': next_rank,
            'total_points': total_points,
            'points_needed': points_needed,
            'progress_percentage': int(progress_percentage)
        }
    
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
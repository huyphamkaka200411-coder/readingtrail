from datetime import datetime
from config import db


class Achievement(db.Model):
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(
        db.String(50),
        nullable=False)  # 'books', 'reviews', 'social', 'special'
    points = db.Column(db.Integer, default=10)
    requirement_type = db.Column(
        db.String(50),
        nullable=False)  # 'borrow_count', 'post_count', 'review_count', etc.
    requirement_value = db.Column(db.Integer, nullable=False)
    icon = db.Column(db.String(50), default='fa-trophy')
    color = db.Column(db.String(20), default='#ffd700')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user_achievements = db.relationship('UserAchievement',
                                        backref='achievement',
                                        lazy=True)

    def __repr__(self):
        return f'<Achievement {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'points': self.points,
            'requirement_type': self.requirement_type,
            'requirement_value': self.requirement_value,
            'icon': self.icon,
            'color': self.color,
            'is_active': self.is_active,
            'created_at':
            self.created_at.isoformat() if self.created_at else None
        }


class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer,
                               db.ForeignKey('achievements.id'),
                               nullable=False)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_seen = db.Column(db.Boolean, default=False)

    # Relationships
    user = db.relationship('User', backref='user_achievements')

    # Unique constraint to prevent duplicate achievements
    __table_args__ = (db.UniqueConstraint('user_id',
                                          'achievement_id',
                                          name='unique_user_achievement'), )

    def __repr__(self):
        return f'<UserAchievement {self.user_id} - {self.achievement_id}>'

    def to_dict(self):
        from pytz import timezone
        vn_tz = timezone('Asia/Ho_Chi_Minh')
        local_time = self.unlocked_at.replace(
            tzinfo=timezone('UTC')).astimezone(vn_tz)

        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'unlocked_at': self.unlocked_at.isoformat(),
            'is_seen': self.is_seen,
            'formatted_time': local_time.strftime('%d/%m/%Y %H:%M'),
            'achievement':
            self.achievement.to_dict() if self.achievement else None
        }


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id'),
                        nullable=False,
                        unique=True)
    banner_style = db.Column(db.String(50), default='default')
    custom_title = db.Column(db.String(30))
    title_color = db.Column(db.String(30))  # ✅ fixed line

    def __repr__(self):
        return f'<UserProfile {self.user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'banner_style': self.banner_style,
            'custom_title': self.custom_title,
            'title_color': self.title_color
        }

from datetime import datetime, timedelta
from config import db


class PowerUp(db.Model):
    __tablename__ = 'powerups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Integer, nullable=False)  # Cost in points
    powerup_type = db.Column(db.String(50), nullable=False)  # 'leech', 'double_points'
    duration_hours = db.Column(db.Integer)  # Duration in hours (null for instant effects)
    effect_value = db.Column(db.Float)  # Effect strength (e.g., 2.0 for double points)
    icon = db.Column(db.String(50), default='fa-bolt')
    color = db.Column(db.String(20), default='#e74c3c')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user_powerups = db.relationship('UserPowerUp', backref='powerup', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PowerUp {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'cost': self.cost,
            'powerup_type': self.powerup_type,
            'duration_hours': self.duration_hours,
            'effect_value': self.effect_value,
            'icon': self.icon,
            'color': self.color,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserPowerUp(db.Model):
    __tablename__ = 'user_powerups'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    powerup_id = db.Column(db.Integer, db.ForeignKey('powerups.id'), nullable=False)
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    activated_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)
    is_consumed = db.Column(db.Boolean, default=False)  # For one-time use powerups
    
    # For leech powerup - track which user was leeched and how much
    leeched_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    leeched_points = db.Column(db.Integer, default=0)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='user_powerups')
    leeched_user = db.relationship('User', foreign_keys=[leeched_user_id])
    
    def __repr__(self):
        return f'<UserPowerUp {self.user_id} - {self.powerup_id}>'
    
    def is_expired(self):
        """Check if the powerup has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def time_remaining(self):
        """Get time remaining for active powerup"""
        if not self.expires_at or self.is_expired():
            return None
        return self.expires_at - datetime.utcnow()
    
    def activate(self):
        """Activate the powerup"""
        if self.is_consumed or (self.is_active and not self.is_expired()):
            return False
        
        self.activated_at = datetime.utcnow()
        self.is_active = True
        
        # Set expiration time if powerup has duration
        if self.powerup.duration_hours:
            self.expires_at = datetime.utcnow() + timedelta(hours=self.powerup.duration_hours)
        
        return True
    
    def to_dict(self):
        from pytz import timezone
        vn_tz = timezone('Asia/Ho_Chi_Minh')
        
        # Format times in Vietnam timezone
        purchased_time = None
        activated_time = None
        expires_time = None
        
        if self.purchased_at:
            local_purchased = self.purchased_at.replace(tzinfo=timezone('UTC')).astimezone(vn_tz)
            purchased_time = local_purchased.strftime('%d/%m/%Y %H:%M')
        
        if self.activated_at:
            local_activated = self.activated_at.replace(tzinfo=timezone('UTC')).astimezone(vn_tz)
            activated_time = local_activated.strftime('%d/%m/%Y %H:%M')
        
        if self.expires_at:
            local_expires = self.expires_at.replace(tzinfo=timezone('UTC')).astimezone(vn_tz)
            expires_time = local_expires.strftime('%d/%m/%Y %H:%M')
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'powerup_id': self.powerup_id,
            'purchased_at': purchased_time,
            'activated_at': activated_time,
            'expires_at': expires_time,
            'is_active': self.is_active,
            'is_consumed': self.is_consumed,
            'is_expired': self.is_expired(),
            'time_remaining': str(self.time_remaining()) if self.time_remaining() else None,
            'leeched_user_id': self.leeched_user_id,
            'leeched_points': self.leeched_points,
            'powerup': self.powerup.to_dict() if self.powerup else None
        }
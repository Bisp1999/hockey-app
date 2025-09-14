"""
Tenant model for multi-tenant architecture.
"""
from datetime import datetime
from app import db

class Tenant(db.Model):
    """Tenant model for multi-tenant architecture."""
    
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    subdomain = db.Column(db.String(50), unique=True, nullable=True, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Configuration settings
    position_mode = db.Column(db.String(20), default='three_position', nullable=False)  # 'three_position' or 'two_position'
    team_name_1 = db.Column(db.String(50), default='Team 1')
    team_name_2 = db.Column(db.String(50), default='Team 2')
    team_color_1 = db.Column(db.String(20), default='blue')
    team_color_2 = db.Column(db.String(20), default='red')
    assignment_mode = db.Column(db.String(20), default='manual', nullable=False)  # 'manual' or 'automatic'
    
    # Relationships
    users = db.relationship('User', backref='tenant', lazy=True, cascade='all, delete-orphan')
    players = db.relationship('Player', backref='tenant', lazy=True, cascade='all, delete-orphan')
    games = db.relationship('Game', backref='tenant', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Tenant {self.name}>'
    
    def to_dict(self):
        """Convert tenant to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'subdomain': self.subdomain,
            'is_active': self.is_active,
            'position_mode': self.position_mode,
            'team_name_1': self.team_name_1,
            'team_name_2': self.team_name_2,
            'team_color_1': self.team_color_1,
            'team_color_2': self.team_color_2,
            'assignment_mode': self.assignment_mode,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

"""
Team model with names and jersey colors.
"""
from datetime import datetime
from app import db

class Team(db.Model):
    """Team model for game organization."""
    
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    jersey_color = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Multi-tenant foreign key
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    def __repr__(self):
        return f'<Team {self.name} ({self.jersey_color})>'
    
    def to_dict(self):
        """Convert team to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'jersey_color': self.jersey_color,
            'is_active': self.is_active,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

"""
Tenant model for multi-tenant architecture.
"""
from datetime import datetime
from app import db
from sqlalchemy import event
import re

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

    # Default player requirements for games
    default_goaltenders = db.Column(db.Integer, default=2, nullable=False)
    default_defence = db.Column(db.Integer, default=4, nullable=True)  # null for 2-position mode
    default_forwards = db.Column(db.Integer, default=6, nullable=True)  # null for 2-position mode
    default_skaters = db.Column(db.Integer, default=10, nullable=True)  # for 2-position mode
    
    # Relationships
    users = db.relationship('User', backref='tenant', lazy=True, cascade='all, delete-orphan')
    players = db.relationship('Player', backref='tenant', lazy=True, cascade='all, delete-orphan')
    games = db.relationship('Game', backref='tenant', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Tenant {self.name}>'
    
    @staticmethod
    def generate_slug(name):
        """Generate a URL-safe slug from tenant name."""
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    @staticmethod
    def is_valid_subdomain(subdomain):
        """Validate subdomain format."""
        if not subdomain:
            return True  # Subdomain is optional
        
        # Check length (3-50 characters)
        if len(subdomain) < 3 or len(subdomain) > 50:
            return False
        
        # Check format: alphanumeric and hyphens, start/end with alphanumeric
        pattern = r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'
        return bool(re.match(pattern, subdomain))
    
    def get_url(self, scheme='http'):
        """Get the tenant's URL based on configuration."""
        from flask import current_app
        
        if self.subdomain and current_app.config.get('TENANT_URL_SUBDOMAIN_ENABLED'):
            domain = current_app.config.get('SERVER_NAME', 'localhost:5000')
            return f"{scheme}://{self.subdomain}.{domain}"
        elif current_app.config.get('TENANT_URL_PATH_ENABLED'):
            domain = current_app.config.get('SERVER_NAME', 'localhost:5000')
            return f"{scheme}://{domain}/{self.slug}"
        
        return None
    
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
            'default_goaltenders': self.default_goaltenders,
            'default_defence': self.default_defence,
            'default_forwards': self.default_forwards,
            'default_skaters': self.default_skaters,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'url': self.get_url()
        }

# Event listeners for automatic slug generation
@event.listens_for(Tenant.name, 'set')
def generate_slug_on_name_change(target, value, oldvalue, initiator):
    """Automatically generate slug when name is set."""
    if value and (not target.slug or target.slug == Tenant.generate_slug(oldvalue)):
        target.slug = Tenant.generate_slug(value)

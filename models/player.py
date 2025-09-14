"""
Player model with positions, types, and photo upload.
"""
from datetime import datetime
from app import db
from utils.base_model import TenantMixin
from utils.tenant_isolation import enforce_tenant_isolation

@enforce_tenant_isolation
class Player(TenantMixin, db.Model):
    """Player model with multi-tenant support."""
    
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    position = db.Column(db.String(20), nullable=False)  # 'goaltender', 'defence', 'forward', 'skater'
    player_type = db.Column(db.String(20), nullable=False)  # 'regular', 'spare'
    spare_priority = db.Column(db.Integer, nullable=True)  # 1 or 2 for spare players, null for regulars
    photo_filename = db.Column(db.String(255), nullable=True)
    language = db.Column(db.String(5), default='en', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # tenant_id is inherited from TenantMixin
    
    # Unique constraint on email within tenant
    __table_args__ = (db.UniqueConstraint('email', 'tenant_id', name='unique_player_email_per_tenant'),)
    
    # Relationships
    invitations = db.relationship('Invitation', backref='player', lazy=True, cascade='all, delete-orphan')
    statistics = db.relationship('PlayerStatistic', backref='player', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='player', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Player {self.name} ({self.position})>'
    
    def to_dict(self):
        """Convert player to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'position': self.position,
            'player_type': self.player_type,
            'spare_priority': self.spare_priority,
            'photo_filename': self.photo_filename,
            'language': self.language,
            'is_active': self.is_active,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @property
    def photo_url(self):
        """Get photo URL if photo exists."""
        if self.photo_filename:
            return f'/uploads/{self.photo_filename}'
        return None

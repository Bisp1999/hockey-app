"""
Player model with positions, types, and photo upload.
"""
from datetime import datetime
from app import db
from utils.base_model import TenantMixin
from utils.tenant_isolation import enforce_tenant_isolation

# Position constants
POSITION_GOALTENDER = 'goaltender'
POSITION_DEFENCE = 'defence'
POSITION_FORWARD = 'forward'
POSITION_SKATER = 'skater'

# Player type constants
PLAYER_TYPE_REGULAR = 'regular'
PLAYER_TYPE_SPARE = 'spare'

# Spare priority constants
SPARE_PRIORITY_1 = 1
SPARE_PRIORITY_2 = 2

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
    email_invitations = db.Column(db.Boolean, default=True, nullable=False)
    email_reminders = db.Column(db.Boolean, default=True, nullable=False)
    email_notifications = db.Column(db.Boolean, default=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # tenant_id is inherited from TenantMixin
    
    # Unique constraint on email within tenant
    __table_args__ = (db.UniqueConstraint('email', 'tenant_id', name='unique_player_email_per_tenant'),)
    
    # Relationships
    invitations = db.relationship('Invitation', back_populates='player', lazy=True, cascade='all, delete-orphan')
    statistics = db.relationship('PlayerStatistic', backref='player', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='player', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Player {self.name} ({self.position})>'
    
    @property
    def photo_url(self):
        """Get photo URL if photo exists."""
        if self.photo_filename:
            return f'/uploads/players/{self.photo_filename}'
        return None
    
    @property
    def is_spare(self):
        """Check if player is a spare."""
        return self.player_type == PLAYER_TYPE_SPARE
    
    @property
    def is_regular(self):
        """Check if player is a regular."""
        return self.player_type == PLAYER_TYPE_REGULAR
    
    @property
    def is_goaltender(self):
        """Check if player is a goaltender."""
        return self.position == POSITION_GOALTENDER
    
    @property
    def preferred_language(self):
        """Alias for language field (used in email service)."""
        return self.language
    
    def to_dict(self, include_photo_url=True):
        """Convert player to dictionary."""
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'position': self.position,
            'player_type': self.player_type,
            'spare_priority': self.spare_priority,
            'photo_filename': self.photo_filename,
            'language': self.language,
            'email_invitations': self.email_invitations,
            'email_reminders': self.email_reminders,
            'email_notifications': self.email_notifications,
            'is_active': self.is_active,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_photo_url:
            data['photo_url'] = self.photo_url
        
        return data

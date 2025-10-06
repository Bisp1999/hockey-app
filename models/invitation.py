"""
Invitation and availability response models.
"""
from datetime import datetime
import secrets
from app import db
from utils.base_model import TenantMixin
from utils.tenant_isolation import enforce_tenant_isolation

@enforce_tenant_isolation
class Invitation(TenantMixin, db.Model):
    """Invitation model for game invitations with tracking."""
    
    __tablename__ = 'invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    invitation_type = db.Column(db.String(20), nullable=False)  # 'regular', 'spare'
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'sent', 'delivered', 'opened', 'responded', 'bounced', 'failed'
    
    # Response tracking
    response = db.Column(db.String(20), nullable=True)  # 'available', 'unavailable', 'tentative'
    response_method = db.Column(db.String(20), nullable=True)  # 'email', 'web', 'admin'
    response_notes = db.Column(db.Text, nullable=True)
    
    # Email tracking
    email_sent_at = db.Column(db.DateTime, nullable=True)
    email_delivered_at = db.Column(db.DateTime, nullable=True)
    email_opened_at = db.Column(db.DateTime, nullable=True)
    email_bounced_at = db.Column(db.DateTime, nullable=True)
    email_error = db.Column(db.Text, nullable=True)
    
    # Response tracking
    responded_at = db.Column(db.DateTime, nullable=True)
    
    # Reminder tracking
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    reminder_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Security token for email responses
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Multi-tenant foreign keys
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False, index=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False, index=True)
    
    # Relationships
    game = db.relationship('Game', back_populates='invitations')
    player = db.relationship('Player', back_populates='invitations')
    
    # Unique constraint: one invitation per player per game
    __table_args__ = (
        db.UniqueConstraint('game_id', 'player_id', name='unique_game_player_invitation'),
        {'extend_existing': True}
    )
    
    def __init__(self, **kwargs):
        """Initialize invitation with a unique token."""
        super().__init__(**kwargs)
        if not self.token:
            self.token = secrets.token_urlsafe(32)
    
    def __repr__(self):
        return f'<Invitation {self.id} for Game {self.game_id} - {self.status}>'
    
    def mark_sent(self):
        """Mark invitation as sent."""
        self.status = 'sent'
        self.email_sent_at = datetime.utcnow()
    
    def mark_delivered(self):
        """Mark invitation as delivered."""
        self.status = 'delivered'
        self.email_delivered_at = datetime.utcnow()
    
    def mark_opened(self):
        """Mark invitation as opened."""
        if self.status in ['sent', 'delivered']:
            self.status = 'opened'
        if not self.email_opened_at:
            self.email_opened_at = datetime.utcnow()
    
    def mark_bounced(self, error_message=None):
        """Mark invitation as bounced."""
        self.status = 'bounced'
        self.email_bounced_at = datetime.utcnow()
        self.email_error = error_message
    
    def record_response(self, response, method='web', notes=None):
        """Record player's response to invitation."""
        self.response = response
        self.response_method = method
        self.response_notes = notes
        self.responded_at = datetime.utcnow()
        self.status = 'responded'
    
    def send_reminder(self):
        """Record that a reminder was sent."""
        self.reminder_sent_at = datetime.utcnow()
        self.reminder_count += 1
    
    def to_dict(self, include_player=False, include_game=False):
        """Convert invitation to dictionary."""
        data = {
            'id': self.id,
            'invitation_type': self.invitation_type,
            'status': self.status,
            'response': self.response,
            'response_method': self.response_method,
            'response_notes': self.response_notes,
            'email_sent_at': self.email_sent_at.isoformat() if self.email_sent_at else None,
            'email_delivered_at': self.email_delivered_at.isoformat() if self.email_delivered_at else None,
            'email_opened_at': self.email_opened_at.isoformat() if self.email_opened_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'reminder_count': self.reminder_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tenant_id': self.tenant_id,
            'game_id': self.game_id,
            'player_id': self.player_id
        }
        
        if include_player and self.player:
            data['player'] = self.player.to_dict()
        
        if include_game and self.game:
            data['game'] = self.game.to_dict()
        
        return data
"""
Invitation and availability response models.
"""
from datetime import datetime
from app import db
from utils.base_model import TenantMixin
from utils.tenant_isolation import enforce_tenant_isolation

@enforce_tenant_isolation
class Invitation(TenantMixin, db.Model):
    """Invitation model for game invitations."""
    
    __tablename__ = 'invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    invitation_type = db.Column(db.String(20), nullable=False)  # 'regular', 'spare'
    status = db.Column(db.String(20), default='sent', nullable=False)  # 'sent', 'opened', 'responded'
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    opened_at = db.Column(db.DateTime, nullable=True)
    responded_at = db.Column(db.DateTime, nullable=True)
    
    # Multi-tenant foreign keys
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False, index=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False, index=True)
    
    # Relationships
    responses = db.relationship('InvitationResponse', backref='invitation', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Invitation {self.id} for Game {self.game_id}>'
    
    def to_dict(self):
        """Convert invitation to dictionary."""
        return {
            'id': self.id,
            'invitation_type': self.invitation_type,
            'status': self.status,
            'sent_at': self.sent_at.isoformat(),
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'tenant_id': self.tenant_id,
            'game_id': self.game_id,
            'player_id': self.player_id
        }

class InvitationResponse(db.Model):
    """Response to game invitations."""
    
    __tablename__ = 'invitation_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    response = db.Column(db.String(10), nullable=False)  # 'yes', 'no'
    response_method = db.Column(db.String(20), nullable=False)  # 'email', 'web'
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Multi-tenant foreign keys
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    invitation_id = db.Column(db.Integer, db.ForeignKey('invitations.id'), nullable=False, index=True)
    
    def __repr__(self):
        return f'<InvitationResponse {self.response} for Invitation {self.invitation_id}>'
    
    def to_dict(self):
        """Convert response to dictionary."""
        return {
            'id': self.id,
            'response': self.response,
            'response_method': self.response_method,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'tenant_id': self.tenant_id,
            'invitation_id': self.invitation_id
        }

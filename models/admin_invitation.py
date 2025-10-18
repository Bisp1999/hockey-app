"""
Admin invitation model for inviting new team managers.
"""
from datetime import datetime, timedelta
import secrets
from app import db

class AdminInvitation(db.Model):
    """Model for storing admin invitations."""
    
    __tablename__ = 'admin_invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='admin', nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, accepted, expired
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Foreign keys
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    invited_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    tenant = db.relationship('Tenant', backref=db.backref('admin_invitations', lazy=True, cascade='all, delete-orphan'))
    invited_by = db.relationship('User', backref=db.backref('sent_admin_invitations', lazy=True))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(days=7)

    def is_valid(self):
        """Check if the invitation is still valid."""
        return self.status == 'pending' and self.expires_at > datetime.utcnow()

    def to_dict(self):
        """Convert invitation to a dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'is_valid': self.is_valid(),
            'expires_at': self.expires_at.isoformat(),
            'created_at': self.created_at.isoformat(),
            'tenant_id': self.tenant_id,
            'invited_by_id': self.invited_by_id
        }
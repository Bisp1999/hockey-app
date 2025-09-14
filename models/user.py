"""
User and admin models with authentication.
"""
from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import secrets

class User(UserMixin, db.Model):
    """User model with multi-tenant support."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'user', 'admin', 'super_admin'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    language = db.Column(db.String(5), default='en', nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Password reset fields
    reset_token = db.Column(db.String(100), nullable=True, index=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    # Email verification fields
    verification_token = db.Column(db.String(100), nullable=True, index=True)
    verification_token_expires = db.Column(db.DateTime, nullable=True)
    
    # Multi-tenant foreign key
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Unique constraint on email within tenant
    __table_args__ = (db.UniqueConstraint('email', 'tenant_id', name='unique_email_per_tenant'),)
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self):
        """Generate password reset token."""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verify password reset token."""
        if (self.reset_token == token and 
            self.reset_token_expires and 
            self.reset_token_expires > datetime.utcnow()):
            return True
        return False
    
    def clear_reset_token(self):
        """Clear password reset token."""
        self.reset_token = None
        self.reset_token_expires = None
    
    def generate_verification_token(self):
        """Generate email verification token."""
        self.verification_token = secrets.token_urlsafe(32)
        self.verification_token_expires = datetime.utcnow() + timedelta(days=7)
        return self.verification_token
    
    def verify_email_token(self, token):
        """Verify email verification token."""
        if (self.verification_token == token and 
            self.verification_token_expires and 
            self.verification_token_expires > datetime.utcnow()):
            self.is_verified = True
            self.verification_token = None
            self.verification_token_expires = None
            return True
        return False
    
    def update_login_info(self):
        """Update login information."""
        self.last_login = datetime.utcnow()
        self.login_count += 1
    
    @property
    def full_name(self):
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.email.split('@')[0]
    
    @property
    def is_admin(self):
        """Check if user has admin privileges."""
        return self.role in ['admin', 'super_admin']
    
    @property
    def is_super_admin(self):
        """Check if user has super admin privileges."""
        return self.role == 'super_admin'
    
    def has_permission(self, permission):
        """Check if user has specific permission."""
        permissions = {
            'user': ['view_own_data', 'edit_own_profile'],
            'admin': ['view_own_data', 'edit_own_profile', 'manage_players', 'manage_games', 'view_statistics'],
            'super_admin': ['*']  # All permissions
        }
        
        user_permissions = permissions.get(self.role, [])
        return '*' in user_permissions or permission in user_permissions
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary."""
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'language': self.language,
            'tenant_id': self.tenant_id,
            'login_count': self.login_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_sensitive:
            data.update({
                'last_login': self.last_login.isoformat() if self.last_login else None,
                'has_reset_token': bool(self.reset_token),
                'has_verification_token': bool(self.verification_token)
            })
        
        return data

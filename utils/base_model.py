"""
Base model class with tenant isolation support.
"""
from flask import g
from app import db
from utils.tenant import get_tenant_id

class TenantMixin:
    """Mixin class to add tenant isolation to models."""
    
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    @classmethod
    def query_for_tenant(cls, tenant_id=None):
        """Get query filtered by tenant."""
        if tenant_id is None:
            tenant_id = get_tenant_id()
        
        if tenant_id:
            return cls.query.filter(cls.tenant_id == tenant_id)
        return cls.query
    
    @classmethod
    def create_for_tenant(cls, **kwargs):
        """Create a new instance for the current tenant."""
        tenant_id = get_tenant_id()
        if tenant_id:
            kwargs['tenant_id'] = tenant_id
        return cls(**kwargs)
    
    def save(self):
        """Save the instance to database."""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete the instance from database."""
        db.session.delete(self)
        db.session.commit()
    
    def update(self, **kwargs):
        """Update the instance with new values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self

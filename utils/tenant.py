"""
Multi-tenant utility functions for tenant context and isolation.
"""
from flask import request, g, current_app, abort
from functools import wraps
from sqlalchemy import text
from app import db

def get_current_tenant():
    """Get the current tenant based on request context."""
    # Check if tenant is already set in g
    if hasattr(g, 'current_tenant'):
        return g.current_tenant
    
    # Extract tenant from subdomain or path
    tenant_identifier = None
    
    # Method 1: Subdomain-based tenant identification
    if current_app.config.get('TENANT_URL_SUBDOMAIN_ENABLED', True):
        host = request.host.lower()
        if '.' in host:
            subdomain = host.split('.')[0]
            if subdomain not in ['www', 'api', 'admin', 'localhost']:
                tenant_identifier = subdomain
    
    # Method 2: Path-based tenant identification
    if not tenant_identifier and current_app.config.get('TENANT_URL_PATH_ENABLED', False):
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) > 0 and path_parts[0] and path_parts[0] not in ['api', 'admin']:
            tenant_identifier = path_parts[0]
    
    # Query database for tenant
    if tenant_identifier:
        from models.tenant import Tenant
        tenant = Tenant.query.filter(
            (Tenant.slug == tenant_identifier) | 
            (Tenant.subdomain == tenant_identifier)
        ).filter(Tenant.is_active == True).first()
        
        if tenant:
            g.current_tenant = tenant
            g.tenant_id = tenant.id
            return tenant
    
    return None

def get_tenant_id():
    """Get the current tenant ID."""
    if hasattr(g, 'tenant_id'):
        return g.tenant_id
    
    tenant = get_current_tenant()
    return tenant.id if tenant else None

def require_tenant(f):
    """Decorator to require tenant context for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant = get_current_tenant()
        if not tenant:
            abort(404, description="Tenant not found")
        return f(*args, **kwargs)
    return decorated_function

def tenant_required(f):
    """Alternative decorator name for requiring tenant context."""
    return require_tenant(f)

def set_tenant_context():
    """Set tenant context for database queries."""
    tenant_id = get_tenant_id()
    if tenant_id:
        # Store in Flask's g object (already done by get_current_tenant)
        # Only set database session variable for PostgreSQL/MySQL, not SQLite
        try:
            # Check database dialect
            if db.engine.dialect.name in ['postgresql', 'mysql']:
                db.session.execute(text("SET @tenant_id = :tenant_id"), {"tenant_id": tenant_id})
        except Exception:
            # Silently fail for SQLite or if there's any issue
            # The tenant_id is already available in g.tenant_id
            pass

def get_tenant_filter():
    """Get tenant filter for database queries."""
    tenant_id = get_tenant_id()
    if tenant_id:
        return {'tenant_id': tenant_id}
    return {}

def validate_tenant_access(model_instance):
    """Validate that the current tenant has access to the model instance."""
    tenant_id = get_tenant_id()
    if tenant_id and hasattr(model_instance, 'tenant_id'):
        if model_instance.tenant_id != tenant_id:
            abort(403, description="Access denied to this resource")
    return True

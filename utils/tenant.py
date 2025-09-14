"""
Multi-tenant utility functions.
"""
from flask import request, g
from models.tenant import Tenant

def get_current_tenant():
    """
    Get the current tenant based on request context.
    Supports both subdomain and path-based tenant identification.
    """
    if hasattr(g, 'current_tenant'):
        return g.current_tenant
    
    tenant = None
    
    # Try subdomain-based tenant identification
    if request.host:
        subdomain = request.host.split('.')[0]
        if subdomain and subdomain != 'www':
            tenant = Tenant.query.filter_by(subdomain=subdomain).first()
    
    # Try path-based tenant identification if subdomain failed
    if not tenant and request.path.startswith('/tenant/'):
        tenant_slug = request.path.split('/')[2]
        tenant = Tenant.query.filter_by(slug=tenant_slug).first()
    
    # Cache the tenant in the request context
    g.current_tenant = tenant
    return tenant

def require_tenant():
    """Decorator to ensure a valid tenant context exists."""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            tenant = get_current_tenant()
            if not tenant:
                return {'error': 'Invalid tenant context'}, 400
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

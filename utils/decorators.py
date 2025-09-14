"""
Custom decorators for multi-tenant application.
"""
from functools import wraps
from flask import g, jsonify, abort
from utils.tenant import get_current_tenant, get_tenant_id, validate_tenant_access

def tenant_required(f):
    """Decorator to require tenant context for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant = get_current_tenant()
        if not tenant:
            if hasattr(f, '__name__') and 'api' in f.__name__:
                return jsonify({'error': 'Tenant context required'}), 400
            abort(404, description="Tenant not found")
        return f(*args, **kwargs)
    return decorated_function

def tenant_admin_required(f):
    """Decorator to require tenant admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        
        # First check if tenant context exists
        tenant = get_current_tenant()
        if not tenant:
            return jsonify({'error': 'Tenant context required'}), 400
        
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user belongs to this tenant and is admin
        if (current_user.tenant_id != tenant.id or 
            current_user.role not in ['admin', 'super_admin']):
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def validate_tenant_resource(model_class):
    """Decorator to validate that a resource belongs to the current tenant."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            tenant_id = get_tenant_id()
            if not tenant_id:
                return jsonify({'error': 'Tenant context required'}), 400
            
            # Get resource ID from kwargs or args
            resource_id = kwargs.get('id') or kwargs.get('resource_id')
            if not resource_id and args:
                resource_id = args[0]
            
            if resource_id:
                # Query the resource and validate tenant access
                resource = model_class.query.get_or_404(resource_id)
                validate_tenant_access(resource)
                
                # Add resource to kwargs for the route function
                kwargs['resource'] = resource
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def inject_tenant_filter(f):
    """Decorator to automatically inject tenant filter into database queries."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant_id = get_tenant_id()
        if tenant_id:
            kwargs['tenant_id'] = tenant_id
        return f(*args, **kwargs)
    return decorated_function

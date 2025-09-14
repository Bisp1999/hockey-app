"""
Middleware for multi-tenant request processing.
"""
from flask import request, g, current_app
from utils.tenant import get_current_tenant, set_tenant_context

class TenantMiddleware:
    """Middleware to handle tenant context for each request."""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with the Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Process tenant context before each request."""
        # Skip tenant processing for certain paths
        if self.should_skip_tenant_processing():
            return
        
        # Get current tenant
        tenant = get_current_tenant()
        
        # Set tenant context for database queries
        if tenant:
            set_tenant_context()
            g.tenant = tenant
            g.tenant_id = tenant.id
        
        # For API routes, ensure tenant is present
        if request.path.startswith('/api/') and not tenant:
            from flask import jsonify
            return jsonify({'error': 'Tenant context required'}), 400
    
    def after_request(self, response):
        """Clean up after request processing."""
        # Clean up tenant context
        if hasattr(g, 'tenant'):
            delattr(g, 'tenant')
        if hasattr(g, 'tenant_id'):
            delattr(g, 'tenant_id')
        if hasattr(g, 'current_tenant'):
            delattr(g, 'current_tenant')
        
        return response
    
    def should_skip_tenant_processing(self):
        """Determine if tenant processing should be skipped for this request."""
        skip_paths = [
            '/health',
            '/metrics',
            '/favicon.ico',
            '/static/',
            '/_debug_toolbar/',
        ]
        
        # Skip for static files and health checks
        for path in skip_paths:
            if request.path.startswith(path):
                return True
        
        # Skip for admin routes (global admin interface)
        if request.path.startswith('/admin/'):
            return True
        
        # Skip for tenant registration/onboarding
        if request.path in ['/register', '/signup', '/onboard']:
            return True
        
        return False

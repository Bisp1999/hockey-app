"""
Middleware for multi-tenant request processing.
"""
from flask import request, g, current_app, session, jsonify
from flask_login import current_user, logout_user
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
                
        # Skip tenant check for certain admin endpoints
        if request.path == '/api/admin/init-db':
            return None
        
        # Skip OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return
        
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
            return jsonify({'error': 'Tenant context required'}), 400
        
        # Enforce tenant-aware sessions: if authenticated, session tenant must match request tenant
        if request.path.startswith('/api/') and current_user.is_authenticated and tenant:
            sess_tenant_id = session.get('tenant_id')
            if sess_tenant_id is None:
                # Backfill missing session binding to current tenant
                session['tenant_id'] = tenant.id
            elif sess_tenant_id != tenant.id:
                # Mismatch: logout to prevent cross-tenant session leakage
                logout_user()
                session.pop('tenant_id', None)
                return jsonify({'error': 'Tenant mismatch. Please sign in for this tenant.'}), 401
    
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
            '/api/email/test-simple',
            '/api/email/test-invitation', 
            '/api/invitations/respond/',  
            '/api/auth/me',  # Add this - allow checking auth status
            '/api/auth/csrf-token',  # Add this too
            '/api/auth/login',  # Add this - allow login without tenant context first
            '/api/auth/logout',  # Add this too
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

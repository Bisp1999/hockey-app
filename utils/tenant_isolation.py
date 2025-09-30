"""
Enhanced tenant isolation middleware with automatic query filtering.
"""
from flask import g, request, has_request_context
from sqlalchemy import event
from sqlalchemy.orm import Query
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class TenantIsolationMiddleware:
    """Comprehensive tenant isolation middleware."""
    
    def __init__(self, app=None, db=None):
        self.app = app
        self.db = db
        if app and db:
            self.init_app(app, db)
    
    def init_app(self, app, db):
        """Initialize the middleware with Flask app and SQLAlchemy db."""
        self.app = app
        self.db = db
        
        # Set up request hooks
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Set up SQLAlchemy event listeners
        self.setup_query_listeners()
        
        logger.info("Tenant isolation middleware initialized")
    
    def before_request(self):
        """Set up tenant context before each request."""
        from utils.tenant import detect_tenant_from_request, set_tenant_context
        
        # Skip tenant detection for certain routes
        if self.should_skip_tenant_detection():
            return
        
        try:
            tenant = detect_tenant_from_request()
            if tenant:
                set_tenant_context(tenant)
                logger.debug(f"Tenant context set: {tenant.slug}")
            else:
                logger.debug("No tenant detected for request")
        except Exception as e:
            logger.error(f"Error setting tenant context: {e}")
    
    def after_request(self, response):
        """Clean up tenant context after request."""
        if hasattr(g, 'current_tenant'):
            delattr(g, 'current_tenant')
        if hasattr(g, 'current_tenant_id'):
            delattr(g, 'current_tenant_id')
        return response
    
    def should_skip_tenant_detection(self):
        """Check if tenant detection should be skipped for this request."""
        skip_paths = [
            '/health',
            '/api/tenants/register',
            '/static/',
            '/_debug_toolbar/'
        ]
        
        path = request.path
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def setup_query_listeners(self):
        """Set up SQLAlchemy event listeners for automatic tenant filtering."""
        
        @event.listens_for(self.db.session, 'before_flush')
        def before_flush(session, flush_context, instances):
            """Ensure all new objects have tenant_id set."""
            from utils.tenant import get_current_tenant_id
            
            if not has_request_context():
                return
            
            tenant_id = get_current_tenant_id()
            if not tenant_id:
                return
            
            for obj in session.new:
                if hasattr(obj, 'tenant_id') and obj.tenant_id is None:
                    obj.tenant_id = tenant_id
                    logger.debug(f"Auto-assigned tenant_id {tenant_id} to {obj.__class__.__name__}")
        
        @event.listens_for(Query, 'before_bulk_update')
        def before_bulk_update(query_context):
            """Filter bulk updates by tenant."""
            self._filter_bulk_operation(query_context)
        
        @event.listens_for(Query, 'before_bulk_delete')
        def before_bulk_delete(query_context):
            """Filter bulk deletes by tenant."""
            self._filter_bulk_operation(query_context)
    
    def _filter_bulk_operation(self, query_context):
        """Apply tenant filter to bulk operations."""
        from utils.tenant import get_current_tenant_id
        
        if not has_request_context():
            return
        
        model_class = query_context.mapper.class_
        if not hasattr(model_class, 'tenant_id'):
            return
        
        tenant_id = get_current_tenant_id()
        if tenant_id:
            # Add tenant filter to the query
            query_context.whereclause = query_context.whereclause & (
                model_class.tenant_id == tenant_id
            )
            logger.debug(f"Applied tenant filter to bulk operation on {model_class.__name__}")

def tenant_required(f):
    """Decorator to ensure a tenant context is available."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from utils.tenant import get_current_tenant
        from flask import jsonify
        
        tenant = get_current_tenant()
        if not tenant:
            return jsonify({'error': 'Tenant context required'}), 400
        
        return f(*args, **kwargs)
    return decorated_function

def validate_tenant_access(model_instance):
    """Validate that the current user can access the given model instance."""
    from utils.tenant import get_current_tenant_id
    from flask_login import current_user
    
    if not hasattr(model_instance, 'tenant_id'):
        return True
    
    current_tenant_id = get_current_tenant_id()
    if not current_tenant_id:
        return False
    
    # Check if the model belongs to the current tenant
    if model_instance.tenant_id != current_tenant_id:
        logger.warning(f"Tenant access violation: user tried to access {model_instance.__class__.__name__} "
                      f"from tenant {model_instance.tenant_id} while in tenant {current_tenant_id}")
        return False
    
    return True

def enforce_tenant_isolation(model_class):
    """Class decorator to enforce tenant isolation on a model."""
    from flask import has_request_context
    
    # Store reference to the original query class
    _original_query_class = model_class.__dict__.get('query_class')
    
    # Don't try to access .query at decoration time - it requires app context
    # Instead, we'll create a custom query class that filters automatically
    
    class TenantQuery(model_class.query_class if hasattr(model_class, 'query_class') else db.Query):
        def get(self, ident):
            # Override get to add tenant filtering
            obj = super().get(ident)
            if obj and hasattr(obj, 'tenant_id'):
                from utils.tenant import get_current_tenant_id
                if has_request_context():
                    tenant_id = get_current_tenant_id()
                    if tenant_id and obj.tenant_id != tenant_id:
                        return None
            return obj
        
        def __iter__(self):
            # Override iteration to add tenant filtering
            from utils.tenant import get_current_tenant_id
            
            if has_request_context() and hasattr(model_class, 'tenant_id'):
                tenant_id = get_current_tenant_id()
                if tenant_id:
                    # Add tenant filter to the query
                    return super().filter(model_class.tenant_id == tenant_id).__iter__()
            
            return super().__iter__()
    
    # Set the custom query class
    model_class.query_class = TenantQuery
    
    return model_class

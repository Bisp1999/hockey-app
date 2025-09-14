"""
Automatic tenant-aware query filtering for SQLAlchemy models.
"""
from flask import g, has_request_context
from sqlalchemy import event
from sqlalchemy.orm import Query
from sqlalchemy.orm.events import InstanceEvents
from utils.tenant import get_current_tenant_id

class TenantQueryFilter:
    """Automatic tenant filtering for SQLAlchemy queries."""
    
    def __init__(self, db):
        self.db = db
        self.setup_query_filters()
    
    def setup_query_filters(self):
        """Set up automatic query filtering for tenant-aware models."""
        
        @event.listens_for(Query, 'before_bulk_update')
        def before_bulk_update(query_context):
            """Filter bulk updates by tenant."""
            self._apply_tenant_filter(query_context.mapper.class_, query_context)
        
        @event.listens_for(Query, 'before_bulk_delete')
        def before_bulk_delete(query_context):
            """Filter bulk deletes by tenant."""
            self._apply_tenant_filter(query_context.mapper.class_, query_context)
    
    def _apply_tenant_filter(self, model_class, query_context):
        """Apply tenant filter to query if model has tenant_id."""
        if not has_request_context():
            return
        
        if hasattr(model_class, 'tenant_id'):
            tenant_id = get_current_tenant_id()
            if tenant_id:
                query_context = query_context.filter(model_class.tenant_id == tenant_id)
    
    def filter_query(self, query, model_class):
        """Apply tenant filter to a query."""
        if not has_request_context():
            return query
        
        if hasattr(model_class, 'tenant_id'):
            tenant_id = get_current_tenant_id()
            if tenant_id:
                return query.filter(model_class.tenant_id == tenant_id)
        
        return query

# Global query filter instance
query_filter = None

def init_query_filter(db):
    """Initialize the global query filter."""
    global query_filter
    query_filter = TenantQueryFilter(db)
    return query_filter

def get_query_filter():
    """Get the global query filter instance."""
    return query_filter

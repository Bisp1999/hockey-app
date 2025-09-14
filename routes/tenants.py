"""
Tenant management routes for multi-tenant architecture.
"""
from flask import Blueprint, request, jsonify, g
from models.tenant import Tenant
from utils.decorators import tenant_admin_required
from utils.tenant import get_current_tenant
from app import db

tenants_bp = Blueprint('tenants', __name__)

@tenants_bp.route('/', methods=['GET'])
def get_current_tenant_info():
    """Get current tenant information."""
    tenant = get_current_tenant()
    if not tenant:
        return jsonify({'error': 'Tenant not found'}), 404
    
    return jsonify({
        'tenant': tenant.to_dict()
    })

@tenants_bp.route('/config', methods=['GET'])
def get_tenant_config():
    """Get tenant configuration settings."""
    tenant = get_current_tenant()
    if not tenant:
        return jsonify({'error': 'Tenant not found'}), 404
    
    config = {
        'position_mode': tenant.position_mode,
        'team_name_1': tenant.team_name_1,
        'team_name_2': tenant.team_name_2,
        'team_color_1': tenant.team_color_1,
        'team_color_2': tenant.team_color_2,
        'assignment_mode': tenant.assignment_mode
    }
    
    return jsonify({'config': config})

@tenants_bp.route('/config', methods=['PUT'])
@tenant_admin_required
def update_tenant_config():
    """Update tenant configuration settings."""
    tenant = get_current_tenant()
    if not tenant:
        return jsonify({'error': 'Tenant not found'}), 404
    
    data = request.get_json()
    
    # Validate position_mode
    if 'position_mode' in data:
        if data['position_mode'] not in ['three_position', 'two_position']:
            return jsonify({'error': 'Invalid position_mode'}), 400
        tenant.position_mode = data['position_mode']
    
    # Validate assignment_mode
    if 'assignment_mode' in data:
        if data['assignment_mode'] not in ['manual', 'automatic']:
            return jsonify({'error': 'Invalid assignment_mode'}), 400
        tenant.assignment_mode = data['assignment_mode']
    
    # Update team names and colors
    if 'team_name_1' in data:
        tenant.team_name_1 = data['team_name_1'][:50]  # Limit length
    if 'team_name_2' in data:
        tenant.team_name_2 = data['team_name_2'][:50]
    if 'team_color_1' in data:
        tenant.team_color_1 = data['team_color_1'][:20]
    if 'team_color_2' in data:
        tenant.team_color_2 = data['team_color_2'][:20]
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Tenant configuration updated successfully',
            'config': {
                'position_mode': tenant.position_mode,
                'team_name_1': tenant.team_name_1,
                'team_name_2': tenant.team_name_2,
                'team_color_1': tenant.team_color_1,
                'team_color_2': tenant.team_color_2,
                'assignment_mode': tenant.assignment_mode
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update configuration'}), 500

@tenants_bp.route('/register', methods=['POST'])
def register_tenant():
    """Register a new tenant (public endpoint)."""
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('name'):
        return jsonify({'error': 'Tenant name is required'}), 400
    
    name = data['name'].strip()
    subdomain = data.get('subdomain', '').strip().lower()
    
    # Validate subdomain format
    if subdomain and not Tenant.is_valid_subdomain(subdomain):
        return jsonify({'error': 'Invalid subdomain format'}), 400
    
    # Generate slug from name
    slug = Tenant.generate_slug(name)
    
    # Check for existing tenant with same slug or subdomain
    existing = Tenant.query.filter(
        (Tenant.slug == slug) | 
        (Tenant.subdomain == subdomain if subdomain else False)
    ).first()
    
    if existing:
        if existing.slug == slug:
            return jsonify({'error': 'A tenant with this name already exists'}), 409
        if existing.subdomain == subdomain:
            return jsonify({'error': 'This subdomain is already taken'}), 409
    
    # Create new tenant
    tenant = Tenant(
        name=name,
        slug=slug,
        subdomain=subdomain if subdomain else None,
        position_mode=data.get('position_mode', 'three_position'),
        assignment_mode=data.get('assignment_mode', 'manual')
    )
    
    try:
        db.session.add(tenant)
        db.session.commit()
        
        return jsonify({
            'message': 'Tenant registered successfully',
            'tenant': tenant.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to register tenant'}), 500

@tenants_bp.route('/check-availability', methods=['POST'])
def check_availability():
    """Check if tenant name/subdomain is available."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request data required'}), 400
    
    results = {}
    
    # Check name/slug availability
    if 'name' in data:
        slug = Tenant.generate_slug(data['name'])
        existing = Tenant.query.filter(Tenant.slug == slug).first()
        results['name_available'] = existing is None
        results['generated_slug'] = slug
    
    # Check subdomain availability
    if 'subdomain' in data:
        subdomain = data['subdomain'].strip().lower()
        if subdomain:
            if not Tenant.is_valid_subdomain(subdomain):
                results['subdomain_valid'] = False
                results['subdomain_available'] = False
            else:
                existing = Tenant.query.filter(Tenant.subdomain == subdomain).first()
                results['subdomain_valid'] = True
                results['subdomain_available'] = existing is None
        else:
            results['subdomain_valid'] = True
            results['subdomain_available'] = True
    
    return jsonify(results)

"""
Team configuration routes.
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from models.tenant import Tenant
from utils.tenant import get_current_tenant
from utils.decorators import tenant_admin_required
from app import db

teams_bp = Blueprint('teams', __name__)

@teams_bp.route('/config', methods=['GET'])
@login_required
def get_team_config():
    """Get current tenant's team configuration."""
    tenant = get_current_tenant()
    
    return jsonify({
        'team_name_1': tenant.team_name_1,
        'team_name_2': tenant.team_name_2,
        'team_color_1': tenant.team_color_1,
        'team_color_2': tenant.team_color_2,
        'default_goaltenders': tenant.default_goaltenders,
        'default_defence': tenant.default_defence,
        'default_forwards': tenant.default_forwards,
        'default_skaters': tenant.default_skaters
    })

@teams_bp.route('/config', methods=['PUT'])
@tenant_admin_required
def update_team_config():
    """Update team configuration (admin only)."""
    tenant = get_current_tenant()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request data required'}), 400
    
    # Update team names
    if 'team_name_1' in data:
        name = data['team_name_1'].strip()
        if not name:
            return jsonify({'error': 'Team 1 name cannot be empty'}), 400
        tenant.team_name_1 = name
    
    if 'team_name_2' in data:
        name = data['team_name_2'].strip()
        if not name:
            return jsonify({'error': 'Team 2 name cannot be empty'}), 400
        tenant.team_name_2 = name
    
    # Update team colors
    if 'team_color_1' in data:
        color = data['team_color_1'].strip().lower()
        if not color:
            return jsonify({'error': 'Team 1 color cannot be empty'}), 400
        tenant.team_color_1 = color
    
    if 'team_color_2' in data:
        color = data['team_color_2'].strip().lower()
        if not color:
            return jsonify({'error': 'Team 2 color cannot be empty'}), 400
        tenant.team_color_2 = color
    
    # Update default player requirements
    if 'default_goaltenders' in data:
        tenant.default_goaltenders = int(data['default_goaltenders'])
    if 'default_defence' in data:
        tenant.default_defence = int(data['default_defence']) if data['default_defence'] else None
    if 'default_forwards' in data:
        tenant.default_forwards = int(data['default_forwards']) if data['default_forwards'] else None
    if 'default_skaters' in data:
        tenant.default_skaters = int(data['default_skaters']) if data['default_skaters'] else None

    try:
        db.session.commit()
        return jsonify({
            'message': 'Team configuration updated successfully',
            'config': {
                'team_name_1': tenant.team_name_1,
                'team_name_2': tenant.team_name_2,
                'team_color_1': tenant.team_color_1,
                'team_color_2': tenant.team_color_2,
                'default_goaltenders': tenant.default_goaltenders,
                'default_defence': tenant.default_defence,
                'default_forwards': tenant.default_forwards,
                'default_skaters': tenant.default_skaters
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update team configuration'}), 500
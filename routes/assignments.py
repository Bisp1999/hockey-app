"""
Assignment management API endpoints.
"""
from flask import Blueprint, request, jsonify
from utils.decorators import tenant_admin_required

assignments_bp = Blueprint('assignments', __name__)

@assignments_bp.route('/', methods=['GET'])
def get_assignments():
    """Get all assignments for current tenant."""
    return {'message': 'Assignments endpoint - to be implemented'}

@assignments_bp.route('/', methods=['POST'])
def create_assignment():
    """Create a new assignment."""
    return {'message': 'Create assignment endpoint - to be implemented'}

@assignments_bp.route('/<int:assignment_id>', methods=['PUT'])
def update_assignment(assignment_id):
    """Update specific assignment."""
    return {'message': f'Update assignment {assignment_id} endpoint - to be implemented'}

@assignments_bp.route('/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(assignment_id):
    """Delete specific assignment."""
    return {'message': f'Delete assignment {assignment_id} endpoint - to be implemented'}

@assignments_bp.route('/game/<int:game_id>', methods=['GET'])
def get_game_assignments(game_id):
    """Get all assignments for a specific game."""
    return {'message': f'Get assignments for game {game_id} endpoint - to be implemented'}

@assignments_bp.route('/game/<int:game_id>/auto-assign', methods=['POST'])
@tenant_admin_required
def auto_assign_teams(game_id):
    """Automatically assign players to balanced teams."""
    from services.team_assignment_service import TeamAssignmentService
    
    data = request.get_json() or {}
    player_ids = data.get('player_ids', [])
    
    if not player_ids:
        return jsonify({'error': 'No players provided'}), 400
    
    result = TeamAssignmentService.auto_assign_teams(game_id, player_ids)
    
    if 'error' in result:
        return jsonify(result), 400
    
    return jsonify(result), 200

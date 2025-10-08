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

@assignments_bp.route('/game/<int:game_id>', methods=['GET'])
def get_game_assignments_detailed(game_id):
    """Get game details with team assignments and balance info."""
    from models.game import Game
    from models.assignment import Assignment
    from models.player import Player
    from services.team_assignment_service import TeamAssignmentService
    from app import db
    
    game = Game.query.get(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    # Get all assignments for this game
    assignments = Assignment.query.filter_by(game_id=game_id).all()
    
    # Group by team
    team_1_players = []
    team_2_players = []
    team_1_score = 0
    team_2_score = 0
    
    for assignment in assignments:
        player = Player.query.get(assignment.player_id)
        if player:
            player_dict = player.to_dict()
            player_dict['assignment_id'] = assignment.id
            score = TeamAssignmentService.calculate_player_score(player)
            
            if assignment.team_number == 1:
                team_1_players.append(player_dict)
                team_1_score += score
            elif assignment.team_number == 2:
                team_2_players.append(player_dict)
                team_2_score += score
    
    return jsonify({
        'game': game.to_dict(),
        'team_1': {
            'players': team_1_players,
            'total_score': team_1_score,
            'count': len(team_1_players)
        },
        'team_2': {
            'players': team_2_players,
            'total_score': team_2_score,
            'count': len(team_2_players)
        },
        'balance_difference': abs(team_1_score - team_2_score)
    }), 200

@assignments_bp.route('/game/<int:game_id>/move-player', methods=['PUT'])
@tenant_admin_required
def move_player_to_team(game_id):
    """Move a player to a different team."""
    from models.assignment import Assignment
    from app import db
    
    data = request.get_json() or {}
    player_id = data.get('player_id')
    new_team = data.get('team_number')
    
    if not player_id or not new_team:
        return jsonify({'error': 'player_id and team_number required'}), 400
    
    if new_team not in [1, 2]:
        return jsonify({'error': 'team_number must be 1 or 2'}), 400
    
    assignment = Assignment.query.filter_by(
        game_id=game_id,
        player_id=player_id
    ).first()
    
    if not assignment:
        return jsonify({'error': 'Assignment not found'}), 404
    
    assignment.team_number = new_team
    db.session.commit()
    
    return jsonify({'success': True, 'assignment': assignment.to_dict()}), 200

@assignments_bp.route('/game/<int:game_id>/swap-players', methods=['PUT'])
@tenant_admin_required
def swap_players(game_id):
    """Swap two players between teams."""
    from models.assignment import Assignment
    from app import db
    
    data = request.get_json() or {}
    player1_id = data.get('player1_id')
    player2_id = data.get('player2_id')
    
    if not player1_id or not player2_id:
        return jsonify({'error': 'player1_id and player2_id required'}), 400
    
    assignment1 = Assignment.query.filter_by(
        game_id=game_id,
        player_id=player1_id
    ).first()
    
    assignment2 = Assignment.query.filter_by(
        game_id=game_id,
        player_id=player2_id
    ).first()
    
    if not assignment1 or not assignment2:
        return jsonify({'error': 'One or both assignments not found'}), 404
    
    # Swap teams
    assignment1.team_number, assignment2.team_number = assignment2.team_number, assignment1.team_number
    db.session.commit()
    
    return jsonify({
        'success': True,
        'assignments': [assignment1.to_dict(), assignment2.to_dict()]
    }), 200
"""
Statistics tracking API endpoints.
"""
from flask import Blueprint

statistics_bp = Blueprint('statistics', __name__)

@statistics_bp.route('/', methods=['GET'])
def get_statistics():
    """Get statistics for current tenant."""
    return {'message': 'Statistics endpoint - to be implemented'}

@statistics_bp.route('/game/<int:game_id>', methods=['POST'])
def record_game_statistics(game_id):
    """Record statistics for a specific game."""
    return {'message': f'Record statistics for game {game_id} endpoint - to be implemented'}

@statistics_bp.route('/player/<int:player_id>', methods=['GET'])
def get_player_statistics(player_id):
    """Get statistics for a specific player."""
    return {'message': f'Get statistics for player {player_id} endpoint - to be implemented'}

@statistics_bp.route('/goaltender', methods=['GET'])
def get_goaltender_statistics():
    """Get goaltender-specific statistics."""
    return {'message': 'Goaltender statistics endpoint - to be implemented'}

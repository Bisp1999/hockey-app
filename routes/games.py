"""
Game scheduling and management API endpoints.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from datetime import datetime, date, time as time_class
from models.game import Game
from models.tenant import Tenant
from utils.tenant import get_current_tenant
from utils.decorators import tenant_admin_required
from app import db
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

games_bp = Blueprint('games', __name__)
limiter = Limiter(key_func=get_remote_address)

@games_bp.route('/', methods=['GET'])
@login_required
def get_games():
    """Get all games for current tenant with optional filtering."""
    tenant = get_current_tenant()
    
    # Build query
    query = Game.query.filter_by(tenant_id=tenant.id)
    
    # Filter by date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        try:
            start = datetime.fromisoformat(start_date).date()
            query = query.filter(Game.date >= start)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format'}), 400
    
    if end_date:
        try:
            end = datetime.fromisoformat(end_date).date()
            query = query.filter(Game.date <= end)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format'}), 400
    
    # Filter by status
    status = request.args.get('status')
    if status:
        query = query.filter(Game.status == status)
    
    # Sort by date and time
    games = query.order_by(Game.date, Game.time).all()
    
    return jsonify({
        'games': [game.to_dict() for game in games],
        'total': len(games)
    })

@games_bp.route('/', methods=['POST'])
@tenant_admin_required
@limiter.limit("20 per minute")
def create_game():
    """Create a new game."""
    tenant = get_current_tenant()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request data required'}), 400
    
    # Validate required fields
    if 'date' not in data:
        return jsonify({'error': 'Date is required'}), 400
    if 'time' not in data:
        return jsonify({'error': 'Time is required'}), 400
    if 'venue' not in data or not data['venue'].strip():
        return jsonify({'error': 'Venue is required'}), 400
    
    # Parse date and time
    try:
        game_date = datetime.fromisoformat(data['date']).date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DD)'}), 400
    
    try:
        # Parse time string (HH:MM:SS format)
        time_str = data['time']
        if isinstance(time_str, str):
            time_parts = time_str.split(':')
            if len(time_parts) >= 2:
                game_time = time_class(
                    int(time_parts[0]), 
                    int(time_parts[1]), 
                    int(time_parts[2]) if len(time_parts) > 2 else 0
                )
            else:
                raise ValueError("Invalid time format")
        else:
            raise ValueError("Time must be a string")
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid time format: {str(e)}'}), 400
    
    # Use tenant's team configuration as defaults
    team_1_name = data.get('team_1_name', tenant.team_name_1)
    team_2_name = data.get('team_2_name', tenant.team_name_2)
    team_1_color = data.get('team_1_color', tenant.team_color_1)
    team_2_color = data.get('team_2_color', tenant.team_color_2)
    
    # Create game
    game = Game(
        date=game_date,
        time=game_time,
        venue=data['venue'].strip(),
        status=data.get('status', 'scheduled'),
        goaltenders_needed=data.get('goaltenders_needed', 2),
        defence_needed=data.get('defence_needed'),
        forwards_needed=data.get('forwards_needed'),
        skaters_needed=data.get('skaters_needed'),
        team_1_name=team_1_name,
        team_2_name=team_2_name,
        team_1_color=team_1_color,
        team_2_color=team_2_color,
        is_recurring=data.get('is_recurring', False),
        recurrence_pattern=data.get('recurrence_pattern'),
        recurrence_end_date=data.get('recurrence_end_date'),
        tenant_id=tenant.id
    )
    
    try:
        db.session.add(game)
        db.session.commit()
        return jsonify({
            'message': 'Game created successfully',
            'game': game.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to create game: {e}")
        return jsonify({'error': 'Failed to create game'}), 500

@games_bp.route('/<int:game_id>', methods=['GET'])
@login_required
def get_game(game_id):
    """Get specific game by ID."""
    tenant = get_current_tenant()
    game = Game.query.filter_by(id=game_id, tenant_id=tenant.id).first_or_404()
    
    return jsonify({'game': game.to_dict()})

@games_bp.route('/<int:game_id>', methods=['PUT'])
@tenant_admin_required
@limiter.limit("20 per minute")
def update_game(game_id):
    """Update specific game."""
    tenant = get_current_tenant()
    game = Game.query.filter_by(id=game_id, tenant_id=tenant.id).first_or_404()
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request data required'}), 400
    
    # Update fields if provided
    if 'date' in data:
        try:
            game.date = datetime.fromisoformat(data['date']).date()
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid date format'}), 400
    
    if 'time' in data:
        try:
            game.time = datetime.fromisoformat(data['time']).time()
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid time format'}), 400
    
    if 'venue' in data:
        venue = data['venue'].strip()
        if not venue:
            return jsonify({'error': 'Venue cannot be empty'}), 400
        game.venue = venue
    
    if 'status' in data:
        if data['status'] not in ['scheduled', 'confirmed', 'cancelled', 'completed']:
            return jsonify({'error': 'Invalid status'}), 400
        game.status = data['status']
    
    # Update player requirements
    if 'goaltenders_needed' in data:
        game.goaltenders_needed = int(data['goaltenders_needed'])
    if 'defence_needed' in data:
        game.defence_needed = int(data['defence_needed']) if data['defence_needed'] else None
    if 'forwards_needed' in data:
        game.forwards_needed = int(data['forwards_needed']) if data['forwards_needed'] else None
    if 'skaters_needed' in data:
        game.skaters_needed = int(data['skaters_needed']) if data['skaters_needed'] else None
    
    # Update team info
    if 'team_1_name' in data:
        game.team_1_name = data['team_1_name']
    if 'team_2_name' in data:
        game.team_2_name = data['team_2_name']
    if 'team_1_color' in data:
        game.team_1_color = data['team_1_color']
    if 'team_2_color' in data:
        game.team_2_color = data['team_2_color']
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Game updated successfully',
            'game': game.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to update game: {e}")
        return jsonify({'error': 'Failed to update game'}), 500

@games_bp.route('/<int:game_id>', methods=['DELETE'])
@tenant_admin_required
@limiter.limit("20 per minute")
def delete_game(game_id):
    """Delete specific game."""
    tenant = get_current_tenant()
    game = Game.query.filter_by(id=game_id, tenant_id=tenant.id).first_or_404()
    
    try:
        db.session.delete(game)
        db.session.commit()
        return jsonify({'message': 'Game deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to delete game: {e}")
        return jsonify({'error': 'Failed to delete game'}), 500

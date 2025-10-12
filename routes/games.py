"""
Game scheduling and management API endpoints.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from datetime import datetime, date, time as time_class, timedelta
from models.game import Game
from models.tenant import Tenant
from utils.tenant import get_current_tenant
from utils.decorators import tenant_admin_required
from app import db
from services.invitation_service import InvitationService

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

games_bp = Blueprint('games', __name__)
limiter = Limiter(key_func=get_remote_address)

def generate_recurring_games(base_game_data, start_date, end_date, pattern, tenant_id):
    """Generate recurring games based on pattern."""
    games = []
    current_date = start_date
    
    # Determine interval
    interval = timedelta(days=7) if pattern == 'weekly' else timedelta(days=14)
    
    while current_date <= end_date:
        game = Game(
            date=current_date,
            time=base_game_data['time'],
            venue=base_game_data['venue'],
            status=base_game_data.get('status', 'scheduled'),
            goaltenders_needed=base_game_data.get('goaltenders_needed', 2),
            defence_needed=base_game_data.get('defence_needed'),
            forwards_needed=base_game_data.get('forwards_needed'),
            skaters_needed=base_game_data.get('skaters_needed'),
            team_1_name=base_game_data.get('team_1_name'),
            team_2_name=base_game_data.get('team_2_name'),
            team_1_color=base_game_data.get('team_1_color'),
            team_2_color=base_game_data.get('team_2_color'),
            is_recurring=True,
            recurrence_pattern=pattern,
            recurrence_end_date=end_date,
            tenant_id=tenant_id
        )
        games.append(game)
        current_date += interval
    
    return games

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
    
    # Calculate skaters_needed based on position mode
    defence_needed = data.get('defence_needed')
    forwards_needed = data.get('forwards_needed')
    skaters_needed = data.get('skaters_needed')

    # For 3-position mode, calculate skaters from defence + forwards
    if tenant.position_mode == 'three_position' and defence_needed and forwards_needed:
        skaters_needed = int(defence_needed) + int(forwards_needed)
    elif skaters_needed:
        skaters_needed = int(skaters_needed)

    # Create game
    if data.get('is_recurring') and data.get('recurrence_pattern') and data.get('recurrence_end_date'):
        # Generate recurring games
        try:
            recurrence_end = datetime.fromisoformat(data['recurrence_end_date']).date()
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid recurrence end date format'}), 400
    
        if recurrence_end < game_date:
            return jsonify({'error': 'Recurrence end date must be after start date'}), 400
    
        # Prepare base game data
        base_game_data = {
            'time': game_time,
            'venue': data['venue'].strip(),
            'status': data.get('status', 'scheduled'),
            'goaltenders_needed': data.get('goaltenders_needed', 2),
            'defence_needed': int(defence_needed) if defence_needed else None,
            'forwards_needed': int(forwards_needed) if forwards_needed else None,
            'skaters_needed': skaters_needed,
            'team_1_name': team_1_name,
            'team_2_name': team_2_name,
            'team_1_color': team_1_color,
            'team_2_color': team_2_color
        }
    
        # Generate all recurring games
        games = generate_recurring_games(
            base_game_data,
            game_date,
            recurrence_end,
            data['recurrence_pattern'],
            tenant.id
        )
    
        try:
            for game in games:
                db.session.add(game)
            db.session.commit()
            
            # Auto-send invitations to regular players for each game if enabled
            auto_invite = data.get('auto_invite_regular_players', True)
            total_invitations = {'sent': 0, 'failed': 0}
            
            if auto_invite:
                for game in games:
                    summary = InvitationService.auto_invite_regular_players(game.id)
                    total_invitations['sent'] += summary.get('sent', 0)
                    total_invitations['failed'] += summary.get('failed', 0)
                current_app.logger.info(f"Auto-invited regular players for {len(games)} games: {total_invitations}")
            
            response_data = {
                'message': f'{len(games)} recurring games created successfully',
                'games': [g.to_dict() for g in games],
                'count': len(games)
            }
            
            if auto_invite:
                response_data['invitations'] = total_invitations
            
            return jsonify(response_data), 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create recurring games: {e}")
            return jsonify({'error': 'Failed to create recurring games'}), 500
    else:
        # Create single game
        game = Game(
            date=game_date,
            time=game_time,
            venue=data['venue'].strip(),
            status=data.get('status', 'scheduled'),
            goaltenders_needed=data.get('goaltenders_needed', 2),
            defence_needed=int(defence_needed) if defence_needed else None,
            forwards_needed=int(forwards_needed) if forwards_needed else None,
            skaters_needed=skaters_needed,
            team_1_name=team_1_name,
            team_2_name=team_2_name,
            team_1_color=team_1_color,
            team_2_color=team_2_color,
            is_recurring=False,
            recurrence_pattern=None,
            recurrence_end_date=None,
            tenant_id=tenant.id
        )
    
        try:
            db.session.add(game)
            db.session.commit()
            
            # Auto-send invitations to regular players if enabled
            auto_invite = data.get('auto_invite_regular_players', False)
            invitation_summary = None
            
            if auto_invite:
                invitation_summary = InvitationService.auto_invite_regular_players(game.id)
                current_app.logger.info(f"Auto-invited regular players: {invitation_summary}")
            
            response_data = {
                'message': 'Game created successfully',
                'game': game.to_dict()
            }
            
            if invitation_summary:
                response_data['invitations'] = invitation_summary
            
            return jsonify(response_data), 201
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
            # Parse time string (HH:MM:SS format)
            time_str = data['time']
            if isinstance(time_str, str):
                time_parts = time_str.split(':')
                if len(time_parts) >= 2:
                    game.time = time_class(
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
    
@games_bp.route('/<int:game_id>/send-invitations', methods=['POST'])
@tenant_admin_required
@limiter.limit("10 per minute")
def send_game_invitations(game_id):
    """Manually send invitations for a game."""
    tenant = get_current_tenant()
    game = Game.query.filter_by(id=game_id, tenant_id=tenant.id).first_or_404()
    
    try:
        # Send invitations to regular players
        invitation_summary = InvitationService.auto_invite_regular_players(game.id)
        current_app.logger.info(f"Manually sent invitations for game {game_id}: {invitation_summary}")
        
        # Record when invitations were sent
        game.invitations_sent_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Invitations sent successfully',
            'invitations': invitation_summary
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to send invitations: {e}")
        return jsonify({'error': 'Failed to send invitations'}), 500

@games_bp.route('/<int:game_id>/send-reminders', methods=['POST'])
@tenant_admin_required
@limiter.limit("10 per minute")
def send_game_reminders(game_id):
    """Send reminder emails for a game with different messages based on response status."""
    from models.invitation import Invitation
    from models.player import Player
    from utils.email_service import EmailService
    
    tenant = get_current_tenant()
    game = Game.query.filter_by(id=game_id, tenant_id=tenant.id).first_or_404()
    
    try:
        # Get all invitations for this game
        invitations = Invitation.query.filter_by(game_id=game.id, tenant_id=tenant.id).all()
        
        if not invitations:
            return jsonify({'error': 'No invitations found for this game'}), 400
        
        sent_count = 0
        failed_count = 0
        
        game_date = game.date.strftime('%A, %B %d, %Y')
        game_time = game.time.strftime('%I:%M %p')
        
        for invitation in invitations:
            player = invitation.player
            
            if not player.email:
                failed_count += 1
                continue
            
            # Determine message type based on response status
            is_reminder = invitation.response is not None
            
            success = EmailService.send_game_invitation(
                player_email=player.email,
                player_name=player.name,
                game_date=game_date,
                game_time=game_time,
                venue=game.venue,
                game_id=game.id,
                language=player.preferred_language or 'en',
                tenant_subdomain=game.tenant.subdomain,
                invitation_token=invitation.token,
                is_reminder=is_reminder,
                has_responded=invitation.response is not None
            )
            
            if success:
                sent_count += 1
                invitation.send_reminder()  # Track reminder sent
            else:
                failed_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Reminders sent to {sent_count} players',
            'reminders': {
                'sent': sent_count,
                'failed': failed_count
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to send reminders: {e}")
        return jsonify({'error': 'Failed to send reminders'}), 500    

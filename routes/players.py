"""
Player management API endpoints with photo upload support.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from models.player import Player, PLAYER_TYPE_REGULAR, PLAYER_TYPE_SPARE
from utils.decorators import tenant_admin_required, tenant_required
from utils.tenant import get_current_tenant
from app import db, limiter
import os
import uuid

players_bp = Blueprint('players', __name__)

# Photo upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_folder():
    """Get upload folder path, create if doesn't exist."""
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads/players')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
    return upload_folder

def save_player_photo(file, tenant_id):
    """Save player photo and return filename."""
    if not file or not allowed_file(file.filename):
        return None
    
    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"player_{tenant_id}_{uuid.uuid4().hex}.{ext}"
    
    upload_folder = get_upload_folder()
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    return filename

def delete_player_photo(filename):
    """Delete player photo file."""
    if not filename:
        return
    
    upload_folder = get_upload_folder()
    filepath = os.path.join(upload_folder, filename)
    
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            current_app.logger.error(f"Failed to delete photo {filename}: {e}")

@players_bp.route('/', methods=['GET'])
@tenant_required
@login_required
def get_players():
    """Get all players for current tenant with search and filtering."""
    tenant = get_current_tenant()
    
    # Base query
    query = Player.query.filter_by(tenant_id=tenant.id)
    
    # Search by name or email
    search = request.args.get('search', '').strip()
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Player.name.ilike(search_pattern),
                Player.email.ilike(search_pattern)
            )
        )
    
    # Filter by position
    position = request.args.get('position')
    if position:
        query = query.filter(Player.position == position.lower())
    
    # Filter by player type
    player_type = request.args.get('player_type')
    if player_type in [PLAYER_TYPE_REGULAR, PLAYER_TYPE_SPARE]:
        query = query.filter(Player.player_type == player_type)
    
    # Filter by spare priority
    spare_priority = request.args.get('spare_priority')
    if spare_priority in ['1', '2']:
        query = query.filter(Player.spare_priority == int(spare_priority))
    
    # Filter by active status
    is_active = request.args.get('is_active')
    if is_active in ['true', 'false', '1', '0']:
        query = query.filter(Player.is_active == (is_active in ['true', '1']))
    
    # Sorting
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    
    if sort_by == 'name':
        query = query.order_by(Player.name.asc() if sort_order == 'asc' else Player.name.desc())
    elif sort_by == 'email':
        query = query.order_by(Player.email.asc() if sort_order == 'asc' else Player.email.desc())
    elif sort_by == 'position':
        query = query.order_by(Player.position.asc() if sort_order == 'asc' else Player.position.desc())
    elif sort_by == 'player_type':
        query = query.order_by(Player.player_type.asc() if sort_order == 'asc' else Player.player_type.desc())
    elif sort_by == 'created_at':
        query = query.order_by(Player.created_at.desc() if sort_order == 'desc' else Player.created_at.asc())
    else:
        query = query.order_by(Player.name.asc())
    
    players = query.all()
    
    return jsonify({
        'players': [p.to_dict() for p in players],
        'total': len(players),
        'filters': {
            'search': search if search else None,
            'position': position,
            'player_type': player_type,
            'spare_priority': spare_priority,
            'is_active': is_active,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
    })

@players_bp.route('/<int:player_id>', methods=['GET'])
@tenant_required
@login_required
def get_player(player_id):
    """Get specific player by ID."""
    tenant = get_current_tenant()
    player = Player.query.filter_by(id=player_id, tenant_id=tenant.id).first_or_404()
    return jsonify({'player': player.to_dict()})

@players_bp.route('/', methods=['POST'])
@tenant_admin_required
@limiter.limit("20 per minute")
def create_player():
    """Create a new player with optional photo upload."""
    tenant = get_current_tenant()
    
    # Handle both JSON and multipart/form-data
    if request.is_json:
        data = request.get_json()
        photo_file = None
    else:
        data = request.form.to_dict()
        photo_file = request.files.get('photo')
    
    if not data:
        return jsonify({'error': 'Request data required'}), 400
    
    # Validate required fields
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    position = data.get('position', '').strip().lower()
    player_type = data.get('player_type', PLAYER_TYPE_REGULAR).strip().lower()
    
    if not name:
        return jsonify({'error': 'Player name is required'}), 400
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    if not position:
        # Validate position for tenant's mode
        if not validate_position_for_tenant(position, tenant):
            valid_positions = get_valid_positions(tenant)
            return jsonify({
                'error': f'Invalid position for {tenant.position_mode} mode',
                'valid_positions': valid_positions
            }), 400
    
    # Validate player type
    if player_type not in [PLAYER_TYPE_REGULAR, PLAYER_TYPE_SPARE]:
        return jsonify({'error': f'Player type must be "{PLAYER_TYPE_REGULAR}" or "{PLAYER_TYPE_SPARE}"'}), 400
    
    # Validate spare priority
    spare_priority = None
    if player_type == PLAYER_TYPE_SPARE:
        spare_priority_str = data.get('spare_priority')
        if spare_priority_str:
            spare_priority = int(spare_priority_str)
        if not spare_priority or spare_priority not in [1, 2]:
            return jsonify({'error': 'Spare players must have priority 1 or 2'}), 400
    
    # Check for duplicate email
    existing = Player.query.filter_by(email=email, tenant_id=tenant.id).first()
    if existing:
        return jsonify({'error': 'A player with this email already exists'}), 409
    
    # Handle photo upload
    photo_filename = None
    if photo_file and photo_file.filename:
        if not allowed_file(photo_file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
        photo_filename = save_player_photo(photo_file, tenant.id)
    
    # Handle is_active (defaults to True)
    is_active = True
    if 'is_active' in data:
        is_active_value = data['is_active']
        if isinstance(is_active_value, str):
            is_active = is_active_value.lower() in ['true', '1', 'yes']
        else:
            is_active = bool(is_active_value)

    # Create player
    player = Player(
        name=name,
        email=email,
        position=position,
        player_type=player_type,
        spare_priority=spare_priority,
        photo_filename=photo_filename,
        language=data.get('language', 'en'),
        is_active=is_active,
        tenant_id=tenant.id
)
    
    try:
        db.session.add(player)
        db.session.commit()
        return jsonify({
            'message': 'Player created successfully',
            'player': player.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        if photo_filename:
            delete_player_photo(photo_filename)
        current_app.logger.error(f"Failed to create player: {e}")
        return jsonify({'error': 'Failed to create player'}), 500

@players_bp.route('/<int:player_id>', methods=['PUT'])
@tenant_admin_required
@limiter.limit("20 per minute")
def update_player(player_id):
    """Update specific player with optional photo upload."""
    tenant = get_current_tenant()
    player = Player.query.filter_by(id=player_id, tenant_id=tenant.id).first_or_404()
    
    # Handle both JSON and multipart/form-data
    if request.is_json:
        data = request.get_json()
        photo_file = None
    else:
        data = request.form.to_dict()
        photo_file = request.files.get('photo')
    
    if not data:
        return jsonify({'error': 'Request data required'}), 400
    
    # Update fields if provided
    if 'name' in data:
        name = data['name'].strip()
        if not name:
            return jsonify({'error': 'Player name cannot be empty'}), 400
        player.name = name
    
    if 'email' in data:
        email = data['email'].strip().lower()
        if not email:
            return jsonify({'error': 'Email cannot be empty'}), 400
        
        existing = Player.query.filter(
            Player.email == email,
            Player.tenant_id == tenant.id,
            Player.id != player_id
        ).first()
        
        if existing:
            return jsonify({'error': 'A player with this email already exists'}), 409
        
        player.email = email
    
    if 'position' in data:
        position = data['position'].strip().lower()
        if not position:
            # Validate position for tenant's mode
            if not validate_position_for_tenant(position, tenant):
                valid_positions = get_valid_positions(tenant)
                return jsonify({
                    'error': f'Invalid position for {tenant.position_mode} mode',
                    'valid_positions': valid_positions
                }), 400
        player.position = position
    
    if 'player_type' in data:
        player_type = data['player_type'].strip().lower()
        if player_type not in [PLAYER_TYPE_REGULAR, PLAYER_TYPE_SPARE]:
            return jsonify({'error': f'Player type must be "{PLAYER_TYPE_REGULAR}" or "{PLAYER_TYPE_SPARE}"'}), 400
        
        player.player_type = player_type
        
        if player_type == PLAYER_TYPE_SPARE:
            if 'spare_priority' in data:
                spare_priority = int(data['spare_priority'])
                if spare_priority not in [1, 2]:
                    return jsonify({'error': 'Spare priority must be 1 or 2'}), 400
                player.spare_priority = spare_priority
            elif not player.spare_priority:
                return jsonify({'error': 'Spare players must have priority 1 or 2'}), 400
        else:
            player.spare_priority = None
    
    if 'language' in data:
        player.language = data['language']
    
    if 'is_active' in data:
        # Handle both boolean and string values from FormData
        is_active_value = data['is_active']
        if isinstance(is_active_value, str):
            player.is_active = is_active_value.lower() in ['true', '1', 'yes']
        else:
            player.is_active = bool(is_active_value)
    
    # Handle photo upload
    if photo_file and photo_file.filename:
        if not allowed_file(photo_file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
        
        # Delete old photo
        if player.photo_filename:
            delete_player_photo(player.photo_filename)
        
        # Save new photo
        player.photo_filename = save_player_photo(photo_file, tenant.id)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Player updated successfully',
            'player': player.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to update player: {e}")
        return jsonify({'error': 'Failed to update player'}), 500

@players_bp.route('/<int:player_id>', methods=['DELETE'])
@tenant_admin_required
@limiter.limit("20 per minute")
def delete_player(player_id):
    """Delete specific player."""
    tenant = get_current_tenant()
    player = Player.query.filter_by(id=player_id, tenant_id=tenant.id).first_or_404()
    
    # Delete photo file if exists
    if player.photo_filename:
        delete_player_photo(player.photo_filename)
    
    try:
        db.session.delete(player)
        db.session.commit()
        return jsonify({'message': 'Player deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to delete player: {e}")
        return jsonify({'error': 'Failed to delete player'}), 500

@players_bp.route('/<int:player_id>/photo', methods=['DELETE'])
@tenant_admin_required
def delete_player_photo_endpoint(player_id):
    """Delete player photo."""
    tenant = get_current_tenant()
    player = Player.query.filter_by(id=player_id, tenant_id=tenant.id).first_or_404()
    
    if not player.photo_filename:
        return jsonify({'message': 'Player has no photo'}), 200
    
    delete_player_photo(player.photo_filename)
    player.photo_filename = None
    
    try:
        db.session.commit()
        return jsonify({'message': 'Photo deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to delete photo: {e}")
        return jsonify({'error': 'Failed to delete photo'}), 500

# ============ Player Type Management Endpoints (Task 3.5) ============

@players_bp.route('/spares', methods=['GET'])
@tenant_required
@login_required
def get_spare_players():
    """Get all spare players, optionally filtered by priority."""
    tenant = get_current_tenant()
    
    query = Player.query.filter_by(
        tenant_id=tenant.id,
        player_type=PLAYER_TYPE_SPARE
    )
    
    # Filter by priority if specified
    priority = request.args.get('priority')
    if priority in ['1', '2']:
        query = query.filter(Player.spare_priority == int(priority))
    
    # Filter by active status
    is_active = request.args.get('is_active')
    if is_active in ['true', 'false', '1', '0']:
        query = query.filter(Player.is_active == (is_active in ['true', '1']))
    
    spares = query.order_by(Player.spare_priority, Player.name).all()
    
    return jsonify({
        'spares': [p.to_dict() for p in spares],
        'total': len(spares),
        'priority_filter': priority
    })

@players_bp.route('/regulars', methods=['GET'])
@tenant_required
@login_required
def get_regular_players():
    """Get all regular players."""
    tenant = get_current_tenant()
    
    query = Player.query.filter_by(
        tenant_id=tenant.id,
        player_type=PLAYER_TYPE_REGULAR
    )
    
    # Filter by active status
    is_active = request.args.get('is_active')
    if is_active in ['true', 'false', '1', '0']:
        query = query.filter(Player.is_active == (is_active in ['true', '1']))
    
    regulars = query.order_by(Player.name).all()
    
    return jsonify({
        'regulars': [p.to_dict() for p in regulars],
        'total': len(regulars)
    })

@players_bp.route('/<int:player_id>/convert-to-spare', methods=['PUT'])
@tenant_admin_required
def convert_to_spare(player_id):
    """Convert a regular player to spare with specified priority."""
    tenant = get_current_tenant()
    player = Player.query.filter_by(id=player_id, tenant_id=tenant.id).first_or_404()
    
    data = request.get_json() or {}
    priority = data.get('priority')
    
    if not priority or priority not in [1, 2]:
        return jsonify({'error': 'Priority must be 1 or 2'}), 400
    
    player.player_type = PLAYER_TYPE_SPARE
    player.spare_priority = priority
    
    try:
        db.session.commit()
        return jsonify({
            'message': f'Player converted to spare with priority {priority}',
            'player': player.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to convert player: {e}")
        return jsonify({'error': 'Failed to convert player'}), 500

@players_bp.route('/<int:player_id>/convert-to-regular', methods=['PUT'])
@tenant_admin_required
def convert_to_regular(player_id):
    """Convert a spare player to regular."""
    tenant = get_current_tenant()
    player = Player.query.filter_by(id=player_id, tenant_id=tenant.id).first_or_404()
    
    player.player_type = PLAYER_TYPE_REGULAR
    player.spare_priority = None
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Player converted to regular',
            'player': player.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to convert player: {e}")
        return jsonify({'error': 'Failed to convert player'}), 500

@players_bp.route('/<int:player_id>/priority', methods=['PUT'])
@tenant_admin_required
def update_spare_priority(player_id):
    """Update spare player priority."""
    tenant = get_current_tenant()
    player = Player.query.filter_by(id=player_id, tenant_id=tenant.id).first_or_404()
    
    if player.player_type != PLAYER_TYPE_SPARE:
        return jsonify({'error': 'Player is not a spare'}), 400
    
    data = request.get_json() or {}
    priority = data.get('priority')
    
    if not priority or priority not in [1, 2]:
        return jsonify({'error': 'Priority must be 1 or 2'}), 400
    
    player.spare_priority = priority
    
    try:
        db.session.commit()
        return jsonify({
            'message': f'Spare priority updated to {priority}',
            'player': player.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to update priority: {e}")
        return jsonify({'error': 'Failed to update priority'}), 500

@players_bp.route('/type-summary', methods=['GET'])
@tenant_required
@login_required
def get_player_type_summary():
    """Get summary of player types and counts."""
    tenant = get_current_tenant()
    
    total = Player.query.filter_by(tenant_id=tenant.id).count()
    regulars = Player.query.filter_by(tenant_id=tenant.id, player_type=PLAYER_TYPE_REGULAR).count()
    spares = Player.query.filter_by(tenant_id=tenant.id, player_type=PLAYER_TYPE_SPARE).count()
    priority_1 = Player.query.filter_by(tenant_id=tenant.id, player_type=PLAYER_TYPE_SPARE, spare_priority=1).count()
    priority_2 = Player.query.filter_by(tenant_id=tenant.id, player_type=PLAYER_TYPE_SPARE, spare_priority=2).count()
    
    return jsonify({
        'total': total,
        'regulars': regulars,
        'spares': spares,
        'spare_priority_1': priority_1,
        'spare_priority_2': priority_2
    })

# ============ Position Configuration System (Task 3.6) ============

def get_valid_positions(tenant):
    """Get valid positions based on tenant's position mode."""
    if tenant.position_mode == 'three_position':
        return [POSITION_GOALTENDER, POSITION_DEFENCE, POSITION_FORWARD]
    else:  # two_position
        return [POSITION_GOALTENDER, POSITION_SKATER]

def validate_position_for_tenant(position, tenant):
    """Validate if position is valid for tenant's position mode."""
    valid_positions = get_valid_positions(tenant)
    return position in valid_positions

@players_bp.route('/positions', methods=['GET'])
@tenant_required
@login_required
def get_available_positions():
    """Get available positions based on tenant's position mode."""
    tenant = get_current_tenant()
    
    positions = get_valid_positions(tenant)
    
    return jsonify({
        'positions': positions,
        'position_mode': tenant.position_mode,
        'description': {
            'three_position': 'Goaltender, Defence, Forward',
            'two_position': 'Goaltender, Skaters'
        }[tenant.position_mode]
    })

@players_bp.route('/position-summary', methods=['GET'])
@tenant_required
@login_required
def get_position_summary():
    """Get summary of players by position."""
    tenant = get_current_tenant()
    
    # Get counts for each position
    summary = {}
    
    if tenant.position_mode == 'three_position':
        summary['goaltenders'] = Player.query.filter_by(
            tenant_id=tenant.id,
            position=POSITION_GOALTENDER
        ).count()
        summary['defence'] = Player.query.filter_by(
            tenant_id=tenant.id,
            position=POSITION_DEFENCE
        ).count()
        summary['forwards'] = Player.query.filter_by(
            tenant_id=tenant.id,
            position=POSITION_FORWARD
        ).count()
    else:  # two_position
        summary['goaltenders'] = Player.query.filter_by(
            tenant_id=tenant.id,
            position=POSITION_GOALTENDER
        ).count()
        summary['skaters'] = Player.query.filter_by(
            tenant_id=tenant.id,
            position=POSITION_SKATER
        ).count()
    
    summary['total'] = Player.query.filter_by(tenant_id=tenant.id).count()
    summary['position_mode'] = tenant.position_mode
    
    return jsonify(summary)

@players_bp.route('/<int:player_id>/position', methods=['PUT'])
@tenant_admin_required
def update_player_position(player_id):
    """Update player position with validation."""
    tenant = get_current_tenant()
    player = Player.query.filter_by(id=player_id, tenant_id=tenant.id).first_or_404()
    
    data = request.get_json() or {}
    new_position = data.get('position', '').strip().lower()
    
    if not new_position:
        return jsonify({'error': 'Position is required'}), 400
    
    # Validate position for tenant's mode
    if not validate_position_for_tenant(new_position, tenant):
        valid_positions = get_valid_positions(tenant)
        return jsonify({
            'error': f'Invalid position for {tenant.position_mode} mode',
            'valid_positions': valid_positions
        }), 400
    
    player.position = new_position
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Player position updated successfully',
            'player': player.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to update position: {e}")
        return jsonify({'error': 'Failed to update position'}), 500

@players_bp.route('/by-position/<string:position>', methods=['GET'])
@tenant_required
@login_required
def get_players_by_position(position):
    """Get all players for a specific position."""
    tenant = get_current_tenant()
    
    position = position.lower()
    
    # Validate position for tenant's mode
    if not validate_position_for_tenant(position, tenant):
        valid_positions = get_valid_positions(tenant)
        return jsonify({
            'error': f'Invalid position for {tenant.position_mode} mode',
            'valid_positions': valid_positions
        }), 400
    
    players = Player.query.filter_by(
        tenant_id=tenant.id,
        position=position
    ).order_by(Player.name).all()
    
    return jsonify({
        'position': position,
        'players': [p.to_dict() for p in players],
        'total': len(players)
    })

# ============ Player Profile with Statistics (Task 3.7) ============

@players_bp.route('/<int:player_id>/profile', methods=['GET'])
@tenant_required
@login_required
def get_player_profile(player_id):
    """Get comprehensive player profile with statistics summary."""
    tenant = get_current_tenant()
    player = Player.query.filter_by(id=player_id, tenant_id=tenant.id).first_or_404()
    
    # Get basic player info
    profile = player.to_dict()
    
    # Get invitation statistics
    from models.invitation import Invitation
    total_invitations = Invitation.query.filter_by(player_id=player.id).count()
    accepted_invitations = Invitation.query.filter_by(
        player_id=player.id,
        status='accepted'
    ).count()
    declined_invitations = Invitation.query.filter_by(
        player_id=player.id,
        status='declined'
    ).count()
    pending_invitations = Invitation.query.filter_by(
        player_id=player.id,
        status='pending'
    ).count()
    
    # Calculate acceptance rate
    acceptance_rate = (accepted_invitations / total_invitations * 100) if total_invitations > 0 else 0
    
    # Get game statistics
    from models.statistics import PlayerStatistic
    stats = PlayerStatistic.query.filter_by(player_id=player.id).all()
    
    total_games = len(stats)
    total_goals = sum(s.goals for s in stats if s.goals)
    total_assists = sum(s.assists for s in stats if s.assists)
    total_points = total_goals + total_assists
    total_penalties = sum(s.penalty_minutes for s in stats if s.penalty_minutes)
    
    # Goaltender-specific stats
    goalie_stats = None
    if player.is_goaltender:
        total_saves = sum(s.saves for s in stats if s.saves)
        total_goals_against = sum(s.goals_against for s in stats if s.goals_against)
        games_as_goalie = sum(1 for s in stats if s.saves is not None)
        
        save_percentage = 0
        if total_saves + total_goals_against > 0:
            save_percentage = (total_saves / (total_saves + total_goals_against)) * 100
        
        goalie_stats = {
            'games_played': games_as_goalie,
            'saves': total_saves,
            'goals_against': total_goals_against,
            'save_percentage': round(save_percentage, 2)
        }
    
    # Get assignment history
    from models.assignment import Assignment
    assignments = Assignment.query.filter_by(player_id=player.id).all()
    total_assignments = len(assignments)
    
    # Build profile response
    profile['statistics'] = {
        'games_played': total_games,
        'goals': total_goals,
        'assists': total_assists,
        'points': total_points,
        'penalty_minutes': total_penalties,
        'goalie_stats': goalie_stats
    }
    
    profile['invitations'] = {
        'total': total_invitations,
        'accepted': accepted_invitations,
        'declined': declined_invitations,
        'pending': pending_invitations,
        'acceptance_rate': round(acceptance_rate, 2)
    }
    
    profile['assignments'] = {
        'total': total_assignments
    }
    
    return jsonify({'profile': profile})

@players_bp.route('/<int:player_id>/statistics', methods=['GET'])
@tenant_required
@login_required
def get_player_statistics(player_id):
    """Get detailed player statistics."""
    tenant = get_current_tenant()
    player = Player.query.filter_by(id=player_id, tenant_id=tenant.id).first_or_404()
    
    from models.statistics import PlayerStatistic
    stats = PlayerStatistic.query.filter_by(player_id=player.id).order_by(
        PlayerStatistic.game_date.desc()
    ).all()
    
    return jsonify({
        'player_id': player.id,
        'player_name': player.name,
        'statistics': [s.to_dict() for s in stats],
        'total_games': len(stats)
    })

@players_bp.route('/<int:player_id>/invitations', methods=['GET'])
@tenant_required
@login_required
def get_player_invitations(player_id):
    """Get player's invitation history."""
    tenant = get_current_tenant()
    player = Player.query.filter_by(id=player_id, tenant_id=tenant.id).first_or_404()
    
    from models.invitation import Invitation
    
    # Filter by status if provided
    status = request.args.get('status')
    query = Invitation.query.filter_by(player_id=player.id)
    
    if status in ['pending', 'accepted', 'declined']:
        query = query.filter_by(status=status)
    
    invitations = query.order_by(Invitation.created_at.desc()).all()
    
    return jsonify({
        'player_id': player.id,
        'player_name': player.name,
        'invitations': [i.to_dict() for i in invitations],
        'total': len(invitations)
    })

@players_bp.route('/<int:player_id>/assignments', methods=['GET'])
@tenant_required
@login_required
def get_player_assignments(player_id):
    """Get player's team assignment history."""
    tenant = get_current_tenant()
    player = Player.query.filter_by(id=player_id, tenant_id=tenant.id).first_or_404()
    
    from models.assignment import Assignment
    assignments = Assignment.query.filter_by(player_id=player.id).order_by(
        Assignment.created_at.desc()
    ).all()
    
    return jsonify({
        'player_id': player.id,
        'player_name': player.name,
        'assignments': [a.to_dict() for a in assignments],
        'total': len(assignments)
    })

@players_bp.route('/<int:player_id>/recent-activity', methods=['GET'])
@tenant_required
@login_required
def get_player_recent_activity(player_id):
    """Get player's recent activity summary."""
    tenant = get_current_tenant()
    player = Player.query.filter_by(id=player_id, tenant_id=tenant.id).first_or_404()
    
    from models.invitation import Invitation
    from models.statistics import PlayerStatistic
    from models.assignment import Assignment
    from datetime import datetime, timedelta
    
    # Get activity from last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    recent_invitations = Invitation.query.filter(
        Invitation.player_id == player.id,
        Invitation.created_at >= thirty_days_ago
    ).count()
    
    recent_games = PlayerStatistic.query.filter(
        PlayerStatistic.player_id == player.id,
        PlayerStatistic.game_date >= thirty_days_ago
    ).count()
    
    recent_assignments = Assignment.query.filter(
        Assignment.player_id == player.id,
        Assignment.created_at >= thirty_days_ago
    ).count()
    
    return jsonify({
        'player_id': player.id,
        'player_name': player.name,
        'period': '30_days',
        'recent_activity': {
            'invitations': recent_invitations,
            'games_played': recent_games,
            'assignments': recent_assignments
        }
    })
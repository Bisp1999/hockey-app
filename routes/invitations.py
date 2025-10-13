"""
Invitation and availability API endpoints.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from datetime import datetime, timedelta
from app import db
from models.invitation import Invitation
from models.game import Game
from models.player import Player
from models.admin_invitation import AdminInvitation
from models.user import User
from flask_login import login_user
from utils.decorators import tenant_required, tenant_admin_required
from utils.email_service import EmailService

invitations_bp = Blueprint('invitations', __name__)

@invitations_bp.route('/game/<int:game_id>', methods=['GET'])
@tenant_required
def get_game_invitations(game_id):
    """Get all invitations for a specific game."""
    try:
        game = Game.query.get_or_404(game_id)
        
        invitations = Invitation.query.filter_by(game_id=game_id).all()
        
        return jsonify({
            'invitations': [inv.to_dict(include_player=True) for inv in invitations],
            'total': len(invitations),
            'summary': {
                'sent': sum(1 for inv in invitations if inv.status in ['sent', 'delivered', 'opened']),
                'responded': sum(1 for inv in invitations if inv.status == 'responded'),
                'available': sum(1 for inv in invitations if inv.response == 'available'),
                'unavailable': sum(1 for inv in invitations if inv.response == 'unavailable'),
                'pending': sum(1 for inv in invitations if inv.status == 'pending'),
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching game invitations: {e}")
        return jsonify({'error': 'Failed to fetch invitations'}), 500

@invitations_bp.route('/game/<int:game_id>/send', methods=['POST'])
@tenant_admin_required
def send_game_invitations(game_id):
    """Create and send invitations for a game."""
    try:
        data = request.get_json()
        player_ids = data.get('player_ids', [])
        invitation_type = data.get('invitation_type', 'regular')  # 'regular' or 'spare'
        
        if not player_ids:
            return jsonify({'error': 'No players specified'}), 400
        
        game = Game.query.get_or_404(game_id)
        
        sent_count = 0
        failed_count = 0
        errors = []
        
        for player_id in player_ids:
            try:
                player = Player.query.get(player_id)
                if not player:
                    errors.append(f"Player {player_id} not found")
                    failed_count += 1
                    continue
                
                if not player.email:
                    errors.append(f"Player {player.name} has no email address")
                    failed_count += 1
                    continue
                
                # Check if invitation already exists
                existing = Invitation.query.filter_by(
                    game_id=game_id,
                    player_id=player_id
                ).first()
                
                if existing:
                    errors.append(f"Invitation already exists for {player.name}")
                    failed_count += 1
                    continue
                
                # Create invitation
                invitation = Invitation(
                    game_id=game_id,
                    player_id=player_id,
                    invitation_type=invitation_type,
                    status='pending'
                )
                
                db.session.add(invitation)
                db.session.flush()  # Get the invitation ID
                
                # Send email
                game_date = game.date.strftime('%A, %B %d, %Y')
                game_time = game.time.strftime('%I:%M %p')
                
                success = EmailService.send_game_invitation(
                    player_email=player.email,
                    player_name=player.name,
                    game_date=game_date,
                    game_time=game_time,
                    venue=game.venue,
                    game_id=game_id,
                    language=player.preferred_language or 'en',
                    tenant_subdomain=None,  # Will be set from request context
                    invitation_token=invitation.token  # Add this line
                )
                
                if success:
                    invitation.mark_sent()
                    sent_count += 1
                else:
                    invitation.mark_bounced("Failed to send email")
                    failed_count += 1
                    errors.append(f"Failed to send email to {player.name}")
                
            except Exception as e:
                current_app.logger.error(f"Error sending invitation to player {player_id}: {e}")
                failed_count += 1
                errors.append(f"Error with player {player_id}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'message': f'Sent {sent_count} invitations',
            'sent': sent_count,
            'failed': failed_count,
            'errors': errors if errors else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error sending game invitations: {e}")
        return jsonify({'error': 'Failed to send invitations'}), 500

@invitations_bp.route('/<int:invitation_id>/respond', methods=['POST'])
@tenant_required
def respond_to_invitation(invitation_id):
    """Respond to an invitation (available/unavailable)."""
    try:
        data = request.get_json()
        response = data.get('response')  # 'available', 'unavailable', 'tentative'
        notes = data.get('notes')
        
        if response not in ['available', 'unavailable', 'tentative']:
            return jsonify({'error': 'Invalid response. Must be available, unavailable, or tentative'}), 400
        
        invitation = Invitation.query.get_or_404(invitation_id)
        
        # Record response
        invitation.record_response(response, method='web', notes=notes)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Response recorded',
            'invitation': invitation.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error responding to invitation: {e}")
        return jsonify({'error': 'Failed to record response'}), 500

@invitations_bp.route('/respond/<token>', methods=['GET', 'POST'])
def respond_by_token(token):
    """Respond to invitation via email link (no auth required)."""
    try:
        invitation = Invitation.query.filter_by(token=token).first_or_404()
        
        # Mark as opened
        invitation.mark_opened()
        
        if request.method == 'GET':
            # Return invitation details for frontend to display
            return jsonify({
                'invitation': invitation.to_dict(include_game=True, include_player=True),
                'game': invitation.game.to_dict() if invitation.game else None
            }), 200
        
        # POST - record response
        data = request.get_json()
        response = data.get('response')
        notes = data.get('notes')
        
        if response not in ['available', 'unavailable', 'tentative']:
            return jsonify({'error': 'Invalid response'}), 400
        
        invitation.record_response(response, method='email', notes=notes)
        db.session.commit()
        
        return jsonify({
            'message': 'Thank you! Your response has been recorded.',
            'invitation': invitation.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error responding by token: {e}")
        return jsonify({'error': 'Failed to process response'}), 500

@invitations_bp.route('/admin/verify/<token>', methods=['GET'])
def verify_admin_invitation(token):
    """Verify an admin invitation token."""
    invitation = AdminInvitation.query.filter_by(token=token).first()

    if not invitation or not invitation.is_valid():
        return jsonify({'error': 'This invitation is invalid or has expired.'}), 404

    return jsonify({
        'message': 'Invitation is valid.',
        'invitation': {
            'email': invitation.email,
            'tenant_name': invitation.tenant.name,
            'role': invitation.role
        }
    }), 200

@invitations_bp.route('/admin/accept', methods=['POST'])
def accept_admin_invitation():
    """Accept an admin invitation and create the new user account."""
    data = request.get_json()
    token = data.get('token')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')

    if not all([token, password, first_name, last_name]):
        return jsonify({'error': 'Missing required fields.'}), 400

    invitation = AdminInvitation.query.filter_by(token=token).first()

    if not invitation or not invitation.is_valid():
        return jsonify({'error': 'This invitation is invalid or has expired.'}), 404

    # Check if a user with this email already exists in the tenant
    if User.query.filter_by(email=invitation.email, tenant_id=invitation.tenant_id).first():
        invitation.status = 'expired'
        db.session.commit()
        return jsonify({'error': 'A user with this email already exists in the organization.'}), 409

    # Create the new user
    new_user = User(
        email=invitation.email,
        first_name=first_name,
        last_name=last_name,
        role=invitation.role,
        tenant_id=invitation.tenant_id,
        is_active=True,
        is_verified=True # Email is verified by accepting the invitation
    )
    new_user.set_password(password)

    # Update the invitation status
    invitation.status = 'accepted'

    db.session.add(new_user)
    db.session.commit()

    # Log the new user in
    login_user(new_user)

    return jsonify({
        'message': 'Account created successfully! You are now logged in.',
        'user': new_user.to_dict(),
        'tenant': new_user.tenant.to_dict()
    }), 201

@invitations_bp.route('/<int:invitation_id>/reminder', methods=['POST'])
@tenant_admin_required
def send_reminder(invitation_id):
    """Send a reminder email for an invitation."""
    try:
        invitation = Invitation.query.get_or_404(invitation_id)
        
        if invitation.response:
            return jsonify({'error': 'Player has already responded'}), 400
        
        player = invitation.player
        game = invitation.game
        
        if not player.email:
            return jsonify({'error': 'Player has no email address'}), 400
        
        # Send reminder email
        game_date = game.date.strftime('%A, %B %d, %Y')
        game_time = game.time.strftime('%I:%M %p')
        
        success = EmailService.send_game_invitation(
            player_email=player.email,
            player_name=player.name,
            game_date=game_date,
            game_time=game_time,
            venue=game.venue,
            game_id=game.id,
            language=player.preferred_language or 'en',
            tenant_subdomain=game.tenant.subdomain,
            invitation_token=invitation.token  # Add this line
        )
        
        if success:
            invitation.send_reminder()
            db.session.commit()
            return jsonify({'message': 'Reminder sent'}), 200
        else:
            return jsonify({'error': 'Failed to send reminder'}), 500
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error sending reminder: {e}")
        return jsonify({'error': 'Failed to send reminder'}), 500
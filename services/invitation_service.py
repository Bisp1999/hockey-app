"""
Service for automated invitation management.
"""
from datetime import datetime
from flask import current_app
from app import db
from models.player import Player, PLAYER_TYPE_REGULAR
from models.game import Game
from models.invitation import Invitation
from utils.email_service import EmailService

class InvitationService:
    """Service for managing automated invitations."""
    
    @staticmethod
    def send_invitations_for_game(game_id, player_type='regular', player_ids=None):
        """
        Send invitations for a game.
        
        Args:
            game_id: Game ID
            player_type: Type of players to invite ('regular' or 'spare')
            player_ids: Optional list of specific player IDs. If None, invites all regular players.
        
        Returns:
            dict: Summary of sent invitations
        """
        try:
            game = Game.query.get(game_id)
            if not game:
                return {'error': 'Game not found', 'sent': 0, 'failed': 0}
            
            # Get players to invite
            if player_ids:
                players = Player.query.filter(
                    Player.id.in_(player_ids),
                    Player.is_active == True
                ).all()
            else:
                # Get all regular active players
                players = Player.query.filter_by(
                    player_type=player_type,
                    is_active=True
                ).all()
            
            sent_count = 0
            failed_count = 0
            errors = []
            
            for player in players:
                try:
                    # Check if invitation already exists
                    existing = Invitation.query.filter_by(
                        game_id=game_id,
                        player_id=player.id
                    ).first()
                    
                    if existing:
                        current_app.logger.info(f"Invitation already exists for player {player.name}")
                        continue
                    
                    if not player.email:
                        errors.append(f"Player {player.name} has no email")
                        failed_count += 1
                        continue
                    
                    # Create invitation
                    invitation = Invitation(
                        game_id=game_id,
                        player_id=player.id,
                        invitation_type=player_type,
                        status='pending',
                        tenant_id=game.tenant_id  # Add this line
                    )
                    
                    db.session.add(invitation)
                    db.session.flush()
                    
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
                        language=player.preferred_language,
                        tenant_subdomain=None,
                        invitation_token=invitation.token
                    )
                    
                    if success:
                        invitation.mark_sent()
                        sent_count += 1
                        current_app.logger.info(f"Invitation sent to {player.name}")
                    else:
                        invitation.mark_bounced("Failed to send email")
                        failed_count += 1
                        errors.append(f"Failed to send email to {player.name}")
                
                except Exception as e:
                    current_app.logger.error(f"Error sending invitation to {player.name}: {e}")
                    failed_count += 1
                    errors.append(f"Error with {player.name}: {str(e)}")
            
            db.session.commit()
            
            return {
                'sent': sent_count,
                'failed': failed_count,
                'errors': errors if errors else None,
                'total_players': len(players)
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error in send_invitations_for_game: {e}")
            return {'error': str(e), 'sent': 0, 'failed': 0}
    
    @staticmethod
    def auto_invite_regular_players(game_id):
        """
        Automatically invite all regular players to a game.
        
        Args:
            game_id: Game ID
        
        Returns:
            dict: Summary of sent invitations
        """
        return InvitationService.send_invitations_for_game(
            game_id=game_id,
            player_type=PLAYER_TYPE_REGULAR
        )
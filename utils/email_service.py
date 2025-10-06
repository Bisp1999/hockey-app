"""
Email service for sending game invitations and notifications.
"""
from flask import current_app, render_template
from flask_mail import Message
from app import mail
from typing import List, Optional

class EmailService:
    """Service for sending emails to players."""
    
    @staticmethod
    def send_email(subject: str, recipients: List[str], body: str, html: Optional[str] = None):
        """
        Send an email.
        
        Args:
            subject: Email subject
            recipients: List of recipient email addresses
            body: Plain text body
            html: Optional HTML body
        """
        try:
            msg = Message(
                subject=subject,
                recipients=recipients,
                body=body,
                html=html,
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            mail.send(msg)
            current_app.logger.info(f"Email sent successfully to {recipients}: {subject}")
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")
            current_app.logger.exception("Full traceback:")
            return False
    
    @staticmethod
    def send_game_invitation(player_email: str, player_name: str, game_date: str, 
                        game_time: str, venue: str, game_id: int, language: str = 'en',
                        tenant_subdomain: str = None, invitation_token: str = None):
        """
        Send a game invitation email to a player using templates.
    
        Args:
            player_email: Player's email address
            player_name: Player's name
            game_date: Game date (formatted)
            game_time: Game time
            venue: Game venue
            game_id: Game ID for generating URLs
            language: Email language ('en' or 'fr')
            tenant_subdomain: Tenant subdomain for URL generation
            invitation_token: Secure token for email responses
        """
        # Generate URLs for confirmation/decline
        base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        if tenant_subdomain:
            base_url = f"http://{tenant_subdomain}.localhost:3000"
    
        # Use token-based URLs if token is provided
        if invitation_token:
            confirm_url = f"{base_url}/invitations/respond/{invitation_token}?response=available"
            decline_url = f"{base_url}/invitations/respond/{invitation_token}?response=unavailable"
            tenant_url = f"{base_url}/invitations/respond/{invitation_token}"
        else:
            # Fallback to game-based URLs
            confirm_url = f"{base_url}/games/{game_id}/respond?status=available"
            decline_url = f"{base_url}/games/{game_id}/respond?status=unavailable"
            tenant_url = f"{base_url}/games/{game_id}"
    
        # Select template based on language
        template = f'email/game_invitation_{language}.html'
    
        # Render HTML template
        html = render_template(
            template,
            player_name=player_name,
            game_date=game_date,
            game_time=game_time,
            venue=venue,
            confirm_url=confirm_url,
            decline_url=decline_url,
            tenant_url=tenant_url
        )
    
        # Create plain text version
        if language == 'fr':
            subject = f"Invitation au match - {game_date}"
            body = f"""
    Bonjour {player_name},

    Vous êtes invité(e) au match suivant :

    Date : {game_date}
    Heure : {game_time}
    Lieu : {venue}

    Veuillez confirmer votre disponibilité :
    Disponible : {confirm_url}
    Non disponible : {decline_url}

    Merci,
    Hockey Pickup Manager
            """
        else:
            subject = f"Game Invitation - {game_date}"
            body = f"""
    Hello {player_name},

    You are invited to the following game:

    Date: {game_date}
    Time: {game_time}
    Venue: {venue}

    Please confirm your availability:
    Available: {confirm_url}
    Not Available: {decline_url}

    Thanks,
    Hockey Pickup Manager
            """
    
        return EmailService.send_email(subject, [player_email], body, html)
    
    @staticmethod
    def send_test_email(recipient: str):
        """Send a test email to verify configuration."""
        subject = "Hockey Pickup Manager - Test Email"
        body = "This is a test email from Hockey Pickup Manager. If you received this, your email configuration is working correctly!"
        html = """
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #0066cc;">Test Email</h2>
    <p>This is a test email from <strong>Hockey Pickup Manager</strong>.</p>
    <p>If you received this, your email configuration is working correctly! ✅</p>
</body>
</html>
        """
        return EmailService.send_email(subject, [recipient], body, html)
"""
Email testing routes (for development only).
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from utils.email_service import EmailService
from utils.decorators import tenant_admin_required

email_test_bp = Blueprint('email_test', __name__)

@email_test_bp.route('/test', methods=['POST'])
@login_required
def send_test_email():
    """Send a test email to verify configuration."""
    data = request.get_json()
    recipient = data.get('email')
    
    if not recipient:
        return jsonify({'error': 'Email address required'}), 400
    
    success = EmailService.send_test_email(recipient)
    
    if success:
        return jsonify({'message': f'Test email sent to {recipient}'}), 200
    else:
        return jsonify({'error': 'Failed to send test email'}), 500

@email_test_bp.route('/test-simple', methods=['POST'])
def send_test_email_simple():
    """Send a test email without authentication (development only)."""
    data = request.get_json()
    recipient = data.get('email')
    
    if not recipient:
        return jsonify({'error': 'Email address required'}), 400
    
    success = EmailService.send_test_email(recipient)
    
    if success:
        return jsonify({'message': f'Test email sent to {recipient}'}), 200
    else:
        return jsonify({'error': 'Failed to send test email'}), 500

@email_test_bp.route('/test-invitation', methods=['POST'])
def send_test_invitation():
    """Send a test game invitation email (development only)."""
    data = request.get_json()
    
    recipient = data.get('email')
    language = data.get('language', 'en')
    
    if not recipient:
        return jsonify({'error': 'Email address required'}), 400
    
    # Test data
    success = EmailService.send_game_invitation(
        player_email=recipient,
        player_name="Test Player",
        game_date="Saturday, October 12, 2025",
        game_time="7:00 PM",
        venue="Community Arena - Rink 1",
        game_id=1,
        language=language,
        tenant_subdomain="myteam"
    )
    
    if success:
        return jsonify({'message': f'Test invitation sent to {recipient} in {language}'}), 200
    else:
        return jsonify({'error': 'Failed to send test invitation'}), 500
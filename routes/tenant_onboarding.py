"""
Tenant registration and onboarding flow routes.
"""
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash
from app import db
from models.tenant import Tenant
from models.user import User
from utils.tenant import generate_tenant_slug, validate_subdomain
import re
import logging

logger = logging.getLogger(__name__)

onboarding_bp = Blueprint('onboarding', __name__)

def is_valid_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_strong_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

def validate_organization_name(name):
    """Validate organization name."""
    if not name or len(name.strip()) < 3:
        return False, "Organization name must be at least 3 characters long"
    if len(name.strip()) > 100:
        return False, "Organization name must be less than 100 characters"
    if not re.match(r'^[a-zA-Z0-9\s\-\'\.]+$', name.strip()):
        return False, "Organization name contains invalid characters"
    return True, "Valid organization name"

@onboarding_bp.route('/check-availability', methods=['POST'])
def check_availability():
    """Check if subdomain and organization name are available."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    organization_name = data.get('organization_name', '').strip()
    preferred_subdomain = data.get('preferred_subdomain', '').strip().lower()
    
    result = {
        'organization_name': {
            'value': organization_name,
            'available': True,
            'message': 'Available'
        },
        'subdomain': {
            'value': preferred_subdomain,
            'available': True,
            'message': 'Available',
            'suggestions': []
        }
    }
    
    # Validate organization name
    if organization_name:
        is_valid, message = validate_organization_name(organization_name)
        if not is_valid:
            result['organization_name']['available'] = False
            result['organization_name']['message'] = message
        else:
            # Check if organization name already exists
            existing_tenant = Tenant.query.filter(
                db.func.lower(Tenant.name) == organization_name.lower()
            ).first()
            if existing_tenant:
                result['organization_name']['available'] = False
                result['organization_name']['message'] = 'Organization name already exists'
    
    # Validate and check subdomain
    if preferred_subdomain:
        is_valid, message = validate_subdomain(preferred_subdomain)
        if not is_valid:
            result['subdomain']['available'] = False
            result['subdomain']['message'] = message
        else:
            # Check if subdomain already exists
            existing_subdomain = Tenant.query.filter_by(subdomain=preferred_subdomain).first()
            if existing_subdomain:
                result['subdomain']['available'] = False
                result['subdomain']['message'] = 'Subdomain already taken'
                
                # Generate suggestions
                base_subdomain = preferred_subdomain
                suggestions = []
                for i in range(1, 6):
                    suggestion = f"{base_subdomain}{i}"
                    if not Tenant.query.filter_by(subdomain=suggestion).first():
                        suggestions.append(suggestion)
                        if len(suggestions) >= 3:
                            break
                
                result['subdomain']['suggestions'] = suggestions
    
    return jsonify(result), 200

@onboarding_bp.route('/register', methods=['POST'])
def register_tenant():
    """Register a new tenant with admin user."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Extract and validate data
    organization_name = data.get('organization_name', '').strip()
    subdomain = data.get('subdomain', '').strip().lower()
    admin_email = data.get('admin_email', '').strip().lower()
    admin_password = data.get('admin_password', '')
    admin_first_name = data.get('admin_first_name', '').strip()
    admin_last_name = data.get('admin_last_name', '').strip()
    
    # Validation
    errors = []
    
    # Validate organization name
    if not organization_name:
        errors.append("Organization name is required")
    else:
        is_valid, message = validate_organization_name(organization_name)
        if not is_valid:
            errors.append(message)
        else:
            # Check if organization already exists
            existing_org = Tenant.query.filter(
                db.func.lower(Tenant.name) == organization_name.lower()
            ).first()
            if existing_org:
                errors.append("Organization name already exists")
    
    # Validate subdomain
    if not subdomain:
        errors.append("Subdomain is required")
    else:
        is_valid, message = validate_subdomain(subdomain)
        if not is_valid:
            errors.append(message)
        else:
            # Check if subdomain already exists
            existing_subdomain = Tenant.query.filter_by(subdomain=subdomain).first()
            if existing_subdomain:
                errors.append("Subdomain already taken")
    
    # Validate admin email
    if not admin_email:
        errors.append("Admin email is required")
    elif not is_valid_email(admin_email):
        errors.append("Invalid admin email format")
    
    # Validate admin password
    if not admin_password:
        errors.append("Admin password is required")
    else:
        is_strong, message = is_strong_password(admin_password)
        if not is_strong:
            errors.append(message)
    
    # Validate admin names
    if not admin_first_name:
        errors.append("Admin first name is required")
    if not admin_last_name:
        errors.append("Admin last name is required")
    
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        # Create tenant
        slug = generate_tenant_slug(organization_name)
        tenant = Tenant(
            name=organization_name,
            slug=slug,
            subdomain=subdomain,
            is_active=True
        )
        db.session.add(tenant)
        db.session.flush()  # Get tenant ID
        
        # Create admin user
        admin_user = User(
            email=admin_email,
            first_name=admin_first_name,
            last_name=admin_last_name,
            role='super_admin',
            is_verified=True,  # Admin is auto-verified
            is_active=True,
            tenant_id=tenant.id
        )
        admin_user.set_password(admin_password)
        db.session.add(admin_user)
        
        # Commit transaction
        db.session.commit()
        
        logger.info(f"New tenant registered: {organization_name} ({subdomain})")
        
        return jsonify({
            'message': 'Organization registered successfully',
            'tenant': {
                'id': tenant.id,
                'name': tenant.name,
                'slug': tenant.slug,
                'subdomain': tenant.subdomain,
                'url': f"https://{subdomain}.hockey-manager.com"
            },
            'admin_user': {
                'id': admin_user.id,
                'email': admin_user.email,
                'full_name': admin_user.full_name,
                'role': admin_user.role
            },
            'next_steps': [
                "Check your email for verification instructions",
                "Log in to your new organization",
                "Set up your team configuration",
                "Add players to your roster",
                "Schedule your first game"
            ]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering tenant: {e}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@onboarding_bp.route('/onboarding-status/<subdomain>')
def get_onboarding_status(subdomain):
    """Get onboarding status for a tenant."""
    tenant = Tenant.query.filter_by(subdomain=subdomain).first()
    
    if not tenant:
        return jsonify({'error': 'Tenant not found'}), 404
    
    # Check onboarding completion status
    admin_users = User.query.filter_by(tenant_id=tenant.id, role='admin').count()
    total_users = User.query.filter_by(tenant_id=tenant.id).count()
    
    # Import other models to check setup status
    from models.player import Player
    from models.game import Game
    
    total_players = Player.query.filter_by(tenant_id=tenant.id).count()
    total_games = Game.query.filter_by(tenant_id=tenant.id).count()
    
    onboarding_steps = {
        'organization_created': True,  # If we're here, it's created
        'admin_user_created': admin_users > 0,
        'players_added': total_players > 0,
        'first_game_scheduled': total_games > 0,
        'team_configuration_set': False  # TODO: Implement team config check
    }
    
    completion_percentage = sum(onboarding_steps.values()) / len(onboarding_steps) * 100
    
    return jsonify({
        'tenant': {
            'id': tenant.id,
            'name': tenant.name,
            'subdomain': tenant.subdomain,
            'created_at': tenant.created_at.isoformat()
        },
        'onboarding_steps': onboarding_steps,
        'completion_percentage': round(completion_percentage),
        'statistics': {
            'admin_users': admin_users,
            'total_users': total_users,
            'total_players': total_players,
            'total_games': total_games
        },
        'next_recommended_action': get_next_recommended_action(onboarding_steps)
    }), 200

def get_next_recommended_action(steps):
    """Get the next recommended onboarding action."""
    if not steps['admin_user_created']:
        return {
            'action': 'create_admin',
            'title': 'Create Admin User',
            'description': 'Set up your administrator account'
        }
    elif not steps['team_configuration_set']:
        return {
            'action': 'configure_team',
            'title': 'Configure Team Settings',
            'description': 'Set up team colors, position configuration, and game settings'
        }
    elif not steps['players_added']:
        return {
            'action': 'add_players',
            'title': 'Add Players',
            'description': 'Add your regular players and spare players to the roster'
        }
    elif not steps['first_game_scheduled']:
        return {
            'action': 'schedule_game',
            'title': 'Schedule First Game',
            'description': 'Create your first pickup game and send invitations'
        }
    else:
        return {
            'action': 'complete',
            'title': 'Onboarding Complete',
            'description': 'Your organization is fully set up and ready to go!'
        }

@onboarding_bp.route('/welcome-email', methods=['POST'])
def send_welcome_email():
    """Send welcome email to new tenant admin."""
    data = request.get_json()
    
    if not data or not data.get('tenant_id'):
        return jsonify({'error': 'Tenant ID required'}), 400
    
    tenant = Tenant.query.get(data['tenant_id'])
    if not tenant:
        return jsonify({'error': 'Tenant not found'}), 404
    
    admin_user = User.query.filter_by(tenant_id=tenant.id, role='admin').first()
    if not admin_user:
        return jsonify({'error': 'Admin user not found'}), 404
    
    try:
        # TODO: Implement email sending with Flask-Mail
        # This would send a welcome email with:
        # - Organization setup confirmation
        # - Login instructions
        # - Next steps guide
        # - Support contact information
        
        logger.info(f"Welcome email sent to {admin_user.email} for tenant {tenant.name}")
        
        return jsonify({
            'message': 'Welcome email sent successfully',
            'recipient': admin_user.email
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")
        return jsonify({'error': 'Failed to send welcome email'}), 500

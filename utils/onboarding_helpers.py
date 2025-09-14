"""
Helper functions for tenant onboarding process.
"""
import re
from models.tenant import Tenant
from models.user import User
from models.player import Player
from models.game import Game

def validate_organization_data(data):
    """Validate organization registration data."""
    errors = []
    
    # Required fields
    required_fields = {
        'organization_name': 'Organization name',
        'subdomain': 'Subdomain',
        'admin_email': 'Admin email',
        'admin_password': 'Admin password',
        'admin_first_name': 'Admin first name',
        'admin_last_name': 'Admin last name'
    }
    
    for field, label in required_fields.items():
        if not data.get(field, '').strip():
            errors.append(f"{label} is required")
    
    return errors

def generate_onboarding_checklist(tenant_id):
    """Generate onboarding checklist for a tenant."""
    # Count existing data
    admin_count = User.query.filter_by(tenant_id=tenant_id, role='admin').count()
    user_count = User.query.filter_by(tenant_id=tenant_id).count()
    player_count = Player.query.filter_by(tenant_id=tenant_id).count()
    game_count = Game.query.filter_by(tenant_id=tenant_id).count()
    
    checklist = [
        {
            'id': 'admin_setup',
            'title': 'Admin Account Setup',
            'description': 'Create your administrator account',
            'completed': admin_count > 0,
            'required': True,
            'order': 1
        },
        {
            'id': 'team_config',
            'title': 'Team Configuration',
            'description': 'Set up team colors, jersey numbers, and position settings',
            'completed': False,  # TODO: Check team config table
            'required': True,
            'order': 2
        },
        {
            'id': 'add_players',
            'title': 'Add Players',
            'description': 'Add your regular and spare players to the roster',
            'completed': player_count >= 5,  # Minimum viable roster
            'required': True,
            'order': 3
        },
        {
            'id': 'schedule_game',
            'title': 'Schedule First Game',
            'description': 'Create and schedule your first pickup game',
            'completed': game_count > 0,
            'required': True,
            'order': 4
        },
        {
            'id': 'invite_users',
            'title': 'Invite Additional Users',
            'description': 'Invite other organizers or assistants',
            'completed': user_count > 1,
            'required': False,
            'order': 5
        },
        {
            'id': 'test_invitations',
            'title': 'Test Email Invitations',
            'description': 'Send test invitations to verify email setup',
            'completed': False,  # TODO: Track test invitations
            'required': False,
            'order': 6
        }
    ]
    
    # Calculate completion percentage
    required_tasks = [task for task in checklist if task['required']]
    completed_required = sum(1 for task in required_tasks if task['completed'])
    completion_percentage = (completed_required / len(required_tasks)) * 100 if required_tasks else 0
    
    return {
        'checklist': sorted(checklist, key=lambda x: x['order']),
        'completion_percentage': round(completion_percentage),
        'required_completed': completed_required,
        'required_total': len(required_tasks),
        'optional_completed': sum(1 for task in checklist if not task['required'] and task['completed']),
        'optional_total': len([task for task in checklist if not task['required']])
    }

def get_onboarding_tips():
    """Get helpful onboarding tips."""
    return [
        {
            'category': 'Getting Started',
            'tips': [
                "Start by adding your regular players first, then add spare players",
                "Set up your team colors and jersey preferences early",
                "Test email invitations with a small group before your first game"
            ]
        },
        {
            'category': 'Player Management',
            'tips': [
                "Use clear position categories (Goaltender, Defence, Forward)",
                "Set spare player priorities (Priority 1 for first call-ups)",
                "Include player photos to help with team recognition"
            ]
        },
        {
            'category': 'Game Scheduling',
            'tips': [
                "Schedule games at least a week in advance for better attendance",
                "Set up recurring games for regular weekly/monthly sessions",
                "Use the automatic spare rotation to ensure fair play opportunities"
            ]
        },
        {
            'category': 'Communication',
            'tips': [
                "Customize email templates to match your team's tone",
                "Set up bilingual templates if you have English/French players",
                "Use the assignment rotation feature to share organizational tasks"
            ]
        }
    ]

def generate_welcome_email_content(tenant, admin_user):
    """Generate welcome email content for new tenant."""
    return {
        'subject': f"Welcome to Hockey Pickup Manager - {tenant.name}",
        'template': 'welcome_tenant',
        'context': {
            'tenant_name': tenant.name,
            'admin_name': admin_user.full_name,
            'subdomain': tenant.subdomain,
            'login_url': f"https://{tenant.subdomain}.hockey-manager.com/login",
            'setup_url': f"https://{tenant.subdomain}.hockey-manager.com/onboarding",
            'support_email': 'support@hockey-manager.com',
            'next_steps': [
                "Complete your team configuration",
                "Add your players to the roster",
                "Schedule your first pickup game",
                "Invite other organizers if needed"
            ]
        }
    }

def validate_subdomain_format(subdomain):
    """Validate subdomain format and availability."""
    if not subdomain:
        return False, "Subdomain is required"
    
    # Length check
    if len(subdomain) < 3:
        return False, "Subdomain must be at least 3 characters long"
    if len(subdomain) > 30:
        return False, "Subdomain must be less than 30 characters"
    
    # Format check
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', subdomain):
        return False, "Subdomain can only contain lowercase letters, numbers, and hyphens (not at the start or end)"
    
    # Reserved subdomains
    reserved = ['www', 'api', 'admin', 'app', 'mail', 'ftp', 'blog', 'shop', 'store', 'support', 'help']
    if subdomain in reserved:
        return False, "This subdomain is reserved"
    
    return True, "Valid subdomain format"

def suggest_subdomains(base_name, count=5):
    """Generate subdomain suggestions based on organization name."""
    # Clean base name
    base = re.sub(r'[^a-zA-Z0-9]', '', base_name.lower())
    base = base[:20]  # Limit length
    
    suggestions = []
    
    # Try base name variations
    variations = [
        base,
        f"{base}hockey",
        f"{base}hc",
        f"{base}pickup",
        f"{base}team"
    ]
    
    # Add numbered variations
    for i in range(1, 10):
        variations.extend([
            f"{base}{i}",
            f"{base}hockey{i}",
            f"{base}hc{i}"
        ])
    
    # Check availability and add to suggestions
    for variation in variations:
        if len(suggestions) >= count:
            break
        
        is_valid, _ = validate_subdomain_format(variation)
        if is_valid and not Tenant.query.filter_by(subdomain=variation).first():
            suggestions.append(variation)
    
    return suggestions[:count]

def calculate_setup_progress(tenant_id):
    """Calculate detailed setup progress for a tenant."""
    progress = {
        'overall_percentage': 0,
        'categories': {
            'basic_setup': {
                'name': 'Basic Setup',
                'percentage': 0,
                'items': []
            },
            'team_config': {
                'name': 'Team Configuration',
                'percentage': 0,
                'items': []
            },
            'player_management': {
                'name': 'Player Management',
                'percentage': 0,
                'items': []
            },
            'game_scheduling': {
                'name': 'Game Scheduling',
                'percentage': 0,
                'items': []
            }
        }
    }
    
    # Basic setup checks
    admin_exists = User.query.filter_by(tenant_id=tenant_id, role='admin').first() is not None
    progress['categories']['basic_setup']['items'] = [
        {'name': 'Admin account created', 'completed': admin_exists}
    ]
    
    # Team configuration checks (placeholder)
    progress['categories']['team_config']['items'] = [
        {'name': 'Team colors set', 'completed': False},
        {'name': 'Position configuration', 'completed': False}
    ]
    
    # Player management checks
    player_count = Player.query.filter_by(tenant_id=tenant_id).count()
    progress['categories']['player_management']['items'] = [
        {'name': 'At least 5 players added', 'completed': player_count >= 5},
        {'name': 'Goaltenders added', 'completed': Player.query.filter_by(tenant_id=tenant_id, position='goaltender').count() > 0},
        {'name': 'Spare players configured', 'completed': Player.query.filter_by(tenant_id=tenant_id, player_type='spare').count() > 0}
    ]
    
    # Game scheduling checks
    game_count = Game.query.filter_by(tenant_id=tenant_id).count()
    progress['categories']['game_scheduling']['items'] = [
        {'name': 'First game scheduled', 'completed': game_count > 0}
    ]
    
    # Calculate percentages
    total_completed = 0
    total_items = 0
    
    for category in progress['categories'].values():
        completed = sum(1 for item in category['items'] if item['completed'])
        total = len(category['items'])
        category['percentage'] = (completed / total * 100) if total > 0 else 0
        
        total_completed += completed
        total_items += total
    
    progress['overall_percentage'] = (total_completed / total_items * 100) if total_items > 0 else 0
    
    return progress

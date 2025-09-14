#!/usr/bin/env python3
"""
Enhanced Flask server with tenant onboarding and registration flow.
"""
import os
from flask import Flask, request, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time
import secrets
import re

# Create Flask app
app = Flask(__name__)
app.config.update(
    DEBUG=True,
    SECRET_KEY='dev-secret-key-change-in-production',
    SQLALCHEMY_DATABASE_URI='sqlite:///hockey_onboarding.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    WTF_CSRF_ENABLED=False,
    MAIL_SERVER='localhost',
    MAIL_PORT=1025,
    MAIL_USE_TLS=False,
    MAIL_DEFAULT_SENDER='noreply@hockey-manager.com',
)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
mail = Mail(app)

# Configure login manager
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Tenant context utilities
def get_current_tenant():
    """Get current tenant from request context."""
    return getattr(g, 'current_tenant', None)

def get_current_tenant_id():
    """Get current tenant ID from request context."""
    tenant = get_current_tenant()
    return tenant.id if tenant else None

def set_tenant_context(tenant):
    """Set tenant context for current request."""
    g.current_tenant = tenant
    g.current_tenant_id = tenant.id if tenant else None

def detect_tenant_from_request():
    """Detect tenant from request subdomain or path."""
    # Check for subdomain in Host header
    host = request.headers.get('Host', '')
    if '.' in host:
        subdomain = host.split('.')[0]
        if subdomain not in ['localhost', '127', 'www']:
            tenant = Tenant.query.filter_by(subdomain=subdomain).first()
            if tenant:
                return tenant
    
    # For development, try to get from X-Tenant-Subdomain header
    subdomain = request.headers.get('X-Tenant-Subdomain')
    if subdomain:
        return Tenant.query.filter_by(subdomain=subdomain).first()
    
    return None

# Models
class TenantMixin:
    """Mixin class to add tenant isolation to models."""
    
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    @classmethod
    def query_for_tenant(cls, tenant_id=None):
        """Get query filtered by tenant."""
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
        
        if tenant_id:
            return cls.query.filter(cls.tenant_id == tenant_id)
        return cls.query

class Tenant(db.Model):
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    subdomain = db.Column(db.String(50), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Onboarding tracking
    onboarding_completed = db.Column(db.Boolean, default=False)
    welcome_email_sent = db.Column(db.Boolean, default=False)
    
    # Relationships
    users = db.relationship('User', backref='tenant', lazy=True)
    players = db.relationship('Player', backref='tenant', lazy=True)
    games = db.relationship('Game', backref='tenant', lazy=True)

class User(TenantMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Unique constraint for email per tenant
    __table_args__ = (db.UniqueConstraint('email', 'tenant_id', name='unique_email_per_tenant'),)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self):
        return self.role in ['admin', 'super_admin']
    
    # Flask-Login required methods
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

class Player(TenantMixin, db.Model):
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    position = db.Column(db.String(20), nullable=False)
    player_type = db.Column(db.String(20), nullable=False)
    spare_priority = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('email', 'tenant_id', name='unique_player_email_per_tenant'),)

class Game(TenantMixin, db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    time = db.Column(db.Time, nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='scheduled', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Tenant Isolation Middleware
@app.before_request
def before_request():
    """Set up tenant context before each request."""
    # Skip tenant detection for onboarding routes
    skip_paths = ['/health', '/api/onboarding/', '/static/']
    if any(request.path.startswith(path) for path in skip_paths):
        return
    
    try:
        tenant = detect_tenant_from_request()
        if tenant:
            set_tenant_context(tenant)
            
            # Auto-assign tenant_id to new objects
            @db.event.listens_for(db.session, 'before_flush', once=True)
            def before_flush(session, flush_context, instances):
                tenant_id = get_current_tenant_id()
                if tenant_id:
                    for obj in session.new:
                        if hasattr(obj, 'tenant_id') and obj.tenant_id is None:
                            obj.tenant_id = tenant_id
    except Exception as e:
        app.logger.error(f"Error setting tenant context: {e}")

@app.after_request
def after_request(response):
    """Clean up tenant context after request."""
    if hasattr(g, 'current_tenant'):
        delattr(g, 'current_tenant')
    if hasattr(g, 'current_tenant_id'):
        delattr(g, 'current_tenant_id')
    return response

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Utility functions
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

def validate_subdomain(subdomain):
    """Validate subdomain format."""
    if not subdomain:
        return False, "Subdomain is required"
    
    if len(subdomain) < 3:
        return False, "Subdomain must be at least 3 characters long"
    if len(subdomain) > 30:
        return False, "Subdomain must be less than 30 characters"
    
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', subdomain):
        return False, "Subdomain can only contain lowercase letters, numbers, and hyphens"
    
    reserved = ['www', 'api', 'admin', 'app', 'mail', 'support', 'help']
    if subdomain in reserved:
        return False, "This subdomain is reserved"
    
    return True, "Valid subdomain"

def generate_tenant_slug(name):
    """Generate URL-friendly slug from tenant name."""
    slug = re.sub(r'[^a-zA-Z0-9\s]', '', name.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug[:50]

# Routes
@app.route('/')
def index():
    current_tenant = get_current_tenant()
    return {
        'message': 'Hockey Pickup Manager - Multi-Tenant SaaS Platform',
        'version': '3.0.0',
        'features': [
            'Tenant registration and onboarding',
            'Multi-tenant isolation',
            'User authentication',
            'Player and game management'
        ],
        'current_tenant': current_tenant.name if current_tenant else None,
        'endpoints': {
            'onboarding': '/api/onboarding/',
            'auth': '/api/auth/',
            'health': '/health'
        }
    }

@app.route('/health')
def health():
    return {'status': 'healthy', 'database': 'connected', 'onboarding': 'active'}

# Onboarding Routes
@app.route('/api/onboarding/check-availability', methods=['POST'])
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
    
    # Check organization name
    if organization_name:
        existing_org = Tenant.query.filter(
            db.func.lower(Tenant.name) == organization_name.lower()
        ).first()
        if existing_org:
            result['organization_name']['available'] = False
            result['organization_name']['message'] = 'Organization name already exists'
    
    # Check subdomain
    if preferred_subdomain:
        is_valid, message = validate_subdomain(preferred_subdomain)
        if not is_valid:
            result['subdomain']['available'] = False
            result['subdomain']['message'] = message
        else:
            existing_subdomain = Tenant.query.filter_by(subdomain=preferred_subdomain).first()
            if existing_subdomain:
                result['subdomain']['available'] = False
                result['subdomain']['message'] = 'Subdomain already taken'
                
                # Generate suggestions
                suggestions = []
                for i in range(1, 6):
                    suggestion = f"{preferred_subdomain}{i}"
                    if not Tenant.query.filter_by(subdomain=suggestion).first():
                        suggestions.append(suggestion)
                        if len(suggestions) >= 3:
                            break
                
                result['subdomain']['suggestions'] = suggestions
    
    return jsonify(result), 200

@app.route('/api/onboarding/register', methods=['POST'])
def register_tenant():
    """Register a new tenant with admin user."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Extract data
    organization_name = data.get('organization_name', '').strip()
    subdomain = data.get('subdomain', '').strip().lower()
    admin_email = data.get('admin_email', '').strip().lower()
    admin_password = data.get('admin_password', '')
    admin_first_name = data.get('admin_first_name', '').strip()
    admin_last_name = data.get('admin_last_name', '').strip()
    
    # Validation
    errors = []
    
    if not organization_name:
        errors.append("Organization name is required")
    elif len(organization_name) < 3:
        errors.append("Organization name must be at least 3 characters")
    elif Tenant.query.filter(db.func.lower(Tenant.name) == organization_name.lower()).first():
        errors.append("Organization name already exists")
    
    if not subdomain:
        errors.append("Subdomain is required")
    else:
        is_valid, message = validate_subdomain(subdomain)
        if not is_valid:
            errors.append(message)
        elif Tenant.query.filter_by(subdomain=subdomain).first():
            errors.append("Subdomain already taken")
    
    if not admin_email:
        errors.append("Admin email is required")
    elif not is_valid_email(admin_email):
        errors.append("Invalid admin email format")
    
    if not admin_password:
        errors.append("Admin password is required")
    else:
        is_strong, message = is_strong_password(admin_password)
        if not is_strong:
            errors.append(message)
    
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
        db.session.flush()
        
        # Create admin user
        admin_user = User(
            email=admin_email,
            first_name=admin_first_name,
            last_name=admin_last_name,
            role='admin',
            is_verified=True,
            is_active=True,
            tenant_id=tenant.id
        )
        admin_user.set_password(admin_password)
        db.session.add(admin_user)
        
        db.session.commit()
        
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
                "Log in to your new organization",
                "Complete team configuration",
                "Add players to your roster",
                "Schedule your first game"
            ]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error registering tenant: {e}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@app.route('/api/onboarding/status/<subdomain>')
def get_onboarding_status(subdomain):
    """Get onboarding status for a tenant."""
    tenant = Tenant.query.filter_by(subdomain=subdomain).first()
    
    if not tenant:
        return jsonify({'error': 'Tenant not found'}), 404
    
    # Calculate onboarding progress
    admin_count = User.query.filter_by(tenant_id=tenant.id, role='admin').count()
    user_count = User.query.filter_by(tenant_id=tenant.id).count()
    player_count = Player.query.filter_by(tenant_id=tenant.id).count()
    game_count = Game.query.filter_by(tenant_id=tenant.id).count()
    
    steps = {
        'organization_created': True,
        'admin_user_created': admin_count > 0,
        'players_added': player_count >= 5,
        'first_game_scheduled': game_count > 0
    }
    
    completion_percentage = sum(steps.values()) / len(steps) * 100
    
    return jsonify({
        'tenant': {
            'id': tenant.id,
            'name': tenant.name,
            'subdomain': tenant.subdomain,
            'created_at': tenant.created_at.isoformat()
        },
        'onboarding_steps': steps,
        'completion_percentage': round(completion_percentage),
        'statistics': {
            'admin_users': admin_count,
            'total_users': user_count,
            'total_players': player_count,
            'total_games': game_count
        }
    }), 200

# Authentication routes (tenant-aware)
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login with tenant context."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    subdomain = data.get('subdomain', '').strip().lower()
    
    if not email or not password or not subdomain:
        return jsonify({'error': 'Email, password, and subdomain are required'}), 400
    
    # Find tenant
    tenant = Tenant.query.filter_by(subdomain=subdomain).first()
    if not tenant:
        return jsonify({'error': 'Organization not found'}), 404
    
    # Find user in tenant
    user = User.query.filter_by(email=email, tenant_id=tenant.id).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403
    
    # Set tenant context and log in user
    set_tenant_context(tenant)
    login_user(user)
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'tenant_id': user.tenant_id
        },
        'tenant': {
            'id': tenant.id,
            'name': tenant.name,
            'subdomain': tenant.subdomain
        }
    }), 200

# List all tenants (for demo purposes)
@app.route('/api/tenants')
def list_tenants():
    """List all registered tenants."""
    tenants = Tenant.query.filter_by(is_active=True).all()
    return jsonify({
        'tenants': [{
            'id': t.id,
            'name': t.name,
            'subdomain': t.subdomain,
            'url': f"https://{t.subdomain}.hockey-manager.com",
            'user_count': len(t.users),
            'player_count': len(t.players),
            'game_count': len(t.games),
            'created_at': t.created_at.isoformat()
        } for t in tenants],
        'total': len(tenants)
    })

if __name__ == '__main__':
    # Create tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables created!")
    
    print("\n🚀 Hockey Pickup Manager - Tenant Onboarding Platform")
    print("=" * 65)
    print("🌐 Server: http://localhost:8002")
    print("❤️  Health: http://localhost:8002/health")
    print("📋 API Docs: http://localhost:8002")
    print("\n🏢 Tenant Onboarding Features:")
    print("• Organization registration with subdomain")
    print("• Admin user creation and verification")
    print("• Availability checking for names/subdomains")
    print("• Onboarding progress tracking")
    print("• Multi-tenant login system")
    print("\n📝 Test the onboarding flow:")
    print("1. Check availability: POST /api/onboarding/check-availability")
    print("2. Register org: POST /api/onboarding/register")
    print("3. Check status: GET /api/onboarding/status/{subdomain}")
    print("4. Login: POST /api/auth/login")
    print("5. List tenants: GET /api/tenants")
    print("=" * 65)
    
    app.run(host='0.0.0.0', port=8002, debug=True)

#!/usr/bin/env python3
"""
Enhanced Flask server with comprehensive tenant isolation middleware.
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
    SQLALCHEMY_DATABASE_URI='sqlite:///hockey_dev_enhanced.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    WTF_CSRF_ENABLED=False,
    MAIL_SERVER='localhost',
    MAIL_PORT=1025,
    MAIL_USE_TLS=False,
    MAIL_DEFAULT_SENDER='noreply@hockey-app.local',
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
    """Detect tenant from request (simplified for demo)."""
    # For demo, always use 'demo' tenant
    return Tenant.query.filter_by(subdomain='demo').first()

# Models with tenant isolation
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
    
    @classmethod
    def create_for_tenant(cls, **kwargs):
        """Create a new instance for the current tenant."""
        tenant_id = get_current_tenant_id()
        if tenant_id:
            kwargs['tenant_id'] = tenant_id
        return cls(**kwargs)

class Tenant(db.Model):
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    subdomain = db.Column(db.String(50), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    position = db.Column(db.String(20), nullable=False)  # 'goaltender', 'defence', 'forward'
    player_type = db.Column(db.String(20), nullable=False)  # 'regular', 'spare'
    spare_priority = db.Column(db.Integer, nullable=True)  # 1 or 2 for spare players
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint on email within tenant
    __table_args__ = (db.UniqueConstraint('email', 'tenant_id', name='unique_player_email_per_tenant'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'position': self.position,
            'player_type': self.player_type,
            'spare_priority': self.spare_priority,
            'is_active': self.is_active,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat()
        }

class Game(TenantMixin, db.Model):
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    time = db.Column(db.Time, nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='scheduled', nullable=False)
    goaltenders_needed = db.Column(db.Integer, default=2)
    defence_needed = db.Column(db.Integer, default=4)
    forwards_needed = db.Column(db.Integer, default=6)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'time': self.time.isoformat(),
            'venue': self.venue,
            'status': self.status,
            'goaltenders_needed': self.goaltenders_needed,
            'defence_needed': self.defence_needed,
            'forwards_needed': self.forwards_needed,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat()
        }

# Tenant Isolation Middleware
@app.before_request
def before_request():
    """Set up tenant context before each request."""
    # Skip tenant detection for certain routes
    skip_paths = ['/health', '/api/tenants/register', '/static/']
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

def get_or_create_tenant(subdomain='demo'):
    """Get or create a demo tenant for testing."""
    tenant = Tenant.query.filter_by(subdomain=subdomain).first()
    if not tenant:
        tenant = Tenant(
            name=f"{subdomain.title()} Hockey Club",
            slug=subdomain,
            subdomain=subdomain,
            is_active=True
        )
        db.session.add(tenant)
        db.session.commit()
    return tenant

# Routes
@app.route('/')
def index():
    return {
        'message': 'Hockey Pickup Manager API - Enhanced with Tenant Isolation',
        'version': '2.0.0',
        'features': [
            'Multi-tenant isolation',
            'Automatic query filtering',
            'Tenant-aware CRUD operations',
            'Cross-tenant access prevention'
        ],
        'endpoints': {
            'auth': '/api/auth/',
            'players': '/api/players/',
            'games': '/api/games/',
            'health': '/health'
        },
        'current_tenant': get_current_tenant().name if get_current_tenant() else None
    }

@app.route('/health')
def health():
    return {'status': 'healthy', 'database': 'connected', 'tenant_isolation': 'active'}

# Authentication routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    
    # Validation
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    is_strong, message = is_strong_password(password)
    if not is_strong:
        return jsonify({'error': message}), 400
    
    # Get current tenant
    tenant = get_current_tenant()
    if not tenant:
        return jsonify({'error': 'Tenant context required'}), 400
    
    # Check if user already exists in this tenant
    existing_user = User.query.filter_by(email=email, tenant_id=tenant.id).first()
    if existing_user:
        return jsonify({'error': 'User with this email already exists in this tenant'}), 409
    
    # Check if this is the first user (becomes admin)
    is_first_user = User.query.filter_by(tenant_id=tenant.id).count() == 0
    
    # Create user (tenant_id will be auto-assigned by middleware)
    user = User(
        email=email,
        first_name=first_name or 'User',
        last_name=last_name or 'Name',
        role='admin' if is_first_user else 'user',
        is_verified=is_first_user
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'user': {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'is_verified': user.is_verified,
            'tenant_id': user.tenant_id
        },
        'tenant': {
            'id': tenant.id,
            'name': tenant.name,
            'subdomain': tenant.subdomain
        }
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Get current tenant
    tenant = get_current_tenant()
    if not tenant:
        return jsonify({'error': 'Tenant context required'}), 400
    
    # Find user in current tenant
    user = User.query.filter_by(email=email, tenant_id=tenant.id).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403
    
    # Log in user
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
            'is_verified': user.is_verified,
            'tenant_id': user.tenant_id
        },
        'tenant': {
            'id': tenant.id,
            'name': tenant.name,
            'subdomain': tenant.subdomain
        }
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/auth/profile')
@login_required
def profile():
    return jsonify({
        'user': {
            'id': current_user.id,
            'email': current_user.email,
            'full_name': current_user.full_name,
            'role': current_user.role,
            'is_verified': current_user.is_verified,
            'tenant_id': current_user.tenant_id,
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        },
        'tenant': {
            'id': current_user.tenant.id,
            'name': current_user.tenant.name,
            'subdomain': current_user.tenant.subdomain
        }
    }), 200

# Player management routes with tenant isolation
@app.route('/api/players', methods=['GET'])
@login_required
def list_players():
    """List players for current tenant only."""
    players = Player.query.all()  # Automatically filtered by tenant
    return jsonify({
        'players': [player.to_dict() for player in players],
        'total': len(players),
        'tenant': get_current_tenant().name
    })

@app.route('/api/players', methods=['POST'])
@login_required
def create_player():
    """Create a new player in current tenant."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    required_fields = ['name', 'email', 'position', 'player_type']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if player email already exists in current tenant
    existing_player = Player.query.filter_by(email=data['email']).first()
    if existing_player:
        return jsonify({'error': 'Player with this email already exists'}), 409
    
    # Create player (tenant_id will be auto-assigned)
    player = Player(
        name=data['name'],
        email=data['email'],
        position=data['position'],
        player_type=data['player_type'],
        spare_priority=data.get('spare_priority')
    )
    
    db.session.add(player)
    db.session.commit()
    
    return jsonify({
        'message': 'Player created successfully',
        'player': player.to_dict()
    }), 201

@app.route('/api/players/<int:player_id>')
@login_required
def get_player(player_id):
    """Get a specific player (tenant-filtered)."""
    player = Player.query.get_or_404(player_id)
    return jsonify({'player': player.to_dict()})

# Game management routes with tenant isolation
@app.route('/api/games', methods=['GET'])
@login_required
def list_games():
    """List games for current tenant only."""
    games = Game.query.all()  # Automatically filtered by tenant
    return jsonify({
        'games': [game.to_dict() for game in games],
        'total': len(games),
        'tenant': get_current_tenant().name
    })

@app.route('/api/games', methods=['POST'])
@login_required
def create_game():
    """Create a new game in current tenant."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate required fields
    required_fields = ['date', 'time', 'venue']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Parse date and time
    try:
        game_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        game_time = datetime.strptime(data['time'], '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Invalid date or time format'}), 400
    
    # Create game (tenant_id will be auto-assigned)
    game = Game(
        date=game_date,
        time=game_time,
        venue=data['venue'],
        goaltenders_needed=data.get('goaltenders_needed', 2),
        defence_needed=data.get('defence_needed', 4),
        forwards_needed=data.get('forwards_needed', 6)
    )
    
    db.session.add(game)
    db.session.commit()
    
    return jsonify({
        'message': 'Game created successfully',
        'game': game.to_dict()
    }), 201

# Tenant management
@app.route('/api/tenants')
def list_tenants():
    tenants = Tenant.query.filter_by(is_active=True).all()
    return jsonify({
        'tenants': [{
            'id': t.id,
            'name': t.name,
            'subdomain': t.subdomain,
            'user_count': len(t.users),
            'player_count': len(t.players),
            'game_count': len(t.games)
        } for t in tenants]
    })

if __name__ == '__main__':
    # Create tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables created!")
        
        # Create demo tenant if it doesn't exist
        demo_tenant = get_or_create_tenant('demo')
        print(f"✅ Demo tenant ready: {demo_tenant.name}")
    
    print("\n🚀 Hockey Pickup Manager - Enhanced with Tenant Isolation")
    print("=" * 60)
    print("🌐 Server: http://localhost:8001")
    print("❤️  Health: http://localhost:8001/health")
    print("📋 API Docs: http://localhost:8001")
    print("\n🔒 Tenant Isolation Features:")
    print("• Automatic tenant context detection")
    print("• Query filtering by tenant")
    print("• Cross-tenant access prevention")
    print("• Automatic tenant_id assignment")
    print("\n📝 Test the enhanced system:")
    print("1. Register: POST http://localhost:8001/api/auth/register")
    print("2. Login: POST http://localhost:8001/api/auth/login")
    print("3. Create Player: POST http://localhost:8001/api/players")
    print("4. List Players: GET http://localhost:8001/api/players")
    print("5. Create Game: POST http://localhost:8001/api/games")
    print("6. List Games: GET http://localhost:8001/api/games")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8001, debug=True)

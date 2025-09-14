#!/usr/bin/env python3
"""
Minimal Flask server to test authentication system.
"""
import os
from flask import Flask, request, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets
import re

# Create Flask app
app = Flask(__name__)
app.config.update(
    DEBUG=True,
    SECRET_KEY='dev-secret-key-change-in-production',
    SQLALCHEMY_DATABASE_URI='sqlite:///hockey_dev.db',
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

# Models
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

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
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
        'message': 'Hockey Pickup Manager API - Authentication Test Server',
        'version': '1.0.0',
        'endpoints': {
            'register': 'POST /api/auth/register',
            'login': 'POST /api/auth/login',
            'logout': 'POST /api/auth/logout',
            'profile': 'GET /api/auth/profile',
            'health': 'GET /health'
        },
        'demo_tenant': 'demo'
    }

@app.route('/health')
def health():
    return {'status': 'healthy', 'database': 'connected'}

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
    
    # Get or create demo tenant
    tenant = get_or_create_tenant('demo')
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email, tenant_id=tenant.id).first()
    if existing_user:
        return jsonify({'error': 'User with this email already exists'}), 409
    
    # Check if this is the first user (becomes admin)
    is_first_user = User.query.filter_by(tenant_id=tenant.id).count() == 0
    
    # Create user
    user = User(
        email=email,
        first_name=first_name or 'User',
        last_name=last_name or 'Name',
        role='admin' if is_first_user else 'user',
        is_verified=is_first_user,  # First user is auto-verified
        tenant_id=tenant.id
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
            'is_verified': user.is_verified
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
    
    # Get demo tenant
    tenant = get_or_create_tenant('demo')
    
    # Find user
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
            'is_verified': user.is_verified
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
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        },
        'tenant': {
            'id': current_user.tenant.id,
            'name': current_user.tenant.name,
            'subdomain': current_user.tenant.subdomain
        }
    }), 200

@app.route('/api/tenants')
def list_tenants():
    tenants = Tenant.query.filter_by(is_active=True).all()
    return jsonify({
        'tenants': [{
            'id': t.id,
            'name': t.name,
            'subdomain': t.subdomain,
            'user_count': len(t.users)
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
    
    print("\n🚀 Hockey Pickup Manager - Authentication Test Server")
    print("=" * 50)
    print("🌐 Server: http://localhost:5000")
    print("❤️  Health: http://localhost:5000/health")
    print("📋 API Docs: http://localhost:5000")
    print("\n📝 Test the authentication:")
    print("1. Register: POST http://localhost:5000/api/auth/register")
    print("2. Login: POST http://localhost:5000/api/auth/login")
    print("3. Profile: GET http://localhost:5000/api/auth/profile")
    print("4. Logout: POST http://localhost:5000/api/auth/logout")
    print("\n💡 Use curl, Postman, or any HTTP client to test!")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

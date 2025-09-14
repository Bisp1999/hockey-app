#!/usr/bin/env python3
"""
Simple development server startup script.
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

# Set environment
os.environ['FLASK_ENV'] = 'development'

# Create Flask app
app = Flask(__name__)

# Simple configuration for development
app.config.update(
    DEBUG=True,
    SECRET_KEY='dev-secret-key-change-in-production',
    SQLALCHEMY_DATABASE_URI='sqlite:///hockey_dev.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ECHO=True,
    WTF_CSRF_ENABLED=False,
    MAIL_SERVER='localhost',
    MAIL_PORT=1025,
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=False,
    MAIL_DEFAULT_SENDER='noreply@hockey-app.local',
    TENANT_URL_SUBDOMAIN_ENABLED=True,
    TENANT_URL_PATH_ENABLED=False,
)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
mail = Mail(app)

# Configure login manager
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.query.get(int(user_id))

# Initialize tenant middleware
from utils.middleware import TenantMiddleware
TenantMiddleware(app)

# Register blueprints
from routes.auth import auth_bp
from routes.tenants import tenants_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(tenants_bp, url_prefix='/api/tenant')

# Import models to register them
from models import tenant, user

# Create tables
with app.app_context():
    db.create_all()
    print("Database tables created!")

# Add a simple test route
@app.route('/')
def index():
    return {
        'message': 'Hockey Pickup Manager API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/auth/',
            'tenants': '/api/tenant/'
        }
    }

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    print("Starting Hockey Pickup Manager development server...")
    print("API available at: http://localhost:5000")
    print("Health check: http://localhost:5000/health")
    print("Auth endpoints: http://localhost:5000/api/auth/")
    print("Tenant endpoints: http://localhost:5000/api/tenant/")
    app.run(host='0.0.0.0', port=5000, debug=True)

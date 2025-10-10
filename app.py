"""
Main Flask application entry point with multi-tenant configuration.
"""
from load_env import load_environment

# Load environment FIRST, before any other imports that might use it
load_environment()

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"
)

def create_app(config_name='development'):
    """Application factory pattern for Flask app creation."""
    import os  # Add this line
    
    import logging

    # Disable SQLAlchemy SQL logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    app = Flask(__name__)
    app.config.from_object(config[config_name]) 
    
    # Debug: Log which config is being used and SameSite setting
    print(f"=== USING CONFIG: {config_name} ===")
    print(f"=== SESSION_COOKIE_SAMESITE: {app.config.get('SESSION_COOKIE_SAMESITE')} ===")
    
    # Override config from environment variables (ensures env vars take precedence)
    env_overrides = {
        'MAIL_SERVER': os.getenv('MAIL_SERVER'),
        'MAIL_PORT': int(os.getenv('MAIL_PORT', 587)) if os.getenv('MAIL_PORT') else None,
        'MAIL_USE_TLS': os.getenv('MAIL_USE_TLS', '').lower() == 'true' if os.getenv('MAIL_USE_TLS') else None,
        'MAIL_USE_SSL': os.getenv('MAIL_USE_SSL', '').lower() == 'true' if os.getenv('MAIL_USE_SSL') else None,
        'MAIL_USERNAME': os.getenv('MAIL_USERNAME'),
        'MAIL_PASSWORD': os.getenv('MAIL_PASSWORD'),
        'MAIL_DEFAULT_SENDER': os.getenv('MAIL_DEFAULT_SENDER') or os.getenv('MAIL_USERNAME'),
    }
    
    # Apply non-None overrides
    for key, value in env_overrides.items():
        if value is not None:
            app.config[key] = value

    # Enable CORS for frontend - support wildcard subdomains
    CORS(app, resources={r"/api/*": {
        "origins": [
            r"https://.*\.pickupteams\.com",  # Wildcard subdomains
            "https://pickupteams.com",
            "http://localhost:3000",
            "https://frontend-production-1f530.up.railway.app"
        ],
        "supports_credentials": True
    }})
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    # Initialize rate limiter
    limiter.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))
    
    # Initialize tenant middleware
    from utils.middleware import TenantMiddleware
    TenantMiddleware(app)
    
    # Initialize email test blueprint
    from routes.email_test import email_test_bp
    app.register_blueprint(email_test_bp, url_prefix='/api/email')
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.players import players_bp
    from routes.games import games_bp
    from routes.invitations import invitations_bp
    from routes.statistics import statistics_bp
    from routes.assignments import assignments_bp
    from routes.tenants import tenants_bp
    from routes.tenant_onboarding import onboarding_bp
    from routes.teams import teams_bp
    from routes.admin import admin_bp
    
    # Register blueprints with /api prefix (for direct access)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(players_bp, url_prefix='/api/players')
    app.register_blueprint(games_bp, url_prefix='/api/games')
    app.register_blueprint(invitations_bp, url_prefix='/api/invitations')
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')
    app.register_blueprint(assignments_bp, url_prefix='/api/assignments')
    app.register_blueprint(tenants_bp, url_prefix='/api/tenant')
    app.register_blueprint(onboarding_bp, url_prefix='/api/onboarding')
    app.register_blueprint(teams_bp, url_prefix='/api/teams')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # CSRF error handler (JSON response for API)
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return jsonify({'error': 'CSRF token missing or invalid', 'description': e.description}), 400
    
    # Serve uploaded files
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """Serve uploaded files."""
        import os
        # Use the base uploads folder, not the configured one (which includes /players)
        base_upload_folder = os.path.join(os.path.dirname(__file__), 'uploads')
        return send_from_directory(base_upload_folder, filename)
    
    # Import models to ensure they are registered with SQLAlchemy
    from models import tenant, user, player, team, game, invitation, statistics, assignment
    
    return app

if __name__ == '__main__':
    import os
    config_name = os.environ.get('FLASK_ENV', 'development')
    app = create_app(config_name)
    app.run(debug=True)

# Create app instance for production servers (gunicorn, etc.)
app = create_app()
"""
Main Flask application entry point with multi-tenant configuration.
"""
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import config
from load_env import load_environment

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
    # Load environment variables first
    load_environment()
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
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
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.players import players_bp
    from routes.games import games_bp
    from routes.invitations import invitations_bp
    from routes.statistics import statistics_bp
    from routes.assignments import assignments_bp
    from routes.tenants import tenants_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(players_bp, url_prefix='/api/players')
    app.register_blueprint(games_bp, url_prefix='/api/games')
    app.register_blueprint(invitations_bp, url_prefix='/api/invitations')
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')
    app.register_blueprint(assignments_bp, url_prefix='/api/assignments')
    app.register_blueprint(tenants_bp, url_prefix='/api/tenant')
    
    # CSRF error handler (JSON response for API)
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return jsonify({'error': 'CSRF token missing or invalid', 'description': e.description}), 400
    
    # Import models to ensure they are registered with SQLAlchemy
    from models import tenant, user, player, team, game, invitation, statistics, assignment
    
    return app

if __name__ == '__main__':
    import os
    config_name = os.environ.get('FLASK_ENV', 'development')
    app = create_app(config_name)
    app.run(debug=True)

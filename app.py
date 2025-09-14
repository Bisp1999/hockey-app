"""
Main Flask application entry point with multi-tenant configuration.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()

def create_app(config_class=Config):
    """Application factory pattern for Flask app creation."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.players import players_bp
    from routes.games import games_bp
    from routes.invitations import invitations_bp
    from routes.statistics import statistics_bp
    from routes.assignments import assignments_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(players_bp, url_prefix='/api/players')
    app.register_blueprint(games_bp, url_prefix='/api/games')
    app.register_blueprint(invitations_bp, url_prefix='/api/invitations')
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')
    app.register_blueprint(assignments_bp, url_prefix='/api/assignments')
    
    # Import models to ensure they are registered with SQLAlchemy
    from models import tenant, user, player, team, game, invitation, statistics, assignment
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

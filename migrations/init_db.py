"""
Database initialization script for multi-tenant hockey pickup manager.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import sys

# Add the parent directory to the path so we can import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models.tenant import Tenant
from models.user import User
from models.player import Player
from models.team import Team
from models.game import Game
from models.invitation import Invitation, InvitationResponse
from models.statistics import GameStatistic, PlayerStatistic
from models.assignment import Assignment

def init_database():
    """Initialize the database with tables."""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Create indexes for performance
        db.engine.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_tenant_email ON users(tenant_id, email);
            CREATE INDEX IF NOT EXISTS idx_players_tenant_type ON players(tenant_id, player_type);
            CREATE INDEX IF NOT EXISTS idx_players_tenant_position ON players(tenant_id, position);
            CREATE INDEX IF NOT EXISTS idx_games_tenant_date ON games(tenant_id, date);
            CREATE INDEX IF NOT EXISTS idx_invitations_game_player ON invitations(game_id, player_id);
            CREATE INDEX IF NOT EXISTS idx_statistics_game_player ON game_statistics(game_id, player_id);
            CREATE INDEX IF NOT EXISTS idx_assignments_game_player ON assignments(game_id, player_id);
        """)
        print("Database indexes created successfully!")

if __name__ == '__main__':
    init_database()

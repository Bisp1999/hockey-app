"""
Database models initialization.
"""
from app import db

# Import all models to ensure they are registered with SQLAlchemy
from .tenant import Tenant
from .user import User
from .player import Player
from .team import Team
from .game import Game
from .invitation import Invitation
from .statistics import GameStatistic, PlayerStatistic
from .assignment import Assignment

__all__ = [
    'Tenant',
    'User', 
    'Player',
    'Team',
    'Game',
    'Invitation',
    'GameStatistic',
    'PlayerStatistic',
    'Assignment'
]
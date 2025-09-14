"""
Game statistics and attendance tracking models.
"""
from datetime import datetime
from app import db

class GameStatistic(db.Model):
    """Game statistics model for tracking goals, assists, penalties."""
    
    __tablename__ = 'game_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    statistic_type = db.Column(db.String(20), nullable=False)  # 'goal', 'assist', 'penalty'
    period = db.Column(db.Integer, nullable=True)  # 1, 2, 3, or null for penalties
    time_in_period = db.Column(db.String(10), nullable=True)  # "12:34" format
    penalty_type = db.Column(db.String(50), nullable=True)  # for penalties only
    penalty_duration = db.Column(db.Integer, nullable=True)  # minutes for penalties
    team_number = db.Column(db.Integer, nullable=True)  # 1 or 2
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Multi-tenant foreign keys
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False, index=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False, index=True)
    
    # For assists, link to the goal
    goal_id = db.Column(db.Integer, db.ForeignKey('game_statistics.id'), nullable=True, index=True)
    assists = db.relationship('GameStatistic', backref=db.backref('goal', remote_side=[id]), lazy=True)
    
    def __repr__(self):
        return f'<GameStatistic {self.statistic_type} by Player {self.player_id}>'
    
    def to_dict(self):
        """Convert statistic to dictionary."""
        return {
            'id': self.id,
            'statistic_type': self.statistic_type,
            'period': self.period,
            'time_in_period': self.time_in_period,
            'penalty_type': self.penalty_type,
            'penalty_duration': self.penalty_duration,
            'team_number': self.team_number,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'tenant_id': self.tenant_id,
            'game_id': self.game_id,
            'player_id': self.player_id,
            'goal_id': self.goal_id
        }

class PlayerStatistic(db.Model):
    """Aggregated player statistics."""
    
    __tablename__ = 'player_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    games_played = db.Column(db.Integer, default=0, nullable=False)
    goals = db.Column(db.Integer, default=0, nullable=False)
    assists = db.Column(db.Integer, default=0, nullable=False)
    penalties = db.Column(db.Integer, default=0, nullable=False)
    penalty_minutes = db.Column(db.Integer, default=0, nullable=False)
    
    # Goaltender-specific statistics
    games_as_goaltender = db.Column(db.Integer, default=0, nullable=False)
    wins = db.Column(db.Integer, default=0, nullable=False)
    losses = db.Column(db.Integer, default=0, nullable=False)
    shutouts = db.Column(db.Integer, default=0, nullable=False)
    goals_allowed = db.Column(db.Integer, default=0, nullable=False)
    
    season_year = db.Column(db.Integer, nullable=True)  # for seasonal stats
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Multi-tenant foreign keys
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False, index=True)
    
    # Unique constraint for player per season per tenant
    __table_args__ = (db.UniqueConstraint('player_id', 'season_year', 'tenant_id', name='unique_player_season_stats'),)
    
    @property
    def points(self):
        """Calculate total points (goals + assists)."""
        return self.goals + self.assists
    
    @property
    def goals_per_game(self):
        """Calculate goals per game."""
        if self.games_played == 0:
            return 0.0
        return round(self.goals / self.games_played, 2)
    
    @property
    def assists_per_game(self):
        """Calculate assists per game."""
        if self.games_played == 0:
            return 0.0
        return round(self.assists / self.games_played, 2)
    
    @property
    def goals_against_average(self):
        """Calculate goals against average for goaltenders."""
        if self.games_as_goaltender == 0:
            return 0.0
        return round(self.goals_allowed / self.games_as_goaltender, 2)
    
    def __repr__(self):
        return f'<PlayerStatistic Player {self.player_id} Season {self.season_year}>'
    
    def to_dict(self):
        """Convert player statistics to dictionary."""
        return {
            'id': self.id,
            'games_played': self.games_played,
            'goals': self.goals,
            'assists': self.assists,
            'points': self.points,
            'penalties': self.penalties,
            'penalty_minutes': self.penalty_minutes,
            'games_as_goaltender': self.games_as_goaltender,
            'wins': self.wins,
            'losses': self.losses,
            'shutouts': self.shutouts,
            'goals_allowed': self.goals_allowed,
            'goals_per_game': self.goals_per_game,
            'assists_per_game': self.assists_per_game,
            'goals_against_average': self.goals_against_average,
            'season_year': self.season_year,
            'last_updated': self.last_updated.isoformat(),
            'tenant_id': self.tenant_id,
            'player_id': self.player_id
        }

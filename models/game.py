"""
Game scheduling and management models.
"""
from datetime import datetime
from app import db
from utils.base_model import TenantMixin
from utils.tenant_isolation import enforce_tenant_isolation

@enforce_tenant_isolation
class Game(TenantMixin, db.Model):
    """Game model for scheduling pickup games."""
    
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    time = db.Column(db.Time, nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='scheduled', nullable=False)  # 'scheduled', 'confirmed', 'cancelled', 'completed'
    
    # Player requirements
    goaltenders_needed = db.Column(db.Integer, default=2, nullable=False)
    defence_needed = db.Column(db.Integer, default=4, nullable=True)  # null for 2-position mode
    forwards_needed = db.Column(db.Integer, default=6, nullable=True)  # null for 2-position mode
    skaters_needed = db.Column(db.Integer, default=10, nullable=True)  # for 2-position mode
    
    # Team assignments
    team_1_name = db.Column(db.String(50), nullable=True)
    team_2_name = db.Column(db.String(50), nullable=True)
    team_1_color = db.Column(db.String(20), nullable=True)
    team_2_color = db.Column(db.String(20), nullable=True)
    
    # Recurring game template
    is_recurring = db.Column(db.Boolean, default=False, nullable=False)
    recurrence_pattern = db.Column(db.String(50), nullable=True)  # 'weekly', 'biweekly', 'monthly'
    recurrence_end_date = db.Column(db.Date, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # tenant_id is inherited from TenantMixin
    
    # Relationships
    invitations = db.relationship('Invitation', back_populates='game', lazy=True, cascade='all, delete-orphan')
    statistics = db.relationship('GameStatistic', backref='game', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='game', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Game {self.date} at {self.time}>'
    
    def to_dict(self):
        """Convert game to dictionary."""
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'time': self.time.isoformat(),
            'venue': self.venue,
            'status': self.status,
            'goaltenders_needed': self.goaltenders_needed,
            'defence_needed': self.defence_needed,
            'forwards_needed': self.forwards_needed,
            'skaters_needed': self.skaters_needed,
            'team_1_name': self.team_1_name,
            'team_2_name': self.team_2_name,
            'team_1_color': self.team_1_color,
            'team_2_color': self.team_2_color,
            'is_recurring': self.is_recurring,
            'recurrence_pattern': self.recurrence_pattern,
            'recurrence_end_date': self.recurrence_end_date.isoformat() if self.recurrence_end_date else None,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

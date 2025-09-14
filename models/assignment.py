"""
Assignment management models.
"""
from datetime import datetime
from app import db

class Assignment(db.Model):
    """Assignment model for game logistics tasks."""
    
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_description = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='assigned', nullable=False)  # 'assigned', 'completed', 'cancelled'
    assignment_type = db.Column(db.String(20), default='manual', nullable=False)  # 'manual', 'automatic'
    notes = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Multi-tenant foreign keys
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False, index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False, index=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False, index=True)
    
    def __repr__(self):
        return f'<Assignment {self.task_description} for Player {self.player_id}>'
    
    def to_dict(self):
        """Convert assignment to dictionary."""
        return {
            'id': self.id,
            'task_description': self.task_description,
            'status': self.status,
            'assignment_type': self.assignment_type,
            'notes': self.notes,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tenant_id': self.tenant_id,
            'game_id': self.game_id,
            'player_id': self.player_id
        }

"""
Service for automatic team assignment with skill balancing.
"""
from flask import current_app
from models.player import Player, POSITION_GOALTENDER
from models.assignment import Assignment
from models.game import Game
from app import db

class TeamAssignmentService:
    """Service for balancing team assignments based on skill and position."""
    
    # Skill rating weights
    GOALIE_WEIGHT = 5
    SKATER_WEIGHT = 1
    DEFAULT_RATING = 2  # For unrated players
    
    @staticmethod
    def calculate_player_score(player):
        """Calculate weighted score for a player."""
        rating = player.skill_rating if player.skill_rating else TeamAssignmentService.DEFAULT_RATING
        weight = TeamAssignmentService.GOALIE_WEIGHT if player.is_goaltender else TeamAssignmentService.SKATER_WEIGHT
        return rating * weight
    
    @staticmethod
    def auto_assign_teams(game_id, player_ids):
        """
        Automatically assign players to teams with balanced skill and positions.
        
        Args:
            game_id: Game ID
            player_ids: List of player IDs to assign
            
        Returns:
            dict: Assignment results with team compositions
        """
        try:
            game = Game.query.get(game_id)
            if not game:
                return {'error': 'Game not found'}
            
            # Get players
            players = Player.query.filter(Player.id.in_(player_ids)).all()
            if not players:
                return {'error': 'No players found'}
            
            # Separate by position
            goalies = [p for p in players if p.is_goaltender]
            skaters = [p for p in players if not p.is_goaltender]
            
            # Sort by skill rating (highest first)
            goalies.sort(key=lambda p: p.skill_rating or TeamAssignmentService.DEFAULT_RATING, reverse=True)
            skaters.sort(key=lambda p: p.skill_rating or TeamAssignmentService.DEFAULT_RATING, reverse=True)
            
            # Initialize teams
            team_1 = []
            team_2 = []
            team_1_score = 0
            team_2_score = 0
            
            # Assign goalies first (alternating)
            for i, goalie in enumerate(goalies):
                score = TeamAssignmentService.calculate_player_score(goalie)
                if i % 2 == 0:
                    team_1.append(goalie)
                    team_1_score += score
                else:
                    team_2.append(goalie)
                    team_2_score += score
            
            # Assign skaters using greedy algorithm (balance total score)
            for skater in skaters:
                score = TeamAssignmentService.calculate_player_score(skater)
                if team_1_score <= team_2_score:
                    team_1.append(skater)
                    team_1_score += score
                else:
                    team_2.append(skater)
                    team_2_score += score
            
            # Delete existing assignments for this game
            Assignment.query.filter_by(game_id=game_id).delete()
            
            # Create new assignments
            for player in team_1:
                assignment = Assignment(
                    game_id=game_id,
                    player_id=player.id,
                    team_number=1,
                    tenant_id=game.tenant_id
                )
                db.session.add(assignment)
            
            for player in team_2:
                assignment = Assignment(
                    game_id=game_id,
                    player_id=player.id,
                    team_number=2,
                    tenant_id=game.tenant_id
                )
                db.session.add(assignment)
            
            db.session.commit()
            
            return {
                'success': True,
                'team_1': {
                    'players': [p.to_dict() for p in team_1],
                    'total_score': team_1_score,
                    'count': len(team_1)
                },
                'team_2': {
                    'players': [p.to_dict() for p in team_2],
                    'total_score': team_2_score,
                    'count': len(team_2)
                },
                'balance_difference': abs(team_1_score - team_2_score)
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error in auto_assign_teams: {e}")
            return {'error': str(e)}
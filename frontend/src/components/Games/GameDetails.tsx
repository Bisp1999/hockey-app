import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { gameService, Game } from '../../services/gameService';
import { assignmentService, GameAssignments, PlayerAssignment } from '../../services/assignmentService';
import { useTenant } from '../../contexts/TenantContext';
import './GameDetails.css';

const GameDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { tenant } = useTenant();
  const [game, setGame] = useState<Game | null>(null);
  const [assignments, setAssignments] = useState<GameAssignments | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draggedPlayer, setDraggedPlayer] = useState<PlayerAssignment | null>(null);
  const [sendingInvitations, setSendingInvitations] = useState(false);
const [invitationMessage, setInvitationMessage] = useState<string | null>(null);

  useEffect(() => {
    loadGameData();
  }, [id]);

  const loadGameData = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      const [gameData, assignmentsData] = await Promise.all([
        gameService.getGame(parseInt(id)),
        assignmentService.getGameAssignments(parseInt(id))
      ]);
      setGame(gameData);
      setAssignments(assignmentsData);
    } catch (err: any) {
      setError('Failed to load game details');
    } finally {
      setLoading(false);
    }
  };

  const handleSendInvitations = async () => {
    if (!id) return;
    
    try {
      setSendingInvitations(true);
      setInvitationMessage(null);
      const result = await gameService.sendInvitations(parseInt(id));
      setInvitationMessage(`✅ ${result.invitations.sent} invitations sent successfully!`);
    } catch (err: any) {
      setInvitationMessage(`❌ Failed to send invitations: ${err.response?.data?.error || 'Unknown error'}`);
    } finally {
      setSendingInvitations(false);
    }
  };

  const handleDragStart = (player: PlayerAssignment) => {
    setDraggedPlayer(player);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = async (targetTeam: number) => {
    if (!draggedPlayer || !id) return;

    try {
      await assignmentService.movePlayer(parseInt(id), draggedPlayer.id, targetTeam);
      await loadGameData(); // Reload to show updated teams
      setDraggedPlayer(null);
    } catch (err) {
      alert('Failed to move player');
    }
  };

  const formatDate = (dateStr: string) => {
    // Parse as local date to avoid timezone issues
    const [year, month, day] = dateStr.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getStatusBadge = (status: string) => {
    const badges: { [key: string]: string } = {
      scheduled: 'badge-scheduled',
      confirmed: 'badge-confirmed',
      cancelled: 'badge-cancelled',
      completed: 'badge-completed'
    };
    return badges[status] || 'badge-scheduled';
  };

  const renderPlayerCard = (player: PlayerAssignment) => (
    <div
      key={player.id}
      className="player-card"
      draggable
      onDragStart={() => handleDragStart(player)}
    >
      <div className="player-info">
        <span className="player-name">{player.first_name} {player.last_name}</span>
        <span className="player-position">{player.position}</span>
      </div>
      {player.skill_rating && (
        <span className="player-rating">⭐ {player.skill_rating}</span>
      )}
    </div>
  );

  if (loading) {
    return <div className="loading">Loading game details...</div>;
  }

  if (error || !game) {
    return (
      <div className="game-details-container">
        <div className="error-message">{error || 'Game not found'}</div>
        <button className="btn btn-secondary" onClick={() => navigate('/games')}>
          Back to Games
        </button>
      </div>
    );
  }

  return (
    <div className="game-details-container">
      <div className="game-details-header">
        <button className="btn btn-secondary" onClick={() => navigate('/games')}>
          ← Back to Games
        </button>
        <h1>Game Details</h1>
      </div>

      <div className="game-info-card">
        <div className="game-info-header">
          <h2>{formatDate(game.date)}</h2>
          <span className={`status-badge ${getStatusBadge(game.status)}`}>
            {game.status.toUpperCase()}
          </span>
        </div>

        <div className="game-info-grid">
          <div className="info-item">
            <span className="info-label">Time</span>
            <span className="info-value">{game.time}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Venue</span>
            <span className="info-value">{game.venue}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Goaltenders Needed</span>
            <span className="info-value">{game.goaltenders_needed}</span>
          </div>
          {tenant?.position_mode === 'three_position' ? (
            <>
              <div className="info-item">
                <span className="info-label">Defence Needed</span>
                <span className="info-value">{game.defence_needed || 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Forwards Needed</span>
                <span className="info-value">{game.forwards_needed || 'N/A'}</span>
              </div>
            </>
          ) : (
            <div className="info-item">
              <span className="info-label">Skaters Needed</span>
              <span className="info-value">{game.skaters_needed || 'N/A'}</span>
            </div>
          )}
        </div>
      </div>

      <div className="game-actions">
          <button 
            className="btn btn-primary"
            onClick={handleSendInvitations}
            disabled={sendingInvitations}
          >
            {sendingInvitations ? 'Sending...' : '📧 Send Invitations'}
          </button>
          {invitationMessage && (
            <div className={`invitation-message ${invitationMessage.includes('✅') ? 'success' : 'error'}`}>
              {invitationMessage}
            </div>
          )}
      </div>

      {assignments && (
        <>
          <div className="balance-info">
            <div className="balance-score">
              Balance Difference: <strong>{assignments.balance_difference?.toFixed(1) ?? 'N/A'}</strong>
            </div>
          </div>

          <div className="teams-section">
            <div 
              className="team-card"
              onDragOver={handleDragOver}
              onDrop={() => handleDrop(1)}
            >
              <div className="team-header" style={{ borderColor: game.team_1_color }}>
                <h3>{game.team_1_name}</h3>
                <span className="team-color-badge" style={{ backgroundColor: game.team_1_color }}></span>
              </div>
              <div className="team-stats">
                <span>Players: {assignments.team_1?.count ?? assignments.team_1?.players.length ?? 0}</span>
                <span>Score: {assignments.team_1?.total_score.toFixed(1) ?? 'N/A'}</span>
              </div>
              <div className="team-roster">
                {assignments.team_1?.players.length > 0 ? (
                  assignments.team_1?.players.map(renderPlayerCard)
                ) : (
                  <p className="empty-roster">No players assigned yet</p>
                )}
              </div>
            </div>

            <div 
              className="team-card"
              onDragOver={handleDragOver}
              onDrop={() => handleDrop(2)}
            >
              <div className="team-header" style={{ borderColor: game.team_2_color }}>
                <h3>{game.team_2_name}</h3>
                <span className="team-color-badge" style={{ backgroundColor: game.team_2_color }}></span>
              </div>
              <div className="team-stats">
                <span>Players: {assignments.team_2?.count ?? assignments.team_2?.players.length ?? 0}</span>                
                <span>Score: {assignments.team_2?.total_score?.toFixed(1) ?? 'N/A'}</span>
              </div>
              <div className="team-roster">
                {assignments.team_2?.players.length > 0 ? (
                  assignments.team_2?.players.map(renderPlayerCard)
                ) : (
                  <p className="empty-roster">No players assigned yet</p>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default GameDetails;
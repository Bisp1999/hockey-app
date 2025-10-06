import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { gameService, Game } from '../../services/gameService';
import { useTenant } from '../../contexts/TenantContext';
import './GameDetails.css';

const GameDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { tenant } = useTenant();
  const [game, setGame] = useState<Game | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadGame();
  }, [id]);

  const loadGame = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      const data = await gameService.getGame(parseInt(id));
      setGame(data);
    } catch (err: any) {
      setError('Failed to load game details');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
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

      <div className="teams-section">
        <div className="team-card">
          <div className="team-header" style={{ borderColor: game.team_1_color }}>
            <h3>{game.team_1_name}</h3>
            <span className="team-color-badge" style={{ backgroundColor: game.team_1_color }}></span>
          </div>
          <div className="team-roster">
            <p className="empty-roster">No players assigned yet</p>
            {/* Player assignments will be added in next step */}
          </div>
        </div>

        <div className="team-card">
          <div className="team-header" style={{ borderColor: game.team_2_color }}>
            <h3>{game.team_2_name}</h3>
            <span className="team-color-badge" style={{ backgroundColor: game.team_2_color }}></span>
          </div>
          <div className="team-roster">
            <p className="empty-roster">No players assigned yet</p>
            {/* Player assignments will be added in next step */}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameDetails;
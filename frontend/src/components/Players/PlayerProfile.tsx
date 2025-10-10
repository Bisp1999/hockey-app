import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { playerService } from '../../services/playerService';
import { Player } from '../../types';
import './PlayerProfile.css';
import { apiClient } from '../../utils/api';

interface PlayerProfile extends Player {
  statistics?: {
    games_played: number;
    goals: number;
    assists: number;
    points: number;
    penalty_minutes: number;
    goalie_stats?: {
      games_played: number;
      saves: number;
      goals_against: number;
      save_percentage: number;
    };
  };
  invitations?: {
    total: number;
    accepted: number;
    declined: number;
    pending: number;
    acceptance_rate: number;
  };
  assignments?: {
    total: number;
  };
}

const PlayerProfile: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [player, setPlayer] = useState<PlayerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadPlayerProfile(parseInt(id));
    }
  }, [id]);

  const loadPlayerProfile = async (playerId: number) => {
    try {
      setLoading(true);
      // This endpoint returns comprehensive profile with stats
      const response = await apiClient.get(`/players/${playerId}/profile`);
      const data = response.data;
      setPlayer(data.profile);
      setError(null);
    } catch (err: any) {
      setError('Failed to load player profile');
    } finally {
      setLoading(false);
    }
  };

  const updateEmailPreference = async (field: string, value: boolean) => {
    if (!player) return;

    try {
      const response = await apiClient.put(`/players/${player.id}/email-preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          [field]: value
        })
      });

      if (response.ok) {
        // Update local state
        setPlayer({
          ...player,
          [field]: value
        });
      } else {
        setError('Failed to update email preferences');
      }
    } catch (err) {
      setError('Failed to update email preferences');
    }
  };

  if (loading) {
    return <div className="loading">Loading player profile...</div>;
  }

  if (error || !player) {
    return (
      <div className="error-container">
        <div className="error-message">{error || 'Player not found'}</div>
        <button className="btn btn-primary" onClick={() => navigate('/players')}>
          Back to Players
        </button>
      </div>
    );
  }

  const getPositionLabel = (position: string) => {
    const labels: Record<string, string> = {
      goaltender: 'Goaltender',
      defence: 'Defence',
      forward: 'Forward',
      skater: 'Skater'
    };
    return labels[position] || position;
  };

  return (
    <div className="player-profile">
      <div className="profile-header">
        <button className="back-btn" onClick={() => navigate('/players')}>
          ← Back to Players
        </button>
        <h1>Player Profile</h1>
      </div>

      {/* Player Info Card */}
      <div className="profile-card">
        <div className="profile-photo-section">
          {player.photo_url ? (
            <img src={player.photo_url} alt={player.name} className="profile-photo" />
          ) : (
            <div className="profile-photo-placeholder">
              {player.name.charAt(0)}
            </div>
          )}
        </div>

        {/* Email Preferences Section */}
        <div className="email-preferences-section">
          <h3>Email Preferences</h3>
          <div className="preferences-grid">
            <div className="preference-item">
              <label className="preference-label">
                <input
                  type="checkbox"
                  checked={player.email_invitations}
                  onChange={(e) => updateEmailPreference('email_invitations', e.target.checked)}
                />
                <span>Game Invitations</span>
              </label>
              <p className="preference-description">Receive emails when invited to games</p>
            </div>
            <div className="preference-item">
              <label className="preference-label">
                <input
                  type="checkbox"
                  checked={player.email_reminders}
                  onChange={(e) => updateEmailPreference('email_reminders', e.target.checked)}
                />
                <span>Game Reminders</span>
              </label>
              <p className="preference-description">Receive reminder emails before games</p>
            </div>
            <div className="preference-item">
              <label className="preference-label">
                <input
                  type="checkbox"
                  checked={player.email_notifications}
                  onChange={(e) => updateEmailPreference('email_notifications', e.target.checked)}
                />
                <span>General Notifications</span>
              </label>
              <p className="preference-description">Receive emails about schedule changes and updates</p>
            </div>
          </div>
        </div>

        <div className="profile-info">
          <h2>{player.name}</h2>
          <div className="profile-details">
            <div className="detail-item">
              <span className="detail-label">Email:</span>
              <span className="detail-value">{player.email}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Position:</span>
              <span className="detail-value badge badge-position">
                {getPositionLabel(player.position)}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Type:</span>
              <span className="detail-value badge badge-type">
                {player.player_type === 'spare'
                  ? `Spare (Priority ${player.spare_priority})`
                  : 'Regular'}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Status:</span>
              <span className={`detail-value badge ${player.is_active ? 'badge-active' : 'badge-inactive'}`}>
                {player.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Language:</span>
              <span className="detail-value">{player.language === 'en' ? 'English' : 'Français'}</span>
            </div>
            {player.skill_rating && (
              <div className="detail-item">
                <span className="detail-label">Skill Rating:</span>
                <span className="detail-value badge badge-skill">
                  {player.skill_rating === 1 && 'Developing'}
                  {player.skill_rating === 2 && 'Average'}
                  {player.skill_rating === 3 && 'Strong'}
                  {player.skill_rating === 4 && 'Elite'}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Statistics Section */}
      {player.statistics && (
        <div className="stats-section">
          <h3>Statistics</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{player.statistics.games_played}</div>
              <div className="stat-label">Games Played</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{player.statistics.goals}</div>
              <div className="stat-label">Goals</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{player.statistics.assists}</div>
              <div className="stat-label">Assists</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{player.statistics.points}</div>
              <div className="stat-label">Points</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{player.statistics.penalty_minutes}</div>
              <div className="stat-label">Penalty Minutes</div>
            </div>
          </div>

          {/* Goalie Stats */}
          {player.statistics.goalie_stats && (
            <div className="goalie-stats">
              <h4>Goaltender Statistics</h4>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-value">{player.statistics.goalie_stats.games_played}</div>
                  <div className="stat-label">Games as Goalie</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{player.statistics.goalie_stats.saves}</div>
                  <div className="stat-label">Saves</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{player.statistics.goalie_stats.goals_against}</div>
                  <div className="stat-label">Goals Against</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{player.statistics.goalie_stats.save_percentage.toFixed(1)}%</div>
                  <div className="stat-label">Save %</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Invitations Section */}
      {player.invitations && (
        <div className="invitations-section">
          <h3>Invitation History</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{player.invitations.total}</div>
              <div className="stat-label">Total Invitations</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{player.invitations.accepted}</div>
              <div className="stat-label">Accepted</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{player.invitations.declined}</div>
              <div className="stat-label">Declined</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{player.invitations.pending}</div>
              <div className="stat-label">Pending</div>
            </div>
            <div className="stat-card highlight">
              <div className="stat-value">{player.invitations.acceptance_rate.toFixed(1)}%</div>
              <div className="stat-label">Acceptance Rate</div>
            </div>
          </div>
        </div>
      )}

      {/* Assignments Section */}
      {player.assignments && (
        <div className="assignments-section">
          <h3>Team Assignments</h3>
          <div className="stat-card-large">
            <div className="stat-value">{player.assignments.total}</div>
            <div className="stat-label">Total Assignments</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PlayerProfile;
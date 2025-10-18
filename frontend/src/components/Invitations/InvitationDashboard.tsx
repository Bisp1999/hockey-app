import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../utils/api';
import './InvitationDashboard.css';

interface Game {
  id: number;
  date: string;
  time: string;
  venue: string;
  status: string;
}

interface Player {
  id: number;
  name: string;
  email: string;
  position: string;
}

interface Invitation {
  id: number;
  status: string;
  response: string | null;
  response_method: string | null;
  response_notes: string | null;
  email_sent_at: string | null;
  email_opened_at: string | null;
  responded_at: string | null;
  reminder_count: number;
  player: Player;
}

interface InvitationSummary {
  sent: number;
  responded: number;
  available: number;
  unavailable: number;
  pending: number;
}

const InvitationDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [games, setGames] = useState<Game[]>([]);
  const [selectedGameId, setSelectedGameId] = useState<number | null>(null);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [summary, setSummary] = useState<InvitationSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [sendingReminder, setSendingReminder] = useState<number | null>(null);

  // Fetch games on mount
  useEffect(() => {
    fetchGames();
  }, []);

  // Fetch invitations when game is selected
  useEffect(() => {
    if (selectedGameId) {
      fetchInvitations(selectedGameId);
    }
  }, [selectedGameId]);

  const fetchGames = async () => {
    try {
      const response = await apiClient.get('/games/');
      setGames(response.data.games || []);
      
      // Auto-select the first upcoming game
      if (response.data.games && response.data.games.length > 0) {
        const upcomingGames = response.data.games.filter((g: Game) => 
          new Date(g.date) >= new Date()
        );
        if (upcomingGames.length > 0) {
          setSelectedGameId(upcomingGames[0].id);
        } else {
          setSelectedGameId(response.data.games[0].id);
        }
      }
    } catch (error) {
      console.error('Error fetching games:', error);
    }
  };

  const fetchInvitations = async (gameId: number) => {
    setLoading(true);
    try {
      const response = await apiClient.get(`/invitations/game/${gameId}`);
      setInvitations(response.data.invitations || []);
      setSummary(response.data.summary || null);
    } catch (error) {
      console.error('Error fetching invitations:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendReminder = async (invitationId: number) => {
    setSendingReminder(invitationId);
    try {
      await apiClient.post(`/invitations/${invitationId}/reminder`);
      // Refresh invitations
      if (selectedGameId) {
        await fetchInvitations(selectedGameId);
      }
      alert('Reminder sent successfully!');
    } catch (error: any) {
      alert(error.response?.data?.error || 'Failed to send reminder');
    } finally {
      setSendingReminder(null);
    }
  };

  const getStatusBadge = (invitation: Invitation) => {
    if (invitation.response === 'available') {
      return <span className="badge badge-success">✅ Available</span>;
    } else if (invitation.response === 'unavailable') {
      return <span className="badge badge-danger">❌ Unavailable</span>;
    } else if (invitation.response === 'tentative') {
      return <span className="badge badge-warning">⚠️ Maybe</span>;
    } else if (invitation.email_opened_at) {
      return <span className="badge badge-info">👁️ Opened</span>;
    } else if (invitation.email_sent_at) {
      return <span className="badge badge-secondary">📧 Sent</span>;
    } else {
      return <span className="badge badge-light">⏳ Pending</span>;
    }
  };

  const selectedGame = games.find(g => g.id === selectedGameId);

  return (
    <div className="invitation-dashboard">
      <div className="dashboard-header">
        <h1>📊 Availability Dashboard</h1>
        
        <div className="game-selector">
          <label htmlFor="game-select">Select Game:</label>
          <select
            id="game-select"
            value={selectedGameId || ''}
            onChange={(e) => setSelectedGameId(Number(e.target.value))}
          >
            <option value="">-- Select a game --</option>
            {games.map(game => {
              // Parse date without timezone conversion
              const [year, month, day] = game.date.split('-').map(Number);
              const dateStr = new Date(year, month - 1, day).toLocaleDateString();
              return (
                <option key={game.id} value={game.id}>
                  {dateStr} - {game.time} - {game.venue}
                </option>
              );
            })}
          </select>
        </div>
      </div>

      {selectedGame && (
        <div className="game-info">
          <h2>🏒 {(() => {
            // Parse date without timezone conversion
            const [year, month, day] = selectedGame.date.split('-').map(Number);
            return new Date(year, month - 1, day).toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            });
          })()}</h2>
          <p><strong>Time:</strong> {selectedGame.time}</p>
          <p><strong>Venue:</strong> {selectedGame.venue}</p>
        </div>
      )}

      {summary && (
        <div className="summary-stats">
          <div className="stat-card">
            <div className="stat-value">{summary.sent}</div>
            <div className="stat-label">Invitations Sent</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{summary.responded}</div>
            <div className="stat-label">Responses</div>
          </div>
          <div className="stat-card success">
            <div className="stat-value">{summary.available}</div>
            <div className="stat-label">Available</div>
          </div>
          <div className="stat-card danger">
            <div className="stat-value">{summary.unavailable}</div>
            <div className="stat-label">Unavailable</div>
          </div>
          <div className="stat-card warning">
            <div className="stat-value">{summary.pending}</div>
            <div className="stat-label">No Response</div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading invitations...</div>
      ) : (
        <div className="invitations-table">
          <table>
            <thead>
              <tr>
                <th>Player</th>
                <th>Position</th>
                <th>Status</th>
                <th>Opened</th>
                <th>Responded</th>
                <th>Notes</th>
                <th>Reminders</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invitations.length === 0 ? (
                <tr>
                  <td colSpan={8} className="no-data">
                    No invitations found for this game
                  </td>
                </tr>
              ) : (
                invitations.map(invitation => (
                  <tr key={invitation.id}>
                    <td>
                      <strong>{invitation.player.name}</strong>
                      <br />
                      <small>{invitation.player.email}</small>
                    </td>
                    <td>{invitation.player.position}</td>
                    <td>{getStatusBadge(invitation)}</td>
                    <td>
                      {invitation.email_opened_at ? (
                        <span className="text-success">✓</span>
                      ) : (
                        <span className="text-muted">-</span>
                      )}
                    </td>
                    <td>
                      {invitation.responded_at ? (
                        new Date(invitation.responded_at).toLocaleDateString()
                      ) : (
                        <span className="text-muted">-</span>
                      )}
                    </td>
                    <td>
                      {invitation.response_notes ? (
                        <span className="notes-preview" title={invitation.response_notes}>
                          {invitation.response_notes.substring(0, 30)}
                          {invitation.response_notes.length > 30 ? '...' : ''}
                        </span>
                      ) : (
                        <span className="text-muted">-</span>
                      )}
                    </td>
                    <td className="text-center">{invitation.reminder_count}</td>
                    <td>
                      {!invitation.response && (
                        <button
                          className="btn-reminder"
                          onClick={() => sendReminder(invitation.id)}
                          disabled={sendingReminder === invitation.id}
                        >
                          {sendingReminder === invitation.id ? '⏳' : '🔔'} Remind
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default InvitationDashboard;

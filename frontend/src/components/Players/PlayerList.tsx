import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { playerService } from '../../services/playerService';
import { Player } from '../../types';
import PlayerForm from './PlayerForm';
import './PlayerList.css';
import { useNavigate } from 'react-router-dom';

// Helper to get full photo URL
const getPhotoUrl = (photoUrl: string | null | undefined) => {
  if (!photoUrl) return null;
  if (photoUrl.startsWith('http')) return photoUrl;
  const apiUrl = process.env.REACT_APP_API_URL?.replace('/api', '') || '';
  return `${apiUrl}${photoUrl}`;
};

const PlayerList: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);  // ADD THIS LINE
  const [showForm, setShowForm] = useState(false);
  const [editingPlayer, setEditingPlayer] = useState<Player | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    position: '',
    player_type: '',
    spare_priority: '',
    is_active: 'true'
  });

  // Helper to get the combined type filter value for the dropdown
  const getTypeFilterValue = () => {
    if (filters.player_type === 'spare' && filters.spare_priority === '1') {
      return 'spare_priority_1';
    }
    if (filters.player_type === 'spare' && filters.spare_priority === '2') {
      return 'spare_priority_2';
    }
    if (filters.player_type === 'spare' && !filters.spare_priority) {
      return 'spare';
    }
    return filters.player_type;
  };

  useEffect(() => {
    loadPlayers();
  }, [searchTerm, filters]);

  const loadPlayers = async () => {
    try {
      setLoading(true);
      const data = await playerService.getPlayers({
        search: searchTerm || undefined,
        ...filters
      });
      setPlayers(data.players);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load players');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingPlayer(null);
    setShowForm(true);
  };

  const handleEdit = (player: Player) => {
    setEditingPlayer(player);
    setShowForm(true);
  };

  const handleDelete = async (player: Player) => {
    if (!window.confirm(`Are you sure you want to delete ${player.name}?`)) {
      return;
    }

    try {
      await playerService.deletePlayer(player.id);
      setSuccess(`${player.name} deleted successfully`);  // ADD THIS
      setTimeout(() => setSuccess(null), 3000);  // ADD THIS
      loadPlayers();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to delete player');
    }
  };

  const handleFormClose = (successMessage?: string) => {
    setShowForm(false);
    setEditingPlayer(null);
    loadPlayers();

    // Show success message if provided
    if (successMessage) {
      setSuccess(successMessage);
      // Auto-hide after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    }
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setFilters({
      position: '',
      player_type: '',
      spare_priority: '',
      is_active: 'true'
    });
  };

  const getPositionBadge = (position: string) => {
    const badges: Record<string, string> = {
      goaltender: '🥅 G',
      defence: '🛡️ D',
      forward: '⚡ F',
      skater: '⛸️ S'
    };
    return badges[position] || position;
  };

  const getTypeBadge = (player: Player) => {
    if (player.player_type === 'spare') {
      return `🔄 Spare (P${player.spare_priority})`;
    }
    return '⭐ Regular';
  };

  if (loading && players.length === 0) {
    return <div className="loading">Loading players...</div>;
  }

  return (
    <div className="player-list">
      <div className="player-list-header">
        <h1>{t('players.title', 'Players')}</h1>
        <button className="btn btn-primary" onClick={handleCreate}>
          + Add Player
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}  {/* ADD THIS LINE */}

      {/* Search and Filters */}
      <div className="player-filters">
        <input
          type="text"
          placeholder="Search by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />

        <select
          value={filters.position}
          onChange={(e) => setFilters({ ...filters, position: e.target.value })}
          className="filter-select"
        >
          <option value="">All Positions</option>
          <option value="goaltender">Goaltender</option>
          <option value="defence">Defence</option>
          <option value="forward">Forward</option>
          <option value="skater">Skater</option>
        </select>

        <select
          value={getTypeFilterValue()}
          onChange={(e) => {
            const value = e.target.value;
            // Handle combined type+priority filter
            if (value === 'spare_priority_1') {
              setFilters({ ...filters, player_type: 'spare', spare_priority: '1' });
            } else if (value === 'spare_priority_2') {
              setFilters({ ...filters, player_type: 'spare', spare_priority: '2' });
            } else if (value === 'spare') {
              setFilters({ ...filters, player_type: 'spare', spare_priority: '' });
            } else if (value === 'regular') {
              setFilters({ ...filters, player_type: 'regular', spare_priority: '' });
            } else {
              setFilters({ ...filters, player_type: '', spare_priority: '' });
            }
          }}
          className="filter-select"
        >
          <option value="">All Types</option>
          <option value="regular">Regular</option>
          <option value="spare">All Spares</option>
          <option value="spare_priority_1">Spare - Priority 1</option>
          <option value="spare_priority_2">Spare - Priority 2</option>
        </select>

        <select
          value={filters.is_active}
          onChange={(e) => setFilters({ ...filters, is_active: e.target.value })}
          className="filter-select"
        >
          <option value="">All Status</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
        </select>
        
        <button 
          className="btn btn-secondary clear-filters-btn" 
          onClick={handleClearFilters}
        >
          Clear Filters
        </button>

      </div>

      {/* Player Table */}
      <div className="player-table-container">
        <table className="player-table">
          <thead>
            <tr>
              <th>Photo</th>
              <th>Name</th>
              <th>Email</th>
              <th>Position</th>
              <th>Type</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {players.length === 0 ? (
              <tr>
                <td colSpan={7} className="no-data">
                  No players found. Click "Add Player" to create one.
                </td>
              </tr>
            ) : (
              players.map((player) => (
                <tr key={player.id}>
                  <td>
                    {player.photo_url ? (
                      <img
                        src={getPhotoUrl(player.photo_url)}
                        alt={player.name}
                        className="player-photo-thumb"
                      />
                    ) : (
                      <div className="player-photo-placeholder">
                        {player.name.charAt(0)}
                      </div>
                    )}
                  </td>
                  <td className="player-name">{player.name}</td>
                  <td>{player.email}</td>
                  <td>
                    <span className="badge badge-position">
                      {getPositionBadge(player.position)}
                    </span>
                  </td>
                  <td>
                    <span className="badge badge-type">
                      {getTypeBadge(player)}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${player.is_active ? 'badge-active' : 'badge-inactive'}`}>
                      {player.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="actions">
                    <button
                      className="btn btn-sm btn-info"
                      onClick={() => navigate(`/players/${player.id}`)}
                    >
                      View
                    </button>
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => handleEdit(player)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn btn-sm btn-danger"
                      onClick={() => handleDelete(player)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="player-count">
        Total: {players.length} player{players.length !== 1 ? 's' : ''}
      </div>

      {/* Player Form Modal */}
      {showForm && (
        <PlayerForm
          player={editingPlayer}
          onClose={handleFormClose}
        />
      )}
    </div>
  );
};

export default PlayerList;

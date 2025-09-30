import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { playerService } from '../../services/playerService';
import { Player } from '../../types';
import PlayerForm from './PlayerForm';
import './PlayerList.css';
import { useNavigate } from 'react-router-dom';



const PlayerList: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingPlayer, setEditingPlayer] = useState<Player | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    position: '',
    player_type: '',
    spare_priority: '',
    is_active: 'true'
  });

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
      loadPlayers();
    } catch (err: any) {
      alert(err.response?.data?.error || 'Failed to delete player');
    }
  };

  const handleFormClose = () => {
    setShowForm(false);
    setEditingPlayer(null);
    loadPlayers();
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
          value={filters.player_type}
          onChange={(e) => setFilters({ ...filters, player_type: e.target.value })}
          className="filter-select"
        >
          <option value="">All Types</option>
          <option value="regular">Regular</option>
          <option value="spare">Spare</option>
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
                        src={player.photo_url}
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

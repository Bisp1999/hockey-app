import React, { useState, useEffect } from 'react';
import { gameService, Game } from '../../services/gameService';
import GameForm from './GameForm';
import './GameList.css';

const GameList: React.FC = () => {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingGame, setEditingGame] = useState<Game | null>(null);
  
  const [filters, setFilters] = useState({
    status: '',
    start_date: '',
    end_date: ''
  });

  useEffect(() => {
    loadGames();
  }, [filters]);

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  const loadGames = async () => {
    try {
      setLoading(true);
      const data = await gameService.getGames(filters);
      setGames(data.games);
    } catch (err: any) {
      setError('Failed to load games');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingGame(null);
    setShowForm(true);
  };

  const handleEdit = (game: Game) => {
    setEditingGame(game);
    setShowForm(true);
  };

  const handleDelete = async (game: Game) => {
    if (!window.confirm(`Are you sure you want to delete the game on ${game.date} at ${game.time}?`)) {
      return;
    }

    try {
      await gameService.deleteGame(game.id);
      setSuccess(`Game on ${game.date} deleted successfully`);
      loadGames();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to delete game');
    }
  };

  const handleFormClose = (successMessage?: string) => {
    setShowForm(false);
    setEditingGame(null);
    loadGames();
    
    if (successMessage) {
      setSuccess(successMessage);
    }
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, string> = {
      scheduled: 'badge-scheduled',
      confirmed: 'badge-confirmed',
      cancelled: 'badge-cancelled',
      completed: 'badge-completed'
    };
    return badges[status] || 'badge-scheduled';
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const formatTime = (timeStr: string) => {
    // timeStr is in format "HH:MM:SS"
    const [hours, minutes] = timeStr.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  if (loading && games.length === 0) {
    return <div className="loading">Loading games...</div>;
  }

  return (
    <div className="game-list">
      <div className="game-list-header">
        <h1>Games</h1>
        <button className="btn btn-primary" onClick={handleCreate}>
          + Schedule Game
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      {/* Filters */}
      <div className="game-filters">
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className="filter-select"
        >
          <option value="">All Status</option>
          <option value="scheduled">Scheduled</option>
          <option value="confirmed">Confirmed</option>
          <option value="cancelled">Cancelled</option>
          <option value="completed">Completed</option>
        </select>

        <input
          type="date"
          value={filters.start_date}
          onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
          className="filter-input"
          placeholder="Start Date"
        />

        <input
          type="date"
          value={filters.end_date}
          onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
          className="filter-input"
          placeholder="End Date"
        />

        <button 
          className="btn btn-secondary" 
          onClick={() => setFilters({ status: '', start_date: '', end_date: '' })}
        >
          Clear Filters
        </button>
      </div>

      {/* Games Table */}
      <div className="table-container">
        <table className="games-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Time</th>
              <th>Venue</th>
              <th>Status</th>
              <th>Players Needed</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {games.length === 0 ? (
              <tr>
                <td colSpan={6} className="no-data">
                  No games scheduled. Click "Schedule Game" to create one.
                </td>
              </tr>
            ) : (
              games.map((game) => (
                <tr key={game.id}>
                  <td>{formatDate(game.date)}</td>
                  <td>{formatTime(game.time)}</td>
                  <td>{game.venue}</td>
                  <td>
                    <span className={`badge ${getStatusBadge(game.status)}`}>
                      {game.status}
                    </span>
                  </td>
                  <td>
                    {game.goaltenders_needed}G
                    {game.defence_needed && `, ${game.defence_needed}D`}
                    {game.forwards_needed && `, ${game.forwards_needed}F`}
                    {game.skaters_needed && `, ${game.skaters_needed}S`}
                  </td>
                  <td className="actions-cell">
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => handleEdit(game)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn btn-sm btn-danger"
                      onClick={() => handleDelete(game)}
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

      {showForm && (
        <GameForm
          game={editingGame}
          onClose={handleFormClose}
        />
      )}
    </div>
  );
};

export default GameList;
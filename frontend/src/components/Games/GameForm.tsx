import React, { useState, useEffect } from 'react';
import { gameService, Game, GameFormData } from '../../services/gameService';
import { useTenant } from '../../contexts/TenantContext';
import './GameForm.css';

interface GameFormProps {
  game: Game | null;
  onClose: (successMessage?: string) => void;
  initialDate?: string; // Add this line
}

const GameForm: React.FC<GameFormProps> = ({ game, onClose, initialDate }) => {
  const { tenant } = useTenant();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<GameFormData>({
    date: game?.date || initialDate || '',
    time: game?.time || '',
    venue: game?.venue || '',
    status: game?.status || 'scheduled',
    goaltenders_needed: game?.goaltenders_needed || tenant?.default_goaltenders || 2,
    defence_needed: game?.defence_needed || tenant?.default_defence,
    forwards_needed: game?.forwards_needed || tenant?.default_forwards,
    skaters_needed: game?.skaters_needed || tenant?.default_skaters,
    team_1_name: game?.team_1_name || tenant?.team_name_1,
    team_2_name: game?.team_2_name || tenant?.team_name_2,
    team_1_color: game?.team_1_color || tenant?.team_color_1,
    team_2_color: game?.team_2_color || tenant?.team_color_2,
    is_recurring: game?.is_recurring || false,
    recurrence_pattern: game?.recurrence_pattern,
    recurrence_end_date: game?.recurrence_end_date
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
  
    try {
      // Validate required fields
      if (!formData.date) {
        setError('Date is required');
        setLoading(false);
        return;
      }
      if (!formData.time) {
        setError('Time is required');
        setLoading(false);
        return;
      }
      if (!formData.venue) {
        setError('Venue is required');
        setLoading(false);
        return;
      }
  
      // Format time to include seconds (HTML time input returns HH:MM)
      let formattedTime = formData.time.trim();
      const timeParts = formattedTime.split(':');
      if (timeParts.length === 2) {
        formattedTime = `${formattedTime}:00`;
      }
  
      // Ensure date is in YYYY-MM-DD format
      const submitData = {
        ...formData,
        date: formData.date,
        time: formattedTime
      };
  
      console.log('Submitting data:', submitData);
      console.log('Time value:', formattedTime);
  
      if (game) {
        await gameService.updateGame(game.id, submitData);
        onClose(`Game on ${formData.date} updated successfully`);
      } else {
        await gameService.createGame(submitData);
        onClose(`Game on ${formData.date} created successfully`);
      }
    } catch (err: any) {
      console.error('Error saving game:', err);
      console.error('Error response:', err.response?.data);
      setError(err.response?.data?.error || 'Failed to save game');
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{game ? 'Edit Game' : 'Create New Game'}</h2>
          <button className="close-btn" onClick={() => onClose()}>×</button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="game-form">
          {/* Date and Time */}
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="date">Date *</label>
              <input
                type="date"
                id="date"
                name="date"
                value={formData.date}
                onChange={handleChange}
                required
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label htmlFor="time">Time *</label>
              <input
                type="time"
                id="time"
                name="time"
                value={formData.time}
                onChange={handleChange}
                required
                className="form-control"
              />
            </div>
          </div>

          {/* Venue */}
          <div className="form-group">
            <label htmlFor="venue">Venue *</label>
            <input
              type="text"
              id="venue"
              name="venue"
              value={formData.venue}
              onChange={handleChange}
              required
              className="form-control"
              placeholder="e.g., Arena Name, Rink 1"
            />
          </div>

          {/* Player Requirements */}
          <h3>Player Requirements</h3>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="goaltenders_needed">Goaltenders</label>
              <input
                type="number"
                id="goaltenders_needed"
                name="goaltenders_needed"
                value={formData.goaltenders_needed}
                onChange={handleChange}
                min="0"
                className="form-control"
              />
            </div>

            {tenant?.position_mode === 'three_position' ? (
              <>
                <div className="form-group">
                  <label htmlFor="defence_needed">Defence</label>
                  <input
                    type="number"
                    id="defence_needed"
                    name="defence_needed"
                    value={formData.defence_needed || ''}
                    onChange={handleChange}
                    min="0"
                    className="form-control"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="forwards_needed">Forwards</label>
                  <input
                    type="number"
                    id="forwards_needed"
                    name="forwards_needed"
                    value={formData.forwards_needed || ''}
                    onChange={handleChange}
                    min="0"
                    className="form-control"
                  />
                </div>
              </>
            ) : (
              <div className="form-group">
                <label htmlFor="skaters_needed">Skaters</label>
                <input
                  type="number"
                  id="skaters_needed"
                  name="skaters_needed"
                  value={formData.skaters_needed || ''}
                  onChange={handleChange}
                  min="0"
                  className="form-control"
                />
              </div>
            )}
          </div>

          {/* Form Actions */}
          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={() => onClose()}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Saving...' : game ? 'Update Game' : 'Create Game'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default GameForm;
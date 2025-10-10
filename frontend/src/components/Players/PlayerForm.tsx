import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { playerService } from '../../services/playerService';
import { Player, PlayerFormData } from '../../types';
import './PlayerForm.css';

interface PlayerFormProps {
  player: Player | null;
  onClose: (successMessage?: string) => void;  // UPDATE THIS LINE
}

const PlayerForm: React.FC<PlayerFormProps> = ({ player, onClose }) => {
  const { t } = useTranslation();

  // Helper to get full photo URL
  const getPhotoUrl = (photoUrl: string | null | undefined) => {
    if (!photoUrl) return null;
    if (photoUrl.startsWith('data:')) return photoUrl;
    // Use localhost for backend (Docker maps to localhost, not myteam.localhost)
    const apiUrl = process.env.REACT_APP_API_URL?.replace('/api', '') || '';
    return `${apiUrl}${photoUrl}`;
  };

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(
    getPhotoUrl(player?.photo_url)
  );

  const [formData, setFormData] = useState<PlayerFormData>({
    name: player?.name || '',
    email: player?.email || '',
    position: player?.position || 'forward',
    player_type: player?.player_type || 'regular',
    spare_priority: player?.spare_priority || undefined,
    language: player?.language || 'en',
    skill_rating: player?.skill_rating || undefined,
    photo: undefined,
    is_active: player?.is_active !== undefined ? player.is_active : true
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: checked
    }));
  };

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
      if (!validTypes.includes(file.type)) {
        setError('Invalid file type. Please upload PNG, JPG, GIF, or WebP');
        return;
      }

      // Validate file size (5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('File too large. Maximum size is 5MB');
        return;
      }

      setFormData(prev => ({ ...prev, photo: file }));

      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
      setError(null);
    }
  };

  const handleRemovePhoto = async () => {
    if (player?.id && player.photo_filename) {
      if (window.confirm('Are you sure you want to remove this photo?')) {
        try {
          await playerService.deletePlayerPhoto(player.id);
          setPhotoPreview(null);
          setFormData(prev => ({ ...prev, photo: undefined }));
        } catch (err: any) {
          setError(err.response?.data?.error || 'Failed to delete photo');
        }
      }
    } else {
      setPhotoPreview(null);
      setFormData(prev => ({ ...prev, photo: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (player) {
        // Update existing player
        await playerService.updatePlayer(player.id, formData);
        onClose(`${formData.name} updated successfully`);  // UPDATE THIS LINE
      } else {
        // Create new player
        await playerService.createPlayer(formData);
        onClose(`${formData.name} created successfully`);  // UPDATE THIS LINE
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to save player');
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={() => onClose()}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{player ? 'Edit Player' : 'Add New Player'}</h2>
          <button className="close-btn" onClick={() => onClose()}>×</button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="player-form">
          {/* Photo Upload */}
          <div className="form-group photo-upload-section">
            <label>Photo</label>
            <div className="photo-upload-container">
              {photoPreview ? (
                <div className="photo-preview">
                  <img src={photoPreview} alt="Preview" />
                  <button
                    type="button"
                    className="remove-photo-btn"
                    onClick={handleRemovePhoto}
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div className="photo-placeholder">
                  <span>No photo</span>
                </div>
              )}
              <input
                type="file"
                accept="image/png,image/jpeg,image/jpg,image/gif,image/webp"
                onChange={handlePhotoChange}
                className="photo-input"
              />
            </div>
          </div>

          {/* Name */}
          <div className="form-group">
            <label htmlFor="name">Name *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="form-control"
            />
          </div>

          {/* Email */}
          <div className="form-group">
            <label htmlFor="email">Email *</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="form-control"
            />
          </div>

          {/* Position */}
          <div className="form-group">
            <label htmlFor="position">Position *</label>
            <select
              id="position"
              name="position"
              value={formData.position}
              onChange={handleChange}
              required
              className="form-control"
            >
              <option value="goaltender">Goaltender</option>
              <option value="defence">Defence</option>
              <option value="forward">Forward</option>
              <option value="skater">Skater</option>
            </select>
          </div>

          {/* Player Type */}
          <div className="form-group">
            <label htmlFor="player_type">Player Type *</label>
            <select
              id="player_type"
              name="player_type"
              value={formData.player_type}
              onChange={handleChange}
              required
              className="form-control"
            >
              <option value="regular">Regular</option>
              <option value="spare">Spare</option>
            </select>
          </div>

          {/* Spare Priority (only show if spare) */}
          {formData.player_type === 'spare' && (
            <div className="form-group">
              <label htmlFor="spare_priority">Spare Priority *</label>
              <select
                id="spare_priority"
                name="spare_priority"
                value={formData.spare_priority || ''}
                onChange={handleChange}
                required
                className="form-control"
              >
                <option value="">Select Priority</option>
                <option value="1">Priority 1</option>
                <option value="2">Priority 2</option>
              </select>
            </div>
          )}

          {/* Language */}
          <div className="form-group">
            <label htmlFor="language">Language</label>
            <select
              id="language"
              name="language"
              value={formData.language}
              onChange={handleChange}
              className="form-control"
            >
              <option value="en">English</option>
              <option value="fr">Français</option>
            </select>
          </div>

          {/* Skill Rating */}
          <div className="form-group">
            <label htmlFor="skill_rating">Skill Rating (Optional)</label>
            <select
              id="skill_rating"
              name="skill_rating"
              value={formData.skill_rating || ''}
              onChange={handleChange}
              className="form-control"
            >
              <option value="">Unrated (Average)</option>
              <option value="1">Developing</option>
              <option value="2">Average</option>
              <option value="3">Strong</option>
              <option value="4">Elite</option>
            </select>
            <small className="form-text">Admin only - used for team balancing</small>
          </div>

          {/* Active Status */}
          <div className="form-group checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active ?? true}
                onChange={handleCheckboxChange}
                className="checkbox-input"
              />
              Active Player
            </label>
          </div>

          {/* Form Actions */}
          <div className="form-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => onClose()}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Saving...' : player ? 'Update Player' : 'Create Player'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PlayerForm;

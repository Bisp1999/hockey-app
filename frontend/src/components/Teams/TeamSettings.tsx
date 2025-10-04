import React, { useState, useEffect } from 'react';
import { teamService, TeamConfig } from '../../services/teamService';
import { useTenant } from '../../contexts/TenantContext';
import './TeamSettings.css';

const TeamSettings: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const { tenant } = useTenant(); 
  
  const [config, setConfig] = useState<TeamConfig>({
    team_name_1: '',
    team_name_2: '',
    team_color_1: '',
    team_color_2: '',
    default_goaltenders: 2,
    default_defence: 4,
    default_forwards: 6,
    default_skaters: 10
  });

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const data = await teamService.getTeamConfig();
      setConfig(data);
    } catch (err: any) {
      setError('Failed to load team configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setConfig(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await teamService.updateTeamConfig(config);
      setSuccess('Team configuration updated successfully!');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update team configuration');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading team settings...</div>;
  }

  return (
    <div className="team-settings">
      <div className="settings-header">
        <h1>Team Configuration</h1>
        <p>Configure your team names and jersey colors</p>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <form onSubmit={handleSubmit} className="team-settings-form">
        <div className="team-section">
          <h2>Team 1</h2>
          <div className="form-group">
            <label htmlFor="team_name_1">Team Name *</label>
            <input
              type="text"
              id="team_name_1"
              name="team_name_1"
              value={config.team_name_1}
              onChange={handleChange}
              required
              className="form-control"
              placeholder="e.g., Blues, Sharks, etc."
            />
          </div>

          <div className="form-group">
            <label htmlFor="team_color_1">Jersey Color *</label>
            <div className="color-input-group">
              <input
                type="text"
                id="team_color_1"
                name="team_color_1"
                value={config.team_color_1}
                onChange={handleChange}
                required
                className="form-control"
                placeholder="e.g., blue, red, white"
              />
              <div 
                className="color-preview" 
                style={{ backgroundColor: config.team_color_1 }}
              />
            </div>
          </div>
        </div>

        <div className="team-section">
          <h2>Team 2</h2>
          <div className="form-group">
            <label htmlFor="team_name_2">Team Name *</label>
            <input
              type="text"
              id="team_name_2"
              name="team_name_2"
              value={config.team_name_2}
              onChange={handleChange}
              required
              className="form-control"
              placeholder="e.g., Reds, Jets, etc."
            />
          </div>

          <div className="form-group">
            <label htmlFor="team_color_2">Jersey Color *</label>
            <div className="color-input-group">
              <input
                type="text"
                id="team_color_2"
                name="team_color_2"
                value={config.team_color_2}
                onChange={handleChange}
                required
                className="form-control"
                placeholder="e.g., red, black, yellow"
              />
              <div 
                className="color-preview" 
                style={{ backgroundColor: config.team_color_2 }}
              />
            </div>
          </div>
        </div>

        <div className="team-section">
          <h2>Default Player Requirements</h2>
          <p className="section-description">
            Set default player requirements for new games. These values will auto-populate when creating a game.
          </p>

          <div className="form-group">
            <label htmlFor="default_goaltenders">Goaltenders *</label>
            <input
              type="number"
              id="default_goaltenders"
              name="default_goaltenders"
              value={config.default_goaltenders}
              onChange={handleChange}
              required
              min="0"
              className="form-control"
            />
          </div>

          {tenant?.position_mode === 'three_position' ? (
            <>
              <div className="form-group">
                <label htmlFor="default_defence">Defence</label>
                <input
                  type="number"
                  id="default_defence"
                  name="default_defence"
                  value={config.default_defence || ''}
                  onChange={handleChange}
                  min="0"
                  className="form-control"
                />
              </div>

              <div className="form-group">
                <label htmlFor="default_forwards">Forwards</label>
                <input
                  type="number"
                  id="default_forwards"
                  name="default_forwards"
                  value={config.default_forwards || ''}
                  onChange={handleChange}
                  min="0"
                  className="form-control"
                />
              </div>
            </>
          ) : (
            <div className="form-group">
              <label htmlFor="default_skaters">Skaters</label>
              <input
                type="number"
                id="default_skaters"
                name="default_skaters"
                value={config.default_skaters || ''}
                onChange={handleChange}
                min="0"
                className="form-control"
              />
            </div>
          )}
        </div>

        <div className="form-actions">
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Team Configuration'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TeamSettings;
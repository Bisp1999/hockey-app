import React, { useState, useEffect } from 'react';
import { teamService, TeamConfig } from '../../services/teamService';
import './TeamSettings.css';

const TeamSettings: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const [config, setConfig] = useState<TeamConfig>({
    team_name_1: '',
    team_name_2: '',
    team_color_1: '',
    team_color_2: ''
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
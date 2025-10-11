import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import './InvitationResponse.css';

interface Invitation {
  id: number;
  status: string;
  response: string | null;
  game_id: number;
  player_id: number;
}

interface Game {
  id: number;
  date: string;
  time: string;
  venue: string;
  team_1_name: string;
  team_2_name: string;
}

const InvitationResponse: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const [searchParams] = useSearchParams();
  const preselectedResponse = searchParams.get('response');
  
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [game, setGame] = useState<Game | null>(null);
  const [selectedResponse, setSelectedResponse] = useState<string>(preselectedResponse || '');
  const [notes, setNotes] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInvitation = async () => {
      try {
        const response = await axios.get(`${process.env.REACT_APP_API_URL}/invitations/respond/${token}`);
        setInvitation(response.data.invitation);
        setGame(response.data.game);
        
        // If already responded, show the existing response
        if (response.data.invitation.response) {
          setSelectedResponse(response.data.invitation.response);
          setNotes(response.data.invitation.response_notes || '');
          setSubmitted(true);
        }
      } catch (err: any) {
        setError(err.response?.data?.error || 'Failed to load invitation');
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchInvitation();
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedResponse) {
      setError('Please select your availability');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await axios.post(`${process.env.REACT_APP_API_URL}/invitations/respond/${token}`, {
        response: selectedResponse,
        notes: notes.trim() || undefined
      });
      
      setSubmitted(true);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to submit response');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="invitation-response-container">
        <div className="loading">Loading invitation...</div>
      </div>
    );
  }

  if (error && !game) {
    return (
      <div className="invitation-response-container">
        <div className="error-card">
          <h2>❌ Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="invitation-response-container">
        <div className="success-card">
          <h2>✅ Response Recorded</h2>
          <p>Thank you! Your response has been recorded.</p>
          
          {game && (
            <div className="game-summary">
              <h3>Game Details</h3>
              <p><strong>Date:</strong> {new Date(game.date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
              <p><strong>Time:</strong> {game.time}</p>
              <p><strong>Venue:</strong> {game.venue}</p>
            </div>
          )}
          
          <div className="response-summary">
            <p><strong>Your Response:</strong> {selectedResponse === 'available' ? '✅ Available' : selectedResponse === 'unavailable' ? '❌ Not Available' : '⚠️ Tentative'}</p>
            {notes && <p><strong>Notes:</strong> {notes}</p>}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="invitation-response-container">
      <div className="invitation-card">
        <div className="header">
          <h1>🏒 Game Invitation</h1>
        </div>

        {game && (
          <div className="game-details">
            <h2>Game Details</h2>
            <div className="detail-row">
              <span className="label">Date:</span>
              <span className="value">{new Date(game.date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
            </div>
            <div className="detail-row">
              <span className="label">Time:</span>
              <span className="value">{game.time}</span>
            </div>
            <div className="detail-row">
              <span className="label">Venue:</span>
              <span className="value">{game.venue}</span>
            </div>
            <div className="detail-row">
              <span className="label">Teams:</span>
              <span className="value">{game.team_1_name} vs {game.team_2_name}</span>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="response-form">
          <h3>Your Availability</h3>
          
          <div className="response-options">
            <button
              type="button"
              className={`response-btn available ${selectedResponse === 'available' ? 'selected' : ''}`}
              onClick={() => setSelectedResponse('available')}
            >
              ✅ Available
            </button>
            
            <button
              type="button"
              className={`response-btn unavailable ${selectedResponse === 'unavailable' ? 'selected' : ''}`}
              onClick={() => setSelectedResponse('unavailable')}
            >
              ❌ Can't Make It
            </button>
            
            <button
              type="button"
              className={`response-btn tentative ${selectedResponse === 'tentative' ? 'selected' : ''}`}
              onClick={() => setSelectedResponse('tentative')}
            >
              ⚠️ Maybe
            </button>
          </div>

          <div className="notes-section">
            <label htmlFor="notes">Notes (optional)</label>
            <textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any comments or notes..."
              rows={3}
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button
            type="submit"
            className="submit-btn"
            disabled={!selectedResponse || submitting}
          >
            {submitting ? 'Submitting...' : 'Submit Response'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default InvitationResponse;
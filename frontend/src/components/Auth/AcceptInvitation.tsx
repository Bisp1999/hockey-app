import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import './AcceptInvitation.css';

interface InvitationDetails {
  email: string;
  tenant_name: string;
  role: string;
}

const AcceptInvitation: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { login } = useAuth();

  const [invitation, setInvitation] = useState<InvitationDetails | null>(null);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const verifyToken = async () => {
      try {
        const response = await apiClient.get(`/invitations/admin/verify/${token}`);
        setInvitation(response.data.invitation);
      } catch (err: any) {
        setError(err.response?.data?.error || 'Invalid or expired invitation link.');
      } finally {
        setLoading(false);
      }
    };
    verifyToken();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    if (password.length < 8) {
        setError('Password must be at least 8 characters long.');
        return;
    }

    setError('');
    setSubmitting(true);

    try {
      const response = await apiClient.post('/invitations/admin/accept', {
        token,
        password,
        first_name: firstName,
        last_name: lastName,
      });
      
      // On success, the backend logs the user in and returns user/tenant data
      login(response.data.user, response.data.tenant);
      navigate('/dashboard');

    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create account. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="accept-invitation-container"><div className="card"><h2>Verifying Invitation...</h2></div></div>;
  }

  if (error && !invitation) {
    return <div className="accept-invitation-container"><div className="card error"><h2>Error</h2><p>{error}</p></div></div>;
  }

  if (!invitation) {
    return null;
  }

  return (
    <div className="accept-invitation-container">
      <div className="card">
        <h2>Join {invitation.tenant_name}</h2>
        <p>Create your account to accept your invitation as a {invitation.role}.</p>
        <p><strong>Email:</strong> {invitation.email}</p>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="firstName">First Name</label>
            <input
              type="text"
              id="firstName"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="lastName">Last Name</label>
            <input
              type="text"
              id="lastName"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="error-message">{error}</p>}
          <button type="submit" disabled={submitting}>
            {submitting ? 'Creating Account...' : 'Create Account and Join'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AcceptInvitation;
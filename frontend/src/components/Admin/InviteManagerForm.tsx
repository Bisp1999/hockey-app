import React, { useState } from 'react';
import { apiClient } from '../../utils/api';

const InviteManagerForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('admin');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setSubmitting(true);

    try {
      const response = await apiClient.post('/admin/invitations', { email, role });
      setMessage(response.data.message);
      setEmail(''); // Clear form on success
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to send invitation.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="invite-form">
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="email">Manager's Email</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="new.manager@example.com"
            required
          />
        </div>
        <div className="form-group">
            <label htmlFor="role">Role</label>
            <select id="role" value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="admin">Admin</option>
                <option value="user">User</option>
                {/* Add other roles as needed */}
            </select>
        </div>
        <button type="submit" disabled={submitting}>
          {submitting ? 'Sending...' : 'Send Invitation'}
        </button>
      </div>
      {message && <p className="success-message">{message}</p>}
      {error && <p className="error-message">{error}</p>}
    </form>
  );
};

export default InviteManagerForm;
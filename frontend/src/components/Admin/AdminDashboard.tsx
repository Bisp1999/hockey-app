import React from 'react';
import InviteManagerForm from './InviteManagerForm';
import './AdminDashboard.css';

const AdminDashboard: React.FC = () => {
  return (
    <div className="admin-dashboard">
      <h1>Admin Dashboard</h1>
      <div className="admin-section">
        <h2>Invite New Manager</h2>
        <p>Invite a new team manager to help you manage your organization.</p>
        <hr />
        <InviteManagerForm />
      </div>
      {/* Future admin sections can be added here */}
    </div>
  );
};

export default AdminDashboard;
import React from 'react';
import { useTranslation } from 'react-i18next';

const Dashboard: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="dashboard">
      <h1>{t('navigation.dashboard')}</h1>
      <div className="dashboard-content">
        <div className="dashboard-card">
          <h3>Recent Games</h3>
          <p>Dashboard content - to be implemented</p>
        </div>
        <div className="dashboard-card">
          <h3>Player Status</h3>
          <p>Dashboard content - to be implemented</p>
        </div>
        <div className="dashboard-card">
          <h3>Upcoming Invitations</h3>
          <p>Dashboard content - to be implemented</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

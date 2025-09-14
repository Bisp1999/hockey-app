import React from 'react';
import { useTranslation } from 'react-i18next';

const InvitationDashboard: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="invitation-dashboard">
      <h1>{t('invitations.title')}</h1>
      <div className="invitation-dashboard-content">
        <p>Availability tracking dashboard - to be implemented</p>
      </div>
    </div>
  );
};

export default InvitationDashboard;

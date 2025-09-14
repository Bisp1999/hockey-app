import React from 'react';
import { useTranslation } from 'react-i18next';

const StatsDashboard: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="stats-dashboard">
      <h1>{t('statistics.title')}</h1>
      <div className="stats-dashboard-content">
        <p>Game statistics interface - to be implemented</p>
      </div>
    </div>
  );
};

export default StatsDashboard;

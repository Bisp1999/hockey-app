import React from 'react';
import { useTranslation } from 'react-i18next';

const TeamConfig: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="team-config">
      <h1>{t('teams.title')}</h1>
      <div className="team-config-content">
        <p>Team configuration interface - to be implemented</p>
      </div>
    </div>
  );
};

export default TeamConfig;

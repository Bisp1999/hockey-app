import React from 'react';
import { useTranslation } from 'react-i18next';

const PlayerList: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="player-list">
      <h1>{t('players.title')}</h1>
      <div className="player-list-content">
        <p>Player management interface - to be implemented</p>
      </div>
    </div>
  );
};

export default PlayerList;

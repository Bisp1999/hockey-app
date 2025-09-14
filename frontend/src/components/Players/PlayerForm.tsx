import React from 'react';
import { useTranslation } from 'react-i18next';

const PlayerForm: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="player-form">
      <h2>{t('players.addPlayer')}</h2>
      <div className="player-form-content">
        <p>Add/edit player form - to be implemented</p>
      </div>
    </div>
  );
};

export default PlayerForm;

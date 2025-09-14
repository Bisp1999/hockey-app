import React from 'react';
import { useTranslation } from 'react-i18next';

const GameForm: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="game-form">
      <h2>{t('games.addGame')}</h2>
      <div className="game-form-content">
        <p>Game creation/editing form - to be implemented</p>
      </div>
    </div>
  );
};

export default GameForm;

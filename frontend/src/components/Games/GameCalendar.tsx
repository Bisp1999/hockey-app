import React from 'react';
import { useTranslation } from 'react-i18next';

const GameCalendar: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="game-calendar">
      <h1>{t('games.title')}</h1>
      <div className="game-calendar-content">
        <p>Game scheduling calendar - to be implemented</p>
      </div>
    </div>
  );
};

export default GameCalendar;

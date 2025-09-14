import React from 'react';
import { useTranslation } from 'react-i18next';

const GameDetails: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="game-details">
      <h2>Game Details</h2>
      <div className="game-details-content">
        <p>Game details and availability view - to be implemented</p>
      </div>
    </div>
  );
};

export default GameDetails;

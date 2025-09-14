import React from 'react';
import { useTranslation } from 'react-i18next';

const StatsEntry: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="stats-entry">
      <h2>Statistics Entry</h2>
      <div className="stats-entry-content">
        <p>Statistics entry form - to be implemented</p>
      </div>
    </div>
  );
};

export default StatsEntry;

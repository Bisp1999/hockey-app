import React from 'react';
import { useTranslation } from 'react-i18next';

const AssignmentManager: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="assignment-manager">
      <h1>{t('assignments.title')}</h1>
      <div className="assignment-manager-content">
        <p>Assignment management interface - to be implemented</p>
      </div>
    </div>
  );
};

export default AssignmentManager;

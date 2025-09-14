import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import { useTenant } from '../../contexts/TenantContext';

const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const { tenant } = useTenant();
  const { t, i18n } = useTranslation();

  const handleLanguageChange = (language: string) => {
    i18n.changeLanguage(language);
  };

  const handleLogout = () => {
    logout();
  };

  return (
    <header className="header">
      <div className="header-left">
        <h1 className="app-title">Hockey Pickup Manager</h1>
        {tenant && <span className="tenant-name">{tenant.name}</span>}
      </div>
      <div className="header-right">
        <div className="language-selector">
          <button
            className={i18n.language === 'en' ? 'active' : ''}
            onClick={() => handleLanguageChange('en')}
          >
            EN
          </button>
          <button
            className={i18n.language === 'fr' ? 'active' : ''}
            onClick={() => handleLanguageChange('fr')}
          >
            FR
          </button>
        </div>
        {user && (
          <div className="user-menu">
            <span className="user-email">{user.email}</span>
            <button onClick={handleLogout} className="logout-button">
              {t('auth.logout')}
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;

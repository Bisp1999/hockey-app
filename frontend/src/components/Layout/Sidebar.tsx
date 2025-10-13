import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';

const Sidebar: React.FC = () => {
    const { t } = useTranslation();
  const { user } = useAuth();

  const navItems = [
    { path: '/dashboard', key: 'dashboard' },
    { path: '/players', key: 'players' },
    { path: '/games', key: 'games' },
    { path: '/invitations', key: 'invitations' },
    { path: '/statistics', key: 'statistics' },
    { path: '/assignments', key: 'assignments' },
    { path: '/teams', key: 'teams' },
    { path: '/admin', key: 'admin', roles: ['super_admin'] },
  ];

  return (
    <nav className="sidebar">
      <ul className="nav-list">
        {navItems
          .filter(item => !item.roles || (user && item.roles.includes(user.role)))
          .map((item) => (
          <li key={item.key} className="nav-item">
            <NavLink
              to={item.path}
              className={({ isActive }) =>
                isActive ? 'nav-link active' : 'nav-link'
              }
            >
              {t(`navigation.${item.key}`)}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Sidebar;

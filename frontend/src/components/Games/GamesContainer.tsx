import React, { useState } from 'react';
import GameList from './GameList';
import GameCalendar from './GameCalendar';
import './GamesContainer.css';

const GamesContainer: React.FC = () => {
  const [view, setView] = useState<'list' | 'calendar'>('calendar');

  return (
    <div className="games-container">
      <div className="view-toggle">
        <button
          className={`toggle-btn ${view === 'calendar' ? 'active' : ''}`}
          onClick={() => setView('calendar')}
        >
          📅 Calendar View
        </button>
        <button
          className={`toggle-btn ${view === 'list' ? 'active' : ''}`}
          onClick={() => setView('list')}
        >
          📋 List View
        </button>
      </div>

      {view === 'calendar' ? <GameCalendar /> : <GameList />}
    </div>
  );
};

export default GamesContainer;
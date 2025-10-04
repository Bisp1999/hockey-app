import React, { useState, useEffect, useCallback } from 'react';
import { Calendar, dateFnsLocalizer, View } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import { enUS } from 'date-fns/locale';
import { gameService, Game } from '../../services/gameService';
import GameForm from './GameForm';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import './GameCalendar.css';

const locales = {
  'en-US': enUS,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

interface CalendarEvent {
  id: number;
  title: string;
  start: Date;
  end: Date;
  resource: Game;
}

const GameCalendar: React.FC = () => {
  const [games, setGames] = useState<Game[]>([]);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingGame, setEditingGame] = useState<Game | null>(null);
  const [selectedDate, setSelectedDate] = useState<string | undefined>(undefined);
  const [view, setView] = useState<View>('month');
  const [date, setDate] = useState(new Date());

  useEffect(() => {
    loadGames();
  }, []);

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  const loadGames = async () => {
    try {
      setLoading(true);
      const data = await gameService.getGames();
      setGames(data.games);
      
      // Convert games to calendar events
      const calendarEvents: CalendarEvent[] = data.games.map(game => {
        // Parse date as local date (not UTC)
        const [year, month, day] = game.date.split('-').map(Number);
        const gameDate = new Date(year, month - 1, day); // month is 0-indexed
        
        const [hours, minutes] = game.time.split(':');
        const startTime = new Date(gameDate);
        startTime.setHours(parseInt(hours), parseInt(minutes), 0);
        
        // Assume 1.5 hour duration
        const endTime = new Date(startTime);
        endTime.setHours(endTime.getHours() + 1, endTime.getMinutes() + 30);
        
        return {
          id: game.id,
          title: `${game.venue} - ${game.status}`,
          start: startTime,
          end: endTime,
          resource: game
        };
      });
      
      setEvents(calendarEvents);
    } catch (err: any) {
      setError('Failed to load games');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSlot = useCallback(({ start }: { start: Date }) => {
    const dateStr = format(start, 'yyyy-MM-dd');
    setSelectedDate(dateStr);
    setEditingGame(null);
    setShowForm(true);
  }, []);

  const handleSelectEvent = useCallback((event: CalendarEvent) => {
    setSelectedDate(undefined);
    setEditingGame(event.resource);
    setShowForm(true);
  }, []);

  const handleFormClose = (successMessage?: string) => {
    setShowForm(false);
    setEditingGame(null);
    setSelectedDate(undefined);
    loadGames();
    
    if (successMessage) {
      setSuccess(successMessage);
    }
  };

  const eventStyleGetter = (event: CalendarEvent) => {
    const game = event.resource;
    let backgroundColor = '#3174ad';
    
    switch (game.status) {
      case 'scheduled':
        backgroundColor = '#3174ad';
        break;
      case 'confirmed':
        backgroundColor = '#28a745';
        break;
      case 'cancelled':
        backgroundColor = '#dc3545';
        break;
      case 'completed':
        backgroundColor = '#6c757d';
        break;
    }
    
    return {
      style: {
        backgroundColor,
        borderRadius: '5px',
        opacity: 0.8,
        color: 'white',
        border: '0px',
        display: 'block'
      }
    };
  };

  if (loading && games.length === 0) {
    return <div className="loading">Loading calendar...</div>;
  }

  return (
    <div className="game-calendar-container">
      <div className="calendar-header">
        <h1>Game Schedule</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          + Schedule Game
        </button>
      </div>
      
      <p className="calendar-instruction">Click on a date to create a new game</p>
  
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div className="calendar-wrapper">
        <Calendar
          localizer={localizer}
          events={events}
          startAccessor="start"
          endAccessor="end"
          style={{ height: 700 }}
          onSelectSlot={handleSelectSlot}
          onSelectEvent={handleSelectEvent}
          selectable
          view={view}
          onView={setView}
          date={date}
          onNavigate={setDate}
          eventPropGetter={eventStyleGetter}
          popup
        />
      </div>

      {showForm && (
        <GameForm
          game={editingGame}
          onClose={handleFormClose}
          initialDate={selectedDate}
        />
      )}
    </div>
  );
};

export default GameCalendar;

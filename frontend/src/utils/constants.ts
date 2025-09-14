/**
 * Application constants and configuration values.
 */

export const POSITIONS = {
  THREE_POSITION: {
    GOALTENDER: 'goaltender',
    DEFENCE: 'defence',
    FORWARD: 'forward',
  },
  TWO_POSITION: {
    GOALTENDER: 'goaltender',
    SKATER: 'skater',
  },
} as const;

export const PLAYER_TYPES = {
  REGULAR: 'regular',
  SPARE: 'spare',
} as const;

export const SPARE_PRIORITIES = {
  PRIORITY_1: 1,
  PRIORITY_2: 2,
} as const;

export const GAME_STATUS = {
  SCHEDULED: 'scheduled',
  CONFIRMED: 'confirmed',
  CANCELLED: 'cancelled',
  COMPLETED: 'completed',
} as const;

export const INVITATION_STATUS = {
  SENT: 'sent',
  OPENED: 'opened',
  RESPONDED: 'responded',
} as const;

export const INVITATION_RESPONSE = {
  YES: 'yes',
  NO: 'no',
} as const;

export const ASSIGNMENT_STATUS = {
  ASSIGNED: 'assigned',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
} as const;

export const LANGUAGES = {
  ENGLISH: 'en',
  FRENCH: 'fr',
} as const;

export const RECURRENCE_PATTERNS = {
  WEEKLY: 'weekly',
  BIWEEKLY: 'biweekly',
  MONTHLY: 'monthly',
} as const;

export const TEAM_COLORS = [
  'blue',
  'red',
  'green',
  'yellow',
  'orange',
  'purple',
  'black',
  'white',
  'gray',
  'navy',
  'maroon',
  'teal',
] as const;

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    ME: '/auth/me',
  },
  PLAYERS: {
    LIST: '/api/players',
    CREATE: '/api/players',
    GET: (id: number) => `/api/players/${id}`,
    UPDATE: (id: number) => `/api/players/${id}`,
    DELETE: (id: number) => `/api/players/${id}`,
  },
  GAMES: {
    LIST: '/api/games',
    CREATE: '/api/games',
    GET: (id: number) => `/api/games/${id}`,
    UPDATE: (id: number) => `/api/games/${id}`,
    DELETE: (id: number) => `/api/games/${id}`,
  },
  INVITATIONS: {
    LIST: '/api/invitations',
    CREATE: '/api/invitations',
    RESPOND: (id: number) => `/api/invitations/${id}/respond`,
    GAME: (gameId: number) => `/api/invitations/game/${gameId}`,
  },
  STATISTICS: {
    LIST: '/api/statistics',
    GAME: (gameId: number) => `/api/statistics/game/${gameId}`,
    PLAYER: (playerId: number) => `/api/statistics/player/${playerId}`,
    GOALTENDER: '/api/statistics/goaltender',
  },
  ASSIGNMENTS: {
    LIST: '/api/assignments',
    CREATE: '/api/assignments',
    UPDATE: (id: number) => `/api/assignments/${id}`,
    DELETE: (id: number) => `/api/assignments/${id}`,
    GAME: (gameId: number) => `/api/assignments/game/${gameId}`,
  },
} as const;

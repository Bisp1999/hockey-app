/**
 * TypeScript type definitions for the Hockey Pickup Manager application.
 */

export interface Tenant {
  id: number;
  name: string;
  slug: string;
  subdomain?: string;
  is_active: boolean;
  position_mode: 'three_position' | 'two_position';
  team_name_1: string;
  team_name_2: string;
  team_color_1: string;
  team_color_2: string;
  assignment_mode: 'manual' | 'automatic';
  created_at: string;
  updated_at: string;
}

export interface User {
  id: number;
  email: string;
  is_admin: boolean;
  is_active: boolean;
  language: 'en' | 'fr';
  tenant_id: number;
  created_at: string;
  updated_at: string;
}

export interface Player {
  id: number;
  name: string;
  email: string;
  position: 'goaltender' | 'defence' | 'forward' | 'skater';
  player_type: 'regular' | 'spare';
  spare_priority?: 1 | 2;
  photo_filename?: string;
  photo_url?: string;
  language: 'en' | 'fr';
  is_active: boolean;
  tenant_id: number;
  created_at: string;
  updated_at: string;
}

export interface Team {
  id: number;
  name: string;
  jersey_color: string;
  is_active: boolean;
  tenant_id: number;
  created_at: string;
  updated_at: string;
}

export interface Game {
  id: number;
  date: string;
  time: string;
  venue: string;
  status: 'scheduled' | 'confirmed' | 'cancelled' | 'completed';
  goaltenders_needed: number;
  defence_needed?: number;
  forwards_needed?: number;
  skaters_needed?: number;
  team_1_name?: string;
  team_2_name?: string;
  team_1_color?: string;
  team_2_color?: string;
  is_recurring: boolean;
  recurrence_pattern?: 'weekly' | 'biweekly' | 'monthly';
  recurrence_end_date?: string;
  tenant_id: number;
  created_at: string;
  updated_at: string;
}

export interface Invitation {
  id: number;
  invitation_type: 'regular' | 'spare';
  status: 'sent' | 'opened' | 'responded';
  sent_at: string;
  opened_at?: string;
  responded_at?: string;
  tenant_id: number;
  game_id: number;
  player_id: number;
  player?: Player;
  game?: Game;
}

export interface InvitationResponse {
  id: number;
  response: 'yes' | 'no';
  response_method: 'email' | 'web';
  notes?: string;
  created_at: string;
  tenant_id: number;
  invitation_id: number;
}

export interface GameStatistic {
  id: number;
  statistic_type: 'goal' | 'assist' | 'penalty';
  period?: number;
  time_in_period?: string;
  penalty_type?: string;
  penalty_duration?: number;
  team_number?: number;
  notes?: string;
  created_at: string;
  tenant_id: number;
  game_id: number;
  player_id: number;
  goal_id?: number;
  player?: Player;
  game?: Game;
}

export interface PlayerStatistic {
  id: number;
  games_played: number;
  goals: number;
  assists: number;
  points: number;
  penalties: number;
  penalty_minutes: number;
  games_as_goaltender: number;
  wins: number;
  losses: number;
  shutouts: number;
  goals_allowed: number;
  goals_per_game: number;
  assists_per_game: number;
  goals_against_average: number;
  season_year?: number;
  last_updated: string;
  tenant_id: number;
  player_id: number;
  player?: Player;
}

export interface Assignment {
  id: number;
  task_description: string;
  status: 'assigned' | 'completed' | 'cancelled';
  assignment_type: 'manual' | 'automatic';
  notes?: string;
  due_date?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  tenant_id: number;
  game_id: number;
  player_id: number;
  player?: Player;
  game?: Game;
}

export interface AuthContextType {
  user: User | null;
  tenant: Tenant | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
}

export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

export interface GameFormData {
  date: string;
  time: string;
  venue: string;
  goaltenders_needed: number;
  defence_needed?: number;
  forwards_needed?: number;
  skaters_needed?: number;
  team_1_name?: string;
  team_2_name?: string;
  team_1_color?: string;
  team_2_color?: string;
  is_recurring: boolean;
  recurrence_pattern?: 'weekly' | 'biweekly' | 'monthly';
  recurrence_end_date?: string;
}

export interface PlayerFormData {
  name: string;
  email: string;
  position: 'goaltender' | 'defence' | 'forward' | 'skater';
  player_type: 'regular' | 'spare';
  spare_priority?: 1 | 2;
  language: 'en' | 'fr';
  photo?: File;
}

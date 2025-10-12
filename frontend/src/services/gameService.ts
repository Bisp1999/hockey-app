import { apiClient } from '../utils/api';

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
  recurrence_pattern?: string;
  recurrence_end_date?: string;
  tenant_id: number;
  invitations_sent_at?: string;
  created_at: string;
  updated_at: string;
}

export interface GameFormData {
  date: string;
  time: string;
  venue: string;
  status?: string;
  goaltenders_needed?: number;
  defence_needed?: number;
  forwards_needed?: number;
  skaters_needed?: number;
  team_1_name?: string;
  team_2_name?: string;
  team_1_color?: string;
  team_2_color?: string;
  is_recurring?: boolean;
  recurrence_pattern?: string;
  recurrence_end_date?: string;
}

export const gameService = {
  // Get all games with optional filters
  async getGames(filters?: {
    start_date?: string;
    end_date?: string;
    status?: string;
  }): Promise<{ games: Game[]; total: number }> {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.status) params.append('status', filters.status);
    
    const paramsString = params.toString();
    const response = await apiClient.get(`/games/${paramsString ? '?' + paramsString : ''}`);
    return response.data;
  },

  // Get single game
  async getGame(id: number): Promise<Game> {
    const response = await apiClient.get(`/games/${id}`);
    return response.data.game;
  },

  // Create game
  async createGame(data: GameFormData): Promise<Game> {
    const response = await apiClient.post('/games/', data);
    return response.data.game;
  },

  // Update game
  async updateGame(id: number, data: Partial<GameFormData>): Promise<Game> {
    const response = await apiClient.put(`/games/${id}`, data);
    return response.data.game;
  },

  // Delete game
  async deleteGame(id: number): Promise<void> {
    await apiClient.delete(`/games/${id}`);
  },

  // Send invitations for a game
  async sendInvitations(id: number): Promise<{ message: string; invitations: { sent: number; failed: number } }> {
    const response = await apiClient.post(`/games/${id}/send-invitations`);
    return response.data;
  },

  // Send reminders for a game
  async sendReminders(id: number): Promise<{ message: string; reminders: { sent: number; failed: number } }> {
    const response = await apiClient.post(`/games/${id}/send-reminders`);
    return response.data;
  }
};
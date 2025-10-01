import { apiClient } from '../utils/api';
import { Player, PlayerFormData } from '../types';

export const playerService = {
  // Get all players with optional filters
  async getPlayers(filters?: {
    search?: string;
    position?: string;
    player_type?: string;
    spare_priority?: string;
    is_active?: string;
    sort_by?: string;
    sort_order?: string;
  }): Promise<{ players: Player[]; total: number; filters: any }> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
    }
    const response = await apiClient.get(`/players?${params.toString()}`);
    return response.data;
  },

  // Get single player
  async getPlayer(id: number): Promise<Player> {
    const response = await apiClient.get(`/players/${id}`);
    return response.data.player;
  },

  // Create player
  async createPlayer(data: PlayerFormData): Promise<Player> {
    const formData = new FormData();
    formData.append('name', data.name);
    formData.append('email', data.email);
    formData.append('position', data.position);
    formData.append('player_type', data.player_type);
    formData.append('language', data.language);
    
    if (data.spare_priority) {
      formData.append('spare_priority', data.spare_priority.toString());
    }
    
    if (data.photo) {
      formData.append('photo', data.photo);
    }

    const response = await apiClient.post(`/players`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data.player;
  },

  // Update player
  async updatePlayer(id: number, data: Partial<PlayerFormData>): Promise<Player> {
    const formData = new FormData();
    
    if (data.name) formData.append('name', data.name);
    if (data.email) formData.append('email', data.email);
    if (data.position) formData.append('position', data.position);
    if (data.player_type) formData.append('player_type', data.player_type);
    if (data.language) formData.append('language', data.language);
    if (data.spare_priority) formData.append('spare_priority', data.spare_priority.toString());
    if (data.photo) formData.append('photo', data.photo);

    const response = await apiClient.put(`/players/${id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data.player;
  },

  // Delete player
  async deletePlayer(id: number): Promise<void> {
    await apiClient.delete(`/players/${id}`);
  },

  // Delete player photo
  async deletePlayerPhoto(id: number): Promise<void> {
    await apiClient.delete(`/players/${id}/photo`);
  }
};
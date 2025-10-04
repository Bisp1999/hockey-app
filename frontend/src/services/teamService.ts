import { apiClient } from '../utils/api';

export interface TeamConfig {
  team_name_1: string;
  team_name_2: string;
  team_color_1: string;
  team_color_2: string;
  default_goaltenders: number;
  default_defence?: number;
  default_forwards?: number;
  default_skaters?: number;
}

export const teamService = {
  // Get team configuration
  async getTeamConfig(): Promise<TeamConfig> {
    const response = await apiClient.get('/teams/config');
    return response.data;
  },

  // Update team configuration
  async updateTeamConfig(config: Partial<TeamConfig>): Promise<TeamConfig> {
    const response = await apiClient.put('/teams/config', config);
    return response.data.config;
  }
};
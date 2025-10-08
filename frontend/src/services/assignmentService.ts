import { api } from '../utils/api';

export interface PlayerAssignment {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  position: string;
  skill_rating: number | null;
  is_goaltender: boolean;
  assignment_id: number;
}

export interface TeamData {
  players: PlayerAssignment[];
  total_score: number;
  count: number;
}

export interface GameAssignments {
  game: any;
  team_1: TeamData;
  team_2: TeamData;
  balance_difference: number;
}

export const assignmentService = {
  async getGameAssignments(gameId: number): Promise<GameAssignments> {
    const response = await api.get<GameAssignments>(`/assignments/game/${gameId}`);
    return response as GameAssignments;
  },

  async autoAssignTeams(gameId: number, playerIds: number[]): Promise<GameAssignments> {
    const response = await api.post<GameAssignments>(`/assignments/game/${gameId}/auto-assign`, {
      player_ids: playerIds
    });
    return response as GameAssignments;
  },

  async movePlayer(gameId: number, playerId: number, teamNumber: number): Promise<any> {
    return await api.put(`/assignments/game/${gameId}/move-player`, {
      player_id: playerId,
      team_number: teamNumber
    });
  },

  async swapPlayers(gameId: number, player1Id: number, player2Id: number): Promise<any> {
    return await api.put(`/assignments/game/${gameId}/swap-players`, {
      player1_id: player1Id,
      player2_id: player2Id
    });
  }
};
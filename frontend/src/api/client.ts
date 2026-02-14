import axios from 'axios';

/**
 * API client configured for the Football Analytics backend
 * Base URL: http://localhost:8000
 */
export const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface PlayerSearchResult {
  id: number;
  name: string;
  position: string;
}

export const searchPlayers = async (query: string): Promise<PlayerSearchResult[]> => {
  const response = await apiClient.get<PlayerSearchResult[]>('/players/search', {
    params: { name: query },
  });
  return response.data;
};

/**
 * Player season stats response from backend
 * Endpoint: GET /players/{id}/stats/season/{season}
 */
export interface PlayerSeasonStats {
  player_id: number;
  season_id: number;
  matches_played: number;
  total_passes: number;
  successful_passes: number;
  pass_completion_rate: number;
  total_xg: number;
  advanced_metrics?: {
    // Raw counts
    passes_attempted?: number;
    passes_completed?: number;
    progressive_passes?: number;
    shot_assists?: number;
    progressive_carries?: number;
    carry_distance?: number;
    shots_total?: number;
    xg_total?: number;
    dribbles_attempted?: number;
    interceptions?: number;
    pressures_applied?: number;
    tackles?: number;
    minutes_played?: number;
    pass_completion_rate?: number;

    // Per-90 normalized metrics
    passes_attempted_p90?: number;
    passes_completed_p90?: number;
    progressive_passes_p90?: number;
    shot_assists_p90?: number;
    progressive_carries_p90?: number;
    carry_distance_p90?: number;
    shots_total_p90?: number;
    xg_total_p90?: number;
    dribbles_attempted_p90?: number;
    interceptions_p90?: number;
    pressures_applied_p90?: number;
    tackles_p90?: number;

    // Spatial
    avg_action_x?: number;
    avg_action_y?: number;
    position_group?: string;
  };
}

/**
 * Fetch player statistics for a specific season
 */
export const getPlayerStats = async (
  playerId: number,
  seasonId: number
): Promise<PlayerSeasonStats> => {
  const response = await apiClient.get<PlayerSeasonStats>(
    `/players/${playerId}/stats/season/${seasonId}`
  );
  return response.data;
};

/**
 * Fetch available seasons for a player
 */
export const getPlayerSeasons = async (playerId: number): Promise<number[]> => {
  const response = await apiClient.get<number[]>(`/players/${playerId}/seasons`);
  return response.data;
};

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

/**
 * Detailed season information for display
 */
export interface SeasonInfo {
  season_id: number;
  competition_id: number;
  competition_name: string;
  display_name: string; // e.g., "UEFA Euro 24 (282)"
  year: number;
}

/**
 * Fetch detailed season info for a player (with competition names)
 */
export const getPlayerSeasonsDetailed = async (playerId: number): Promise<SeasonInfo[]> => {
  const response = await apiClient.get<SeasonInfo[]>(`/players/${playerId}/seasons-detailed`);
  return response.data;
};

/**
 * Doppelgänger Engine Types (Player Similarity Search)
 */
export interface SimilarPlayerExplanation {
  shared_strengths: string[];
  key_difference?: string;
}

export interface SimilarPlayerResult {
  player_id: number;
  name: string;
  season_id: number;
  similarity_score: number;
  explanation: SimilarPlayerExplanation;
}

export interface DoppelgangerMeta {
  model_version: string;
  position_group: string;
  vector_count: number;
}

export interface TargetPlayer {
  name: string;
  season_id: number;
  position: string;
}

export interface DoppelgangerResponse {
  meta: DoppelgangerMeta;
  target: TargetPlayer;
  similar_players: SimilarPlayerResult[];
}

/**
 * Fetch similar players using the Doppelgänger Engine
 * Endpoint: GET /analytics/doppelganger
 */
export const getSimilarPlayers = async (
  playerId: number,
  seasonId: number,
  limit: number = 10,
  positionGroup?: string
): Promise<DoppelgangerResponse> => {
  const response = await apiClient.get<DoppelgangerResponse>('/analytics/doppelganger', {
    params: {
      player_id: playerId,
      season_id: seasonId,
      limit,
      position_group: positionGroup,
    },
  });
  return response.data;
};

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

/**
 * Player search API
 * Endpoint: GET /players/search?name={query}
 */
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

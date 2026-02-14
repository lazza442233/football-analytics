import { useQuery } from '@tanstack/react-query';
import { getPlayerSeasons, getPlayerStats, searchPlayers } from './client';

export const usePlayerSearch = (query: string) => {
  return useQuery({
    queryKey: ['players', 'search', query],
    queryFn: () => searchPlayers(query),
    enabled: !!query,
    staleTime: 1000 * 60 * 5, // Cache for 5 mins
  });
};

export const usePlayerStats = (playerId: number, seasonId: number) => {
  return useQuery({
    queryKey: ['player', playerId, 'stats', seasonId],
    queryFn: () => getPlayerStats(playerId, seasonId),
    enabled: !!playerId && !!seasonId,
    retry: 1,
    staleTime: 1000 * 60 * 30, // Stats rarely change for past seasons
  });
};

export const usePlayerSeasons = (playerId: number) => {
  return useQuery({
    queryKey: ['player', playerId, 'seasons'],
    queryFn: () => getPlayerSeasons(playerId),
    enabled: !!playerId,
    staleTime: 1000 * 60 * 60 * 24, // Seasons list changes rarely
  });
};

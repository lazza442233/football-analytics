import { AlertCircle, ArrowRight, Loader2, Users } from 'lucide-react';
import type { SimilarPlayerResult } from '../api/client';
import { useSimilarPlayers } from '../api/hooks';

interface SimilarPlayersProps {
  playerId: number;
  seasonId: number;
  onPlayerSelect?: (playerId: number) => void;
  limit?: number;
  positionGroup?: string;
}

/**
 * SimilarPlayers Component
 * Phase 3 Deliverable: Similarity Results Visualization
 * - Displays "nearest neighbors" from the Doppelgänger Engine
 * - Shows similarity scores with visual progress bars
 * - Explains why players are similar (shared strengths)
 * - Supports navigation to similar player profiles
 */
export const SimilarPlayers = ({
  playerId,
  seasonId,
  onPlayerSelect,
  limit = 10,
  positionGroup,
}: SimilarPlayersProps) => {
  const { data, isLoading, error } = useSimilarPlayers(playerId, seasonId, limit, positionGroup);

  // Loading State
  if (isLoading) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-lg">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
          <span className="ml-3 text-slate-400">Finding similar players...</span>
        </div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <div className="bg-slate-800 border border-rose-500/50 rounded-lg p-6 shadow-lg">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-rose-400 font-semibold">Failed to load similar players</h3>
            <p className="text-slate-400 text-sm mt-1">
              This could mean the player doesn't have enough data, or the similarity model hasn't
              been trained yet.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Empty State - No similar players found
  if (!data || data.similar_players.length === 0) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-lg">
        <div className="flex items-start gap-3">
          <Users className="w-5 h-5 text-slate-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-slate-300 font-semibold">No similar players found</h3>
            <p className="text-slate-400 text-sm mt-1">
              This player has a unique playstyle, or there isn't enough data to find matches.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-emerald-400" />
          <h3 className="text-lg font-semibold text-slate-50">Similar Players</h3>
        </div>
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <span>Position: {data.meta.position_group}</span>
          <span>•</span>
          <span>{data.similar_players.length} matches</span>
        </div>
      </div>

      {/* Similar Players List */}
      <div className="space-y-3">
        {data.similar_players.map((player) => (
          <SimilarPlayerCard
            key={`${player.player_id}-${player.season_id}`}
            player={player}
            onSelect={onPlayerSelect}
          />
        ))}
      </div>

      {/* Footer Info */}
      <div className="mt-4 pt-4 border-t border-slate-700">
        <p className="text-xs text-slate-500">
          Powered by the Doppelgänger Engine • Similarity threshold: 70% • Compared against{' '}
          {data.meta.vector_count} players
        </p>
      </div>
    </div>
  );
};

/**
 * Individual Similar Player Card
 */
interface SimilarPlayerCardProps {
  player: SimilarPlayerResult;
  onSelect?: (playerId: number) => void;
}

const SimilarPlayerCard = ({ player, onSelect }: SimilarPlayerCardProps) => {
  const similarityPercentage = (player.similarity_score * 100).toFixed(1);
  const isHighMatch = player.similarity_score >= 0.9;
  const isMediumMatch = player.similarity_score >= 0.8;

  // Color coding based on similarity score
  const progressColor = isHighMatch
    ? 'bg-emerald-500'
    : isMediumMatch
      ? 'bg-blue-500'
      : 'bg-slate-500';

  const badgeColor = isHighMatch
    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50'
    : isMediumMatch
      ? 'bg-blue-500/20 text-blue-400 border-blue-500/50'
      : 'bg-slate-500/20 text-slate-400 border-slate-500/50';

  const handleClick = () => {
    if (onSelect) {
      onSelect(player.player_id);
    }
  };

  return (
    <div
      onClick={handleClick}
      className={`
        bg-slate-900/50 border border-slate-700 rounded-lg p-4
        transition-all duration-200
        ${onSelect ? 'cursor-pointer hover:border-emerald-500/50 hover:bg-slate-900/80' : ''}
      `}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-slate-100 font-semibold">{player.name}</h4>
            {onSelect && (
              <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 transition-colors" />
            )}
          </div>
          <p className="text-xs text-slate-400">Season {player.season_id}</p>
        </div>

        {/* Similarity Badge */}
        <div className={`px-3 py-1 rounded-full border text-sm font-mono ${badgeColor}`}>
          {similarityPercentage}% Match
        </div>
      </div>

      {/* Similarity Progress Bar */}
      <div className="mb-3">
        <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full ${progressColor} transition-all duration-500 ease-out`}
            style={{ width: `${similarityPercentage}%` }}
          />
        </div>
      </div>

      {/* Explanation */}
      <div className="space-y-2">
        {/* Shared Strengths */}
        {player.explanation.shared_strengths.length > 0 && (
          <div>
            <p className="text-xs text-slate-500 mb-1">Shared Strengths:</p>
            <div className="flex flex-wrap gap-1">
              {player.explanation.shared_strengths.slice(0, 3).map((strength, idx) => (
                <span
                  key={idx}
                  className="text-xs bg-emerald-500/10 text-emerald-400 px-2 py-1 rounded border border-emerald-500/20"
                >
                  {formatMetricName(strength)}
                </span>
              ))}
              {player.explanation.shared_strengths.length > 3 && (
                <span className="text-xs text-slate-500 px-2 py-1">
                  +{player.explanation.shared_strengths.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Key Difference */}
        {player.explanation.key_difference && (
          <div>
            <p className="text-xs text-slate-500 mb-1">Key Difference:</p>
            <span className="text-xs bg-amber-500/10 text-amber-400 px-2 py-1 rounded border border-amber-500/20">
              {formatMetricName(player.explanation.key_difference)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Format metric names for display
 * Example: "progressive_passes_per90" -> "Progressive Passes"
 */
const formatMetricName = (metric: string): string => {
  return metric
    .replace(/_per90|_p90/g, '')
    .replace(/_/g, ' ')
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

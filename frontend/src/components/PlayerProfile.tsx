import { Clock, Info, Loader2 } from 'lucide-react';
import { useState } from 'react';
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import type { PlayerSeasonStats } from '../api/client';
import { usePlayerSeasons, usePlayerStats } from '../api/hooks';
import { StatCard } from './StatCard';

interface PlayerProfileProps {
  playerId: number;
  playerName: string;
  seasonId?: number;
}

/**
 * PlayerProfile Component
 * Phase 2 Deliverable: The "DNA" View
 * - Fetches player season stats
 * - Displays StatCards for key metrics
 * - Renders a Radar Chart showing player's playstyle profile
 */
export const PlayerProfile = ({
  playerId,
  playerName,
  seasonId: propSeasonId,
}: PlayerProfileProps) => {
  // 1. Fetch available seasons
  const { data: seasons, isLoading: isLoadingSeasons } = usePlayerSeasons(playerId);

  // 2. Determine active season (Prop > Latest Available)
  const seasonId = propSeasonId ?? seasons?.[0];

  // 3. Fetch stats for that season
  const { data: stats, isLoading: isLoadingStats, error } = usePlayerStats(playerId, seasonId ?? 0);

  // 4. State for info tooltip
  const [showMetricsInfo, setShowMetricsInfo] = useState(false);

  const isLoading = isLoadingSeasons || (!!seasonId && isLoadingStats);

  /**
   * Metric Definitions for DNA Profile
   * Based on realistic elite-level per-90 maximums from top European leagues
   */
  const METRIC_DEFINITIONS = {
    'Goal Threat': {
      key: 'xg_total_p90',
      max: 1.0, // Elite strikers: ~0.8-1.0 xG/90
      description: 'Expected Goals per 90 minutes',
      unit: 'xG/90',
    },
    Progression: {
      key: 'progressive_passes_p90',
      max: 10.0, // Elite playmakers: ~8-10 progressive passes/90
      description: 'Passes moving ball 10m+ towards goal',
      unit: 'passes/90',
    },
    'Pass Accuracy': {
      key: 'pass_completion_rate',
      max: 100, // Percentage (already 0-100)
      description: 'Percentage of successful passes',
      unit: '%',
    },
    Volume: {
      key: 'passes_attempted_p90',
      max: 100.0, // Elite midfielders: ~80-100 passes/90
      description: 'Total passes attempted per 90',
      unit: 'passes/90',
    },
    Creativity: {
      key: 'shot_assists_p90',
      max: 3.5, // Elite creators: ~3.0-4.0 key passes/90
      description: 'Passes leading directly to shots',
      unit: 'passes/90',
    },
    'Defensive Action': {
      key: 'tackles_p90',
      max: 5.0, // Elite defenders/midfielders: ~4-5 tackles/90
      description: 'Tackles attempted per 90',
      unit: 'tackles/90',
    },
  };

  /**
   * Transform stats into radar chart data using per-90 metrics
   * Normalized against realistic elite-level maximums for meaningful context
   */
  const getRadarData = (stats: PlayerSeasonStats) => {
    const metrics = stats.advanced_metrics || {};

    const normalize = (value: number | undefined, max: number, fallback = 0) => {
      if (value === undefined || value === null) return fallback;
      return Math.min((value / max) * 100, 100);
    };

    return Object.entries(METRIC_DEFINITIONS).map(([axis, def]) => {
      let rawValue: number;

      if (def.key === 'pass_completion_rate') {
        // Pass completion is already a percentage
        rawValue = stats.pass_completion_rate || 0;
      } else {
        // Use per-90 metrics from advanced_metrics
        rawValue = (metrics[def.key as keyof typeof metrics] as number) || 0;
      }

      const normalizedValue =
        def.key === 'pass_completion_rate'
          ? rawValue // Already 0-100
          : normalize(rawValue, def.max);

      return {
        axis,
        value: normalizedValue,
        rawValue,
        unit: def.unit,
        description: def.description,
        fullMark: 100,
      };
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
        <span className="ml-3 text-slate-400">Loading {playerName}'s profile...</span>
      </div>
    );
  }

  if (!seasonId || error || !stats) {
    return (
      <div className="bg-rose-900/20 border border-rose-500/50 rounded-lg p-6 text-center">
        <p className="text-rose-400">
          {!seasonId
            ? 'No season data found for this player.'
            : 'Failed to load stats for this season.'}
        </p>
      </div>
    );
  }

  const radarData = getRadarData(stats);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Player Header */}
      <div className="border-b border-slate-700 pb-4 flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold text-slate-50">{playerName}</h2>
          <p className="text-emerald-400 text-sm mt-1 font-mono">
            ID: {playerId} • Season {seasonId}
          </p>
        </div>
        <div className="text-right">
          <span className="text-slate-400 text-sm">Matches Played</span>
          <div className="text-2xl font-bold text-slate-200">{stats.matches_played}</div>
        </div>
      </div>

      {/* Stat Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Total xG"
          value={(stats.advanced_metrics?.xg_total ?? stats.total_xg ?? 0).toFixed(2)}
          subtitle="Expected Goals"
          accentColor="emerald"
        />
        <StatCard
          label="Pass Accuracy"
          value={`${stats.pass_completion_rate.toFixed(1)}%`}
          subtitle={`${stats.successful_passes} / ${stats.total_passes}`}
          accentColor="blue"
        />
        <StatCard
          label="Prog. Passes"
          value={stats.advanced_metrics?.progressive_passes?.toFixed(0) ?? '0'}
          subtitle="Forward movement"
          accentColor="blue"
        />
        <StatCard
          label="Play Time"
          value={Number(stats.advanced_metrics?.minutes_played ?? 0).toFixed(0)}
          subtitle={`Matches: ${stats.matches_played}`}
          accentColor="amber"
          icon={Clock}
        />
      </div>

      {/* Radar Chart - The "DNA" Visualizer */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-slate-50">Player DNA Profile</h3>
            <button
              onClick={() => setShowMetricsInfo(!showMetricsInfo)}
              className="text-slate-400 hover:text-emerald-400 transition-colors"
              title="What do these metrics mean?"
            >
              <Info className="w-4 h-4" />
            </button>
          </div>
          <span className="px-3 py-1 bg-slate-700 rounded-full text-xs text-slate-300">
            Per-90 Metrics
          </span>
        </div>

        {/* Metrics Info Panel */}
        {showMetricsInfo && (
          <div className="mb-4 p-4 bg-slate-900/50 border border-slate-600 rounded-lg space-y-2">
            <h4 className="text-sm font-semibold text-emerald-400 mb-2">Metric Definitions</h4>
            {Object.entries(METRIC_DEFINITIONS).map(([name, def]) => (
              <div key={name} className="text-xs">
                <span className="font-medium text-slate-300">{name}:</span>{' '}
                <span className="text-slate-400">{def.description}</span>
              </div>
            ))}
            <p className="text-xs text-slate-500 mt-2 pt-2 border-t border-slate-700">
              All metrics are normalized to 0-100 scale based on elite-level performances in top
              European leagues. Hover over the chart to see actual values.
            </p>
          </div>
        )}

        <div className="h-[400px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis
                dataKey="axis"
                tick={{ fill: '#94a3b8', fontSize: 12, fontWeight: 500 }}
              />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
              <Tooltip
                content={({ payload }) => {
                  if (!payload || payload.length === 0) return null;
                  const data = payload[0].payload;
                  return (
                    <div className="bg-slate-900 border border-slate-600 rounded-lg p-3 shadow-xl">
                      <p className="text-slate-200 font-semibold text-sm mb-1">{data.axis}</p>
                      <p className="text-slate-400 text-xs mb-2">{data.description}</p>
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-emerald-400 font-mono text-sm">
                          {data.rawValue.toFixed(2)} {data.unit}
                        </span>
                        <span className="text-slate-500 text-xs">{data.value.toFixed(0)}/100</span>
                      </div>
                    </div>
                  );
                }}
              />
              <Radar
                name={playerName}
                dataKey="value"
                stroke="#10b981"
                fill="#10b981"
                fillOpacity={0.4}
                strokeWidth={2}
                isAnimationActive={true}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        <p className="text-xs text-slate-500 text-center mt-2">
          Hover over the chart to see detailed values. Click the <Info className="w-3 h-3 inline" />{' '}
          icon to learn what each metric represents.
        </p>
      </div>
    </div>
  );
};

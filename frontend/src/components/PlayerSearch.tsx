import { Loader2, Search } from 'lucide-react';
import { useState } from 'react';
import type { PlayerSearchResult } from '../api/client';
import { usePlayerSearch } from '../api/hooks';

interface PlayerSearchProps {
  onPlayerSelect?: (player: PlayerSearchResult) => void;
}

/**
 * PlayerSearch Component
 * Phase 2+ Refactor: Uses React Query via custom hook
 */
export const PlayerSearch = ({ onPlayerSelect }: PlayerSearchProps) => {
  const [inputValue, setInputValue] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const { data: results, isLoading, isError, isFetched } = usePlayerSearch(searchTerm);

  const handleSearch = () => {
    if (inputValue.trim()) {
      setSearchTerm(inputValue.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-4">
      <div className="flex flex-col gap-4">
        <label htmlFor="player-search" className="text-slate-50 text-sm font-medium">
          Search for a player
        </label>
        <div className="flex gap-2">
          <input
            id="player-search"
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="e.g., Harry Kane"
            className="flex-1 px-4 py-2 bg-slate-800 text-slate-50 border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
            disabled={isLoading}
          />
          <button
            onClick={handleSearch}
            disabled={isLoading || !inputValue.trim()}
            className="px-6 py-2 bg-emerald-500 text-slate-900 font-medium rounded-lg hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Search className="w-4 h-4" />
            )}
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Results Area */}
        {isFetched && (
          <div className="mt-4 animate-in fade-in slide-in-from-top-4 duration-300">
            {isError ? (
              <div className="text-rose-400 text-center py-4">
                Failed to search players. Please try again.
              </div>
            ) : results && results.length > 0 ? (
              <ul className="space-y-2">
                {results.map((player) => (
                  <li
                    key={player.id}
                    className="p-3 bg-slate-800 border border-slate-700 rounded-lg hover:border-emerald-500 cursor-pointer transition-colors flex justify-between items-center group"
                    onClick={() => {
                      onPlayerSelect?.(player);
                      // Clear search after selection if desired, or keep it. Keeping it.
                    }}
                  >
                    <div>
                      <span className="text-slate-50 font-medium group-hover:text-emerald-400 transition-colors">
                        {player.name}
                      </span>
                      <span className="ml-2 text-slate-400 text-sm">({player.position})</span>
                    </div>
                    <span className="text-xs text-slate-500">ID: {player.id}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-slate-400 text-center py-4">
                No players found matching "{searchTerm}"
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

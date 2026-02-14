import { useState } from 'react';
import { Search } from 'lucide-react';

/**
 * PlayerSearch Component
 * Phase 1 Deliverable: A text box that finds "Harry Kane"
 *
 * Current behavior: Logs the search query to console
 * Future: Will integrate with /players/search API endpoint
 */
export const PlayerSearch = () => {
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = () => {
    console.log('Searching for player:', searchQuery);
    // Phase 2: Will call searchPlayers(searchQuery) from API client
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-4">
      <div className="flex flex-col gap-2">
        <label htmlFor="player-search" className="text-slate-50 text-sm font-medium">
          Search for a player
        </label>
        <div className="flex gap-2">
          <input
            id="player-search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="e.g., Harry Kane"
            className="flex-1 px-4 py-2 bg-slate-800 text-slate-50 border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
          <button
            onClick={handleSearch}
            className="px-6 py-2 bg-emerald-500 text-slate-900 font-medium rounded-lg hover:bg-emerald-400 transition-colors flex items-center gap-2"
          >
            <Search className="w-4 h-4" />
            Search
          </button>
        </div>
      </div>
    </div>
  );
};

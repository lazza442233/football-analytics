import { useState } from 'react';
import type { PlayerSearchResult } from './api/client';
import { PlayerProfile } from './components/PlayerProfile';
import { PlayerSearch } from './components/PlayerSearch';

function App() {
  const [selectedPlayer, setSelectedPlayer] = useState<PlayerSearchResult | null>(null);

  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="w-full max-w-6xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-50 mb-2">
            Scout's Eye
          </h1>
          <p className="text-slate-400">
            Football Analytics Dashboard - Phase 2: The "DNA" View
          </p>
        </header>

        {/* Search Interface */}
        <div className="bg-slate-800 rounded-xl p-8 shadow-xl mb-8">
          <PlayerSearch onPlayerSelect={setSelectedPlayer} />
        </div>

        {/* Player Profile - Shows when a player is selected */}
        {selectedPlayer && (
          <div className="bg-slate-800 rounded-xl p-8 shadow-xl">
            <PlayerProfile
              playerId={selectedPlayer.id}
              playerName={selectedPlayer.name}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

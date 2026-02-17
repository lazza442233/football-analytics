import { useState } from 'react';
import type { PlayerSearchResult } from './api/client';
import { PlayerProfile } from './components/PlayerProfile';
import { PlayerSearch } from './components/PlayerSearch';

function App() {
  const [selectedPlayer, setSelectedPlayer] = useState<PlayerSearchResult | null>(null);
  const [selectedSeason, setSelectedSeason] = useState<number | undefined>(undefined);

  /**
   * Handle selecting a new player - reset season to default
   */
  const handlePlayerSelect = (player: PlayerSearchResult | null) => {
    setSelectedPlayer(player);
    setSelectedSeason(undefined); // Reset to default (most recent) season
  };

  /**
   * Handle navigation to a similar player's profile
   * Note: We only have player_id from similarity results, so we use a simplified approach
   */
  const handleSimilarPlayerSelect = (playerId: number) => {
    // Create a temporary player result to trigger profile load
    // The actual name will be shown in the profile itself
    setSelectedPlayer({
      id: playerId,
      name: `Player ${playerId}`, // Placeholder - actual name loads from API
      position: 'Unknown', // Will be determined by the profile
    });
    setSelectedSeason(undefined); // Reset to default season

    // Scroll to top to show the new profile
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="w-full max-w-6xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-50 mb-2">Scout's Eye</h1>
          <p className="text-slate-400">
            Football Analytics Dashboard - Phase 3: The Similarity Engine
          </p>
        </header>

        {/* Search Interface */}
        <div className="bg-slate-800 rounded-xl p-8 shadow-xl mb-8">
          <PlayerSearch onPlayerSelect={handlePlayerSelect} />
        </div>

        {/* Player Profile - Shows when a player is selected */}
        {selectedPlayer && (
          <div className="bg-slate-800 rounded-xl p-8 shadow-xl">
            <PlayerProfile
              playerId={selectedPlayer.id}
              playerName={selectedPlayer.name}
              seasonId={selectedSeason}
              onSeasonChange={setSelectedSeason}
              onPlayerSelect={handleSimilarPlayerSelect}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

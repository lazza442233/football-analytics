import { PlayerSearch } from './components/PlayerSearch';

function App() {
  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-8">
      <div className="w-full max-w-4xl">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-50 mb-2">
            Scout's Eye
          </h1>
          <p className="text-slate-400">
            Football Analytics Dashboard - Phase 1
          </p>
        </header>

        <div className="bg-slate-800 rounded-xl p-8 shadow-xl">
          <PlayerSearch />
        </div>
      </div>
    </div>
  );
}

export default App;

# Scout's Eye - Frontend Dashboard

React-based frontend for the Football Analytics platform, visualizing player statistics and similarity analysis from the Doppelgänger Engine.

## Tech Stack

- **Framework**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS v4
- **Data Fetching**: Axios + TanStack Query (React Query)
- **Visualization**: Recharts
- **Icons**: Lucide React

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
npm install
```

### Development

Start the development server with hot-reload:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build

Build for production:

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
src/
├── api/
│   └── client.ts          # Axios API client configuration
├── components/
│   └── PlayerSearch.tsx   # Player search component
├── App.tsx                # Main app component
├── main.tsx               # Entry point
└── index.css              # Tailwind imports
```

## Implementation Status

### Phase 1: Skeleton & Connectivity ✅
- ✅ Vite + Tailwind project initialized
- ✅ API client structure created
- ✅ PlayerSearch component (console logging)
- ✅ Dark mode theme applied (slate-900 background)

### Phase 2: The "DNA" View (Metrics) 🚧
- Fetch player stats from `/players/{id}/stats/season/{id}`
- Build StatCard components
- Implement Radar Chart with Recharts

### Phase 3: Similarity & Comparison 🚧
- Fetch similar players from `/analytics/doppelganger`
- Render SimilarPlayerCard list
- Add comparison overlay to Radar Chart
- Display API-provided explanations

## API Endpoints

The frontend integrates with these backend endpoints:

| Feature | Endpoint | Method |
|---------|----------|--------|
| Search | `/players/search?name={query}` | GET |
| Get DNA | `/players/{id}/stats/season/{season}` | GET |
| Similarity | `/analytics/doppelganger` | GET |

## Theme Colors

Following the "Dark Mode Sports Analytics" design system:

- Background: `slate-900`
- Card Surface: `slate-800`
- Primary Text: `slate-50`
- Accent (Attack): `emerald-500`
- Accent (Defense): `rose-500`
- Accent (Possession): `blue-500`

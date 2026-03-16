# Architecture Spec: The Oracle — Natural Language Query Interface

**Date:** 2026-03-16
**Status:** DRAFT
**Feature:** Natural Language Query over Football Analytics Data
**Author:** Architecture Spike

---

## 1. Goal

**The Oracle** is a natural language query interface that lets non-technical users (scouts, coaches) ask plain-English questions about football analytics data and receive structured, accurate answers — without needing to know endpoint names, player IDs, or season codes.

**Example queries and their intended mappings:**

| User Question | Oracle Behaviour |
|---|---|
| "Who plays like a young Müller?" | Search player by name → call `GET /analytics/doppelganger` |
| "What was Kane's xG last season?" | Resolve player + season → call `GET /players/{id}/stats/season/{season_id}` |
| "Show me the most progressive passers in Bundesliga 23/24" | Map to analytics query → call `GET /matches/{id}/analytics/summary` or aggregate stats |
| "Find me a budget striker who plays like Firmino" | Doppelgänger search → filter by position group FWD |

The Oracle does **not** generate SQL. It maps natural language intent to the existing FastAPI endpoints — acting as a smart router on top of the current API layer.

---

## 2. LLM Selection

### Options Evaluated

| Model | Tool-Calling | Latency | Cost / 1K tokens | Context | Verdict |
|---|---|---|---|---|---|
| **Claude claude-sonnet-4-6** | ✅ Native | ~1-2s | ~$0.003 / $0.015 | 200K tokens | ✅ **Recommended** |
| GPT-4o | ✅ Native | ~1-2s | ~$0.005 / $0.015 | 128K tokens | ✅ Viable alternative |
| GPT-4o-mini | ✅ Native | ~0.5s | ~$0.00015 / $0.0006 | 128K tokens | ⚠️ May miss nuanced queries |
| Llama 3.1 (local) | ⚠️ Limited | ~2-5s (CPU) | Free | 128K tokens | ❌ Tool-calling unreliable at scale |

### Decision: Claude claude-sonnet-4-6 (primary), GPT-4o-mini (fallback / cost optimisation)

**Rationale:**
- Claude claude-sonnet-4-6's tool-use format is well-suited to structured function-calling over a fixed set of API endpoints
- 200K context window allows passing full player stats and full tool schemas without truncation
- Cost at anticipated query volume (100-500 queries/day) is negligible (<$5/day)
- `anthropic` Python SDK is already a known dependency pattern in the codebase; adding it aligns with project conventions
- GPT-4o-mini is documented as a fallback option for cost-sensitive scenarios

**Environment variable required:** `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY` for fallback). Add to `.env` and `src/config.py`.

---

## 3. Architecture Pattern

### Selected Pattern: Tool-Calling / Function-Calling

The LLM is given:
1. A system prompt describing the football analytics domain and available data
2. A set of **tool definitions** (one per relevant API endpoint)
3. The user's natural language question

The LLM responds with either:
- A **tool call** (structured JSON specifying which endpoint + parameters to invoke)
- A **direct answer** (if no API call is needed, e.g. explaining what xG means)

The Oracle service executes the tool call against the internal FastAPI endpoints and returns the result to the LLM for a final natural-language response.

```
User NL Query
     │
     ▼
┌─────────────────────────────┐
│  OracleService               │
│  1. Build tool schemas       │
│  2. Call LLM with question   │
│  3. LLM returns tool call    │
│  4. Execute tool call        │──→ FastAPI internal endpoints
│  5. Return result to LLM     │◄── JSON response
│  6. LLM formats final answer │
└─────────────────────────────┘
     │
     ▼
Structured JSON response to client
```

### Why Not RAG?

RAG over player stat embeddings was considered. It was rejected for v1 because:
- The data is structured and relational, not document-based — k-NN lookup already exists in the Doppelgänger Engine
- The existing API layer already provides the right abstractions; duplicating them as embeddings adds maintenance burden
- Tool-calling gives exact, verifiable answers; RAG introduces hallucination risk over numerical data

RAG remains a valid future option for natural language queries over **unstructured** content (match commentary, scouting reports).

---

## 4. Tool Definitions (Available Functions)

The LLM will be given the following tools, mapping to existing routers:

### Tool 1: `search_player`
```json
{
  "name": "search_player",
  "description": "Search for a player by name. Returns a list of matching players with their IDs and positions. Use this first to resolve a player name to an ID before calling other tools.",
  "parameters": {
    "name": { "type": "string", "description": "Player name or partial name (e.g. 'Kane', 'Müller')" }
  }
}
```
→ Calls `GET /players/search?name={name}`

---

### Tool 2: `get_player_stats`
```json
{
  "name": "get_player_stats",
  "description": "Get a player's season statistics including per-90 metrics (xG, passes, pressures, dribbles) and their DNA vector. Requires a player_id and season_id.",
  "parameters": {
    "player_id": { "type": "integer" },
    "season_id": { "type": "integer" }
  }
}
```
→ Calls `GET /players/{player_id}/stats/season/{season_id}`

---

### Tool 3: `get_player_seasons`
```json
{
  "name": "get_player_seasons",
  "description": "Get the list of seasons (with competition info) that a player has data for. Use this to resolve 'last season' or 'Euro 2024' to a concrete season_id.",
  "parameters": {
    "player_id": { "type": "integer" }
  }
}
```
→ Calls `GET /players/{player_id}/seasons-detailed`

---

### Tool 4: `find_similar_players`
```json
{
  "name": "find_similar_players",
  "description": "Find players who play statistically similarly to a target player in a given season. Returns ranked list with similarity scores and explanations.",
  "parameters": {
    "player_id": { "type": "integer" },
    "season_id": { "type": "integer" },
    "position_group": { "type": "string", "enum": ["GK", "DEF", "MID", "FWD"], "optional": true },
    "limit": { "type": "integer", "default": 5, "optional": true }
  }
}
```
→ Calls `GET /analytics/doppelganger`

---

### Tool 5: `get_match_xg`
```json
{
  "name": "get_match_xg",
  "description": "Get the expected goals (xG) summary for a specific match.",
  "parameters": {
    "match_id": { "type": "integer" }
  }
}
```
→ Calls `GET /matches/{match_id}/analytics/summary`

---

## 5. API Design

### Endpoint

```
POST /oracle/query
```

### Request

```json
{
  "question": "Who plays most like Toni Kroos in the 2023/24 season?"
}
```

### Response

```json
{
  "answer": "Based on the 2023/24 season data, the players who play most like Toni Kroos are...",
  "tool_calls_made": [
    { "tool": "search_player", "params": { "name": "Kroos" }, "result_count": 1 },
    { "tool": "find_similar_players", "params": { "player_id": 5503, "season_id": 281 }, "result_count": 5 }
  ],
  "sources": [
    { "player_id": 5503, "season_id": 281, "endpoint": "/analytics/doppelganger" }
  ]
}
```

### Router location

`src/api/routers/oracle.py` — registered in `src/main.py` as `app.include_router(oracle.router)`.

### Service location

`src/services/oracle.py` — `OracleService` class following the existing service layer pattern.

---

## 6. Failure Modes & Fallback Behaviour

| Failure | Behaviour |
|---|---|
| **LLM hallucinates a player name** | `search_player` returns empty list. Oracle returns: "I couldn't find a player named X in the database. Try using their full name." |
| **LLM calls a tool with invalid params** (e.g. non-existent season_id) | Downstream FastAPI returns 404. Oracle catches the error, includes it in the next LLM turn, and asks the LLM to retry with corrected parameters (max 2 retries). |
| **LLM returns nonsensical tool call** | Schema validation via Pydantic rejects the call. Oracle returns a generic error: "I wasn't able to process that query. Please try rephrasing." |
| **Upstream LLM API is down** (Anthropic/OpenAI outage) | HTTP timeout or 5xx from LLM provider. Oracle catches the exception, logs it via structured JSON logger, and returns HTTP 503 with `{"detail": "AI service temporarily unavailable"}`. Do not let the error propagate to unhandled 500. |
| **Query has no relevant tool** (e.g. "What is offside?") | LLM answers directly without tool calls — this is valid and correct behaviour. |
| **Multi-turn conversation requested** | Not supported in v1. Each `POST /oracle/query` is stateless. Return a note in the response if the question appears to be a follow-up. |

**Max tool call chain**: 5 tool calls per query. If the LLM attempts more, abort and return a partial answer with a warning. This prevents runaway API consumption.

---

## 7. Implementation Conventions

Per `CLAUDE.md` and `project-context.md`:

- **Async-first**: `OracleService` must be `async def`. LLM SDK calls are inherently async (both `anthropic` and `openai` SDKs support async clients). No `asyncio.to_thread()` needed.
- **Service layer**: All LLM orchestration logic lives in `src/services/oracle.py`. The router (`src/api/routers/oracle.py`) only handles HTTP concerns.
- **Structured logging**: Use `logging.getLogger(__name__)`. Log each tool call at `DEBUG`, log LLM errors at `ERROR`.
- **Config via settings**: Add `ANTHROPIC_API_KEY: str` and `ORACLE_MODEL: str = "claude-sonnet-4-6"` to `src/config.py`. Never hardcode API keys.
- **Session injection**: If Oracle tools need DB access, pass `AsyncSession` via `Depends(get_session)` — do not instantiate sessions inside `OracleService`.
- **Internal tool execution**: Tools should call the internal service layer directly (e.g. `DoppelgangerService`, `AnalyticsService`) rather than making HTTP calls back to the FastAPI server. This avoids network round-trips and keeps the execution in-process.

---

## 8. Dependencies

| Package | Purpose | Add via |
|---|---|---|
| `anthropic>=0.40.0` | Claude API client (primary LLM) | `poetry add anthropic` |
| `openai>=1.0.0` | OpenAI fallback (optional) | `poetry add openai` |

No LangChain, no LlamaIndex. Keep the dependency footprint minimal — the tool-calling pattern is simple enough to implement directly against the SDK without an orchestration framework.

**New environment variables:**
```
ANTHROPIC_API_KEY=sk-ant-...
ORACLE_MODEL=claude-sonnet-4-6          # Override to switch models
ORACLE_MAX_TOOL_CALLS=5             # Safety ceiling on tool call chains
```

---

## 9. Scope Boundary (What v1 Does NOT Do)

- ❌ No multi-turn conversation — each query is stateless
- ❌ No writes — Oracle is read-only; it cannot trigger ingestion or modify data
- ❌ No real-time data — limited to what is currently ingested in the database
- ❌ No user-specific context — no "my saved players" or personalised results
- ❌ No fallback to raw SQL generation — Oracle only routes to existing API endpoints
- ❌ No streaming responses — v1 returns a complete answer in a single response
- ❌ No caching of LLM responses — identical queries will re-invoke the LLM (caching can be added in v2 via Redis)

---

## 10. Open Questions (Resolve Before Implementation)

1. **Internal service calls vs HTTP calls**: Should Oracle tools call service classes directly (preferred, faster) or hit the FastAPI endpoints over HTTP (simpler but adds latency and coupling)? **Recommendation: service classes directly.**
2. **Player name disambiguation**: If `search_player("Müller")` returns Thomas Müller and Gerd Müller, how should Oracle present the choice? Options: ask the user (requires multi-turn, not in v1) or pick the most recently active player. **Needs a decision.**
3. **Season resolution**: "Last season" is ambiguous — last season in which competition? How should Oracle handle users who haven't specified a competition? **Needs a default strategy documented.**
4. **Rate limiting**: Should `/oracle/query` be rate-limited more aggressively than other endpoints, given LLM API cost? Suggested: 10 req/min/IP via `slowapi`. Aligns with the rate-limiting note in `arch_doppelganger.md`.

---

## 11. Suggested Acceptance Criteria (v1 Story)

- **Given** a user asks "Who plays like Harry Kane?", **When** `POST /oracle/query` is called, **Then** the response contains at least 3 similar players with similarity scores and the `tool_calls_made` field lists `search_player` and `find_similar_players`.
- **Given** the user asks about a player not in the database, **When** `POST /oracle/query` is called, **Then** the response returns HTTP 200 with an `answer` explaining the player was not found — not a 404 or 500.
- **Given** the Anthropic API is unavailable, **When** `POST /oracle/query` is called, **Then** the response returns HTTP 503 with `{"detail": "AI service temporarily unavailable"}` and the error is logged as `ERROR` in structured JSON.
- **Given** a non-football question ("What is the capital of France?"), **When** `POST /oracle/query` is called, **Then** Oracle returns a polite out-of-scope message without making any tool calls.

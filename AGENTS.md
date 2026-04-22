# AGENTS.md — City Bike Log

## Quick Start
```bash
# Local
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# Docker
docker compose up --build
```

## Architecture
- **Entry:** `app/main.py` — FastAPI app, single entrypoint
- **DB:** `app/database.py` — raw `sqlite3`, no migrations. Schema in `init_db()`
- **Analysis:** `app/analysis.py` — Ollama vision (JSON schema output), `analyze_image()` returns parsed dict
- **CRUD:** `app/crud.py` — thin sqlite3 wrappers
- **Config:** `app/config.py` — env vars: `DB_PATH`, `OLLAMA_URL`, `OLLAMA_MODEL`
- **Schema:** `app/schemas/trip.py` — Pydantic models

## Critical Details
- **Ollama required** on host with `qwen3.6-35b-a3b` loaded before running
- Docker Compose uses `host.docker.internal:11434` to reach host Ollama — do not change this unless Ollama is also in Docker
- Upload endpoint (`POST /api/trips/upload`) expects multipart image, saves to `uploads/`, calls Ollama, returns parsed trip data
- Time fields extracted as `HH:MM` — dates are combined with today's date at runtime in `combine_with_date()`
- **No database migrations** — schema is hardcoded in `init_db()`. Changing schema requires manual DB migration
- **No auth, no validation of Ollama response** beyond Pydantic — if analysis fails, returns 500
- `uploads/` and `trips.db` are gitignored

## API
| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/trips/upload` | Multipart image → returns TripResponse (201) |
| GET | `/api/trips` | Paginated (`?limit=50&offset=0`) |
| GET | `/api/trips/{id}` | 404 if not found |
| DELETE | `/api/trips/{id}` | 204 on success, 404 if not found |

## Example Image
`tests/example.png` — trip summary screenshot used for prompt tuning.

## Gotchas
- No lint/format/typecheck config — none is set up
- No tests — none are set up
- `created_at` in responses uses `datetime.utcnow()` — not from the DB row
- If Ollama is unavailable, the upload endpoint returns 500 with analysis error detail

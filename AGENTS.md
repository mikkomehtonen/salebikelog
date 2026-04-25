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
- **Analysis:** `app/analysis.py` — LM Studio vision (JSON schema output), `analyze_image()` returns parsed dict
- **CRUD:** `app/crud.py` — thin sqlite3 wrappers
- **Config:** `app/config.py` — env vars: `DB_PATH`, `LM_STUDIO_URL`, `LM_STUDIO_MODEL`
- **Schema:** `app/schemas/trip.py` — TripCreate/TripResponse Pydantic models
- **Schema:** `app/schemas/position.py` — PositionCreate/PositionResponse Pydantic models

## Critical Details
- **LM Studio required** on host (port `1234`) with `qwen/qwen3.6-35b-a3b` loaded before running
- Docker Compose uses `host.docker.internal:1234` to reach host LM Studio — do not change this unless LM Studio is also in Docker
- Upload endpoint (`POST /api/trips/upload`) expects multipart image, saves to `uploads/`, calls LM Studio, returns parsed trip data
- Time fields extracted as `HH:MM` — dates are combined with today's date at runtime in `combine_with_date()`
- **No database migrations** — schema is hardcoded in `init_db()`. Changing schema requires manual DB migration
- **No auth, no validation of vision model response** beyond Pydantic — if analysis fails, returns 500
- `uploads/` and `trips.db` are gitignored

## Database
| Table | Columns |
|-------|---------|
| `trips` | `id`, `bike_id`, `serial`, `length_min`, `start_time`, `end_time`, `start_pos`, `end_pos`, `image_url`, `created_at` |
| `positions` | `id`, `name` (UNIQUE), `latitude`, `longitude`, `altitude`, `created_at`, `updated_at` |

- `trips` table is **never altered** after initial creation — `start_pos`/`end_pos` are address strings
- `positions` table is looked up by `name` matching `start_pos`/`end_pos` address strings
- `latitude`/`longitude`/`altitude` in positions are nullable — admin fills them in later

## API
| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/trips/upload` | Multipart image → returns TripResponse (201) |
| GET | `/api/trips` | Paginated (`?limit=50&offset=0`) |
| GET | `/api/trips/{id}` | 404 if not found |
| DELETE | `/api/trips/{id}` | 204 on success, 404 if not found |
| GET | `/api/positions` | Paginated (`?limit=50&offset=0`) |
| GET | `/api/positions/{id}` | 404 if not found |
| POST | `/api/positions` | Create/update position (201, idempotent by name) |
| PATCH | `/api/positions/{id}` | Update position coords |
| DELETE | `/api/positions/{id}` | 204 on success, 404 if not found |

## Example Image
`tests/example.png` — trip summary screenshot used for prompt tuning.

## Lint & Format
```bash
ruff check app/
ruff format --check app/
ruff check --fix app/
ruff format app/
basedpyright app/
```

## Gotchas
- `created_at` in responses uses `datetime.utcnow()` — not from the DB row
- If LM Studio is unavailable, the upload endpoint returns 500 with analysis error detail

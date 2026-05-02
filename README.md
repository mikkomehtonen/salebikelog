# City Bike Log

Backend for logging city bike trips from uploaded trip summary images.

## Setup

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env

# Run the server
uvicorn app.main:app --reload
```

### Docker

```bash
docker compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/trips/upload` | Upload trip summary image |
| GET | `/api/trips` | List all trips |
| GET | `/api/trips/{id}` | Get trip by ID |
| DELETE | `/api/trips/{id}` | Delete a trip |

## LM Studio

Requires LM Studio running locally on port `1234` with `qwen3.6-35b-a3b` model loaded.

When running in Docker with LM Studio on the host, `host.docker.internal` is used to reach it.

## Dev Tooling

### Lint & Format

```bash
# Lint
.venv/bin/ruff check app/

# Format
.venv/bin/ruff format app/

# Check format
.venv/bin/ruff format --check app/
```

### Type Checking

```bash
.venv/bin/mypy app/
```

### ASCII Check

```bash
bash scripts/check-ascii.sh
```

### Coverage Ratchet

```bash
.venv/bin/python scripts/coverage_ratchet.py
```

### Pre-commit

```bash
pre-commit install
```

## Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

Tests use a temporary SQLite database that is automatically cleaned up. LM Studio is mocked — it does not need to be running.

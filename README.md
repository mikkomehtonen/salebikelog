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

## Ollama

Requires Ollama running locally with `qwen3.6-35b-a3b` model loaded:

```bash
ollama pull qwen3.6-35b-a3b
ollama serve
```

When running in Docker with Ollama on the host, `host.docker.internal` is used to reach it.

## Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

Tests use a temporary SQLite database that is automatically cleaned up. Ollama is mocked — it does not need to be running.

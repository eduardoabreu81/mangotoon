# MangoToon

MangoToon is a local-first manga library baseline built with FastAPI and a static vanilla frontend.

## Setup

```bash
uv sync --extra dev
```

If you are not using `uv`, install the runtime dependencies with:

```bash
python -m pip install -r requirements.txt
```

## Initialize Local Data

```bash
python scripts/init_data.py
```

This creates:

- `data/library.json`
- `data/history.json`
- `data/settings.json`
- `data/comics/`

Local data is ignored by Git.

## Run

```bash
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/` for the Library page.

## Test

```bash
uv run pytest
```

## Current Scope

Phase 0 only includes the installable backend package, health endpoint, static frontend serving, local data initialization, and tests. Downloading, source adapters, scraping, and MangaDex support are intentionally not implemented yet.

## Legal Note

This tool is for personal use only. It does not bypass paywalls, DRM, or authentication. Respect source terms of service.

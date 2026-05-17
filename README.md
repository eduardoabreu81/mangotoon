# 📖 MangoToon

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Local-first manga reader and downloader**

</div>

MangoToon is a local-first manga reader built with FastAPI and a static vanilla JS frontend. Paste a supported source URL, fetch metadata, download chapters for offline reading, and track your progress — all stored locally in JSON files.

No cloud sync. No accounts. No tracking. No React. No database.

---

## 📋 Table of Contents

- [What's New](#-whats-new)
- [Changelog](#-changelog)
- [Roadmap](#️-roadmap)
- [Features](#-features)
- [Setup](#-setup)
- [Run](#-run)
- [Test](#-test)
- [Project Structure](#-project-structure)
- [Legal Note](#-legal-note)

---

## 🆕 What's New

### Phase 13 — Universal Import Preview Flow

- **3-step import wizard** — URL → Preview → Confirm before adding to library
- **ImportPreview model** — shows title, cover, chapter count, source, languages, duplicate warning
- **POST /api/library/import/preview** — fetch metadata without saving
- **POST /api/library/import/confirm** — save with optional title override and auto-download toggle
- **Legacy /api/library/add preserved** — backward compatible

### Phase 17 — Download Integrity

- **Content-type validation** — rejects HTML, JSON, or other non-image responses
- **Magic bytes validation** — verifies JPEG, PNG, WEBP, GIF signatures
- **Failed pages tracking** — per-chapter list of failed page indices with error messages
- **Partial download accuracy** — succeeded pages saved, failed pages tracked, chapter status becomes `partial` or `error`
- **No retry on validation errors** — avoids wasting bandwidth on permanently invalid responses

### Phase 16 — Download Queue Reliability

- **Pause/resume/cancel event-based system** per job
- **Cancelled status** for chapters (not error)
- **Retry improvements** — works for `error`, `partial`, and `cancelled` chapters
- **Race condition fixes** — `_remove_queued_items` uses new queue to avoid `task_done` mismatch

### Phase 15 — Refresh Metadata

- **Refresh action** — re-fetch source metadata without losing downloaded content
- **POST /api/library/{comic_id}/refresh** — merge fresh metadata, preserve local state
- **Frontend context menu** — "Refresh Metadata" option with toast feedback

### Phase 14 — Packaging

- **Windows launcher** — `run.bat` checks Python/uv, installs dependencies, initializes data, starts the server, and opens the browser
- **Docker image** — Python 3.12 slim image with uv-managed dependencies
- **Docker Compose** — persistent local `data/` volume and port `8000:8000`

### Phase 12 — Source Capability Matrix

- **Adapter capabilities exposed via API** — each source declares what it supports
- **Frontend capability badges** — shown in Add Manga modal
- **SourceCapabilities model** — metadata, cover, chapters, download, languages, refresh, search, auth, javascript

### Phase 11 — Adapter-First Core Refactor

- **Removed MangaDex hardcodes from core** — source registry pattern
- **FakeSourceAdapter** for testing without network
- **Reader uses local_pages as source of truth**

### Phase 10 — Download Controls

- **Pause, resume, cancel downloads** — per-comic and per-chapter
- **Retry failed chapters** — granular retry endpoint
- **Download status polling** — real-time UI updates

### Phase 9 — Library UX Upgrade

- **Sidebar filters** — by status, source
- **Context menu** — quick actions on manga cards
- **Sort options** — title, updated, progress, status

### Phase 8 — Settings Page

- **Reader preferences** — fit mode, zoom, auto-advance
- **Download settings** — concurrency, rate limit
- **Appearance** — theme toggle

### Phase 7 — History Page

- **Last read tracking** — automatic on chapter close
- **Resume functionality** — continue from last page

### Phase 6 — Reader Polish

- **Fullscreen mode**
- **Fit modes** — width, height, original
- **Zoom controls**
- **Auto-advance**

### Phase 5 — Reader MVP

- **Offline chapter viewer** — serves local images
- **Keyboard navigation** — arrow keys, space
- **Progress save** — page and chapter tracking

---

## 📖 Changelog

### Phase 13 — Universal Import Preview Flow
- ImportPreview model with source, title, cover, chapter_count, languages, duplicate, warnings
- POST /api/library/import/preview — returns metadata without saving
- POST /api/library/import/confirm — saves with optional title override and auto-download
- Frontend 3-step wizard: URL → Preview → Confirm
- Typed request models (ImportPreviewRequest, ImportConfirmRequest)
- ImportConfirmResponse model
- Legacy /api/library/add preserved as wrapper

### Phase 17 — Download Integrity
- Content-type validation (reject HTML/JSON)
- Magic bytes validation (JPEG, PNG, WEBP, GIF)
- Failed pages tracking per chapter
- Partial download accuracy
- No retry on validation errors

### Phase 16 — Download Queue Reliability
- Pause/resume/cancel event-based system per job
- Cancelled status for chapters
- Retry works for error, partial, cancelled
- Race condition fixes in queue management

### Phase 15 — Refresh Metadata
- POST /api/library/{comic_id}/refresh endpoint
- Merge fresh metadata, preserve local state (local_pages, reading_progress)
- Frontend context menu with toast feedback

### Phase 14 — Packaging
- run.bat for Windows startup
- Dockerfile with uv-managed dependencies
- docker-compose.yml with data persistence
- Docker startup initializes local data before launching Uvicorn

### Phase 12 — Source Capability Matrix
- SourceCapabilities model (metadata, cover, chapters, download, languages, refresh, search, auth, javascript)
- Each adapter declares capabilities
- /api/sources returns real capabilities and domains
- Frontend displays capability badges in Add Manga modal

### Phase 11 — Adapter-First Core Refactor
- Removed MangaDex hardcodes from core services
- Source registry pattern with get_adapter_for_comic()
- FakeSourceAdapter for tests
- Reader uses local_pages as source of truth

### Phase 10 — Download Controls
- Pause, resume, cancel downloads (per-comic and per-chapter)
- Retry failed chapters
- Download status polling

### Phase 9 — Library UX Upgrade
- Sidebar filters, context menu, sort options

### Phase 8 — Settings Page
- Reader preferences, download settings, appearance

### Phase 7 — History Page
- Last read tracking, resume functionality

### Phase 6 — Reader Polish
- Fullscreen, fit modes, zoom, auto-advance

### Phase 5 — Reader MVP
- Offline chapter viewer, keyboard navigation, progress save

### Phase 4.5 — Stabilization
- Added `local_pages: list[str]` to Chapter model
- `download_manager` persists ordered relative paths for every downloaded page
- Failed page downloads now correctly mark chapter as `error` (0 pages) or `partial` (some pages)
- Removed ad-hoc `total_chapters` and `downloaded_chapters` from library.json
- Comic model validation remains stable after cleanup
- README updated to reflect Phases 0–4.5 scope

### Phase 4 — Download Manager
- Async download queue with configurable concurrency
- Per-domain rate limiting and retry with exponential backoff
- Cover and chapter image download
- Download progress polling in frontend
- Two-tier status lookup (in-memory job + metadata fallback)

### Phase 3 — Source Adapter (MangaDex as first supported source)
- Source adapter protocol with error types
- MangaDex metadata fetch (title, description, cover, chapters)
- Source registry for future multi-source support
- Add Manga modal with URL validation and duplicate detection

### Phase 2 — Library & Settings API
- Library CRUD endpoints
- Settings persistence
- History scaffold
- Frontend library grid with search and sort

### Phase 1 — Static Frontend
- Dark theme with purple accent
- Vanilla JS, no build step
- API client module
- Modal and form components

### Phase 0 — Baseline
- FastAPI app scaffold
- Health endpoint
- Static file serving
- Local data initialization script
- Pydantic models and test suite

---

## 🗺️ Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 0 | ✅ | Baseline — FastAPI, models, tests, static serving |
| 1 | ✅ | Static frontend — dark theme, vanilla JS |
| 2 | ✅ | Library & Settings API |
| 3 | ✅ | Source adapter — MangaDex as first supported source |
| 4 | ✅ | Download manager — async queue, retry, progress |
| 4.5 | ✅ | Stabilization — local page paths, partial download handling |
| 5 | ✅ | Reader MVP — offline chapter viewer, keyboard nav, progress save |
| 6 | ✅ | Reader polish — fullscreen, fit modes, zoom, auto-advance |
| 7 | ✅ | History page — last read tracking, resume |
| 8 | ✅ | Settings page — concurrency, rate limit, theme |
| 9 | ✅ | Library UX upgrade — sidebar, filters, context menu |
| 10 | ✅ | Download controls — pause, resume, cancel, retry |
| 11 | ✅ | Adapter-first core refactor — remove MangaDex hardcodes |
| 12 | ✅ | Source capability matrix — adapter capabilities exposed via API |
| 13 | ✅ | Universal import preview flow — source-agnostic metadata preview before download |
| 14 | ✅ | Packaging — run.bat, Dockerfile, docker-compose |
| 15 | ✅ | Refresh metadata — re-fetch without losing downloads |
| 16 | ✅ | Download queue reliability — pause/resume/cancel fixes |
| 17 | ✅ | **Download integrity** — content-type validation, magic bytes |
| 18 | 📋 | Backup and export |

---

## 🎯 Features

### 📚 Library
- Add manga by URL with 3-step preview wizard (MangaDex as first supported source)
- Preview metadata before import — title, cover, chapter count, duplicate warning
- Automatic metadata fetch and chapter download via source adapter
- Search, sort, and filter library by status and source
- Delete manga (removes local files)
- Download progress polling with status badges

### ⬇️ Download Manager
- Async queue with configurable concurrency (1–5)
- Per-domain rate limiting
- Exponential backoff retry
- Cover and chapter image download
- Pause, resume, cancel downloads
- Retry failed chapters

### 📖 Reader
- Offline chapter viewer — serves local images
- Keyboard navigation — arrow keys, space
- Progress save — page and chapter tracking
- Fullscreen mode
- Fit modes — width, height, original
- Zoom controls
- Auto-advance

### 🎨 UI
- Dark theme with purple accent (`#9b59b6`)
- Responsive grid layout
- Modal-based Add Manga flow with preview
- Real-time download status indicators
- Capability badges per source
- English UI throughout

---

## 🚀 Setup

### Windows

Double-click `run.bat`, or run it from Command Prompt:

```bat
run.bat
```

The launcher checks for Python and uv, installs dependencies, initializes local data, starts MangoToon, and opens `http://127.0.0.1:8000/`.

### Docker

```bash
docker compose up --build
```

Open `http://127.0.0.1:8000/`.

Docker Compose maps `./data` to `/app/data` so library metadata, history, settings, and downloaded chapters persist across container restarts.

### Manual

```bash
# Clone
git clone https://github.com/eduardoabreu81/mangotoon.git
cd mangotoon

# Install dependencies
uv sync --extra dev

# Or with pip
python -m pip install -r requirements.txt
```

### Initialize Local Data

```bash
python scripts/init_data.py
```

This creates:
- `data/library.json`
- `data/history.json`
- `data/settings.json`
- `data/comics/` — downloaded manga storage

Local data is ignored by Git.

---

## ▶️ Run

```bash
python scripts/init_data.py
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/` for the Library page.

---

## 🧪 Test

```bash
uv run pytest tests/ -v
```

---

## 📁 Project Structure

```
mangotoon/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── models/
│   │   └── comic.py         # Pydantic models (Comic, Chapter, ImportPreview, SourceCapabilities)
│   ├── routers/
│   │   ├── library.py       # Library CRUD + add/import preview/confirm
│   │   ├── downloads.py     # Download status endpoints
│   │   ├── reader.py        # Chapter serving + progress save
│   │   ├── history.py       # Reading history
│   │   ├── settings.py      # Settings CRUD
│   │   └── sources.py       # Source registry + detection + capabilities
│   ├── services/
│   │   ├── storage.py       # JSON atomic writes
│   │   ├── download_manager.py  # Async queue + retry
│   │   └── source_registry.py   # Adapter registry
│   └── sources/
│       ├── base.py          # SourceAdapter protocol
│       ├── mangadex.py      # MangaDex adapter
│       └── fake.py          # FakeSourceAdapter for tests
├── frontend/
│   ├── index.html           # Library page
│   ├── reader.html          # Reader page
│   ├── history.html         # History page
│   ├── settings.html        # Settings page
│   ├── css/style.css        # Dark theme
│   └── js/
│       ├── api.js           # API client
│       ├── app.js           # Library UI logic
│       ├── reader.js        # Reader UI logic
│       ├── history.js       # History UI logic
│       └── settings.js      # Settings UI logic
├── tests/                   # pytest suite (77 tests)
├── scripts/
│   └── init_data.py         # Local data bootstrap
├── data/                    # Local storage (gitignored)
└── README.md
```

---

## ⚖️ Legal Note

This tool is for personal use only. It does not bypass paywalls, DRM, or authentication. Respect source terms of service.

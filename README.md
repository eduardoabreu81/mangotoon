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

### Phase 4.5 — Stabilization

- **Chapter metadata now persists ordered local page paths** — the Reader will never have to guess filenames
- **Partial download handling improved** — failed pages mark chapters as `error` or `partial`, not `downloaded`
- **Library metadata cleaned** — `chapter_count` and `downloaded_count` are derived from chapters, not duplicated
- **README aligned with actual scope** — no more "Phase 0 only" confusion

---

## 📖 Changelog

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
| 4.5 | ✅ | **Stabilization — local page paths, partial download handling** |
| 5 | 🔄 | **Reader MVP — offline chapter viewer, keyboard nav, progress save** |
| 6 | 📋 | Reader polish — fullscreen, fit modes, zoom, auto-advance |
| 7 | 📋 | History page — last read tracking, resume |
| 8 | 📋 | Settings page — concurrency, rate limit, theme |
| 9 | 📋 | Library UX upgrade — sidebar, filters, context menu |
| 10 | 📋 | Download controls — pause, resume, cancel, retry |
| 11 | 📋 | **Source adapter quality layer** — MangaDex hardening, shared contract, capability matrix |
| 12 | 📋 | **Universal import preview flow** — source-agnostic metadata preview before download |
| 13 | 📋 | Packaging — run.bat, Dockerfile |
| 14 | 📋 | Backup and export |
| 15 | 📋 | Second source adapter |
| 16 | 📋 | Multi-source normalization |

---

## 🎯 Features

### 📚 Library
- Add manga by URL (MangaDex as first supported source)
- Automatic metadata fetch and chapter download via source adapter
- Search and sort library
- Delete manga (removes local files)
- Download progress polling with status badges

### ⬇️ Download Manager
- Async queue with configurable concurrency (1–5)
- Per-domain rate limiting
- Exponential backoff retry
- Cover and chapter image download
- Resume/retry incomplete downloads

### 🎨 UI
- Dark theme with purple accent (`#9b59b6`)
- Responsive grid layout
- Modal-based Add Manga flow
- Real-time download status indicators
- English UI throughout

---

## 🚀 Setup

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
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/` for the Library page.

---

## 🧪 Test

```bash
uv run pytest
```

---

## 📁 Project Structure

```
mangotoon/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── models/
│   │   └── comic.py         # Pydantic models
│   ├── routers/
│   │   ├── library.py       # Library CRUD + add/download
│   │   ├── downloads.py     # Download status endpoints
│   │   └── settings.py      # Settings CRUD
│   ├── services/
│   │   ├── storage.py       # JSON atomic writes
│   │   ├── download_manager.py  # Async queue + retry
│   │   └── source_registry.py   # Adapter registry
│   └── sources/
│       ├── base.py          # SourceAdapter protocol
│       └── mangadex.py      # MangaDex adapter
├── frontend/
│   ├── index.html           # Library page
│   ├── css/style.css        # Dark theme
│   └── js/
│       ├── api.js           # API client
│       └── app.js           # Library UI logic
├── tests/                   # pytest suite
├── scripts/
│   └── init_data.py         # Local data bootstrap
├── data/                    # Local storage (gitignored)
└── README.md
```

---

## ⚖️ Legal Note

This tool is for personal use only. It does not bypass paywalls, DRM, or authentication. Respect source terms of service.

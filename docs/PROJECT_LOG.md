# MangoToon — Project Log

> Internal change log for AI agents.
> **Never commit this file.**

---

## Project Identity

- **Name:** MangoToon
- **Purpose:** Local-first manga reader and library manager
- **Version:** v0.1.0
- **Stack:** FastAPI + Pydantic (backend), Vanilla JS (frontend), JSON storage
- **Status:** Phases 0-4.5 complete, Phase 5 (Reader MVP) next

---

## Backlog / Roadmap

| Phase | Status | Description |
|---|---|---|
| 0 | ✅ Complete | Baseline — FastAPI, models, tests, static serving |
| 1 | ✅ Complete | Static frontend — dark theme, vanilla JS |
| 2 | ✅ Complete | Library & Settings API |
| 3 | ✅ Complete | MangaDex adapter — metadata fetch |
| 4 | ✅ Complete | Download manager — async queue, retry, progress |
| 4.5 | ✅ Complete | Stabilization — local page paths, partial download, docs |
| 5 | 🔄 Next | Reader MVP — offline viewer, keyboard nav, progress save |
| 6 | ⏳ Planned | Reader polish — fullscreen, fit modes, zoom, auto-advance |
| 7 | ⏳ Planned | History page — last read tracking, resume |
| 8 | ⏳ Planned | Settings page — concurrency, rate limit, theme |
| 9 | ⏳ Planned | Library UX upgrade — sidebar, filters, context menu |
| 10 | ⏳ Planned | Download controls — pause, resume, cancel, retry |
| 11 | ⏳ Planned | MangaDex quality — language filter, dedup, data saver |
| 12 | ⏳ Planned | Import preview — metadata preview before download |
| 13 | ⏳ Planned | Packaging — run.bat, Dockerfile |
| 14 | ⏳ Planned | Backup and export |
| 15 | ⏳ Planned | Second source adapter |
| Documentation | ✅ Complete | AGENTS.md, PROJECT_LOG, TELEGRAM_HANDOFF |

---

## Log Entries

### 2026-05-16 — Phase 0-2 Completion + Multi-Agent Setup

**O que mudou (pt-BR):**

Fizemos o rebuild completo do projeto ComicLib (antigo) para MangoToon. Implementamos as Phases 0, 1 e 2 com arquitetura multi-agent.

**Features:**
- Backend FastAPI com endpoints de health, library e settings
- Storage JSON com atomic writes (temp + rename)
- Models Pydantic (Comic, Chapter, ReadingProgress, Settings)
- Frontend vanilla JS com grid de comics, search, sort, delete
- Modal Add Manga (shell para Phase 3)
- Dark theme com accent purple (#9b59b6)
- 11 testes passando

**Fixes:**
- Rename completo MangaToon → MangoToon em todos os arquivos
- Correção do data format (array → object com version)
- Correção de imports nos testes

**Chore:**
- Setup multi-agent com tmux (Claude manager, Codex backend, OpenCode frontend, Kimi review)
- Criação de AGENTS.md e PROJECT_LOG.md
- Commit com 44 arquivos alterados

**Arquivos alterados:**
- `app/__init__.py` — versão v0.1.0
- `app/main.py` — FastAPI com routers
- `app/core/config.py` — APP_NAME = "MangoToon"
- `app/models/comic.py` — Pydantic models
- `app/services/storage.py` — JSON atomic storage
- `app/routers/library.py` — GET/DELETE /api/library
- `app/routers/settings.py` — GET/POST /api/settings
- `frontend/index.html` — Library page com modal
- `frontend/css/style.css` — Dark design system
- `frontend/js/api.js` — API client
- `frontend/js/app.js` — Library UI
- `scripts/init_data.py` — Data initialization
- `tests/test_api.py` — Health tests
- `tests/test_init_data.py` — Data init tests
- `tests/test_library.py` — Library/settings tests
- `pyproject.toml` — Package config
- `.gitignore` — Python cache, data, etc.
- `.env.example` — Environment template
- `README.md` — Public docs
- `AGENTS.md` — Agent guide
- `TELEGRAM_HANDOFF.md` — Session continuity

**Decisões:**
- Usar tmux sessions para multi-agent (delegate_task falhou com 404)
- Claude como manager (orquestra), Codex/OpenCode como devs
- Hermes como devil's advocate + documentação
- Não usar SQLite ainda (JSON files para MVP)
- Vanilla JS only (sem frameworks)

**Pontos sensíveis:**
- Codex tem problema com sandbox (uv cache read-only) — usar python3 diretamente
- Claude CLI precisa do Bun para hooks
- OpenCode faz bom trabalho no frontend mas precisa de review
- Sempre validar APP_NAME = "MangoToon" em novos arquivos

**Próximos passos / Next steps:**
1. Phase 5: Reader MVP — image serving, navigation, progress tracking
2. Phase 6: Reader polish — fullscreen, fit modes, zoom, auto-advance
3. Phase 7: History page — last read tracking, resume
4. Phase 8: Settings page — full UI for configuration
5. Phase 9: Library UX upgrade — sidebar, filters, context menu
6. Phase 10: Download controls — pause, resume, cancel, retry
7. Phase 11: MangaDex quality — language filter, dedup, data saver
8. Phase 12: Import preview — metadata preview before download
9. Phase 13: Packaging — run.bat, Dockerfile
10. Phase 14: Backup and export
11. Phase 15: Second source adapter

---

## Phase 4.5 Log — 2026-05-17

**Stabilization — Download Metadata + Documentation**

**Backend (Hermes):**
- Added `local_pages: list[str]` to Chapter model
- Updated `download_manager._download_chapter` to persist ordered relative paths
- Improved partial download handling: failed pages → `error` (0 pages) or `partial` (some pages)
- Removed ad-hoc `total_chapters`/`downloaded_chapters` from library.json
- `_update_library_counts` now syncs chapters from metadata to library
- Comic model validation stable

**Docs:**
- Rewrote README.md with full scope, changelog, roadmap, project structure
- Aligned with actual Phases 0-4.5 implementation

**Frontend:**
- Added UI hint in Add Manga modal: "Adding a manga will fetch its metadata and start downloading chapters automatically."

**Tests:**
- 35/35 passing (3 new tests added)
- `test_chapter_status_persisted_after_download` — verifies local_pages persisted
- `test_partial_download_marks_chapter_error` — 0 pages → error status
- `test_partial_download_marks_chapter_partial` — some pages → partial status
- `test_library_response_validates_through_comic_model` — Comic model validation

**Commit:** `9dbc368` — 5 files changed, +246/-26 lines

---

## Phase 4 Log — 2026-05-17

**Download Manager + Progress Polling**

**Backend (dev_codex — gpt-5.5):**
- Created `app/services/download_manager.py` — async queue, rate limiting, retry
- Created `app/routers/downloads.py` — download status endpoints
- Added `get_chapter_pages` to SourceAdapter protocol and MangaDexAdapter
- Added `POST /api/library/{id}/download` and `/chapters/{chid}/download`
- Wired lifespan and downloads router in `app/main.py`
- Tests: 32 passed (23 existing + 9 new)

**Frontend (dev_opencode — DeepSeek V4 Pro):**
- Added download progress polling every 3 seconds
- Added Download button to manga cards (visible on hover)
- Added real-time progress bar and status badge updates
- Added `status-queued` CSS badge variant
- Preserved existing search, sort, delete, Add Manga functionality

**Commit:** `10f18f0` — 9 files changed, +714/-3 lines

---

## Phase 3 Log — 2026-05-17

**MangaDex Metadata Adapter + Add Manga Wiring**

**Backend (dev_codex — gpt-5.5):**
- Created `app/sources/base.py` — SourceAdapter protocol + error types
- Created `app/sources/mangadex.py` — MangaDex adapter using httpx
- Created `app/services/source_registry.py` — Source registry
- Implemented `POST /api/library/add` with duplicate prevention
- Added computed `chapter_count` and `downloaded_count` fields
- Tests: 23 passed in 2.09s

**Frontend (dev_opencode — DeepSeek V4 Pro):**
- Wired Add Manga modal to `POST /api/library/add`
- Added loading state, success, duplicate, error handling
- Added inline error message UI
- Preserved existing search, sort, delete functionality

**Commit:** `30e29b1` — 11 files changed, +684/-4 lines

---

## Sensitive Points

- **Never commit** `docs/`, `AGENTS.md`, `AGENTS.local.md`, or `.env`
- **Always check** app name is "MangoToon" in new files
- **Atomic writes** are required for all JSON file operations
- **Test isolation** — use tmp_path monkeypatch for storage tests
- **No hardcoded secrets** — use .env for API keys

---

## Agent Notes

### Multi-Agent Communication
- Manager reads specs and delegates via `tmux send-keys`
- Devs implement and report files changed
- Devil's advocate validates against SPEC_REBUILT.md
- All tests must pass before phase approval

### Tmux Sessions
```bash
tmux list-sessions
# manager  — Claude (orchestration)
# dev_codex — Codex (backend)
# dev_opencode — OpenCode (frontend)
# dev_kimi — Kimi (review)
```

### Useful Commands
```bash
# Run tests
uv run pytest tests/ -v

# Start server
uv run uvicorn app.main:app --reload

# Init data
python3 scripts/init_data.py

# Check tmux
tmux capture-pane -t <session> -p | tail -30
```

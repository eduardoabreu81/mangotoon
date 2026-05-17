# MangoToon — Handoff para Telegram

> Arquivo gerado em: 2026-05-17
> Para continuar pelo Telegram, envie: "continuar MangoToon"

---

## Estado Atual do Projeto

| Phase | Status | Detalhes |
|-------|--------|----------|
| p0 | ✅ Completo | Cleanup, baseline, tests |
| p1 | ✅ Completo | Storage service, library/settings API |
| p2 | ✅ Completo | Frontend grid, search, sort, modal |
| p3 | ✅ Completo | Source adapter — MangaDex as first supported source |
| p4 | ✅ Completo | Download manager + progress polling |
| p4.5 | ✅ Completo | Stabilization — local page paths, partial download, docs |
| p5 | ✅ Completo | Reader MVP — offline viewer, keyboard nav, progress save |
| p6 | 🔄 Next | Reader polish |
| p7 | ⏳ Pendente | History page |
| p8 | ⏳ Pendente | Settings page |
| p9 | ⏳ Pendente | Library UX upgrade |
| p10 | ⏳ Pendente | Download controls |
| p11 | ⏳ Pendente | Source adapter quality layer |
| p12 | ⏳ Pendente | Universal import preview flow |
| p13 | ⏳ Pendente | Packaging |
| p14 | ⏳ Pendente | Backup and export |
| p15 | ⏳ Pendente | Second source adapter |
| p16 | ⏳ Pendente | Multi-source normalization |

---

## Arquitetura de Agents

| Agent | Role | Model | Status |
|-------|------|-------|--------|
| **manager** (Claude) | Orquestração | Claude Sonnet 4.6 | ⏳ Disponível |
| **dev_codex** | Backend | gpt-5.5 | ⏳ Disponível |
| **dev_opencode** | Frontend | deepseek/deepseek-v4-pro | ⏳ Disponível |
| **dev_kimi** | Code review | kimi-k2.6 | ⏳ Disponível |
| **Hermes** (eu) | Devil's advocate + Docs | kimi-k2.6 | 👁️ Monitorando |

**Tmux sessions:**
```bash
# Iniciar quando necessário:
tmux new-session -d -s manager -n claude "claude"
tmux new-session -d -s dev_codex -n codex "codex"
tmux new-session -d -s dev_opencode -n opencode "opencode"
tmux new-session -d -s dev_kimi -n kimi "kimi"
```

---

## Arquivos Principais

### Backend
- `app/__init__.py` — v0.1.0
- `app/main.py` — FastAPI com lifespan, routers, /reader route
- `app/core/config.py` — Settings (APP_NAME = "MangoToon")
- `app/models/comic.py` — Pydantic models (Comic, Chapter, ReadingProgress, Settings, etc.)
- `app/services/storage.py` — JSON storage com atomic writes
- `app/services/source_registry.py` — Source registry
- `app/services/download_manager.py` — Async download queue, rate limiting, retry, local_pages persistence
- `app/sources/base.py` — SourceAdapter protocol
- `app/sources/mangadex.py` — MangaDex adapter (httpx)
- `app/routers/library.py` — GET/POST/DELETE /api/library
- `app/routers/downloads.py` — GET /api/downloads/status
- `app/routers/settings.py` — GET/POST /api/settings
- `app/routers/reader.py` — Reader endpoints (data, image serving, progress)
- `scripts/init_data.py` — Data initialization
- `pyproject.toml` — Package config

### Frontend
- `frontend/index.html` — Library page com modal Add Manga (wired)
- `frontend/reader.html` — Reader page (full viewport, top/bottom bars)
- `frontend/css/style.css` — Dark theme, purple accent #9b59b6, reader CSS
- `frontend/js/api.js` — API client (GET/POST/DELETE)
- `frontend/js/app.js` — Library grid, search, sort, delete, Add Manga, download polling, card click → reader
- `frontend/js/reader.js` — Reader logic: keyboard nav, tap zones, chapter selector, progress save

### Tests
- `tests/test_api.py` — Health e root
- `tests/test_init_data.py` — Data initialization
- `tests/test_library.py` — Library endpoints, settings, delete
- `tests/test_mangadex_adapter.py` — Mocked MangaDex adapter tests
- `tests/test_frontend_api.py` — Frontend API integration tests
- `tests/test_download_manager.py` — Download manager tests
- `tests/test_reader.py` — Reader tests (9 tests)

### Config
- `.gitignore` — Python cache, .env, data, uv.lock
- `.env.example` — Placeholders seguros
- `README.md` — Public docs (atualizado com scope real, source-agnostic language)
- `AGENTS.md` — Agent guide
- `docs/PROJECT_LOG.md` — Change log

---

## Testes

**Resultado:** 44/44 passam ✅ (Phase 5)
```
tests/test_api.py — 2 tests PASSED
tests/test_download_manager.py — 12 tests PASSED
tests/test_frontend_api.py — 4 tests PASSED
tests/test_init_data.py — 1 test PASSED
tests/test_library.py — 9 tests PASSED
tests/test_mangadex_adapter.py — 7 tests PASSED
tests/test_reader.py — 9 tests PASSED
```

---

## Próximo Passo: Phase 6 — Reader Polish

**Objetivo:** deixar o Reader confortável.

### Funcionalidades
- Auto-hide top/bottom bars
- Fullscreen toggle
- Fit modes: fit width, fit height, original
- Zoom simples: +, -, reset
- Mobile tap zones: esquerda 30% volta, direita 30% avança, centro alterna UI
- Keyboard: Esc volta, F fullscreen, Home primeira página, End última página
- Auto-advance para próximo capítulo
- Mensagem "Chapter complete"

### Aceitação
- Reader já parece produto, não demo técnica
- 44 testes existentes não quebram

---

## Notas Importantes

- **App name:** MangoToon (nunca MangaToon)
- **UI language:** English
- **Frontend:** Vanilla JS only (no React/Vue)
- **Backend:** FastAPI + Pydantic
- **Storage:** JSON files (não SQLite ainda)
- **Tests:** pytest + TestClient
- **Package manager:** uv
- **UV cache fix:** `export UV_CACHE_DIR=/tmp/uv-cache` (Codex sandbox)
- **Download behavior:** Add Manga = fetch metadata + auto-download. Download button = retry/resume.
- **Chapter metadata:** Now includes `local_pages: list[str]` with ordered relative paths
- **Source-agnostic:** MangaDex is "Source Adapter 001", not product identity

---

## Como Continuar pelo Telegram

1. Envie: `"continuar MangoToon"`
2. Ou: `"MangoToon Phase 6"`
3. O Hermes vai carregar este contexto e continuar

**Se precisar de ajuda:**
- `"status"` — mostra estado dos agents
- `"tmux"` — mostra sessions tmux
- `"testes"` — roda pytest
- `"Phase X"` — inicia próxima phase

---

## Skills de Documentação Disponíveis

Em `C:\Users\Eduardo\.config\agents\skills`:
- `daily-wrap` — End-of-day wrap-up
- `project-context` — Load project context
- `project-init` — Initialize project docs

**Quando usar:** Ao final de cada Phase, rodar daily-wrap para atualizar docs.

---

## Contato

- GitHub: eduardoabreu81/mangotoon
- Repo local: /mnt/c/Users/Eduardo/OneDrive/Documentos/GitHub/mangotoon

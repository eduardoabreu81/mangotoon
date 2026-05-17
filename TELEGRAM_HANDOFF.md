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
| p3 | ✅ Completo | MangaDex metadata adapter + Add Manga wiring |
| p4 | ✅ Completo | Download manager + progress polling |
| p5 | 🔄 Em andamento | Reader |
| p6 | ⏳ Pendente | Settings page |
| p7 | ⏳ Pendente | Polish e release readiness |

---

## Arquitetura de Agents

| Agent | Role | Model | Status |
|-------|------|-------|--------|
| **manager** (Claude) | Orquestração | Claude Sonnet 4.6 | 🔄 Rodando no tmux |
| **dev_codex** | Backend | gpt-5.5 | ⏳ Aguardando instruções do manager |
| **dev_opencode** | Frontend | deepseek/deepseek-v4-pro | ⏳ Aguardando instruções do manager |
| **dev_kimi** | Code review | kimi-k2.6 | ⏳ Disponível |
| **Hermes** (eu) | Devil's advocate | kimi-k2.6 | 👁️ Monitorando |

**Tmux sessions:**
```bash
dev_codex: 1 windows
dev_kimi: 1 windows
dev_opencode: 1 windows
manager: 1 windows (Claude ativo, orquestrando)
```

---

## Arquivos Principais

### Backend
- `app/__init__.py` — v0.1.0
- `app/main.py` — FastAPI com lifespan, routers
- `app/core/config.py` — Settings (APP_NAME = "MangoToon")
- `app/models/comic.py` — Pydantic models (Comic, Chapter, ReadingProgress, Settings, etc.)
- `app/services/storage.py` — JSON storage com atomic writes
- `app/services/source_registry.py` — Source registry
- `app/services/download_manager.py` — Async download queue, rate limiting, retry
- `app/sources/base.py` — SourceAdapter protocol
- `app/sources/mangadex.py` — MangaDex adapter (httpx)
- `app/routers/library.py` — GET/POST/DELETE /api/library
- `app/routers/downloads.py` — GET /api/downloads/status
- `app/routers/settings.py` — GET/POST /api/settings
- `scripts/init_data.py` — Data initialization
- `pyproject.toml` — Package config

### Frontend
- `frontend/index.html` — Library page com modal Add Manga (wired)
- `frontend/reader.html` — Placeholder
- `frontend/css/style.css` — Dark theme, purple accent #9b59b6
- `frontend/js/api.js` — API client (GET/POST/DELETE)
- `frontend/js/app.js` — Library grid, search, sort, delete, Add Manga, download polling
- `frontend/js/reader.js` — Placeholder

### Tests
- `tests/test_api.py` — Health e root
- `tests/test_init_data.py` — Data initialization
- `tests/test_library.py` — Library endpoints, settings, delete
- `tests/test_mangadex_adapter.py` — Mocked MangaDex adapter tests
- `tests/test_frontend_api.py` — Frontend API integration tests
- `tests/test_download_manager.py` — Download manager tests

### Config
- `.gitignore` — Python cache, .env, data, uv.lock
- `.env.example` — Placeholders seguros
- `README.md` — Public docs
- `AGENTS.md` — Agent guide
- `docs/PROJECT_LOG.md` — Change log

---

## Testes

**Resultado:** 32/32 passam ✅ (Phase 4)
```
tests/test_api.py::test_health_returns_ok PASSED
tests/test_api.py::test_root_serves_library_page PASSED
tests/test_init_data.py::test_init_data_creates_expected_files PASSED
tests/test_library.py::TestLibrary::test_library_empty_on_fresh_install PASSED
tests/test_library.py::TestLibrary::test_get_comic_not_found PASSED
tests/test_library.py::TestLibrary::test_delete_comic_not_found PASSED
tests/test_library.py::TestLibrary::test_library_with_comic PASSED
tests/test_library.py::TestLibrary::test_get_comic_detail PASSED
tests/test_library.py::TestSettings::test_get_settings PASSED
tests/test_library.py::TestSettings::test_post_settings PASSED
tests/test_library.py::TestSettings::test_post_settings_invalid_concurrency PASSED
tests/test_mangadex_adapter.py — 6 tests PASSED
tests/test_frontend_api.py — 4 tests PASSED
tests/test_download_manager.py — 9 tests PASSED
```

---

## Próximo Passo: Phase 5 — Reader

**Prompt:** `codex_manga_app_phase_prompts/CODEX_PHASE_05_reader.txt`

**O que precisa ser feito:**
1. Rota `GET /reader/{comic_id}/{chapter_id}/{page}` para servir imagens locais
2. Rota `GET /reader/{comic_id}/progress` — get reading progress
3. Rota `POST /reader/{comic_id}/progress` — save reading progress
4. Integrar `frontend/reader.html` com navegação real
5. Keyboard shortcuts (left/right arrow, escape, F)
6. Click zones (left prev, right next, center toggle controls)
7. Chapter selector, progress bar
8. Save/restore reading progress
9. Handle missing images
10. Tests

**Aceitação:**
- Usuário clica em manga card → abre reader
- Reader carrega última página lida
- Navegação por teclado, click, e botões
- Progresso salvo automaticamente
- Próxima sessão resume do ponto certo
- Tests passam

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

---

## Como Continuar pelo Telegram

1. Envie: `"continuar MangoToon"`
2. Ou: `"MangoToon Phase 5"`
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

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
| p3 | 🔄 Em andamento | MangaDex metadata adapter |
| p4 | ⏳ Pendente | Download manager |
| p5 | ⏳ Pendente | Reader |
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
manager: 1 windows (Claude ativo, lendo specs)
```

---

## Arquivos Principais Criados

### Backend
- `app/__init__.py` — v0.1.0
- `app/main.py` — FastAPI com health, static files, routers
- `app/core/config.py` — Settings (APP_NAME = "MangoToon")
- `app/models/comic.py` — Pydantic models (Comic, Chapter, ReadingProgress, Settings, etc.)
- `app/services/storage.py` — JSON storage com atomic writes
- `app/routers/library.py` — GET/DELETE /api/library
- `app/routers/settings.py` — GET/POST /api/settings
- `scripts/init_data.py` — Inicialização de dados
- `pyproject.toml` — packages=["app"]

### Frontend
- `frontend/index.html` — Library page com modal Add Manga
- `frontend/reader.html` — Placeholder
- `frontend/css/style.css` — Dark theme, purple accent #9b59b6
- `frontend/js/api.js` — API client (GET/POST/DELETE)
- `frontend/js/app.js` — Library grid, search, sort, delete
- `frontend/js/reader.js` — Placeholder

### Tests
- `tests/test_api.py` — Health e root
- `tests/test_init_data.py` — Data initialization
- `tests/test_library.py` — Library endpoints, settings, delete

### Config
- `.gitignore` — Python cache, .env, data, uv.lock
- `.env.example` — Placeholders seguros
- `README.md` — Setup, run, test

---

## Testes

**Resultado:** 11/11 passam ✅
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
```

---

## Próximo Passo: Phase 3 — MangaDex Metadata Adapter

**Prompt:** `codex_manga_app_phase_prompts/CODEX_PHASE_03_mangadex_metadata_adapter.txt`

**O que precisa ser feito:**
1. Criar `app/services/mangadex.py` — adapter para API do MangaDex
2. Criar `app/routers/search.py` — POST /api/search (busca por título)
3. Criar `app/routers/import.py` — POST /api/import (importa metadados)
4. Atualizar frontend/js/app.js — conectar modal Add Manga ao endpoint
5. Adicionar tests para MangaDex adapter

**Aceitação:**
- Busca por título retorna resultados do MangaDex
- Importação cria comic no library.json
- Frontend mostra resultados de busca
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

---

## Como Continuar pelo Telegram

1. Envie: `"continuar MangoToon"`
2. Ou: `"MangoToon Phase 3"`
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

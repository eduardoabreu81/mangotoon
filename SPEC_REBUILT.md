# MangaToon, Local Manga Library

> Working name: MangaToon  
> Status: MVP specification for Codex implementation  
> Last updated: 2026-05-16  
> Stack: Python, FastAPI, Vanilla JavaScript, HTML, CSS  
> Primary source for MVP: MangaDex  
> Product principle: local-first, private, offline reading

## Important naming note

MangaToon is a working name only. Before any public release, rename the product because there is already a public MangaToon manga/comics platform and mobile app.

For implementation, keep the repository name and internal package name as `mangotoon` unless the project is renamed later. Avoid hardcoding the visible product name in many places. Use a single app settings constant.

---

## 1. Executive Summary

MangaToon is a local manga reader and downloader.

The user pastes a supported manga URL. The app fetches metadata, downloads chapters to the local machine, and serves a clean web reader for offline reading.

There are no accounts, no cloud sync, no subscriptions, no ads, and no tracking. The user's library, reading progress, settings, covers, chapters, and history stay on the local machine.

The first supported source is MangaDex because it has a public API and does not require JavaScript scraping for the MVP.

---

## 2. Problem

Manga readers often need to repeat the same annoying flow:

1. Open a browser.
2. Visit a manga site.
3. Find the series.
4. Deal with ads, pop-ups, redirects, or slow loading.
5. Wait for lazy-loaded images.
6. Remember where they stopped.
7. Repeat this for every reading session.

Most online readers are built around the website experience, not the user's personal offline library.

The MVP solves this by creating a local, private manga library with persistent reading progress.

---

## 3. Product Goals

### MVP goals

- Add a manga from a supported URL.
- Download metadata, cover, chapters, and page images.
- Store all downloaded content locally.
- Show a polished manga library in a browser UI.
- Let the user read downloaded chapters offline.
- Save and restore reading progress.
- Show download status and errors clearly.
- Keep configuration local.

### Non-goals for MVP

- No user accounts.
- No cloud sync.
- No public hosting requirement.
- No mobile native app.
- No paid source bypass.
- No DRM bypass.
- No generic scraper for every manga website.
- No LLM-dependent workflow.
- No multi-user server mode.

---

## 4. Target User

Individual manga, manhwa, or comic readers who want a clean local library and offline reading.

Primary audience for the first version:

- Desktop users.
- Readers who already use sites like MangaDex.
- Users who prefer local files over cloud services.
- Users who want progress tracking without accounts.

The UI language should be English.

---

## 5. Core Principles

1. Local-first  
   All library data is stored on the user's machine.

2. Privacy by default  
   No tracking, analytics, telemetry, or accounts.

3. Offline reading  
   Once downloaded, chapters should open without internet.

4. Clear source boundaries  
   The MVP supports MangaDex only. More sources can be added later through adapters.

5. No hidden magic  
   Downloads, failures, retries, and source limitations must be visible.

6. Simple stack  
   FastAPI backend, static frontend, JSON storage first.

7. Legal and ethical boundary  
   The app must not bypass paywalls, DRM, authentication walls, or technical access restrictions.

---

## 6. MVP Scope

The MVP has four main screens:

1. Library
2. Add Manga modal
3. Reader
4. Settings

History can be implemented as part of progress data first. A dedicated History page is useful, but not required before the core library and reader work.

---

## 7. User Flows

### 7.1 Add manga

1. User opens the Library page.
2. User clicks Add Manga.
3. User pastes a MangaDex title URL.
4. Frontend calls `POST /api/library/add`.
5. Backend detects the source as MangaDex.
6. Backend fetches title metadata, cover, and chapter list.
7. Backend creates a local comic folder.
8. Backend starts a background download job.
9. UI shows a card with status `downloading`.
10. UI polls download status every 3 seconds.
11. When complete, the card status changes to `complete`.

### 7.2 Read manga

1. User clicks a manga card.
2. App opens the reader.
3. Reader loads the last-read chapter and page if available.
4. User navigates with keyboard, click zones, or buttons.
5. Progress is saved after page changes.
6. When the last page of a chapter is reached, the chapter is marked complete.
7. Next session resumes from the saved page.

### 7.3 Delete manga

1. User opens the card context menu or manga detail controls.
2. User clicks Delete.
3. App shows a confirmation modal.
4. Backend deletes the local folder and metadata entry.
5. Library refreshes.

### 7.4 Refresh metadata

1. User clicks Refresh.
2. Backend re-fetches manga metadata and chapter list.
3. Existing downloaded chapters are kept.
4. New chapters are added as not downloaded.
5. Cover and title are updated only when the source returns valid data.

---

## 8. Functional Requirements

## 8.1 Library

The Library page must show:

- Responsive manga grid.
- Cover image.
- Title.
- Source badge.
- Download status.
- Reading progress.
- Chapter count.
- Last-read timestamp if available.
- Empty state when no manga exists.
- Search by title.
- Sort by:
  - Last read
  - Recently added
  - Title A to Z
  - Download progress

For MVP, filters can be simple. Do not overbuild.

Required actions:

- Add manga.
- Open reader.
- Refresh metadata.
- Delete manga.
- Download missing chapters.

---

## 8.2 Add Manga modal

Fields:

- URL input.
- Detected source display.
- Optional title override.
- Add button.
- Cancel button.

Validation:

- URL is required.
- Unsupported site returns a clear error.
- Invalid MangaDex URL returns a clear error.
- Duplicate manga should not create a second library item.

Duplicate handling:

- If source URL or source ID already exists, return the existing comic ID and show a friendly message.

---

## 8.3 Reader

Reader requirements:

- Full viewport dark background.
- Page image centered.
- Fit image to screen by default.
- Keyboard navigation:
  - Left arrow: previous page.
  - Right arrow: next page.
  - Escape: return to library.
  - F: toggle fullscreen.
  - Plus: zoom in.
  - Minus: zoom out.
- Click zones:
  - Left side: previous page.
  - Right side: next page.
  - Center: show or hide controls.
- Top bar:
  - Back button.
  - Manga title.
  - Chapter title.
  - Page indicator.
- Bottom bar:
  - Previous chapter.
  - Next chapter.
  - Chapter selector.
  - Progress bar.
- Save progress on page change.
- Restore progress on reopen.
- Handle missing image files with a visible error.

Mobile support:

- Responsive layout.
- Swipe left and right.
- Tap zones.
- Pinch zoom can be future work if it complicates MVP.

---

## 8.4 Settings

Settings page requirements:

- Library path.
- Download concurrency.
- Rate limit per domain.
- Theme value, dark by default.
- Optional LLM settings, disabled by default.

MVP settings should be stored in `settings.json`.

Do not store API keys in repository files.

If LLM settings are implemented, keep them optional and clearly separated from the core manga workflow.

---

## 8.5 Download Manager

Requirements:

- Async download queue.
- Default concurrency: 2 chapter downloads.
- Domain rate limit: 1 request per second.
- Retry failed page downloads up to 3 times.
- Use exponential backoff.
- Persist progress after each chapter.
- Resume partially downloaded manga.
- Never block the FastAPI request while downloading full manga.
- Track job status in memory and persist chapter status to metadata.

Download statuses:

- `queued`
- `metadata_fetching`
- `downloading`
- `complete`
- `partial`
- `error`

Chapter statuses:

- `not_downloaded`
- `queued`
- `downloading`
- `downloaded`
- `error`

---

## 8.6 MangaDex Adapter

MVP source adapter: MangaDex.

Responsibilities:

- Detect MangaDex title URLs.
- Extract MangaDex title ID.
- Fetch manga metadata.
- Fetch cover art.
- Fetch chapter list.
- Filter chapters by language, default English.
- Resolve chapter page image URLs.
- Return normalized metadata to the app.

MangaDex adapter must be isolated behind a common source interface so new sources can be added later.

Suggested interface:

```python
class SourceAdapter(Protocol):
    source_name: str

    def can_handle(self, url: str) -> bool:
        ...

    async def get_manga(self, url: str) -> MangaMetadata:
        ...

    async def get_chapters(self, manga_id: str, language: str = "en") -> list[ChapterMetadata]:
        ...

    async def get_chapter_pages(self, chapter_id: str) -> list[PageImage]:
        ...
```

---

## 9. API Specification

Base URL: `/api`

### Library

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/library` | List local manga library |
| GET | `/library/{comic_id}` | Get one manga with metadata and chapters |
| POST | `/library/add` | Add manga by URL and start background download |
| DELETE | `/library/{comic_id}` | Delete manga and local files |
| POST | `/library/{comic_id}/refresh` | Refresh metadata |
| POST | `/library/{comic_id}/download` | Download all missing chapters |

### Chapters

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/library/{comic_id}/chapters` | List chapters |
| POST | `/library/{comic_id}/chapters/{chapter_id}/download` | Download one chapter |

### Reader

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/reader/{comic_id}/{chapter_id}/{page_number}` | Serve local page image |
| GET | `/reader/{comic_id}/progress` | Get reading progress |
| POST | `/reader/{comic_id}/progress` | Save reading progress |

### Downloads

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/downloads/{comic_id}/status` | Get manga download status |
| GET | `/downloads` | List active download jobs |

### Settings

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/settings` | Get local settings |
| POST | `/settings` | Update local settings |

### Health

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Return app status |

---

## 10. Data Architecture

## 10.1 Local folder structure

```text
data/
├── library.json
├── history.json
├── settings.json
└── comics/
    └── {comic_id}/
        ├── metadata.json
        ├── cover.jpg
        └── chapters/
            └── {chapter_id}/
                ├── 001.jpg
                ├── 002.jpg
                └── 003.jpg
```

Use `data/` as the default local app directory for the project. This keeps generated files out of source code folders.

The user can later change the library path through settings.

---

## 10.2 `library.json`

```json
{
  "version": 1,
  "comics": [
    {
      "id": "uuid",
      "title": "Example Manga",
      "source": "mangadex",
      "source_id": "mangadex-title-id",
      "source_url": "https://mangadex.org/title/...",
      "cover_path": "data/comics/uuid/cover.jpg",
      "status": "downloading",
      "total_chapters": 120,
      "downloaded_chapters": 15,
      "last_read_at": null,
      "created_at": "2026-05-16T12:00:00Z",
      "updated_at": "2026-05-16T12:10:00Z"
    }
  ]
}
```

---

## 10.3 `metadata.json`

```json
{
  "id": "uuid",
  "title": "Example Manga",
  "description": "Short description from source.",
  "source": "mangadex",
  "source_id": "mangadex-title-id",
  "source_url": "https://mangadex.org/title/...",
  "original_language": "ja",
  "content_rating": "safe",
  "cover_url": "https://...",
  "cover_path": "cover.jpg",
  "status": "downloading",
  "chapters": [
    {
      "id": "mangadex-chapter-id",
      "number": "1",
      "title": "Chapter title",
      "language": "en",
      "pages": 22,
      "status": "downloaded",
      "path": "chapters/mangadex-chapter-id",
      "downloaded_at": "2026-05-16T12:10:00Z"
    }
  ],
  "reading_progress": {
    "chapter_id": "mangadex-chapter-id",
    "page_number": 8,
    "completed_chapters": [],
    "last_read_at": "2026-05-16T13:00:00Z"
  },
  "errors": [],
  "created_at": "2026-05-16T12:00:00Z",
  "updated_at": "2026-05-16T13:00:00Z"
}
```

---

## 10.4 `settings.json`

```json
{
  "version": 1,
  "library_path": "./data/comics",
  "download_concurrency": 2,
  "rate_limit_per_domain": 1,
  "chapter_language": "en",
  "theme": "dark",
  "llm": {
    "enabled": false,
    "provider": "",
    "api_key": "",
    "base_url": "",
    "model": "",
    "max_tokens": 2048,
    "temperature": 0.2
  }
}
```

---

## 10.5 `history.json`

```json
{
  "version": 1,
  "items": [
    {
      "comic_id": "uuid",
      "title": "Example Manga",
      "cover_path": "data/comics/uuid/cover.jpg",
      "chapter_id": "chapter-id",
      "chapter_number": "12",
      "page_number": 5,
      "last_read_at": "2026-05-16T13:00:00Z"
    }
  ]
}
```

Keep the latest 20 history items.

---

## 11. Suggested Project Structure

```text
mangotoon/
├── README.md
├── SPEC.md
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── paths.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── comic.py
│   │   ├── settings.py
│   │   └── download.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── library.py
│   │   ├── reader.py
│   │   ├── downloads.py
│   │   ├── settings.py
│   │   └── health.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── storage.py
│   │   ├── library_service.py
│   │   ├── progress_service.py
│   │   ├── download_manager.py
│   │   └── source_registry.py
│   └── sources/
│       ├── __init__.py
│       ├── base.py
│       └── mangadex.py
├── frontend/
│   ├── index.html
│   ├── reader.html
│   ├── settings.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── api.js
│       ├── app.js
│       ├── reader.js
│       └── settings.js
├── tests/
│   ├── __init__.py
│   ├── test_health.py
│   ├── test_storage.py
│   ├── test_library_api.py
│   ├── test_progress.py
│   └── test_mangadex_adapter.py
└── scripts/
    └── init_data.py
```

---

## 12. Frontend Design System

## 12.1 Visual direction

Dark, focused, manga-library aesthetic.

Reference feel:

- MangaDex-like density.
- Tachiyomi-like local library logic.
- Clean cards.
- Strong cover art.
- Minimal chrome while reading.

---

## 12.2 Colors

```css
:root {
  --bg-primary: #0f0f17;
  --bg-secondary: #1a1a2e;
  --bg-card: #22223a;
  --bg-elevated: #2a2a45;
  --text-primary: #e8e8f0;
  --text-secondary: #8888a8;
  --text-muted: #55556a;
  --accent: #9b59b6;
  --accent-hover: #b06ed8;
  --accent-glow: rgba(155, 89, 182, 0.25);
  --success: #4ade80;
  --warning: #fbbf24;
  --danger: #ef4444;
  --border: #2e2e4a;
  --border-focus: #9b59b6;
}
```

---

## 12.3 Layout

Library:

- Left sidebar on desktop.
- Top toolbar with search, sort, add button.
- Main grid with manga cards.
- Mobile layout collapses sidebar into top menu.

Reader:

- Black background.
- Image-first.
- Auto-hiding controls.
- Large click zones.
- Minimal text.

Settings:

- Simple form sections.
- Clear save button.
- Clear validation messages.

---

## 12.4 Components

### Manga card

Required elements:

- Cover.
- Status badge.
- Title.
- Source.
- Chapter progress.
- Progress bar.

Interactions:

- Click opens reader.
- Right-click opens context menu.
- Hover lifts card slightly and shows accent glow.

### Buttons

Variants:

- Primary.
- Secondary.
- Danger.
- Ghost.

### Modals

Use one reusable modal pattern.

Required modals:

- Add Manga.
- Delete confirmation.
- Error details if needed.

### Toasts

Use small toast notifications for:

- Added manga.
- Deleted manga.
- Download started.
- Download completed.
- Error.

---

## 13. Backend Implementation Notes

## 13.1 FastAPI

The backend must:

- Serve API routes under `/api`.
- Serve static frontend files.
- Return `index.html` for `/`.
- Return `reader.html` for `/reader`.
- Return `settings.html` for `/settings`.
- Mount static assets from `/static`.

Suggested command:

```bash
uv run uvicorn app.main:app --reload
```

Acceptable fallback:

```bash
python -m uvicorn app.main:app --reload
```

---

## 13.2 Storage

Use JSON files for MVP.

Storage service must provide safe read/write helpers:

- Create data directories if missing.
- Use UTF-8.
- Use atomic writes.
- Handle missing files by creating defaults.
- Avoid corrupting JSON if the app stops mid-write.

Do not use SQLite in MVP unless explicitly requested later.

---

## 13.3 Error handling

API errors must return structured JSON:

```json
{
  "error": {
    "code": "unsupported_source",
    "message": "This URL is not supported yet.",
    "details": {}
  }
}
```

Common error codes:

- `invalid_url`
- `unsupported_source`
- `duplicate_manga`
- `source_unavailable`
- `metadata_fetch_failed`
- `chapter_download_failed`
- `comic_not_found`
- `chapter_not_found`
- `page_not_found`
- `settings_invalid`

---

## 13.4 Tests

Minimum tests:

- Health endpoint returns OK.
- Storage initializes defaults.
- Add Manga rejects invalid URL.
- Add Manga rejects unsupported source.
- Progress save and load works.
- Library list returns expected structure.
- Delete removes metadata entry.
- MangaDex URL detection works.
- Source registry selects MangaDex adapter.
- Reader page endpoint returns 404 for missing page.

Do not require live MangaDex network calls in unit tests. Mock network calls.

---

## 14. Implementation Phases for Codex

## Phase 0, Cleanup and baseline

Goal: make the repo installable and runnable.

Tasks:

- Fix package structure.
- Fix imports.
- Add missing dependencies.
- Add `.gitignore`.
- Add `.env.example`.
- Add basic README.
- Add health endpoint.
- Add static frontend serving.
- Add `scripts/init_data.py`.

Acceptance:

- `uv run uvicorn app.main:app --reload` starts.
- `/api/health` returns OK.
- `/` loads a basic Library page.
- Tests run.

---

## Phase 1, Local storage and library API

Goal: implement local JSON storage and library endpoints.

Tasks:

- Create storage service.
- Create Pydantic models.
- Implement `GET /api/library`.
- Implement `GET /api/library/{comic_id}`.
- Implement `DELETE /api/library/{comic_id}`.
- Implement settings load/save.
- Add tests.

Acceptance:

- App creates `data/library.json`, `data/history.json`, and `data/settings.json`.
- Library endpoint returns empty list on fresh install.
- Delete handles missing IDs cleanly.
- Settings are persisted.

---

## Phase 2, Frontend library UI

Goal: create the polished library screen.

Tasks:

- Build CSS design system.
- Build responsive library grid.
- Build empty state.
- Build search and sort.
- Build manga card component.
- Build Add Manga modal shell.
- Build context menu.

Acceptance:

- Library looks polished.
- Empty library has a clear call to action.
- Search and sort work on local data.
- No broken console errors.

---

## Phase 3, MangaDex metadata adapter

Goal: add real MangaDex metadata import.

Tasks:

- Add source adapter interface.
- Add MangaDex adapter.
- Extract title ID from MangaDex URLs.
- Fetch metadata.
- Fetch cover.
- Fetch chapter list.
- Normalize data.
- Save local metadata.

Acceptance:

- Pasting a valid MangaDex title URL creates a manga entry.
- Title, cover, and chapter list are saved.
- Duplicate URL does not create duplicate manga.
- Errors are clear.

---

## Phase 4, Download manager

Goal: download chapters and pages locally.

Tasks:

- Implement async download queue.
- Download cover image.
- Download page images by chapter.
- Persist chapter status.
- Add retry and rate limiting.
- Add download status endpoint.
- Add frontend polling.

Acceptance:

- Manga card shows progress.
- Download continues after add request returns.
- Downloaded pages exist on disk.
- Failed chapters are marked `error`.
- Refreshing the page keeps progress.

---

## Phase 5, Reader

Goal: read downloaded chapters offline.

Tasks:

- Implement page image endpoint.
- Build reader UI.
- Add keyboard navigation.
- Add click zones.
- Add chapter selector.
- Add progress save/load.
- Add completed chapter tracking.

Acceptance:

- User can open a manga and read pages.
- Progress saves after navigation.
- Reopening resumes the last page.
- Reader works without internet for downloaded chapters.

---

## Phase 6, Settings

Goal: make local configuration editable.

Tasks:

- Build settings page.
- Connect settings API.
- Allow library path update.
- Allow concurrency update.
- Allow language update.
- Keep LLM settings hidden or disabled unless implemented.

Acceptance:

- Settings save and reload.
- Invalid settings show validation errors.
- No API key appears in git-tracked files.

---

## Phase 7, Polish

Goal: make the app feel usable.

Tasks:

- Toast notifications.
- Better error states.
- Skeleton loading.
- Mobile layout improvements.
- README with screenshots placeholders.
- Keyboard shortcut help.
- Final test pass.

Acceptance:

- Core flow feels complete.
- No obvious broken UI paths.
- README explains setup, run, and limitations.
- Tests pass.

---

## 15. Codex Working Rules

When Codex implements this project:

1. Work in small commits or clear steps.
2. Do not rewrite the whole project blindly.
3. Keep the MVP focused on MangaDex first.
4. Do not implement generic scraping before MangaDex works.
5. Do not add a database unless requested.
6. Do not add React, Vue, Next.js, or a frontend build step.
7. Use Vanilla JavaScript.
8. Keep UI files simple and readable.
9. Mock external network calls in tests.
10. Keep generated library data out of git.
11. Keep all code, filenames, comments, docs, and UI labels in English.
12. Do not store API keys in committed files.
13. Do not add cloud sync, login, or telemetry.
14. Do not bypass paywalls, DRM, or protected content.
15. After each phase, run tests and report what changed.

---

## 16. Definition of Done

The MVP is done when:

1. The app starts locally with FastAPI.
2. The Library page loads in the browser.
3. User can paste a MangaDex title URL.
4. The app creates a local manga entry.
5. Cover and metadata appear in the Library.
6. Chapters can be downloaded locally.
7. Download status is visible.
8. User can open the Reader.
9. Reader displays downloaded pages.
10. Keyboard navigation works.
11. Reading progress is saved.
12. Reading progress is restored.
13. User can delete a manga.
14. Settings are persisted locally.
15. Tests pass.
16. README explains setup and usage.
17. No generated library files are committed.
18. No secrets are committed.

---

## 17. Future Roadmap

Only after the MVP works:

### v0.2

- History page.
- Better chapter management.
- Manual chapter selection.
- Batch pause/resume.
- Cover refresh.
- Import existing local folders.

### v0.3

- Mangapark adapter.
- HTML scraper utilities.
- Source-specific rate limits.
- Better failed-download recovery.

### v0.4

- Optional Playwright fallback for JS-heavy sites.
- Optional LLM-assisted unknown-site analysis.
- Advanced settings for providers.

### v0.5

- EPUB/CBZ export.
- Library backup and restore.
- Tags and collections.
- Multi-language UI.

---

## 18. README Outline

The README should include:

1. What the app does.
2. What it does not do.
3. Supported sources.
4. Screenshots placeholder.
5. Requirements.
6. Installation.
7. Running the app.
8. Adding a manga.
9. Local data location.
10. Settings.
11. Limitations.
12. Legal and ethical note.
13. Development commands.
14. Test commands.
15. Roadmap.

---

## 19. Legal and Ethical Note

This app is intended for personal offline access to content available through supported sources and their permitted access methods.

The app must not be designed to bypass:

- Paywalls.
- DRM.
- Authentication restrictions.
- Region restrictions.
- Technical anti-access measures.

Users are responsible for respecting the terms of service and copyright rules of each source.

---

## 20. First Codex Task

Use this as the first implementation task:

```text
Read SPEC.md carefully.

Implement Phase 0 only.

Goal: make the repository installable and runnable with a clean FastAPI backend and static frontend serving.

Requirements:
1. Fix Python package structure.
2. Add or fix pyproject.toml and requirements.txt.
3. Add app/main.py with FastAPI app.
4. Add /api/health endpoint.
5. Serve frontend/index.html at /.
6. Mount frontend assets under /static.
7. Add scripts/init_data.py to create data/library.json, data/history.json, and data/settings.json.
8. Add .gitignore for Python cache, virtualenvs, .env, and local data/comics.
9. Add README.md with setup and run commands.
10. Add minimal tests for health endpoint and data initialization.

Do not implement MangaDex yet.
Do not implement downloading yet.
Do not add React or any build step.
Keep all code and docs in English.

After finishing, report:
- Files changed.
- Commands run.
- Test results.
- Any issues found.
```

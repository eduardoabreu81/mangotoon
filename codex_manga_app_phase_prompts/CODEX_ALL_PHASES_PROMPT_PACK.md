# Codex Implementation Prompt Pack

Working product name: APP_NAME. Replace this placeholder only after the final name is chosen.

Use these prompts one phase at a time. Do not send all phases together. Codex should finish a phase, run tests, report results, and only then receive the next phase.

Global rules for every phase:

- Read `SPEC.md` before making changes.
- Keep code, filenames, comments, docs, and UI labels in English.
- Use Python, FastAPI, Vanilla JavaScript, HTML, and CSS.
- Do not add React, Vue, Next.js, Svelte, Tailwind, or frontend build tooling.
- Use local JSON storage first. Do not add SQLite unless explicitly requested later.
- Do not add accounts, cloud sync, telemetry, analytics, subscriptions, or tracking.
- Do not bypass paywalls, DRM, authentication walls, mature-content restrictions, or technical access controls.
- MVP source is MangaDex only. Do not add generic scraping until later.
- LLM features are future scope. Do not implement them in the MVP phases below.
- Keep changes scoped to the current phase.
- Preserve existing working behavior.
- Add or update tests for the phase.
- Run tests before reporting back.

Recommended execution order:

1. Phase 0, Cleanup and baseline
2. Phase 1, Local storage and library API
3. Phase 2, Frontend library UI
4. Phase 3, MangaDex metadata adapter
5. Phase 4, Download manager
6. Phase 5, Reader
7. Phase 6, Settings
8. Phase 7, Polish and release readiness

---

## 00 Cleanup Baseline

```text
Read SPEC.md carefully and implement Phase 0 only.

Working product name: APP_NAME.
If the repository still contains the old visible name, keep internal paths stable for now, but centralize the visible product name in one config constant so it can be renamed later without touching many files.

Goal: make the repository installable, runnable, and testable with a clean FastAPI backend and static frontend serving.

Requirements:
1. Fix Python package structure so `app` is a proper importable package.
2. Fix or create `pyproject.toml` and `requirements.txt`.
3. Add required runtime dependencies only. Start simple.
4. Add `app/main.py` with FastAPI app creation.
5. Add `GET /api/health` returning a small JSON status payload.
6. Serve `frontend/index.html` at `/`.
7. Mount frontend assets under `/static`.
8. Add `scripts/init_data.py` to create:
   - `data/library.json`
   - `data/history.json`
   - `data/settings.json`
   - `data/comics/`
9. Add `.gitignore` for Python cache, virtualenvs, `.env`, local data, downloaded manga, and generated files.
10. Add `.env.example` with safe placeholder values only.
11. Add `README.md` with setup, install, init, run, and test commands.
12. Add minimal tests for health endpoint and data initialization.

Do not implement MangaDex yet.
Do not implement downloading yet.
Do not implement generic scraping yet.
Do not add React, Vue, Next.js, Tailwind, or any frontend build step.
Use Vanilla JavaScript, HTML, and CSS.
Keep all code, filenames, comments, docs, and UI labels in English.
Do not commit downloaded manga, user data, generated data, or secrets.

Acceptance criteria:
- `uv run uvicorn app.main:app --reload` starts successfully.
- `GET /api/health` returns a valid OK response.
- `/` loads a basic Library page.
- `python scripts/init_data.py` creates local data files.
- Tests pass.

After finishing, report:
- Files changed.
- Commands run.
- Test results.
- Any issues found.

```

---

## 01 Local Storage Library Api

```text
Read SPEC.md carefully and implement Phase 1 only.

Working product name: APP_NAME.
Assume Phase 0 is complete. Do not redesign unrelated files unless required.

Goal: implement local JSON storage and the core library/settings API.

Requirements:
1. Create a storage service responsible for reading and writing local JSON files safely.
2. Use a clear data directory, defaulting to `data/`.
3. Create Pydantic models for:
   - Comic
   - Chapter
   - ReadingProgress
   - LibraryResponse
   - Settings
   - API error payloads if useful
4. Implement local file helpers with atomic writes where practical.
5. Implement `GET /api/library`.
6. Implement `GET /api/library/{comic_id}`.
7. Implement `DELETE /api/library/{comic_id}`.
8. Implement `GET /api/settings`.
9. Implement `POST /api/settings`.
10. Preserve existing downloaded files only when the user is not deleting that comic.
11. When deleting a comic, remove its metadata and local comic folder if present.
12. Add clear error handling for missing IDs and invalid payloads.
13. Add tests for storage, library endpoints, delete behavior, and settings persistence.

Data rules:
- Fresh install returns an empty library list.
- `data/library.json` should be the source of truth for the library index.
- Per-comic metadata can exist under `data/comics/{comic_id}/metadata.json`.
- Do not introduce SQLite yet.
- Do not introduce cloud storage.

Do not implement MangaDex import yet.
Do not implement image downloading yet.
Do not implement the reader yet.
Do not add a frontend framework.

Acceptance criteria:
- App creates required JSON files when initialized.
- `GET /api/library` returns an empty list on fresh install.
- `GET /api/library/{comic_id}` returns 404 for missing comics.
- `DELETE /api/library/{comic_id}` handles missing IDs cleanly.
- Settings save and reload correctly.
- Tests pass.

After finishing, report:
- Files changed.
- Commands run.
- Test results.
- Any issues found.

```

---

## 02 Frontend Library Ui

```text
Read SPEC.md carefully and implement Phase 2 only.

Working product name: APP_NAME.
Assume Phases 0 and 1 are complete. Do not implement MangaDex yet.

Goal: create a polished, responsive Library screen using Vanilla JS, HTML, and CSS.

Requirements:
1. Build a dark visual design system in `frontend/css/style.css`.
2. Use a single visible app name constant or shared place where practical.
3. Build the Library layout with:
   - header
   - sidebar or compact navigation
   - main content area
   - toolbar
   - manga grid
4. Build an empty state with a clear Add Manga call to action.
5. Build responsive manga cards showing:
   - cover
   - title
   - source badge
   - status badge
   - progress bar
   - chapter count
   - last-read metadata when available
6. Build client-side search by title.
7. Build client-side sorting:
   - last read
   - recently added
   - title A to Z
   - download progress
8. Build Add Manga modal shell with URL input, detected source display, title override input, Add and Cancel buttons.
9. Build a context menu shell for each card:
   - Open
   - Refresh
   - Download missing
   - Delete
10. Connect the UI to current API endpoints:
   - `GET /api/library`
   - `DELETE /api/library/{comic_id}`
   - settings if needed
11. Add toast notification helpers for success and error messages, even if basic.
12. Keep JavaScript modular and readable.

Important constraints:
- No React, Vue, Svelte, Next.js, or build tools.
- No Tailwind.
- No fake backend data hardcoded as the final behavior. Use API responses.
- Placeholder covers are allowed only when no cover exists.
- Do not implement real MangaDex import in this phase. The Add button may show a friendly “not implemented yet” message until Phase 3.

Acceptance criteria:
- `/` shows a polished Library UI.
- Empty library state is clean and useful.
- Search and sort work with API data.
- Card actions do not throw console errors.
- Delete action works against the API after confirmation.
- Layout works on desktop and mobile widths.
- Tests still pass.

After finishing, report:
- Files changed.
- Commands run.
- Test results.
- Any issues found.

```

---

## 03 Mangadex Metadata Adapter

```text
Read SPEC.md carefully and implement Phase 3 only.

Working product name: APP_NAME.
Assume Phases 0 through 2 are complete.

Goal: implement real MangaDex metadata import without downloading chapter images yet.

Requirements:
1. Create a source adapter interface that can support multiple sources later.
2. Implement a MangaDex adapter only.
3. Detect MangaDex URLs from supported title URL formats.
4. Extract the MangaDex title ID from URLs.
5. Fetch title metadata from the MangaDex public API.
6. Fetch cover metadata and build a usable cover image URL.
7. Fetch chapter list metadata from MangaDex.
8. Normalize chapters into local Chapter models.
9. Implement `POST /api/library/add`.
10. Save a new comic entry into local storage.
11. Save per-comic metadata under `data/comics/{comic_id}/metadata.json`.
12. Downloading chapter page images is not required in this phase.
13. If practical, download and cache the cover image. If not, store a valid remote cover URL and leave image caching for Phase 4.
14. Prevent duplicate entries for the same source URL or MangaDex title ID.
15. Return clear API errors for invalid URL, unsupported source, MangaDex API failure, and missing title.
16. Wire the Add Manga modal to call the real endpoint.
17. Add tests for URL detection, title ID extraction, adapter normalization, add endpoint, and duplicate prevention.

MangaDex notes:
- Use public MangaDex API endpoints only.
- Respect rate limits.
- Do not bypass authentication, paywalls, mature-content restrictions, or technical access controls.
- Keep request code isolated inside the adapter/service layer.

Important constraints:
- Do not implement generic scraping.
- Do not add Playwright.
- Do not add LLM analysis.
- Do not download all chapter pages yet.
- Do not break existing frontend behavior.

Acceptance criteria:
- User can paste a valid MangaDex title URL.
- A manga card appears in the library with title, source, cover if available, and chapter count.
- Duplicate MangaDex title URLs do not create duplicate comics.
- Invalid URLs show a clear user-facing error.
- Tests pass.

After finishing, report:
- Files changed.
- Commands run.
- Test results.
- Any issues found.

```

---

## 04 Download Manager

```text
Read SPEC.md carefully and implement Phase 4 only.

Working product name: APP_NAME.
Assume Phases 0 through 3 are complete.

Goal: implement local chapter/page downloading with background progress tracking.

Requirements:
1. Create an async download manager service.
2. Add a download queue with configurable concurrency, default 2.
3. Add per-domain rate limiting, default 1 request per second.
4. Implement chapter page discovery for MangaDex using its public API.
5. Download page images into:
   `data/comics/{comic_id}/chapters/{chapter_id}/001.jpg`
   Use stable ordering and safe file extensions based on source URLs or response content type.
6. Download and cache the cover image locally if not already done.
7. Persist chapter status:
   - pending
   - downloading
   - complete
   - error
8. Persist page count, downloaded page count, and error message when applicable.
9. Add retry behavior, 3 attempts with exponential backoff.
10. Implement or complete endpoints:
   - `POST /api/library/{comic_id}/download` for all missing chapters
   - `POST /api/library/{comic_id}/chapters/{chapter_id}/download` for one chapter
   - `GET /api/download/{comic_id}/status`
11. Update the Library UI to poll download status every 3 seconds while a comic is downloading.
12. Show progress on manga cards.
13. Keep progress after browser refresh.
14. Add tests for queue status, state persistence, retry marking, and endpoint behavior.

Important constraints:
- Do not block the add request until every chapter is downloaded.
- Do not redownload completed pages unless explicitly requested.
- Do not bypass source restrictions.
- Do not add generic scraping.
- Do not add LLM.
- Keep the system understandable. Fancy queue libraries are not needed unless clearly justified.

Acceptance criteria:
- Adding or manually triggering download starts background work.
- Manga card shows visible progress.
- Downloaded images exist on disk.
- Failed chapters are marked `error` with readable messages.
- Refreshing the browser keeps known download progress.
- Tests pass.

After finishing, report:
- Files changed.
- Commands run.
- Test results.
- Any issues found.

```

---

## 05 Reader

```text
Read SPEC.md carefully and implement Phase 5 only.

Working product name: APP_NAME.
Assume Phases 0 through 4 are complete.

Goal: implement the offline manga reader for downloaded chapters.

Requirements:
1. Implement page-serving endpoint for downloaded images.
2. Use safe path handling to prevent path traversal.
3. Implement reader data endpoint if needed to return comic, chapter list, current progress, and available pages.
4. Build `frontend/reader.html`.
5. Build `frontend/js/reader.js`.
6. Reader UI must include:
   - full-viewport dark reading area
   - top bar with back button, title, chapter, page count
   - bottom bar with chapter selector and progress bar
   - previous and next controls
7. Add navigation:
   - left/right keyboard arrows
   - Esc to return to Library
   - F for fullscreen where browser allows it
   - click/tap zones, left previous, right next, center toggle UI
8. Add chapter selector.
9. Auto-advance to next chapter when the user passes the last page, if next chapter is downloaded.
10. Persist reading progress on page change.
11. Mark chapter complete when the last page is reached.
12. Resume from last-read chapter and page when opening a manga.
13. Update History data when progress is saved.
14. Add user-friendly errors when no chapters are downloaded.
15. Add tests for progress save/load, safe image path handling, and reader endpoints.

Important constraints:
- Reader must use downloaded local files.
- Do not depend on internet for reading downloaded chapters.
- Do not add a frontend framework.
- Do not overbuild zoom/pinch if core reading is not done. Basic fit-to-screen is enough first.

Acceptance criteria:
- User can open a manga card and read downloaded pages.
- Keyboard navigation works.
- Click zones work.
- Progress saves after navigation.
- Reopening the manga resumes from the last saved page.
- Reader works offline for downloaded chapters.
- Tests pass.

After finishing, report:
- Files changed.
- Commands run.
- Test results.
- Any issues found.

```

---

## 06 Settings

```text
Read SPEC.md carefully and implement Phase 6 only.

Working product name: APP_NAME.
Assume Phases 0 through 5 are complete.

Goal: make local configuration editable through a Settings page.

Requirements:
1. Build `frontend/settings.html`.
2. Build `frontend/js/settings.js`.
3. Add Settings navigation from the main UI.
4. Connect to:
   - `GET /api/settings`
   - `POST /api/settings`
5. User-editable settings for MVP:
   - visible product name, if already centralized
   - library path
   - download concurrency, range 1 to 5
   - theme, dark for now, light can be disabled or marked future
   - UI language, English for now, other languages can be disabled or marked future
6. Keep LLM settings hidden, disabled, or clearly marked as future. Do not implement LLM provider logic.
7. Validate settings on backend.
8. Show validation errors in UI.
9. Never expose secrets in git-tracked files.
10. Add tests for settings validation and persistence.

Important constraints:
- Do not move existing downloaded files automatically when library path changes unless you implement it safely and explicitly.
- If changing library path only affects future downloads, say that clearly in the UI.
- Do not add cloud sync.
- Do not add accounts.
- Do not add LLM integration yet.

Acceptance criteria:
- Settings page loads current settings.
- User can save valid settings.
- Invalid settings show clear errors.
- Saved settings persist after app restart.
- No API keys or secrets are committed.
- Tests pass.

After finishing, report:
- Files changed.
- Commands run.
- Test results.
- Any issues found.

```

---

## 07 Polish Release Readiness

```text
Read SPEC.md carefully and implement Phase 7 only.

Working product name: APP_NAME.
Assume Phases 0 through 6 are complete.

Goal: polish the MVP so the core flow feels complete and stable.

Requirements:
1. Add consistent toast notifications across Library, Reader, and Settings.
2. Add better loading states and skeletons.
3. Add better error states for:
   - unsupported source
   - failed MangaDex request
   - no downloaded chapters
   - download failure
   - invalid settings
4. Improve mobile layout.
5. Add keyboard shortcut help, for example `?` in Reader.
6. Add a clear limitations section in README.
7. Add screenshot placeholders in README.
8. Review all user-facing labels for consistency.
9. Review product naming and make sure visible name is centralized.
10. Add final tests for core smoke flow where practical:
   - health
   - library empty
   - add metadata, mocked if needed
   - settings
   - reader progress
11. Run formatting/linting tools if the repo has them.
12. Fix obvious broken UI paths and console errors.

Important constraints:
- Do not add large new features.
- Do not add new sources.
- Do not add LLM.
- Do not switch frameworks.
- Do not introduce a database.
- Polish what exists. Não inventa moda.

Acceptance criteria:
- Core flow feels usable end to end.
- README explains setup, run, usage, limitations, and source boundaries.
- No obvious broken UI paths.
- No obvious browser console errors during normal use.
- Tests pass.

After finishing, report:
- Files changed.
- Commands run.
- Test results.
- Remaining known limitations.

```

---


import asyncio
import time
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from app.services.storage import (
    COMICS_DIR,
    load_comic_metadata,
    load_library,
    save_comic_metadata,
    save_library,
)
from app.sources.mangadex import MangaDexAdapter


USER_AGENT = "MangoToon/0.1 (local manga reader)"
MAX_RETRIES = 3


class DownloadStatus(str, Enum):
    queued = "queued"
    downloading = "downloading"
    paused = "paused"
    cancelled = "cancelled"
    complete = "complete"
    partial = "partial"
    error = "error"


class DownloadJob:
    def __init__(self, comic_id: str, total_chapters: int):
        self.comic_id = comic_id
        self.status = DownloadStatus.queued.value
        self.total_chapters = total_chapters
        self.downloaded_chapters = 0
        self.error_chapters = 0
        self.current_chapter_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "comic_id": self.comic_id,
            "status": self.status,
            "state": self.status,
            "total_chapters": self.total_chapters,
            "downloaded_chapters": self.downloaded_chapters,
            "error_chapters": self.error_chapters,
            "current_chapter_id": self.current_chapter_id,
        }


class DownloadManager:
    def __init__(self) -> None:
        self._jobs: dict[str, DownloadJob] = {}
        self._queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._domain_locks: dict[str, asyncio.Lock] = {}
        self._last_request: dict[str, float] = {}
        self._rate_limit: float = 1.0

    def start(self, concurrency: int = 2, rate_limit: float = 1.0) -> None:
        """Start background workers. Call from app lifespan startup."""
        self._rate_limit = rate_limit
        if self._workers:
            return
        for _ in range(concurrency):
            task = asyncio.create_task(self._worker())
            self._workers.append(task)

    async def stop(self) -> None:
        """Cancel all workers. Call from app lifespan shutdown."""
        for task in self._workers:
            task.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def enqueue_comic(self, comic_id: str) -> None:
        """Enqueue all not_downloaded chapters for a comic."""
        if comic_id in self._jobs and self._jobs[comic_id].status in (
            DownloadStatus.queued.value,
            DownloadStatus.downloading.value,
            DownloadStatus.paused.value,
        ):
            return

        metadata = load_comic_metadata(comic_id)
        if not metadata:
            return

        missing = [c for c in metadata.get("chapters", []) if c.get("status") == "not_downloaded"]
        if not missing:
            return

        job = DownloadJob(comic_id=comic_id, total_chapters=len(missing))
        self._jobs[comic_id] = job

        asyncio.create_task(self._download_cover(comic_id, metadata))

        self._set_chapters_status(comic_id, [c["chapter_id"] for c in missing], "queued")

        for chapter in missing:
            await self._queue.put((comic_id, chapter))

    async def enqueue_chapter(self, comic_id: str, chapter_id: str) -> None:
        """Enqueue a single chapter for download."""
        metadata = load_comic_metadata(comic_id)
        if not metadata:
            return
        for chapter in metadata.get("chapters", []):
            if chapter["chapter_id"] == chapter_id and chapter.get("status") in ("not_downloaded", "error"):
                if comic_id not in self._jobs:
                    self._jobs[comic_id] = DownloadJob(comic_id=comic_id, total_chapters=1)
                else:
                    self._jobs[comic_id].total_chapters += 1
                self._set_chapters_status(comic_id, [chapter_id], "queued")
                await self._queue.put((comic_id, chapter))
                return

    def get_status(self, comic_id: str) -> dict | None:
        job = self._jobs.get(comic_id)
        return job.to_dict() if job else None

    def list_active(self) -> list[dict]:
        return [
            job.to_dict()
            for job in self._jobs.values()
            if job.status in (
                DownloadStatus.queued.value,
                DownloadStatus.downloading.value,
                DownloadStatus.paused.value,
            )
        ]

    def pause_comic(self, comic_id: str) -> bool:
        job = self._jobs.get(comic_id)
        if not job or job.status not in (DownloadStatus.queued.value, DownloadStatus.downloading.value):
            return False
        job.status = DownloadStatus.paused.value
        self._update_comic_status(comic_id, DownloadStatus.paused.value)
        return True

    def resume_comic(self, comic_id: str) -> bool:
        job = self._jobs.get(comic_id)
        if not job or job.status != DownloadStatus.paused.value:
            return False
        job.status = DownloadStatus.queued.value
        self._update_comic_status(comic_id, DownloadStatus.queued.value)
        return True

    def cancel_comic(self, comic_id: str) -> bool:
        job = self._jobs.get(comic_id)
        metadata = load_comic_metadata(comic_id)
        if not job and not metadata:
            return False

        if job:
            job.status = DownloadStatus.cancelled.value
            job.current_chapter_id = None
        self._remove_queued_items(comic_id)
        self._reset_incomplete_chapters(comic_id)
        self._update_comic_status(comic_id, DownloadStatus.cancelled.value)
        return True

    async def retry_chapter(self, comic_id: str, chapter_id: str) -> bool:
        metadata = load_comic_metadata(comic_id)
        if not metadata:
            return False
        chapter = next(
            (item for item in metadata.get("chapters", []) if item.get("chapter_id") == chapter_id),
            None,
        )
        if not chapter or chapter.get("status") not in ("error", "partial", "cancelled"):
            return False

        if comic_id not in self._jobs or self._jobs[comic_id].status in (
            DownloadStatus.complete.value,
            DownloadStatus.error.value,
            DownloadStatus.partial.value,
            DownloadStatus.cancelled.value,
        ):
            self._jobs[comic_id] = DownloadJob(comic_id=comic_id, total_chapters=1)
        else:
            self._jobs[comic_id].total_chapters += 1
            self._jobs[comic_id].status = DownloadStatus.queued.value

        self._set_chapters_status(comic_id, [chapter_id], "queued")
        await self._queue.put((comic_id, chapter))
        self._update_comic_status(comic_id, DownloadStatus.queued.value)
        return True

    async def _worker(self) -> None:
        while True:
            try:
                comic_id, chapter = await self._queue.get()
                try:
                    job = self._jobs.get(comic_id)
                    if job and job.status == DownloadStatus.cancelled.value:
                        continue
                    if job and job.status == DownloadStatus.paused.value:
                        await self._queue.put((comic_id, chapter))
                        await asyncio.sleep(0.25)
                        continue
                    if job:
                        job.status = DownloadStatus.downloading.value
                        job.current_chapter_id = chapter.get("chapter_id")
                    await self._download_chapter(comic_id, chapter)
                    if job:
                        job.downloaded_chapters += 1
                except Exception:
                    if job := self._jobs.get(comic_id):
                        job.error_chapters += 1
                finally:
                    self._queue.task_done()
                    self._finalize_job_if_done(comic_id)
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    def _finalize_job_if_done(self, comic_id: str) -> None:
        job = self._jobs.get(comic_id)
        if job is None:
            return
        done = job.downloaded_chapters + job.error_chapters
        if done >= job.total_chapters:
            if job.status in (DownloadStatus.cancelled.value, DownloadStatus.paused.value):
                return
            if job.error_chapters == 0:
                job.status = DownloadStatus.complete.value
            elif job.downloaded_chapters == 0:
                job.status = DownloadStatus.error.value
            else:
                job.status = DownloadStatus.partial.value
            job.current_chapter_id = None
            self._update_comic_status(comic_id, job.status)

    async def _download_chapter(self, comic_id: str, chapter: dict[str, Any]) -> None:
        chapter_id = chapter["chapter_id"]
        self._set_chapters_status(comic_id, [chapter_id], "downloading")

        chapter_dir = COMICS_DIR / comic_id / "chapters" / chapter_id
        chapter_dir.mkdir(parents=True, exist_ok=True)

        try:
            adapter = MangaDexAdapter()
            page_urls = await adapter.get_chapter_pages(chapter_id)
        except Exception as exc:
            self._set_chapter_error(comic_id, chapter_id, str(exc))
            raise

        local_pages: list[str] = []
        downloaded = 0
        failed = False
        for idx, url in enumerate(page_urls, start=1):
            url_path = urlparse(url).path
            ext = Path(url_path).suffix or ".jpg"
            dest = chapter_dir / f"{idx:03d}{ext}"

            if dest.exists():
                downloaded += 1
                local_pages.append(str(dest.relative_to(COMICS_DIR.parent)))
                continue

            try:
                content = await self._fetch_with_retry(url)
                dest.write_bytes(content)
                downloaded += 1
                local_pages.append(str(dest.relative_to(COMICS_DIR.parent)))
            except Exception:
                failed = True

        self._persist_chapter_downloaded(
            comic_id, chapter_id, len(page_urls), downloaded, local_pages, failed
        )

    async def _fetch_with_retry(self, url: str) -> bytes:
        host = urlparse(url).hostname or url
        lock = self._domain_locks.setdefault(host, asyncio.Lock())

        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                async with lock:
                    elapsed = time.monotonic() - self._last_request.get(host, 0.0)
                    if elapsed < self._rate_limit:
                        await asyncio.sleep(self._rate_limit - elapsed)
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(url, headers={"User-Agent": USER_AGENT})
                        response.raise_for_status()
                        self._last_request[host] = time.monotonic()
                        return response.content
            except Exception as exc:
                last_exc = exc
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2**attempt)
        raise last_exc or RuntimeError("Download failed.")

    async def _download_cover(self, comic_id: str, metadata: dict[str, Any]) -> None:
        cover_url = metadata.get("cover_url", "")
        if not cover_url:
            return

        comic_dir = COMICS_DIR / comic_id
        comic_dir.mkdir(parents=True, exist_ok=True)
        dest = comic_dir / "cover.jpg"

        if dest.exists():
            return

        try:
            content = await self._fetch_with_retry(cover_url)
            dest.write_bytes(content)
            meta = load_comic_metadata(comic_id) or metadata
            meta["cover_local"] = str(dest.relative_to(COMICS_DIR.parent))
            save_comic_metadata(comic_id, meta)
        except Exception:
            pass

    def _set_chapters_status(self, comic_id: str, chapter_ids: list[str], status: str) -> None:
        meta = load_comic_metadata(comic_id)
        if not meta:
            return
        ids_set = set(chapter_ids)
        for chapter in meta.get("chapters", []):
            if chapter.get("chapter_id") in ids_set:
                chapter["status"] = status
        save_comic_metadata(comic_id, meta)

    def _set_chapter_error(self, comic_id: str, chapter_id: str, message: str) -> None:
        meta = load_comic_metadata(comic_id)
        if not meta:
            return
        for chapter in meta.get("chapters", []):
            if chapter.get("chapter_id") == chapter_id:
                chapter["status"] = "error"
                chapter["error_message"] = message
        save_comic_metadata(comic_id, meta)

    def _persist_chapter_downloaded(
        self,
        comic_id: str,
        chapter_id: str,
        total_pages: int,
        downloaded_pages: int,
        local_pages: list[str],
        failed: bool,
    ) -> None:
        meta = load_comic_metadata(comic_id)
        if not meta:
            return
        for chapter in meta.get("chapters", []):
            if chapter.get("chapter_id") == chapter_id:
                if failed:
                    chapter["status"] = "error" if downloaded_pages == 0 else "partial"
                else:
                    chapter["status"] = "downloaded" if downloaded_pages >= total_pages else "error"
                chapter["pages"] = total_pages
                chapter["downloaded_pages"] = downloaded_pages
                chapter["local_pages"] = local_pages
        save_comic_metadata(comic_id, meta)
        self._update_library_counts(comic_id, meta)

    def _update_library_counts(self, comic_id: str, meta: dict[str, Any]) -> None:
        library = load_library()
        for comic in library.get("comics", []):
            if comic.get("comic_id") == comic_id:
                comic["status"] = meta.get("status", "pending")
                comic["chapters"] = meta.get("chapters", [])
                break
        save_library(library)

    def _update_comic_status(self, comic_id: str, status: str) -> None:
        library = load_library()
        for comic in library.get("comics", []):
            if comic.get("comic_id") == comic_id:
                comic["status"] = status
                break
        save_library(library)
        meta = load_comic_metadata(comic_id)
        if meta:
            meta["status"] = status
            save_comic_metadata(comic_id, meta)

    def _remove_queued_items(self, comic_id: str) -> None:
        """Remove all queued items for a comic without corrupting task_done accounting.

        We create a new queue and transfer only items for other comics.
        This avoids the task_done mismatch that occurs when removing items
        from an asyncio.Queue without a corresponding get().
        """
        new_queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()
        while True:
            try:
                item = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            queued_comic_id, _chapter = item
            if queued_comic_id != comic_id:
                new_queue.put_nowait(item)
            # Do NOT call task_done() for removed items — the worker that
            # called get() will call task_done() after processing.
            # For items we keep, the original worker will still process them.
        self._queue = new_queue

    def _reset_incomplete_chapters(self, comic_id: str) -> None:
        meta = load_comic_metadata(comic_id)
        if not meta:
            return
        for chapter in meta.get("chapters", []):
            if chapter.get("status") in ("queued", "downloading"):
                chapter["status"] = "not_downloaded"
        save_comic_metadata(comic_id, meta)


download_manager = DownloadManager()

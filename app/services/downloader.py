"""Download manager for background comic downloading"""

import asyncio
import os
import re
import json
import fcntl
from pathlib import Path
from typing import Optional
from uuid import uuid4

from app.core.config import settings
from app.services.scraper import ScraperEngine
from app.services.models import ScrapingResult


class DownloadManager:
    """Manages comic downloads in the background"""

    def __init__(self):
        self.scraper = ScraperEngine()
        self.active_downloads: dict[str, asyncio.Task] = {}
        self._shutdown = False

    async def start_download(self, comic_id: str, url: str) -> bool:
        """Start downloading a comic"""
        if comic_id in self.active_downloads:
            return False  # Already downloading

        task = asyncio.create_task(self._download_comic(comic_id, url))
        self.active_downloads[comic_id] = task
        return True

    async def stop_download(self, comic_id: str) -> bool:
        """Stop an active download"""
        if comic_id in self.active_downloads:
            self.active_downloads[comic_id].cancel()
            del self.active_downloads[comic_id]
            return True
        return False

    async def get_status(self, comic_id: str) -> dict:
        """Get download status for a comic"""
        comic = settings.load_comic_metadata(comic_id)
        if not comic:
            return {"status": "unknown"}

        is_active = comic_id in self.active_downloads

        return {
            "comic_id": comic_id,
            "status": comic.get("status", "unknown"),
            "downloaded_chapters": comic.get("downloaded_chapters", []),
            "total_chapters": comic.get("total_chapters", 0),
            "is_active": is_active,
        }

    def _lock_file(self, path: Path) -> Optional[object]:
        """Acquire file lock for safe concurrent writes. Returns lock object or None."""
        try:
            lock_path = path.with_suffix('.lock')
            lock_file = open(lock_path, 'w')
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            return lock_file
        except Exception as e:
            print(f"Failed to acquire lock: {e}")
            return None

    def _unlock_file(self, lock_obj: object):
        """Release file lock."""
        try:
            if lock_obj:
                fcntl.flock(lock_obj.fileno(), fcntl.LOCK_UN)
                lock_obj.close()
        except Exception:
            pass

    def _save_library_safe(self, data: list):
        """Save library.json with file locking to prevent race conditions."""
        lock = self._lock_file(settings.library_db_path)
        try:
            settings.save_library(data)
        finally:
            self._unlock_file(lock)

    def _save_comic_metadata_safe(self, comic_id: str, data: dict):
        """Save comic metadata with file locking."""
        comic_dir = settings.library_path / comic_id
        meta_path = comic_dir / "metadata.json"
        lock = self._lock_file(meta_path)
        try:
            settings.save_comic_metadata(comic_id, data)
        finally:
            self._unlock_file(lock)

    async def _download_comic(self, comic_id: str, url: str):
        """Background task to download a comic"""
        try:
            # Update status to downloading
            comic = settings.load_comic_metadata(comic_id)
            if not comic:
                return

            comic["status"] = "downloading"
            self._save_comic_metadata_safe(comic_id, comic)
            self._sync_library(comic_id, comic)

            # Scrape comic info
            result = await self.scraper.scrape(url)

            if not result.success:
                comic["status"] = "error"
                comic["error"] = result.error_message
                self._save_comic_metadata_safe(comic_id, comic)
                self._sync_library(comic_id, comic)
                return

            # Update comic with scraped data
            comic["title"] = result.title
            comic["cover_url"] = result.cover_url
            comic["source_site"] = result.source_site
            comic["chapters"] = [
                {
                    "number": ch.number,
                    "title": ch.title,
                    "url": ch.url,
                    "downloaded": False,
                    "pages": []
                }
                for ch in result.chapters
            ]
            comic["total_chapters"] = len(result.chapters)
            comic["downloaded_chapters"] = []
            comic["status"] = "downloading"
            self._save_comic_metadata_safe(comic_id, comic)
            self._sync_library(comic_id, comic)

            # Download cover if available
            if result.cover_url:
                await self._download_cover(comic_id, result.cover_url)

            # Download chapters
            for i, chapter in enumerate(result.chapters):
                if self._shutdown:
                    break

                try:
                    downloaded_pages = await self._download_chapter(comic_id, chapter)
                    if downloaded_pages > 0:
                        comic["downloaded_chapters"].append(chapter.number)
                        # Update chapter as downloaded
                        for ch in comic["chapters"]:
                            if ch["number"] == chapter.number:
                                ch["downloaded"] = True
                                break
                        comic["status"] = "downloading"
                        self._save_comic_metadata_safe(comic_id, comic)
                        self._sync_library(comic_id, comic)
                except Exception as e:
                    print(f"Failed to download chapter {chapter.number}: {e}")
                    continue

            # Mark as complete
            comic["status"] = "complete"
            self._save_comic_metadata_safe(comic_id, comic)
            self._sync_library(comic_id, comic)

        except asyncio.CancelledError:
            print(f"Download cancelled for {comic_id}")
        except Exception as e:
            print(f"Download failed for {comic_id}: {e}")
            comic = settings.load_comic_metadata(comic_id)
            if comic:
                comic["status"] = "error"
                comic["error"] = str(e)
                self._save_comic_metadata_safe(comic_id, comic)
                self._sync_library(comic_id, comic)
        finally:
            if comic_id in self.active_downloads:
                del self.active_downloads[comic_id]

    def _sync_library(self, comic_id: str, comic: dict):
        """Sync comic metadata to library.json"""
        library = settings.load_library()

        # Find and update or add comic
        found = False
        for i, c in enumerate(library):
            if c.get("id") == comic_id:
                library[i] = comic
                found = True
                break

        if not found:
            library.append({
                "id": comic["id"],
                "title": comic.get("title", ""),
                "source_url": comic.get("source_url", ""),
                "source_site": comic.get("source_site", ""),
                "cover_url": comic.get("cover_url", ""),
                "total_chapters": comic.get("total_chapters", 0),
                "downloaded_chapters": comic.get("downloaded_chapters", []),
                "status": comic.get("status", "unknown"),
                "last_read_chapter": comic.get("last_read_chapter", 0),
                "last_read_page": comic.get("last_read_page", 0),
            })

        self._save_library_safe(library)

    async def _download_cover(self, comic_id: str, cover_url: str):
        """Download comic cover image"""
        if not cover_url:
            return

        comic_dir = settings.library_path / comic_id
        cover_path = comic_dir / "cover.jpg"

        # Skip if already exists
        if cover_path.exists():
            return

        # Download cover
        await self.scraper.download_page(cover_url, str(cover_path))

    async def _download_chapter(self, comic_id: str, chapter) -> int:
        """Download a single chapter with real pages. Returns number of pages downloaded."""
        comic_dir = settings.library_path / comic_id / "chapters" / str(int(chapter.number))
        comic_dir.mkdir(parents=True, exist_ok=True)

        # Extract chapter ID from MangaDex URL
        chapter_id = self._extract_chapter_id(chapter.url)

        if chapter_id:
            # MangaDex chapter - use API to get pages
            return await self._download_mangadex_chapter(comic_id, chapter, comic_dir)
        else:
            # Generic chapter - placeholder for now
            return await self._download_generic_chapter(chapter, comic_dir)

    async def _download_mangadex_chapter(self, comic_id: str, chapter, comic_dir: Path) -> int:
        """Download MangaDex chapter pages using their API"""
        chapter_id = self._extract_chapter_id(chapter.url)
        if not chapter_id:
            return 0

        server_url, page_urls = await self.scraper.get_mangadex_chapter_pages(chapter_id)

        if not page_urls:
            # Fallback to placeholder if no pages found
            placeholder = comic_dir / "placeholder.txt"
            placeholder.write_text(f"Chapter {chapter.number} - {chapter.title}\nURL: {chapter.url}")
            return 0

        downloaded = 0

        for page_num, page_url in enumerate(page_urls, 1):
            # Try different image formats and extensions
            for ext in ['jpg', 'png', 'webp']:
                save_path = comic_dir / f"{page_num:03d}.{ext}"
                if not save_path.exists():
                    if await self.scraper.download_page(page_url, str(save_path)):
                        downloaded += 1
                        break
            else:
                # If all formats fail, try jpg as last resort
                save_path = comic_dir / f"{page_num:03d}.jpg"
                await self.scraper.download_page(page_url, str(save_path))
                downloaded += 1

        return downloaded

    async def _download_generic_chapter(self, chapter, comic_dir: Path) -> int:
        """Generic chapter download - creates placeholder for now"""
        # For non-MangaDex chapters, this is a placeholder
        # Real implementation would need site-specific handlers
        placeholder = comic_dir / "placeholder.txt"
        placeholder.write_text(f"Chapter {chapter.number} - {chapter.title}\nURL: {chapter.url}")
        return 0

    def _extract_chapter_id(self, url: str) -> Optional[str]:
        """Extract MangaDex chapter ID from URL"""
        match = re.search(r'/chapter/([a-z0-9-]+)', url)
        if match:
            return match.group(1)
        return None

    async def shutdown(self):
        """Graceful shutdown"""
        self._shutdown = True
        for task in self.active_downloads.values():
            task.cancel()
        await asyncio.gather(*self.active_downloads.values(), return_exceptions=True)


# Global instance
download_manager = DownloadManager()
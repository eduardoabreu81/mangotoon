from importlib import import_module

from app.models.comic import Comic
from app.sources.base import SourceAdapter, UnsupportedSource


from app.services.storage import load_settings


def _default_adapters() -> list[SourceAdapter]:
    mangadex_module = import_module("app.sources.mangadex")
    settings = load_settings()
    language = settings.get("mangadex_language", "en")
    return [mangadex_module.MangaDexAdapter(language=language)]


class SourceRegistry:
    def __init__(self, adapters: list[SourceAdapter] | None = None) -> None:
        self.adapters = adapters or _default_adapters()

    def get_adapter(self, url: str) -> SourceAdapter:
        for adapter in self.adapters:
            if adapter.can_handle(url):
                return adapter
        raise UnsupportedSource("Unsupported source. Paste a valid title URL.")

    def get_adapter_for_comic(self, comic: Comic) -> SourceAdapter:
        source = comic.source.lower()
        for adapter in self.adapters:
            if adapter.name.lower() == source:
                return adapter
            if comic.source_url and adapter.can_handle(comic.source_url):
                return adapter
        raise UnsupportedSource(f"Unsupported source for comic '{comic.comic_id}'.")


source_registry = SourceRegistry()

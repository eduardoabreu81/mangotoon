from app.sources.base import SourceAdapter, UnsupportedSource
from app.sources.mangadex import MangaDexAdapter


class SourceRegistry:
    def __init__(self, adapters: list[SourceAdapter] | None = None) -> None:
        self.adapters = adapters or [MangaDexAdapter()]

    def get_adapter(self, url: str) -> SourceAdapter:
        for adapter in self.adapters:
            if adapter.can_handle(url):
                return adapter
        raise UnsupportedSource("Unsupported source. Paste a valid MangaDex title URL.")


source_registry = SourceRegistry()

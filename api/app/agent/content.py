"""Content pack loader – reads packs.json and markdown files for agent context."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class ContentPack:
    id: str
    path: str
    topic_hints: list[str]
    content: str = field(default="", repr=False)


class ContentLoader:
    def __init__(self, content_dir: str) -> None:
        self._dir = Path(content_dir).resolve()
        self._packs: dict[str, ContentPack] = {}

    def load(self) -> None:
        packs_file = self._dir / "packs.json"
        if not packs_file.exists():
            raise FileNotFoundError(f"packs.json not found at {packs_file}")

        with packs_file.open() as f:
            data = json.load(f)

        for raw in data.get("packs", []):
            pack_path = Path(raw["path"])
            # Support both absolute and relative (relative = from repo root)
            if not pack_path.is_absolute():
                pack_path = self._dir.parent / raw["path"]

            if not pack_path.exists():
                log.warning("Content file missing: %s", pack_path)
                continue

            content = pack_path.read_text(encoding="utf-8")
            pack = ContentPack(
                id=raw["id"],
                path=str(pack_path),
                topic_hints=raw.get("topicHints", []),
                content=content,
            )
            self._packs[pack.id] = pack
            log.info("Loaded content pack '%s' (%d chars)", pack.id, len(content))

    def get_pack(self, pack_id: str) -> ContentPack | None:
        return self._packs.get(pack_id)

    def get_all_packs(self) -> list[ContentPack]:
        return list(self._packs.values())

    def build_context_block(self) -> str:
        """Return all pack content formatted for injection into a system prompt."""
        blocks = []
        for pack in self._packs.values():
            blocks.append(f"## {pack.id.upper()} CONTEXT\n\n{pack.content}")
        return "\n\n---\n\n".join(blocks)

    @property
    def checksums(self) -> dict[str, int]:
        """Simple character-count checksum for health checks."""
        return {pid: len(p.content) for pid, p in self._packs.items()}


@lru_cache(maxsize=1)
def _loader_singleton(content_dir: str) -> ContentLoader:
    loader = ContentLoader(content_dir)
    loader.load()
    return loader


def get_content_loader(content_dir: str) -> ContentLoader:
    return _loader_singleton(content_dir)

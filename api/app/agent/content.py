"""Content pack loader – reads packs.json and markdown files for agent context."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Literal

log = logging.getLogger(__name__)

Visibility = Literal["always", "on_demand"]


@dataclass
class ContentPack:
    id: str
    path: str
    category: str
    topic_hints: list[str]
    visibility: Visibility
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
            if not pack_path.is_absolute():
                pack_path = self._dir.parent / raw["path"]

            if not pack_path.exists():
                log.warning("Content file missing: %s", pack_path)
                continue

            content = pack_path.read_text(encoding="utf-8")
            pack = ContentPack(
                id=raw["id"],
                path=str(pack_path),
                category=raw.get("category", "general"),
                topic_hints=raw.get("topicHints", []),
                visibility=raw.get("visibility", "always"),
                content=content,
            )
            self._packs[pack.id] = pack
            log.info(
                "Loaded content pack '%s' (category=%s, visibility=%s, %d chars)",
                pack.id,
                pack.category,
                pack.visibility,
                len(content),
            )

    def get_pack(self, pack_id: str) -> ContentPack | None:
        return self._packs.get(pack_id)

    def get_all_packs(self) -> list[ContentPack]:
        return list(self._packs.values())

    def build_context_block(self) -> str:
        """Return 'always'-visible pack content for injection into the system prompt."""
        blocks = []
        for pack in self._packs.values():
            if pack.visibility == "always":
                blocks.append(f"## {pack.id.upper()} CONTEXT\n\n{pack.content}")
        return "\n\n---\n\n".join(blocks)

    def search_packs(self, topic: str) -> list[ContentPack]:
        """Find content packs whose topic hints match the query.

        Matches are scored by the number of hint tokens found in the topic string.
        Returns all on_demand packs with at least one match, sorted by score.
        Always-visible packs are excluded (they're already in the system prompt).
        """
        topic_lower = topic.lower()
        scored: list[tuple[int, ContentPack]] = []

        for pack in self._packs.values():
            if pack.visibility != "on_demand":
                continue
            score = sum(1 for hint in pack.topic_hints if hint.lower() in topic_lower)
            if score > 0:
                scored.append((score, pack))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [pack for _, pack in scored]

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

"""Tests for the content pack loader."""
import json
import tempfile
from pathlib import Path

import pytest
from app.agent.content import ContentLoader


def _make_content_dir(tmp_path: Path) -> Path:
    resume = tmp_path / "resume.md"
    resume.write_text("# Jai Rathore\n\nStaff Software Engineer at Tesla.")

    packs = {"packs": [{"id": "resume", "path": str(resume), "topicHints": ["tesla"]}]}
    (tmp_path / "packs.json").write_text(json.dumps(packs))
    return tmp_path


def test_loader_loads_packs(tmp_path):
    content_dir = _make_content_dir(tmp_path)
    loader = ContentLoader(str(content_dir))
    loader.load()

    pack = loader.get_pack("resume")
    assert pack is not None
    assert "Jai Rathore" in pack.content


def test_context_block_contains_content(tmp_path):
    content_dir = _make_content_dir(tmp_path)
    loader = ContentLoader(str(content_dir))
    loader.load()

    block = loader.build_context_block()
    assert "Jai Rathore" in block


def test_checksums_returns_lengths(tmp_path):
    content_dir = _make_content_dir(tmp_path)
    loader = ContentLoader(str(content_dir))
    loader.load()

    checksums = loader.checksums
    assert "resume" in checksums
    assert checksums["resume"] > 0

#!/usr/bin/env python3
"""Run OMR-to-organ-MIDI for a section listed in sources/section_manifest.json."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SECTION_MANIFEST = ROOT / "sources" / "section_manifest.json"
SOURCE_MANIFEST = ROOT / "sources" / "source_candidates.json"


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text())


def find_by_id(items: list[dict[str, Any]], item_id: str) -> dict[str, Any]:
    for item in items:
        if item.get("id") == item_id:
            return item
    raise KeyError(f"No manifest entry with id {item_id!r}")


def section_sheets(section: dict[str, Any]) -> str:
    start = int(section["pdf_sheet_start"])
    end = int(section["pdf_sheet_end"])
    return str(start) if start == end else f"{start}-{end}"


def run(command: list[str], dry_run: bool) -> None:
    print(" ".join(command))
    if not dry_run:
        subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("section_id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--channel", type=int, default=0)
    parser.add_argument("--program", type=int, default=19)
    args = parser.parse_args()

    sections = load_json(SECTION_MANIFEST)
    sources = load_json(SOURCE_MANIFEST)
    section = find_by_id(sections, args.section_id)
    source = find_by_id(sources, section["source_candidate_id"])

    if not source.get("full_divine_liturgy"):
        raise ValueError(f"Source {source['id']} is not marked as full_divine_liturgy")

    source_path = ROOT / source["path"]
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    run(
        [
            str(ROOT / "badarak_venv" / "bin" / "python"),
            "tools/omr_to_organ_midi.py",
            source["path"],
            "--sheets",
            section_sheets(section),
            "--name",
            section["id"],
            "--channel",
            str(args.channel),
            "--program",
            str(args.program),
        ],
        args.dry_run,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate generated section MIDI against manifest-level musical sanity gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import mido


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "sources" / "section_manifest.json"


def load_section(section_id: str, manifest_path: Path) -> dict:
    sections = json.loads(manifest_path.read_text())
    for section in sections:
        if section["id"] == section_id:
            return section
    raise KeyError(f"section id not found: {section_id}")


def count_note_ons(midi_file: mido.MidiFile) -> int:
    return sum(
        1
        for track in midi_file.tracks
        for message in track
        if message.type == "note_on" and message.velocity > 0
    )


def validate(
    section: dict,
    min_seconds_per_page: float,
    min_note_ons_per_page: int,
) -> tuple[list[str], dict[str, float | int | str]]:
    midi_path = ROOT / section["organ_midi_output"]
    midi_file = mido.MidiFile(midi_path)
    score_pages = int(section["score_page_end"]) - int(section["score_page_start"]) + 1
    pdf_sheets = int(section["pdf_sheet_end"]) - int(section["pdf_sheet_start"]) + 1
    note_ons = count_note_ons(midi_file)
    duration = float(midi_file.length)

    metrics: dict[str, float | int | str] = {
        "section_id": section["id"],
        "midi_path": str(midi_path.relative_to(ROOT)),
        "tracks": len(midi_file.tracks),
        "duration_seconds": round(duration, 2),
        "note_ons": note_ons,
        "score_pages": score_pages,
        "pdf_sheets": pdf_sheets,
        "seconds_per_score_page": round(duration / score_pages, 2),
        "note_ons_per_score_page": round(note_ons / score_pages, 2),
    }

    errors: list[str] = []
    if len(midi_file.tracks) != 1:
        errors.append(f"expected 1 MIDI track, found {len(midi_file.tracks)}")
    if duration < score_pages * min_seconds_per_page:
        errors.append(
            "duration too short for section range: "
            f"{duration:.2f}s for {score_pages} score pages "
            f"(minimum {score_pages * min_seconds_per_page:.2f}s)"
        )
    if note_ons < score_pages * min_note_ons_per_page:
        errors.append(
            "too few note-on events for section range: "
            f"{note_ons} for {score_pages} score pages "
            f"(minimum {score_pages * min_note_ons_per_page})"
        )
    return errors, metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("section_id")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--min-seconds-per-page", type=float, default=6.0)
    parser.add_argument("--min-note-ons-per-page", type=int, default=75)
    args = parser.parse_args()

    try:
        section = load_section(args.section_id, args.manifest)
        errors, metrics = validate(section, args.min_seconds_per_page, args.min_note_ons_per_page)
    except Exception as exc:
        print(f"section MIDI sanity check failed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(metrics, indent=2, sort_keys=True))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

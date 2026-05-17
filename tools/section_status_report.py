#!/usr/bin/env python3
"""Summarize manifest sections, MIDI sanity, and OMR review counts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import mido


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "sources" / "section_manifest.json"
CHECKBOX_RE = re.compile(r"^- \[ \] `(?P<category>[^`]+)`:", re.MULTILINE)


def count_note_ons(midi_file: mido.MidiFile) -> int:
    return sum(
        1
        for track in midi_file.tracks
        for message in track
        if message.type == "note_on" and message.velocity > 0
    )


def review_counts(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    counts: dict[str, int] = {}
    for match in CHECKBOX_RE.finditer(path.read_text()):
        category = match.group("category")
        counts[category] = counts.get(category, 0) + 1
    return counts


def midi_metrics(path: Path) -> dict[str, float | int | str | bool]:
    if not path.exists():
        return {"exists": False}
    midi_file = mido.MidiFile(path)
    return {
        "exists": True,
        "tracks": len(midi_file.tracks),
        "duration_seconds": round(float(midi_file.length), 2),
        "note_ons": count_note_ons(midi_file),
    }


def section_row(section: dict) -> dict:
    score_pages = int(section["score_page_end"]) - int(section["score_page_start"]) + 1
    midi_path = ROOT / section.get("organ_midi_output", "")
    review_path = ROOT / section.get("review_report", "")
    metrics = midi_metrics(midi_path)
    duration = float(metrics.get("duration_seconds", 0.0) or 0.0)
    note_ons = int(metrics.get("note_ons", 0) or 0)
    sanity_errors: list[str] = []

    if not metrics.get("exists"):
        sanity_errors.append("missing MIDI")
    elif metrics.get("tracks") != 1:
        sanity_errors.append(f"expected 1 track, found {metrics.get('tracks')}")
    if metrics.get("exists") and duration < score_pages * 6.0:
        sanity_errors.append("duration too short")
    if metrics.get("exists") and note_ons < score_pages * 75:
        sanity_errors.append("too few note-on events")

    return {
        "id": section["id"],
        "title": section["title"],
        "score_pages": f"{section['score_page_start']}-{section['score_page_end']}",
        "pdf_sheets": f"{section['pdf_sheet_start']}-{section['pdf_sheet_end']}",
        "status": section.get("status", "unknown"),
        "validation_status": section.get("validation_status", "unknown"),
        "midi": str(midi_path.relative_to(ROOT)) if section.get("organ_midi_output") else "",
        "duration_seconds": duration,
        "note_ons": note_ons,
        "review_counts": review_counts(review_path),
        "sanity": "pass" if not sanity_errors else "fail",
        "sanity_errors": sanity_errors,
    }


def render_markdown(rows: list[dict]) -> str:
    lines = ["# Section Status Report", ""]
    lines.append("| Section | Score pages | MIDI | Sanity | Review items | Status |")
    lines.append("|---|---:|---:|---|---:|---|")
    for row in rows:
        review_total = sum(row["review_counts"].values())
        midi_summary = f"{row['duration_seconds']}s / {row['note_ons']} notes"
        sanity = row["sanity"]
        if row["sanity_errors"]:
            sanity += f" ({'; '.join(row['sanity_errors'])})"
        lines.append(
            "| {id} | {score_pages} | {midi_summary} | {sanity} | {review_total} | {validation_status} |".format(
                id=row["id"],
                score_pages=row["score_pages"],
                midi_summary=midi_summary,
                sanity=sanity,
                review_total=review_total,
                validation_status=row["validation_status"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    sections = json.loads(args.manifest.read_text())
    rows = [section_row(section) for section in sections if section.get("organ_midi_output")]
    content = (
        json.dumps(rows, indent=2, sort_keys=True)
        if args.format == "json"
        else render_markdown(rows)
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content + "\n")
    else:
        print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Create a review checklist from Audiveris OMR log warnings."""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path


SHEET_RE = re.compile(r"\[.*?#(?P<sheet>\d+)\]")
KEY_PATTERNS = (
    "WARN",
    "no correct rhythm",
    "too long",
    "No timeOffset",
    "No chord linked",
    "Missing support",
)


def classify(line: str) -> str:
    lower = line.lower()
    if "no correct rhythm" in lower or "too long" in lower or "no timeoffset" in lower:
        return "rhythm"
    if "no chord linked" in lower:
        return "symbol_link"
    if "tesseract" in lower or "missing support" in lower:
        return "ocr"
    if "warn" in lower:
        return "warning"
    return "review"


def extract_sheet(line: str) -> str:
    match = SHEET_RE.search(line)
    return match.group("sheet") if match else "unknown"


def interesting(line: str) -> bool:
    return any(pattern in line for pattern in KEY_PATTERNS)


def collect(log_paths: list[Path]) -> tuple[Counter[str], dict[str, list[tuple[str, str]]]]:
    totals: Counter[str] = Counter()
    by_sheet: dict[str, list[tuple[str, str]]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()

    for path in log_paths:
        for line in path.read_text(errors="replace").splitlines():
            if not interesting(line):
                continue
            sheet = extract_sheet(line)
            category = classify(line)
            detail = line.split("|", 1)[-1].strip()
            key = (f"{path}:{sheet}", category, detail)
            if key in seen:
                continue
            seen.add(key)
            totals[category] += 1
            by_sheet[f"{path}:{sheet}"].append((category, detail))

    return totals, by_sheet


def render_markdown(log_paths: list[Path]) -> str:
    totals, by_sheet = collect(log_paths)
    lines = ["# OMR Review Report", ""]
    lines.append("Generated from Audiveris log files. Treat every entry as a manual MusicXML/MIDI review item.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    if totals:
        for category, count in sorted(totals.items()):
            lines.append(f"- `{category}`: {count}")
    else:
        lines.append("- No review items found.")

    lines.append("")
    lines.append("## Checklist")
    lines.append("")
    for sheet_key in sorted(by_sheet):
        lines.append(f"### {sheet_key}")
        for category, detail in by_sheet[sheet_key]:
            lines.append(f"- [ ] `{category}`: {detail}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="+", type=Path, help="Audiveris .log files.")
    parser.add_argument("--output", type=Path, default=None, help="Optional Markdown output path.")
    args = parser.parse_args()

    missing = [path for path in args.logs if not path.exists()]
    if missing:
        parser.error(f"missing log file(s): {', '.join(str(path) for path in missing)}")

    report = render_markdown(args.logs)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report)
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

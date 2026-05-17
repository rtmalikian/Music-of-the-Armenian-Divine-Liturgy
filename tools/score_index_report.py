#!/usr/bin/env python3
"""Render the contents-derived Yekmalyan score index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "sources" / "score_index.json"


def pdf_sheets(pages: list[int], offset: int) -> str:
    if not pages:
        return ""
    return ", ".join(str(page + offset) for page in pages)


def render_markdown(index: dict[str, Any]) -> str:
    offset = int(index["pdf_sheet_offset_for_primary_score_pages"])
    lines = [
        "# Score Index",
        "",
        f"Source: `{index['source_path']}`",
        "",
        index["notes"],
        "",
        "| No. | ID | Title | Primary score pages | PDF sheets |",
        "|---|---|---|---:|---:|",
    ]
    for chant in index["chants"]:
        pages = chant["primary_score_pages"]
        page_text = ", ".join(str(page) for page in pages)
        lines.append(
            "| {number} | `{id}` | {title} | {pages} | {sheets} |".format(
                number=chant["number"],
                id=chant["id"],
                title=chant["title"],
                pages=page_text,
                sheets=pdf_sheets(pages, offset),
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    index = json.loads(args.index.read_text())
    content = (
        json.dumps(index, indent=2, sort_keys=True)
        if args.format == "json"
        else render_markdown(index)
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content + "\n")
    else:
        print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

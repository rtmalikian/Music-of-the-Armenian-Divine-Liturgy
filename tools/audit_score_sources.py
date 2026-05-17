#!/usr/bin/env python3
"""Audit candidate score PDFs before they are allowed into the OMR workflow."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "sources" / "source_candidates.json"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def parse_pdfinfo(path: Path) -> tuple[dict[str, str], str | None]:
    result = run(["pdfinfo", str(path)])
    if result.returncode != 0:
        return {}, result.stderr.strip() or result.stdout.strip()

    info: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            info[key.strip()] = value.strip()
    return info, None


def parse_pdfimages(path: Path) -> tuple[list[dict[str, str]], str | None]:
    result = run(["pdfimages", "-list", str(path)])
    if result.returncode != 0:
        return [], result.stderr.strip() or result.stdout.strip()

    rows: list[dict[str, str]] = []
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if len(lines) <= 2:
        return rows, None

    for line in lines[2:]:
        parts = line.split()
        if len(parts) < 14:
            continue
        rows.append(
            {
                "page": parts[0],
                "type": parts[2],
                "width": parts[3],
                "height": parts[4],
                "x_ppi": parts[12],
                "y_ppi": parts[13],
            }
        )
    return rows, None


def score_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / candidate["path"]
    exists = path.exists()
    info: dict[str, str] = {}
    images: list[dict[str, str]] = []
    errors: list[str] = []

    if not exists:
        errors.append("missing_file")
    else:
        info, error = parse_pdfinfo(path)
        if error:
            errors.append(f"pdfinfo_failed: {error.splitlines()[0]}")
        images, error = parse_pdfimages(path)
        if error:
            errors.append(f"pdfimages_failed: {error.splitlines()[0]}")

    raster_ppis = [
        min(int(image["x_ppi"]), int(image["y_ppi"]))
        for image in images
        if image["type"] == "image" and image["x_ppi"].isdigit() and image["y_ppi"].isdigit()
    ]
    stencil_ppis = [
        min(int(image["x_ppi"]), int(image["y_ppi"]))
        for image in images
        if image["type"] == "stencil" and image["x_ppi"].isdigit() and image["y_ppi"].isdigit()
    ]
    vector_like = exists and not errors and len(images) == 0
    min_raster_ppi = min(raster_ppis) if raster_ppis else None

    usable_for_production = bool(
        candidate.get("full_divine_liturgy")
        and not errors
        and (vector_like or (min_raster_ppi is not None and min_raster_ppi >= 300))
    )

    return {
        "id": candidate["id"],
        "title": candidate["title"],
        "path": candidate["path"],
        "full_divine_liturgy": bool(candidate.get("full_divine_liturgy")),
        "exists": exists,
        "pages": info.get("Pages"),
        "creator": info.get("Creator"),
        "vector_like": vector_like,
        "min_raster_ppi": min_raster_ppi,
        "max_stencil_ppi": max(stencil_ppis) if stencil_ppis else None,
        "usable_for_production": usable_for_production,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--require-production", action="store_true")
    args = parser.parse_args()

    candidates = json.loads(args.manifest.read_text())
    reports = [score_candidate(candidate) for candidate in candidates]
    print(json.dumps(reports, indent=2, ensure_ascii=False))

    if args.require_production and not any(report["usable_for_production"] for report in reports):
        print("No production-usable full Divine Liturgy score candidate found.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

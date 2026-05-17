#!/usr/bin/env python3
"""Run Audiveris on selected score sheets and create one-track organ MIDI."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from music21 import converter

from flatten_to_organ_midi import flatten_to_organ


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIVERIS = Path("/Applications/Audiveris.app/Contents/MacOS/Audiveris")


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_pdf", type=Path)
    parser.add_argument("--sheets", required=True, help="Audiveris sheet selector, e.g. 55 or 55-57.")
    parser.add_argument("--name", required=True, help="Output stem name.")
    parser.add_argument("--audiveris", type=Path, default=DEFAULT_AUDIVERIS)
    parser.add_argument("--channel", type=int, default=0)
    parser.add_argument("--program", type=int, default=19)
    args = parser.parse_args()

    omr_dir = ROOT / "omr" / args.name
    omr_dir.mkdir(parents=True, exist_ok=True)

    run(
        [
            str(args.audiveris),
            "-batch",
            "-transcribe",
            "-export",
            "-sheets",
            args.sheets,
            "-output",
            str(omr_dir.relative_to(ROOT)),
            str(args.source_pdf),
        ]
    )

    mxl_candidates = sorted(omr_dir.glob("*.mxl"))
    if not mxl_candidates:
        raise FileNotFoundError(f"No MXL export found in {omr_dir}")
    mxl_path = mxl_candidates[-1]

    raw_midi_path = ROOT / "midi" / f"{args.name}_raw_omr.mid"
    organ_midi_path = ROOT / "midi" / f"{args.name}_organ.mid"
    score = converter.parse(mxl_path)
    score.write("midi", fp=str(raw_midi_path))
    flatten_to_organ(raw_midi_path, organ_midi_path, args.channel, args.program)
    print(organ_midi_path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

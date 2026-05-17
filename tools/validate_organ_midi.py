#!/usr/bin/env python3
"""Validate that a MIDI file is safe for the one-track organ playback path."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import mido


def validate(path: Path, channel: int, program: int) -> list[str]:
    midi = mido.MidiFile(path)
    errors: list[str] = []
    if len(midi.tracks) != 1:
        errors.append(f"expected 1 track, found {len(midi.tracks)}")

    note_count = 0
    program_seen = False
    bad_channels: set[int] = set()
    for track in midi.tracks:
        for message in track:
            if message.type == "program_change" and message.program == program and message.channel == channel:
                program_seen = True
            if message.type in {"note_on", "note_off"}:
                note_count += 1
            if hasattr(message, "channel") and message.channel != channel:
                bad_channels.add(message.channel)

    if note_count == 0:
        errors.append("no note_on/note_off messages found")
    if not program_seen:
        errors.append(f"missing program_change channel={channel} program={program}")
    if bad_channels:
        errors.append(f"unexpected MIDI channels: {sorted(bad_channels)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("midi_file", type=Path)
    parser.add_argument("--channel", type=int, default=0)
    parser.add_argument("--program", type=int, default=19)
    args = parser.parse_args()

    errors = validate(args.midi_file, args.channel, args.program)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"valid organ MIDI: {args.midi_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

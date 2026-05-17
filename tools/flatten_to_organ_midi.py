#!/usr/bin/env python3
"""Flatten an OMR MIDI file into one organ playback track."""

from __future__ import annotations

import argparse
from pathlib import Path

import mido


DEFAULT_PROGRAM = 19


def flatten_to_organ(input_path: Path, output_path: Path, channel: int, program: int) -> None:
    source = mido.MidiFile(input_path)
    output = mido.MidiFile(type=1, ticks_per_beat=source.ticks_per_beat)
    track = mido.MidiTrack()
    output.tracks.append(track)
    track.append(mido.MetaMessage("track_name", name="Badarak organ", time=0))
    track.append(mido.Message("program_change", program=program, channel=channel, time=0))

    for message in mido.merge_tracks(source.tracks):
        if message.is_meta:
            if message.type in {"set_tempo", "time_signature", "key_signature"}:
                track.append(message.copy())
            continue
        if message.type in {"note_on", "note_off"}:
            track.append(message.copy(channel=channel))
        elif message.type == "control_change" and message.control in {64, 120, 121, 123}:
            track.append(message.copy(channel=channel))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.save(output_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--channel", type=int, default=0)
    parser.add_argument("--program", type=int, default=DEFAULT_PROGRAM)
    args = parser.parse_args()
    flatten_to_organ(args.input, args.output, args.channel, args.program)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

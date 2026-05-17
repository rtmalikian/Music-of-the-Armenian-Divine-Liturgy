#!/usr/bin/env python3
"""Create a short one-track organ MIDI proof of concept."""

from __future__ import annotations

from pathlib import Path

import mido


OUTPUT = Path("midi/test_organ_excerpt.mid")
TICKS_PER_BEAT = 480


def add_note(track: mido.MidiTrack, note: int, velocity: int, duration: int, delta: int = 0) -> None:
    track.append(mido.Message("note_on", note=note, velocity=velocity, time=delta, channel=0))
    track.append(mido.Message("note_off", note=note, velocity=0, time=duration, channel=0))


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    midi = mido.MidiFile(type=1, ticks_per_beat=TICKS_PER_BEAT)
    track = mido.MidiTrack()
    midi.tracks.append(track)
    track.append(mido.MetaMessage("track_name", name="Badarak organ proof of concept", time=0))
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(72), time=0))
    track.append(mido.Message("program_change", program=19, time=0, channel=0))

    for note in [60, 62, 64, 65, 67, 65, 64, 62, 60]:
        add_note(track, note, 72, TICKS_PER_BEAT, 0)

    midi.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()


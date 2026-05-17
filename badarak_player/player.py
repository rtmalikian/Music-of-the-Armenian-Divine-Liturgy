#!/usr/bin/env python3
"""Single-track Badarak organ MIDI playback for USB MIDI devices."""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import mido


DEFAULT_CHANNEL = 0
DEFAULT_PROGRAM = 19  # General MIDI Church Organ, zero-based program number.


@dataclass(frozen=True)
class OrganPatch:
    channel: int = DEFAULT_CHANNEL
    program: int = DEFAULT_PROGRAM
    bank_msb: int | None = None
    bank_lsb: int | None = None


def list_ports() -> list[str]:
    """Return available MIDI output ports."""
    return list(mido.get_output_names())


def find_port(query: str | None = None) -> str:
    """Find a MIDI output port, preferring a case-insensitive query match."""
    ports = list_ports()
    if not ports:
        raise RuntimeError("No MIDI output ports are available.")
    if not query:
        fantom = [port for port in ports if "fantom" in port.lower()]
        return fantom[0] if fantom else ports[0]

    needle = query.lower()
    for port in ports:
        if needle in port.lower():
            return port
    raise RuntimeError(f"No MIDI output port matched {query!r}. Available ports: {ports}")


def validate_7bit(name: str, value: int | None) -> None:
    if value is None:
        return
    if value < 0 or value > 127:
        raise ValueError(f"{name} must be between 0 and 127; got {value}")


def send_patch(output: mido.ports.BaseOutput, patch: OrganPatch) -> None:
    """Send bank select and program change messages for the organ patch."""
    validate_7bit("channel", patch.channel)
    validate_7bit("program", patch.program)
    validate_7bit("bank_msb", patch.bank_msb)
    validate_7bit("bank_lsb", patch.bank_lsb)

    if patch.bank_msb is not None:
        output.send(
            mido.Message(
                "control_change",
                control=0,
                value=patch.bank_msb,
                channel=patch.channel,
            )
        )
    if patch.bank_lsb is not None:
        output.send(
            mido.Message(
                "control_change",
                control=32,
                value=patch.bank_lsb,
                channel=patch.channel,
            )
        )
    output.send(mido.Message("program_change", program=patch.program, channel=patch.channel))


def force_single_channel(message: mido.Message, channel: int) -> mido.Message:
    """Return a copy of a MIDI message constrained to the configured organ channel."""
    if hasattr(message, "channel"):
        return message.copy(channel=channel)
    return message


def all_notes_off(output: mido.ports.BaseOutput, channel: int) -> None:
    """Stop sustained notes and reset common continuous controllers."""
    output.send(mido.Message("control_change", control=123, value=0, channel=channel))
    output.send(mido.Message("control_change", control=120, value=0, channel=channel))
    output.send(mido.Message("control_change", control=64, value=0, channel=channel))


def play_midi(midi_path: Path, port_query: str | None, patch: OrganPatch) -> str:
    """Play a MIDI file to a selected output port and return the concrete port name."""
    if not midi_path.exists():
        raise FileNotFoundError(midi_path)

    port_name = find_port(port_query)
    midi_file = mido.MidiFile(midi_path)

    with mido.open_output(port_name) as output:
        send_patch(output, patch)
        try:
            for message in midi_file.play():
                if message.is_meta:
                    continue
                output.send(force_single_channel(message, patch.channel))
        except KeyboardInterrupt:
            all_notes_off(output, patch.channel)
            raise
        finally:
            all_notes_off(output, patch.channel)

    return port_name


def test_phrase(port_query: str | None, patch: OrganPatch) -> str:
    """Send a short C major organ phrase to verify Fantom MIDI reception."""
    port_name = find_port(port_query)
    notes = [60, 64, 67, 72]
    with mido.open_output(port_name) as output:
        send_patch(output, patch)
        try:
            for note in notes:
                output.send(mido.Message("note_on", note=note, velocity=72, channel=patch.channel))
                time.sleep(0.35)
                output.send(mido.Message("note_off", note=note, velocity=0, channel=patch.channel))
        finally:
            all_notes_off(output, patch.channel)
    return port_name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Play Badarak organ MIDI to a Roland Fantom.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-ports", help="List MIDI output ports.")

    play = subparsers.add_parser("play", help="Play a MIDI file.")
    play.add_argument("midi_file", type=Path)
    play.add_argument("--port", default=None, help="Case-insensitive output port match, e.g. FANTOM.")
    add_patch_args(play)

    test = subparsers.add_parser("test-phrase", help="Play a short C major test phrase.")
    test.add_argument("--port", default=None, help="Case-insensitive output port match, e.g. FANTOM.")
    add_patch_args(test)
    return parser


def add_patch_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--channel", type=int, default=DEFAULT_CHANNEL)
    parser.add_argument("--program", type=int, default=DEFAULT_PROGRAM)
    parser.add_argument("--bank-msb", type=int, default=None)
    parser.add_argument("--bank-lsb", type=int, default=None)


def patch_from_args(args: argparse.Namespace) -> OrganPatch:
    return OrganPatch(
        channel=args.channel,
        program=args.program,
        bank_msb=args.bank_msb,
        bank_lsb=args.bank_lsb,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "list-ports":
        ports = list_ports()
        if not ports:
            print("No MIDI output ports found.")
            return 1
        for port in ports:
            print(port)
        return 0

    patch = patch_from_args(args)
    if args.command == "play":
        port_name = play_midi(args.midi_file, args.port, patch)
        print(f"Played {args.midi_file} on {port_name}")
        return 0
    if args.command == "test-phrase":
        port_name = test_phrase(args.port, patch)
        print(f"Played test phrase on {port_name}")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())


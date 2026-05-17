# Verification Report

Author: Raphael Malikian <rtmalikian@gmail.com>

Date: 2026-05-17

## Environment

- Workspace: `/Users/raphael/Coding/badarak`
- Python used for venv: `/Users/raphael/.local/bin/python3.12`
- Virtual environment: `badarak_venv`
- Java available: OpenJDK 17 detected

## Completed

- Created `badarak_venv`.
- Installed Python dependencies: `mido`, `python-rtmidi`, `music21`, and `pretty_midi`.
- Confirmed `prompt.md` exists.
- Added separate `badarak_player/` implementation.
- Added source citation notes.
- Added Audiveris-based OMR workflow.
- Downloaded official Sacred Music Council-linked local-only excerpt score PDFs into ignored `sources/` for quality comparison and workflow testing.
- Verified `sources/hrashapar.pdf` and `sources/vor-uzshnorhus.pdf` are MuseScore vector PDFs with no embedded raster page images, making them stronger OMR candidates than the scanned `sources/unduryalt.pdf`.
- Generated `midi/test_organ_excerpt.mid` as a single-track proof-of-concept MIDI file.
- Verified MIDI port listing outside the sandbox. Available ports at verification time: `Akai Network - DAW Control`, `Akai Network - MIDI`.
- Identified Armenian Sacred Music Project as a full-liturgy candidate lead, but did not promote it as the production source because it is outside the original official source constraint and needs rights/access review.

## Pending / Requires Network or Hardware

- Python dependency install initially failed inside the sandbox because PyPI DNS resolution was blocked; rerun with approved PyPI network access succeeded.
- Audiveris is not currently on PATH and still needs installation. Homebrew was checked and has no `audiveris` formula; use the official Audiveris GitHub release/DMG path.
- No full ordinary-Sunday Badarak organ accompaniment score has been confirmed yet; the current official downloadable score candidates are Episcopal Badarak special-music excerpts and must not be treated as the production source.
- No Badarak score page has been OMR-transcribed yet.
- Fantom hardware playback has not been verified in this run because no Fantom MIDI port was present.

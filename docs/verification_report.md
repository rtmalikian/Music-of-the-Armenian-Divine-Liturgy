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
- Installed Audiveris 5.10.2 from the official macOS Apple Silicon DMG into `/Applications/Audiveris.app`.
- Verified `/Applications/Audiveris.app/Contents/MacOS/Audiveris -version`: version 5.10.2, aarch64, Tesseract OCR 5.5.1.
- Verified the downloaded Audiveris DMG SHA256 matched the official release digest: `727c46b4ca4766349be1f582b67cc5aa0d7306113dcf4a18be169d75959f4288`.
- Downloaded official Sacred Music Council-linked local-only excerpt score PDFs into ignored `sources/` for quality comparison and workflow testing.
- Verified `sources/hrashapar.pdf` and `sources/vor-uzshnorhus.pdf` are MuseScore vector PDFs with no embedded raster page images, making them stronger OMR candidates than the scanned `sources/unduryalt.pdf`.
- Generated `midi/test_organ_excerpt.mid` as a single-track proof-of-concept MIDI file.
- Verified MIDI port listing outside the sandbox. Available ports at verification time: `Akai Network - DAW Control`, `Akai Network - MIDI`.
- Identified Armenian Sacred Music Project as a full-liturgy candidate lead, but did not promote it as the production source because it is outside the original official source constraint and needs rights/access review.
- Added `tools/audit_score_sources.py` and `sources/source_candidates.json` to prevent excerpt/test PDFs from being promoted as production OMR inputs.
- Ran Audiveris batch OMR on local-only test excerpt `sources/hrashapar.pdf`:
  - Command: `/Applications/Audiveris.app/Contents/MacOS/Audiveris -batch -transcribe -export -output omr/hrashapar_test sources/hrashapar.pdf`
  - Output: `omr/hrashapar_test/hrashapar.mxl`
  - Status: successful export, with rhythm/OCR warnings requiring manual validation.
- Converted the test MXL to local-only MIDI with `music21`.
  - Output: `midi/hrashapar_omr_test.mid`
  - MIDI check: 4 tracks, 114.75 seconds.

## Pending / Requires Network or Hardware

- Python dependency install initially failed inside the sandbox because PyPI DNS resolution was blocked; rerun with approved PyPI network access succeeded.
- Audiveris is installed but not placed on PATH; invoke it via `/Applications/Audiveris.app/Contents/MacOS/Audiveris`.
- No full ordinary-Sunday Badarak organ accompaniment score has been confirmed yet; the current official downloadable score candidates are Episcopal Badarak special-music excerpts and must not be treated as the production source.
- A Badarak-related excerpt has been OMR-transcribed for workflow testing, but no full Divine Liturgy source has been transcribed.
- Fantom hardware playback has not been verified in this run because no Fantom MIDI port was present.

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
- Downloaded and inspected `sources/armenianmusic-candidate.pdf`, a 420-page full Yegmalian `Chants of the Divine Liturgy of the Armenian Apostolic Church` PDF. It is now the selected local-only full-score candidate.
- Verified the full candidate is not a scanned full-page raster PDF: `pdfimages -list` reports 32 embedded images across 420 pages, while the PDF was produced by Adobe InDesign CC 2015 and text extraction works.
- Checked the user-supplied Armenian Sacred Music Project SharePoint/OneDrive `yegmalian_childrens.pdf` link. Direct command-line fetches returned Microsoft sign-in HTML, not a PDF, so it remains a preferred authenticated-download lead rather than a usable local OMR input.
- Ran Audiveris batch OMR on local-only test excerpt `sources/hrashapar.pdf`:
  - Command: `/Applications/Audiveris.app/Contents/MacOS/Audiveris -batch -transcribe -export -output omr/hrashapar_test sources/hrashapar.pdf`
  - Output: `omr/hrashapar_test/hrashapar.mxl`
  - Status: successful export, with rhythm/OCR warnings requiring manual validation.
- Converted the test MXL to local-only MIDI with `music21`.
  - Output: `midi/hrashapar_omr_test.mid`
  - MIDI check: 4 tracks, 114.75 seconds.
- Ran Audiveris on sheet 55 of the selected full Yegmalian candidate:
  - Command: `/Applications/Audiveris.app/Contents/MacOS/Audiveris -batch -transcribe -export -sheets 55 -output omr/yegmalian_full_page55_test sources/armenianmusic-candidate.pdf`
  - Output: `omr/yegmalian_full_page55_test/armenianmusic-candidate.mxl`
  - Status: successful export, with a rhythm warning requiring manual correction.
- Converted the full-source sheet 55 MXL to local-only MIDI with `music21`.
  - Output: `midi/yegmalian_full_page55_omr_test.mid`
  - MIDI check: 5 tracks, 15.25 seconds.
- Added `tools/flatten_to_organ_midi.py` to collapse OMR MIDI output into one organ playback track.
- Flattened the full-source sheet 55 OMR MIDI into one organ track:
  - Command: `./badarak_venv/bin/python tools/flatten_to_organ_midi.py midi/yegmalian_full_page55_omr_test.mid midi/yegmalian_full_page55_organ_test.mid`
  - Output: `midi/yegmalian_full_page55_organ_test.mid`
  - MIDI check: 1 track, 14.75 seconds, channel 0, program 19.
- Added `tools/omr_to_organ_midi.py` as a repeatable Audiveris -> MXL -> raw MIDI -> one-track organ MIDI wrapper for selected sheet ranges.
- Verified the wrapper on sheet 55 of the full Yegmalian candidate outside the sandbox.
  - Output: `midi/yegmalian_full_page55_wrapper_test_organ.mid`
  - MIDI check: 1 track, 14.75 seconds.

## Pending / Requires Network or Hardware

- Python dependency install initially failed inside the sandbox because PyPI DNS resolution was blocked; rerun with approved PyPI network access succeeded.
- Audiveris is installed but not placed on PATH; invoke it via `/Applications/Audiveris.app/Contents/MacOS/Audiveris`.
- A full Divine Liturgy score candidate has been identified and downloaded for local-only processing, but it is not from the original Diocese/St. Nersess source preference and rights must be reviewed before redistribution.
- A single page from the full Divine Liturgy candidate has been OMR-transcribed for workflow testing, but the full 420-page score has not been batch-transcribed or manually corrected.
- Fantom hardware playback has not been verified in this run because no Fantom MIDI port was present.

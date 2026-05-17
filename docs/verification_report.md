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
- Verified MIDI port listing outside the sandbox. Available Fantom ports at final verification time: `FANTOM-6 7 8`, `FANTOM-6 7 8 DAW CTRL`, `FANTOM-6 7 8 MIDI OUT 1`, `FANTOM-6 7 8 MIDI OUT 2`.
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
- Added `tools/run_section_omr.py` to execute mapped sections from `sources/section_manifest.json` by section id.
- Verified Roland Fantom USB MIDI test phrase:
  - Command: `./badarak_venv/bin/python -m badarak_player.player test-phrase --port "FANTOM-6 7 8 MIDI OUT 1"`
  - Result: `Played test phrase on FANTOM-6 7 8 MIDI OUT 1`
- Added `tools/validate_organ_midi.py` to verify generated organ MIDI files are one-track, channel-constrained, and include the expected organ program change.
- Added `--start-seconds` to `badarak_player/player.py` for practical start-at-time playback during correction or rehearsal.
- Added explicit section metadata fields in `sources/section_manifest.json`: tempo, meter, mode/key, voicing, and validation status.
- Added `tools/omr_review_report.py` and generated `docs/omr_review_report.md` so Audiveris warnings become an explicit correction checklist.
- Re-ran implementation checks after the transport/metadata update:
  - `./badarak_venv/bin/python -m py_compile badarak_player/player.py tools/audit_score_sources.py tools/omr_to_organ_midi.py tools/run_section_omr.py tools/validate_organ_midi.py`
  - `./badarak_venv/bin/python tools/audit_score_sources.py --require-production`
  - `./badarak_venv/bin/python tools/run_section_omr.py khorurt_khorin --dry-run`
  - `./badarak_venv/bin/python tools/validate_organ_midi.py midi/yegmalian_full_page55_wrapper_test_organ.mid`
  - `./badarak_venv/bin/python -m badarak_player.player play --help`
  - `./badarak_venv/bin/python -c "from pathlib import Path; import mido; from badarak_player.player import iter_timed_messages; mf=mido.MidiFile('midi/test_organ_excerpt.mid'); msgs=list(iter_timed_messages(mf, start_seconds=0.5)); print(len(msgs)); print(round(msgs[0][0], 3), msgs[0][1].type)"`
- Verified OMR review report generation:
  - `./badarak_venv/bin/python tools/omr_review_report.py omr/yegmalian_full_page55_test/armenianmusic-candidate-20260517T0558.log --output docs/omr_review_report.md`
- Ran the first mapped full-score section batch, `khorurt_khorin`, outside the sandbox after the sandboxed Audiveris run aborted with `SIGABRT`.
  - Command: `./badarak_venv/bin/python tools/run_section_omr.py khorurt_khorin`
  - Output MusicXML: `omr/khorurt_khorin/armenianmusic-candidate.mxl`
  - Output organ MIDI: `midi/khorurt_khorin_organ.mid`
  - MIDI validation: `./badarak_venv/bin/python tools/validate_organ_midi.py midi/khorurt_khorin_organ.mid`
  - MIDI structure: 1 track, 173.75 seconds, 2,244 note-on events.
  - Review report: `docs/omr_review_report_khorurt_khorin.md`, with 16 OCR, 14 rhythm, and 23 symbol-link checklist items.
- Verified score-derived section playback over USB MIDI to the Fantom:
  - Command: `./badarak_venv/bin/python -m badarak_player.player play midi/khorurt_khorin_organ.mid --port "FANTOM-6 7 8 MIDI OUT 1"`
  - Result: `Played midi/khorurt_khorin_organ.mid on FANTOM-6 7 8 MIDI OUT 1`
  - Scope: validates the playback transport path for a generated organ MIDI section; it does not validate musical correctness of the raw OMR transcription.
- Ran the second mapped full-score section batch, `hays_hark`.
  - Command: `./badarak_venv/bin/python tools/run_section_omr.py hays_hark`
  - Output MusicXML: `omr/hays_hark/armenianmusic-candidate.mxl`
  - Output organ MIDI: `midi/hays_hark_organ.mid`
  - MIDI validation: `./badarak_venv/bin/python tools/validate_organ_midi.py midi/hays_hark_organ.mid`
  - MIDI structure: 1 track, 150.81 seconds, 1,523 note-on events.
  - Review report: `docs/omr_review_report_hays_hark.md`, with 12 OCR, 13 symbol-link, and 18 time-signature warning checklist items.
- Ran the next inferred full-score section batch, `barekhosutyamp`.
  - Command: `./badarak_venv/bin/python tools/omr_to_organ_midi.py sources/armenianmusic-candidate.pdf --sheets 69-75 --name barekhosutyamp --channel 0 --program 19`
  - Output MusicXML: `omr/barekhosutyamp/armenianmusic-candidate.mvtnull.mxl`
  - Output organ MIDI: `midi/barekhosutyamp_organ.mid`
  - MIDI validation: `./badarak_venv/bin/python tools/validate_organ_midi.py midi/barekhosutyamp_organ.mid`
  - MIDI structure: 1 track, 55.0 seconds, 729 note-on events.
  - Review report: `docs/omr_review_report_barekhosutyamp.md`, with 14 OCR, 38 rhythm, 19 symbol-link, and 8 warning checklist items.
  - Risk note: Audiveris split this range into multiple internal scores and exported `.mvtnull.mxl`; this section needs especially careful manual score review.
- Ran the next inferred section batch, `aysor_zhoghovyal`.
  - Command: `./badarak_venv/bin/python tools/omr_to_organ_midi.py sources/armenianmusic-candidate.pdf --sheets 76-82 --name aysor_zhoghovyal --channel 0 --program 19`
  - Output MusicXML: `omr/aysor_zhoghovyal/armenianmusic-candidate.mvtnull.mxl`
  - Output organ MIDI: `midi/aysor_zhoghovyal_organ.mid`
  - MIDI validation: `./badarak_venv/bin/python tools/validate_organ_midi.py midi/aysor_zhoghovyal_organ.mid`
  - MIDI structure: 1 track, 14.0 seconds, 87 note-on events.
  - Review report: `docs/omr_review_report_aysor_zhoghovyal.md`, with 14 OCR, 2 rhythm, 16 symbol-link, and 30 warning checklist items.
  - Failure note: Audiveris created ten internal scores and logged PartCollation warnings plus a NullPointerException during export. The MIDI is structurally valid but fails musical sanity for a seven-page section.
- Retried `aysor_zhoghovyal` one PDF sheet at a time for sheets 76-82.
  - Outputs: `midi/aysor_zhoghovyal_sheet76_organ.mid` through `midi/aysor_zhoghovyal_sheet82_organ.mid`.
  - MIDI validation: each retry MIDI passes `tools/validate_organ_midi.py` as a one-track organ file.
  - Retry metrics: sheet 76 is 20.00 seconds / 263 note-ons; sheet 77 is 4.00 seconds / 30 note-ons; sheet 78 is 25.00 seconds / 280 note-ons; sheet 79 is 12.50 seconds / 153 note-ons; sheet 80 is 12.00 seconds / 61 note-ons; sheet 81 is 4.00 seconds / 19 note-ons; sheet 82 is 14.00 seconds / 87 note-ons.
  - Result: per-sheet splitting recovered more usable raw material than the seven-sheet export, especially sheets 76 and 78, but the section is still not service-ready and must be manually corrected or re-sourced.
- Extracted the full score table of contents with `pdftotext -layout` and created `sources/score_index.json`.
  - Primary score page 1 maps to PDF sheet 55, so the primary-score to PDF-sheet offset is +54.
  - Rendered `docs/score_index.md` with `tools/score_index_report.py`.
  - Correction: `Aysor zhoghovyal` starts at primary score page 17 / PDF sheet 71. The earlier PDF sheets 76-82 attempt is therefore a misaligned late-Aysor/following-section batch, not a complete Aysor section transcription.
- Added `tools/validate_section_midi.py` to catch structurally valid but musically implausible OMR outputs.
  - `./badarak_venv/bin/python tools/validate_section_midi.py khorurt_khorin` passed: 173.75 seconds, 2,244 note-on events, 8 score pages.
  - `./badarak_venv/bin/python tools/validate_section_midi.py hays_hark` passed: 150.81 seconds, 1,523 note-on events, 6 score pages.
  - `./badarak_venv/bin/python tools/validate_section_midi.py aysor_zhoghovyal` failed as intended: 14.0 seconds and 87 note-on events for 7 score pages.
- Added `tools/section_status_report.py` to summarize all generated sections, review counts, and sanity status.
  - Command: `./badarak_venv/bin/python tools/section_status_report.py --output docs/section_status_report.md`
  - Result: `docs/section_status_report.md` reports three sanity-passing raw sections and one sanity-failing section.

## Pending / Requires Network or Hardware

- Python dependency install initially failed inside the sandbox because PyPI DNS resolution was blocked; rerun with approved PyPI network access succeeded.
- Audiveris is installed but not placed on PATH; invoke it via `/Applications/Audiveris.app/Contents/MacOS/Audiveris`.
- A full Divine Liturgy score candidate has been identified and downloaded for local-only processing, but it is not from the original Diocese/St. Nersess source preference and rights must be reviewed before redistribution.
- Four early inferred section batches from the full Divine Liturgy candidate have been attempted. The contents-derived score index now shows the `aysor_zhoghovyal` attempt was misaligned, so it is retained only as raw recovery evidence. The full 420-page score has not been batch-transcribed or manually corrected.
- Score-derived organ MIDI playback has been transport-tested on the Fantom for one raw section. Musical correctness and service-readiness still require manual correction and listening review.

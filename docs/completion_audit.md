# Completion Audit

Author: Raphael Malikian <rtmalikian@gmail.com>

Date: 2026-05-17

Objective: implement `prompt.md` as a local toolchain for sourcing Armenian Divine Liturgy / Badarak score material, converting score PDF material toward MIDI, flattening it to one organ track, and playing it over USB MIDI on a Roland Fantom.

## Prompt-to-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Find modern high-quality Divine Liturgy / Badarak score PDF | `sources/armenianmusic-candidate.pdf` is a local-only 420-page Yegmalian full reprint; `docs/source_citations.md` records source and quality notes. | Implemented for local processing; rights/source-preference caveat remains |
| Prefer official Diocese / St. Nersess sources | Eastern Diocese Sacred Music Council and St. Nersess were checked; official Diocese downloads found were excerpts, not full liturgy. User-supplied Armenian Sacred Music Project SharePoint lead was checked but required sign-in. | Partially met; best usable full PDF is not from original priority list |
| Compare PDF quality / DPI | `tools/audit_score_sources.py --require-production` passes; vector excerpts and 420-page vector-layout full candidate are documented. | Implemented |
| Create `badarak_venv` | `badarak_venv` exists and imports `mido`, `rtmidi`, `music21`, and `pretty_midi`. | Implemented |
| Install best open-source OMR tool | Audiveris 5.10.2 installed at `/Applications/Audiveris.app`; version and SHA256 documented. | Implemented |
| Convert at least one score page/excerpt to MIDI | Hrashapar excerpt, full Yegmalian page 55, and the mapped 8-page `khorurt_khorin` section were processed through Audiveris -> MXL -> MIDI. | Implemented as proof of concept |
| Build OMR validation workflow | `tools/omr_review_report.py` generates `docs/omr_review_report.md` from Audiveris logs, turning OCR/rhythm/symbol warnings into manual correction checklist items. | Implemented |
| Normalize to one organ track | `tools/flatten_to_organ_midi.py` creates one-track organ MIDI; verified `midi/yegmalian_full_page55_wrapper_test_organ.mid` and `midi/khorurt_khorin_organ.mid` have one track. | Implemented |
| Store per-section metadata | `sources/section_manifest.json` stores title, source page range, PDF sheet range, tempo, meter, mode/key, voicing, and validation status. Unknown musical fields are explicitly `unverified`. | Implemented |
| Build repeatable OMR-to-organ wrapper | `tools/omr_to_organ_midi.py` runs Audiveris, converts MXL to MIDI, and flattens to one organ track. | Implemented |
| Build Roland Fantom USB MIDI player | `badarak_player/player.py` supports list-ports, test-phrase, play, `--start-seconds`, patch/program selection, and all-notes-off cleanup. | Implemented |
| Verify MIDI ports and Fantom | `list-ports` saw Fantom ports; `test-phrase` completed on `FANTOM-6 7 8 MIDI OUT 1`. | Implemented |
| Document setup and usage | `README.md`, `docs/omr_workflow.md`, `docs/source_citations.md`, and `docs/verification_report.md`. | Implemented |
| Keep copyrighted PDFs local-only | `.gitignore` excludes `sources/*.pdf`, OMR outputs, generated score MIDI, venv, and backups. | Implemented |
| Backup before editing existing files | `project-edit-backups.md` logs backups. | Implemented |
| Publish GitHub repository | Public repo exists: https://github.com/rtmalikian/Music-of-the-Armenian-Divine-Liturgy | Implemented |

## Remaining Gaps

- The full 420-page Yegmalian score has not been batch-transcribed end-to-end; one mapped 8-page section has been batch-exported.
- The generated OMR MIDI has not been manually corrected against the score, although warning checklists now exist in `docs/omr_review_report.md` and `docs/omr_review_report_khorurt_khorin.md`.
- The one-page full-score proof includes Audiveris rhythm warnings, so it is not service-ready.
- The user-supplied Armenian Sacred Music Project `yegmalian_childrens.pdf` link could not be fetched anonymously; browser-authenticated download may still be useful.
- Full score-derived organ MIDI playback on the Fantom has not been musically validated in the church-use sense; only the built-in test phrase was sent successfully.

## Current Conclusion

The project now has a working, verified proof-of-concept toolchain and a selected local-only full-score candidate. It is ready for the next phase: authenticated/full-source acquisition if desired, batch OMR by service section, manual MusicXML/MIDI correction, and musical validation on the Fantom.

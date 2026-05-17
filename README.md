# Music of the Armenian Divine Liturgy

Author: Raphael Malikian <rtmalikian@gmail.com>

GitHub: https://github.com/rtmalikian/Music-of-the-Armenian-Divine-Liturgy

This project is a local workflow for preparing organ MIDI from Armenian Divine Liturgy / Badarak score material and playing it over USB MIDI on a Roland Fantom when an organist is not available.

The implementation is intentionally separate from `music_script_python/`. That folder is only a reference for Fantom-oriented orchestration patterns.

## Current Status

- `badarak_venv` has been created with Python 3.12.
- Source research notes are in `docs/source_citations.md`.
- The OMR workflow is documented in `docs/omr_workflow.md`.
- A single-track Fantom-focused MIDI player is in `badarak_player/player.py`.
- A short proof-of-concept MIDI generator is in `tools/create_test_midi.py`.

## Setup

```bash
/Users/raphael/.local/bin/python3.12 -m venv badarak_venv
./badarak_venv/bin/python -m pip install --upgrade pip
./badarak_venv/bin/python -m pip install -r requirements.txt
```

Audiveris is the recommended open-source OMR tool for scanned score PDFs. Homebrew currently does not provide an `audiveris` formula on this machine. Audiveris 5.10.2 was installed from the official macOS Apple Silicon DMG:

```bash
/Applications/Audiveris.app/Contents/MacOS/Audiveris -version
```

The official release source is https://github.com/Audiveris/audiveris/releases/tag/5.10.2.

## Basic MIDI Workflow

List MIDI output ports:

```bash
./badarak_venv/bin/python -m badarak_player.player list-ports
```

Create a short local proof-of-concept MIDI excerpt:

```bash
./badarak_venv/bin/python tools/create_test_midi.py
```

Play a MIDI file to the Roland Fantom:

```bash
./badarak_venv/bin/python -m badarak_player.player play midi/test_organ_excerpt.mid --port "FANTOM"
```

The default patch is General MIDI Church Organ (`program=19` as a zero-based MIDI program number). For a specific Roland Fantom organ tone, pass explicit bank/program values after confirming them on the Fantom:

```bash
./badarak_venv/bin/python -m badarak_player.player play midi/test_organ_excerpt.mid \
  --port "FANTOM" --bank-msb 87 --bank-lsb 64 --program 19
```

## Source Policy

Do not commit copyrighted PDFs or generated reproductions unless the source explicitly permits redistribution. Keep PDFs under `sources/` for local processing only; `.gitignore` excludes those files by default.

## Score Quality Selection

For OMR, prefer vector PDFs over scanned raster PDFs. The current official Sacred Music Council score candidates were checked with `pdfinfo` and `pdfimages -list`:

- `sources/hrashapar.pdf`: MuseScore vector PDF, 5 pages, no embedded raster page images. Recommended first OMR candidate.
- `sources/vor-uzshnorhus.pdf`: MuseScore vector PDF, 2 pages, no embedded raster page images. Also recommended.
- `sources/unduryalt.pdf`: scanned/Canon PDF, 2 pages, 150 PPI grayscale page images plus 300 PPI stencils. Lower priority unless a better source is found.

These three files are excerpts/special-music test fixtures only. The production source must be an entire Divine Liturgy score PDF. If a later official full-liturgy PDF is found, compare it the same way before selecting it for score-to-MIDI.

Run the source audit before any production OMR run:

```bash
./badarak_venv/bin/python tools/audit_score_sources.py --require-production
```

This command intentionally fails until `sources/source_candidates.json` contains a real, locally present, full Divine Liturgy score candidate with either vector notation or raster page images at 300 PPI or better.

Run a one-page OMR-to-organ-MIDI test from the selected full score:

```bash
./badarak_venv/bin/python tools/omr_to_organ_midi.py \
  sources/armenianmusic-candidate.pdf \
  --sheets 55 \
  --name yegmalian_full_page55
```

The generated score-derived files remain local-only under ignored `omr/` and `midi/` paths until rights and musical validation are complete.

Run a known section from `sources/section_manifest.json`:

```bash
./badarak_venv/bin/python tools/run_section_omr.py khorurt_khorin --dry-run
./badarak_venv/bin/python tools/run_section_omr.py khorurt_khorin
```

# Music of the Armenian Divine Liturgy

Author: Raphael Malikian <rtmalikian@gmail.com>

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

Audiveris is the recommended open-source OMR tool for scanned score PDFs. Homebrew currently does not provide an `audiveris` formula on this machine, so install from the official Audiveris release channel:

```bash
open https://github.com/Audiveris/audiveris/releases
```

Download the Apple Silicon macOS DMG when available, install the app, then verify from the app UI or CLI wrapper if one is installed.

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

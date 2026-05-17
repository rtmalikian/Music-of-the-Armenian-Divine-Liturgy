# OMR Workflow

Author: Raphael Malikian <rtmalikian@gmail.com>

Recommended OMR tool: Audiveris 5.10.2.

Reason: Audiveris remains the most mature open-source optical music recognition tool for printed score PDFs/images and can export MusicXML, which can then be converted or cleaned into MIDI.

## Install

```bash
/Applications/Audiveris.app/Contents/MacOS/Audiveris -version
```

Homebrew was checked on 2026-05-17 and did not provide an `audiveris` formula. Audiveris was installed from the official GitHub macOS Apple Silicon DMG:

```bash
curl -L -o /private/tmp/Audiveris-5.10.2-macosx-arm64.dmg \
  https://github.com/Audiveris/audiveris/releases/download/5.10.2/Audiveris-5.10.2-macosx-arm64.dmg
shasum -a 256 /private/tmp/Audiveris-5.10.2-macosx-arm64.dmg
hdiutil attach /private/tmp/Audiveris-5.10.2-macosx-arm64.dmg -nobrowse -readonly
cp -R /Volumes/Audiveris/Audiveris.app /Applications/Audiveris.app
hdiutil detach /Volumes/Audiveris
```

Expected SHA256:

```text
727c46b4ca4766349be1f582b67cc5aa0d7306113dcf4a18be169d75959f4288
```

## Processing Steps

1. Place local-only source PDFs under `sources/`.
2. Split or render the target page range at high resolution if Audiveris needs image input.
3. Run Audiveris on the score PDF or page images.
4. Export MusicXML into `omr/`.
5. Review the MusicXML in notation software before trusting the MIDI.
6. Correct notes, ties, rests, key signatures, meter, repeats, and tempo markings manually as needed.
7. Export cleaned single-track organ MIDI into `midi/`.
8. Record validation notes in `docs/validation_log.md`.

For a repeatable proof-of-concept run against selected sheets:

```bash
./badarak_venv/bin/python tools/omr_to_organ_midi.py \
  sources/armenianmusic-candidate.pdf \
  --sheets 55 \
  --name yegmalian_full_page55
```

This wrapper runs Audiveris, converts the exported MXL to MIDI, and flattens the result to one organ track.

For sections already mapped in `sources/section_manifest.json`, prefer:

```bash
./badarak_venv/bin/python tools/run_section_omr.py khorurt_khorin --dry-run
./badarak_venv/bin/python tools/run_section_omr.py khorurt_khorin
```

Use `--dry-run` first to confirm the selected sheet range before launching a longer Audiveris batch.

## Validation Rules

- Do not treat raw OMR output as service-ready.
- Validate by page and measure.
- Mark each piece as one of: `raw_omr`, `needs_correction`, `corrected`, `playback_tested`, `service_ready`.
- Keep the Fantom playback copy single-channel unless a real organ registration plan requires otherwise.

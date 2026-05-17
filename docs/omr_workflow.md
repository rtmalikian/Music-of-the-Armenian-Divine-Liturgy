# OMR Workflow

Author: Raphael Malikian <rtmalikian@gmail.com>

Recommended OMR tool: Audiveris.

Reason: Audiveris remains the most mature open-source optical music recognition tool for printed score PDFs/images and can export MusicXML, which can then be converted or cleaned into MIDI.

## Install

```bash
open https://github.com/Audiveris/audiveris/releases
```

Homebrew was checked on 2026-05-17 and did not provide an `audiveris` formula. Use the official GitHub release page and download the current macOS Apple Silicon DMG when available. Record the installed version and launch path in `docs/verification_report.md`.

## Processing Steps

1. Place local-only source PDFs under `sources/`.
2. Split or render the target page range at high resolution if Audiveris needs image input.
3. Run Audiveris on the score PDF or page images.
4. Export MusicXML into `omr/`.
5. Review the MusicXML in notation software before trusting the MIDI.
6. Correct notes, ties, rests, key signatures, meter, repeats, and tempo markings manually as needed.
7. Export cleaned single-track organ MIDI into `midi/`.
8. Record validation notes in `docs/validation_log.md`.

## Validation Rules

- Do not treat raw OMR output as service-ready.
- Validate by page and measure.
- Mark each piece as one of: `raw_omr`, `needs_correction`, `corrected`, `playback_tested`, `service_ready`.
- Keep the Fantom playback copy single-channel unless a real organ registration plan requires otherwise.

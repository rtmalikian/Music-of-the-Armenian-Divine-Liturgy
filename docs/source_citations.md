# Source Citations

Author: Raphael Malikian <rtmalikian@gmail.com>

Research date: 2026-05-17

## Candidate Official Sources

1. Eastern Diocese / Sacred Music Council: Holy Badarak
   - URL: https://armenianchurchmusic.org/resources/holy-badarak
   - Evidence: The page links to Badarak-specific materials including `Yekmalian Badarak`, `Children's Badarak book`, `Deacons Chants`, `Zhamamoods`, `Jashoo Sharagans`, and `Episcopal Badarak`.
   - Use: Primary navigation hub for finding Badarak score/music material.
   - Restriction note: The site footer states that trademarks, copyright, and articles belong to their original owners and that reproduction of images or the website is prohibited. Do not commit copied score PDFs or scraped images from this site without explicit permission.

2. Eastern Diocese / Sacred Music Council: Yegmalian Badarak
   - URL: https://armenianchurchmusic.org/tutorials/yegmalian-badarak
   - Evidence: The page exists as a Badarak tutorial resource and currently exposes SoundCloud tutorial audio embeds.
   - Use: Reference/listening support for validating transcribed material.
   - Limitation: This page did not expose a downloadable PDF score during this inspection.

3. St. Nersess Armenian Seminary: Divine Liturgy texts
   - URL: https://stnersess.edu/resources/liturgical-services/divine-liturgy-texts/
   - English PDF: https://stnersess.edu/wp-content/uploads/2022/03/the_divine_liturgy.pdf
   - Armenian PDF: https://stnersess.edu/wp-content/uploads/2022/03/divineliturgyarmunicode.pdf
   - Evidence: The page provides complete Divine Liturgy text downloads in English and Armenian.
   - Use: Liturgical text alignment and section naming.
   - Limitation: These PDFs are text resources, not full organ accompaniment scores.

4. Mother See of Holy Etchmiadzin: Divine Liturgy overview
   - URL: https://www.armenianchurch.org/en/holy-liturgy
   - Evidence: Official explanatory page for the structure of the Divine Liturgy.
   - Use: Context for service structure, not score extraction.

5. Eastern Diocese / Sacred Music Council: Episcopal Badarak special music
   - URL: https://armenianchurchmusic.org/e-sharagan/episcopal-badarak
   - Evidence: The page links to score PDFs for `Hrashapar`, `Unduryalt`, and `Vor uzShnorhus` as special music for Episcopal Badarak.
   - Local-only files downloaded for quality comparison:
     - `sources/hrashapar.pdf`
     - `sources/unduryalt.pdf`
     - `sources/vor-uzshnorhus.pdf`
   - Use: Best current official score candidates for the score-to-MIDI proof-of-concept path.
   - Limitation: These are excerpts/special-music pieces, not the full Divine Liturgy. They are suitable for testing the OMR and playback workflow only.

## Current Source Decision

The strongest official path for score-related material is the Eastern Diocese Sacred Music Council site, starting with the Holy Badarak hub and the Episcopal Badarak special-music score links. The St. Nersess PDFs are useful for liturgical text alignment but are not sufficient as organ-score source material.

The production source has not been selected yet because the downloaded official PDFs are excerpts. The required production source is an entire Divine Liturgy score PDF, preferably vector-generated. The excerpt PDFs remain useful for validating the OMR and Roland playback pipeline.

Keep any downloaded PDFs under `sources/` for local processing only. Do not commit PDFs until their redistribution terms are confirmed.

## PDF Quality Comparison

Command used:

```bash
pdfinfo sources/<file>.pdf
pdfimages -list sources/<file>.pdf
```

Results:

| File | Source type | Pages | Raster image evidence | OMR priority |
|---|---|---:|---|---|
| `sources/hrashapar.pdf` | MuseScore vector PDF | 5 | `pdfimages -list` shows no embedded raster images | Highest |
| `sources/vor-uzshnorhus.pdf` | MuseScore vector PDF | 2 | `pdfimages -list` shows no embedded raster images | Highest |
| `sources/unduryalt.pdf` | Canon scanned PDF | 2 | 150 PPI grayscale page images plus 300 PPI stencils | Lower |

Selection rule: use vector PDFs first because they are resolution-independent and avoid scanner DPI loss. If a raster-only PDF must be used, require at least 300 PPI page images where possible; `unduryalt.pdf` is not the strongest candidate because its main grayscale page images are 150 PPI.

Full-liturgy source rule: do not promote any excerpt score as the production source. Production OMR must use an entire Divine Liturgy score PDF. Excerpts can be used only for installation, OMR, and playback tests.

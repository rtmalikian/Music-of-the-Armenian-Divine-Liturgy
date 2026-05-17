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

## Full-Liturgy Candidate Leads

These leads appear to contain entire Divine Liturgy publications, but they are not yet promoted as the production source because they are outside the original official Diocese/St. Nersess source constraint or require follow-up access/rights review.

1. Armenian Sacred Music Project library
   - URL: https://sacred-music.org/library-%D5%A3%D6%80%D5%A1%D5%A4%D5%A1%D6%80%D5%A1%D5%B6/
   - Evidence: The library page lists full liturgy publications, including Khorenian `Divine Liturgy (1999 - AACCA)` and Yegmalian `C Major`, `D Major`, and `F Major` publications.
   - Use: Candidate lead for locating an entire Divine Liturgy score if official Diocese/St. Nersess paths do not expose a complete downloadable score.
   - Limitation: The linked files are hosted through SharePoint/HathiTrust/MuseScore and need separate access, copyright, and source-eligibility review before use.

1a. Armenian Sacred Music Project / SharePoint: Yegmalian Children's Badarak
   - URL: https://armeniansacredmusicproject-my.sharepoint.com/personal/sderderian_sacred-music_org/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fsderderian%5Fsacred%2Dmusic%5Forg%2FDocuments%2FPublicLibrary%2Fyegmalian%5Fchildrens%2Epdf&parent=%2Fpersonal%2Fsderderian%5Fsacred%2Dmusic%5Forg%2FDocuments%2FPublicLibrary&ga=1
   - Evidence: User supplied as a good starter PDF and it matches the Armenian Sacred Music Project library's Yegmalian `C Major (Children's Badarak)` lead.
   - Attempted local fetch: saved `sources/yegmalian-childrens-sharepoint.pdf` and `sources/yegmalian-childrens-sharepoint-download.pdf`, but both resolved to Microsoft sign-in HTML rather than PDF content.
   - Use: Preferred follow-up lead if browser-authenticated download is available.
   - Limitation: Not usable for command-line OMR in this run because unauthenticated download did not return a PDF.

2. ArmenianMusic full Yegmalian PDF
   - URL: https://armenianmusic.am/data/files/library/1/16130267704941.pdf
   - Local-only path: `sources/armenianmusic-candidate.pdf`
   - Evidence: `pdfinfo` reports 420 pages, Adobe InDesign CC 2015 creator, and PDF version 1.5. `pdftotext` identifies the work as `Chants of the Divine Liturgy of the Armenian Apostolic Church`, transcribed and arranged for three and four voices by M. Yekmalyan, Yerevan 2017. The front matter says this volume is the first complete reprint of Yekmalyan's 1896 Divine Liturgy.
   - Quality: Layout/notation appears vector-based; `pdfimages -list` reports only 32 embedded images across 420 pages rather than full-page raster scans. Some embedded images are 100-150 PPI, but they are not the main score-page source.
   - Use: Selected full-score candidate for local OMR experimentation.
   - Limitation: This is not from the original Diocese/St. Nersess priority list and must stay local-only until rights and redistribution terms are confirmed.

## Current Source Decision

The strongest official path for score-related material is the Eastern Diocese Sacred Music Council site, starting with the Holy Badarak hub and the Episcopal Badarak special-music score links. The St. Nersess PDFs are useful for liturgical text alignment but are not sufficient as organ-score source material.

The production source candidate is now `sources/armenianmusic-candidate.pdf`, a 420-page full Yegmalian Divine Liturgy score. The official Diocese/Sacred Music Council downloads remain excerpt test fixtures. The selected full candidate is suitable for local OMR experimentation but should not be committed or redistributed until rights are confirmed.

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

The machine-readable candidate list is `sources/source_candidates.json`. Run `tools/audit_score_sources.py --require-production` before any production OMR job; it must fail unless at least one candidate is both `full_divine_liturgy: true` and technically suitable.

# Aysor Zhoghovyal Per-Sheet Retry Report

Generated after the seven-sheet `aysor_zhoghovyal` batch produced only 14.0 seconds / 87 note-on events and failed musical sanity.

Important correction: the contents-derived score index places `Aysor zhoghovyal` at primary score page 17, which maps to PDF sheet 71. Therefore the retry of PDF sheets 76-82 is not a complete corrected Aysor transcription. It is a misaligned late-Aysor/following-section recovery batch that still contains useful raw OMR material for manual review.

The retry split PDF sheets 76-82 into one-sheet Audiveris jobs, then converted each MusicXML export to a one-track organ MIDI file.

| PDF sheet | MusicXML export | Organ MIDI | Duration | Note-ons | Review report | Assessment |
| --- | --- | --- | ---: | ---: | --- | --- |
| 76 | `omr/aysor_zhoghovyal_sheet76/armenianmusic-candidate.mxl` | `midi/aysor_zhoghovyal_sheet76_organ.mid` | 20.00s | 263 | `docs/omr_review_report_aysor_zhoghovyal_sheet76.md` | Best recovered sheet; still raw OMR. |
| 77 | `omr/aysor_zhoghovyal_sheet77/armenianmusic-candidate.mvtnull.mxl` | `midi/aysor_zhoghovyal_sheet77_organ.mid` | 4.00s | 30 | `docs/omr_review_report_aysor_zhoghovyal_sheet77.md` | Failed / too sparse. |
| 78 | `omr/aysor_zhoghovyal_sheet78/armenianmusic-candidate.mvtnull.mxl` | `midi/aysor_zhoghovyal_sheet78_organ.mid` | 25.00s | 280 | `docs/omr_review_report_aysor_zhoghovyal_sheet78.md` | Best recovered `.mvtnull` sheet; high risk. |
| 79 | `omr/aysor_zhoghovyal_sheet79/armenianmusic-candidate.mvtnull.mxl` | `midi/aysor_zhoghovyal_sheet79_organ.mid` | 12.50s | 153 | `docs/omr_review_report_aysor_zhoghovyal_sheet79.md` | Partial / high risk. |
| 80 | `omr/aysor_zhoghovyal_sheet80/armenianmusic-candidate.mvtnull.mxl` | `midi/aysor_zhoghovyal_sheet80_organ.mid` | 12.00s | 61 | `docs/omr_review_report_aysor_zhoghovyal_sheet80.md` | Partial / too sparse. |
| 81 | `omr/aysor_zhoghovyal_sheet81/armenianmusic-candidate.mvtnull.mxl` | `midi/aysor_zhoghovyal_sheet81_organ.mid` | 4.00s | 19 | `docs/omr_review_report_aysor_zhoghovyal_sheet81.md` | Failed / too sparse. |
| 82 | `omr/aysor_zhoghovyal_sheet82/armenianmusic-candidate.mxl` | `midi/aysor_zhoghovyal_sheet82_organ.mid` | 14.00s | 87 | `docs/omr_review_report_aysor_zhoghovyal_sheet82.md` | Structurally valid but likely incomplete. |

All seven retry MIDI files pass the structural one-track organ MIDI validator. That does not make them service-ready: the short durations, `.mvtnull.mxl` exports, and Audiveris warnings mean the section still needs manual correction against the PDF score or a better source.

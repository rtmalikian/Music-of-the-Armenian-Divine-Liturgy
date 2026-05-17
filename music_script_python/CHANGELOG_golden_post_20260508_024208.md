# Golden Post Promotion - 2026-05-08 02:42:08

## Backups

- `backups/20260508_024208/orchestrator.py.backup_20260508_024208`
- `backups/20260508_024208/production_engine.py.backup_20260508_024208`

## Promoted Source

- Fresh MIDI-to-golden-post output root: `output/05062026_090555_78bpm_F_F_Major_4-4_drill-lofi_inv/test_improvement/runs/20260508_012313/fresh_midi_to_golden_post_pipeline`
- User-approved render root: `output/05062026_090555_78bpm_F_F_Major_4-4_drill-lofi_inv/test_improvement/runs/20260508_014613/full_song_dry_stereo_wall`
- Approved master: `output/05062026_090555_78bpm_F_F_Major_4-4_drill-lofi_inv/test_improvement/runs/20260508_014613/full_song_dry_stereo_wall/12_dry_stereo_wall/full_song_master.wav`
- Approved streaming master: `output/05062026_090555_78bpm_F_F_Major_4-4_drill-lofi_inv/test_improvement/runs/20260508_014613/full_song_dry_stereo_wall/12_dry_stereo_wall/full_song_streaming_master.wav`

## Production Changes

- Added `golden_post_processor.py` as a production module; it does not import isolated test scripts.
- Added `golden_post_params.json` with the approved candidate parameters.
- Default pan seed mode is `run`, so snare/hat/aux placements vary each render within the approved non-extreme ranges; use `--golden-pan-seed 60233` to reproduce the approved test panning exactly.
- Updated `production_engine.py` so Step 3 uses the promoted golden post path by default:
  - dry stereo-wall drum rebuild from processed component stems
  - snare/clap left-of-center with subtle autopan
  - hats right-of-center with subtle autopan
  - aux percussion wider but gain-tamed
  - post-pan drum gain staging against melody
  - kick parallel support
  - kick-triggered bass ducking
  - melody and pad low-mid cleanup
  - section-aware reverb/delay trimming and dry-program ducking
  - return-to-dry normalization
  - JSON and Markdown objective analysis reports
- Updated `orchestrator.py` with controls:
  - `--golden-post` default enabled
  - `--no-golden-post`
  - `--golden-post-params PATH`
  - `--golden-pan-seed INT`

## Monitoring

Each render writes `mastered/golden_post/golden_post_analysis.json` and `.md` with dry/wet, drum/melody, bass/melody, pads/melody, kick/bass masking, stereo-wall pan, and mono compatibility metrics. Objective gates are monitoring warnings, not hard render blockers.

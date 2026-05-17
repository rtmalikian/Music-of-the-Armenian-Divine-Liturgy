# Golden Post Snare Cut-Through Loop - 2026-05-08 04:32:50

## Backups

- `backups/20260508_043250/orchestrator.py.backup_20260508_043250`
- `backups/20260508_043250/production_engine.py.backup_20260508_043250`
- `backups/20260508_043250/golden_post_processor.py.backup_20260508_043250`
- `backups/20260508_043250/golden_post_params.json.backup_20260508_043250`

## What Changed

- Added a bounded 3-pass golden-post decision loop.
- Added snare/clap transient enhancement and presence lift before dry stereo-wall drum summing.
- Added snare-triggered ducking for melody, pads, FX, reverb, and delay only.
- Default snare duck envelope is intentionally fast: 1 ms attack, 10 ms release.
- Added snare/hat audibility gates so the system does not accept a mix only because global drum balance passed.
- Added report metrics for snare RMS vs drums, hats RMS vs drums, snare presence vs melody, selected pass, and snare ducking depth.

## Guardrails

- Kick, bass, and the drum bus are not ducked by the snare.
- Snare/hat gain lifts are bounded.
- Snare ducking depth is bounded.
- The selected pass is chosen by objective score, with penalties for missed audibility and excessive ducking.

## Why

The render for `05082026_025353_90bpm_G#_G#_Minor_4-4_boom_bap-mpc_soul_inv` had a good overall mix, but the snare and hi-hats were too subtle. The previous gates passed because they checked global balance and stereo placement, but did not explicitly require snare/hat cut-through.

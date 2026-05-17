# Python Revamp Pipeline — Implementation Plan

## Overview

Complete rewrite of the audio production pipeline from FFmpeg-based processing
to pure Python DSP using pedalboard (Spotify's audio library) and pyloudnorm.

**Location:** `scripts/05042026_python_revamp/`
**Existing code:** Untouched — parallel implementation
**Dependencies:** pedalboard 0.9.22, pyloudnorm, numpy, scipy, soundfile, librosa (all installed)

## Problem Statement

The current pipeline (`scripts/audio_pipeline/post_production.py`) has critical issues:

1. **24 dB level destruction** — Pink noise gain staging matches stems to -30 LUFS reference,
   destroying the hot signal from the Roland Fantom (+1.2 dBFS raw → -23 dBFS processed)
2. **FFmpeg `aecho` used as "reverb"** — aecho is echo/delay, NOT reverb. Creates discrete
   repetitions instead of dense, diffuse tails
3. **FFmpeg `acompressor`** — no lookahead, limited control, no program-dependent release
4. **No iterative feedback** — processing is single-pass, no re-measurement after stages
5. **No objective quality checks** — no pass/fail metrics per stem or per mix

## Architecture

### Signal Flow

```
Raw Recording
  → Gain Stage (absolute LUFS targets per role)
  → Phase Correction (DC removal, asymmetry fix)
  → Adaptive Compression (pedalboard, 25ms attack drums, 3:1, 3-5 dB max GR)
  → Saturate (tanh with oversampling)
  → Dynamic EQ (frequency-dependent mud/harshness control)
  → Creative FX (chorus, phaser, delay — per role)
  → Per-Track Reverb Send (grouped by category, individual returns)
  → Quality Assessment (LUFS, crest, peak, stereo — pass/fail)
  → Iterative Correction (max 2-3 attempts, single-pass per attempt)
  → Save processed stem + reverb return + delay return
```

### Bus Processing

```
Processed Stems → Group into buses (drums, bass, melody, fx)
  → Bus unmasking (dynamic EQ between competing buses)
  → Bus iterative processing (spectral profile matching)
  → Sum to mix
```

### Mastering Chain

```
Mix
  → DC Removal & Phase Correction
  → Soft Clipping (-1 dBFS ceiling, tanh waveshaping)
  → 64-Band Reference Match EQ (iterative, max 5 attempts)
  → Spectral Shaping (16-band Mel-spaced, gentle per-band compression)
  → Multiband Compression (3-4 bands, adaptive threshold)
  → Per-Band Stereo Width (mono sub, narrow bass, wide highs)
  → M/S EQ (independent mid/side processing)
  → Glue Compression (1.5:1, only if crest > 9 dB)
  → Brick-Wall Limiter (-1 dBFS, pedalboard Limiter)
  → Loudness Normalization (target -11 LUFS via pyloudnorm)
  → Dither (TPDF, 24-bit)
```

## Files

| # | File | Purpose |
|---|---|---|
| 1 | `__init__.py` | Package init |
| 2 | `config.py` | All presets, targets, constants |
| 3 | `dsp_engine.py` | Pedalboard wrappers for all DSP |
| 4 | `gain_staging.py` | Absolute LUFS targets (replaces pink noise) |
| 5 | `dynamic_eq.py` | Frequency-dependent processing |
| 6 | `stereo_processor.py` | Per-band stereo width, M/S processing |
| 7 | `quality_assessor.py` | Objective metrics (LUFS, crest, peak, stereo, spectral) |
| 8 | `reference_analyzer.py` | 64-band reference track matching |
| 9 | `iterative_processor.py` | Safe feedback loops for stems, buses, master |
| 10 | `production_engine.py` | Main orchestrator (same interface as current) |
| 11 | `run_pipeline.py` | CLI entry point |

## Compression Specifications

| Role | Attack | Release | Ratio | Target GR |
|---|---|---|---|---|
| kick | 25ms | 80ms | 3:1 | 3-5 dB |
| snare | 25ms | 100ms | 3:1 | 3-5 dB |
| hat | 10ms | 60ms | 2:1 | 2-3 dB |
| bass | 20ms | 200ms | 3:1 | 3-5 dB |
| pad | 30ms | 300ms | 2:1 | 2-3 dB |
| melody | 15ms | 150ms | 2.5:1 | 2-3 dB |

- Adaptive threshold: binary search to achieve target GR range
- Makeup gain: `threshold_db × (1 - 1/ratio)`
- Max GR: 5 dB hard limit

## Reverb Send Architecture

Per-track sends grouped by category (like Roland Fantom MFX):

| Category | room_size | damping | wet_level | Used by |
|---|---|---|---|---|
| drum | 0.35 | 0.6 | 0.8 | snare, hat, clap, perc |
| melodic | 0.60 | 0.5 | 0.8 | melody, lead, counter, chorus |
| pad | 0.80 | 0.35 | 0.8 | pad, chord |
| fx | 0.75 | 0.4 | 0.8 | fx stems |

- Bass stays dry (no reverb send)
- Kick stays dry (no reverb send)
- Each stem's reverb return saved as individual file
- `dry_level=0.0` — only wet tail on returns, dry signal already in mix

## Per-Stem Send Levels

| Stem | Reverb Send | Delay Send |
|---|---|---|
| kick | 0.0 | 0.0 |
| snare_body | 0.20 | 0.0 |
| snare_snap | 0.15 | 0.0 |
| snare_air | 0.30 | 0.0 |
| hat | 0.12 | 0.0 |
| clap | 0.25 | 0.0 |
| bass | 0.0 | 0.0 |
| pad | 0.40 | 0.0 |
| melody_lead | 0.30 | 0.25 |
| counter | 0.35 | 0.35 |
| chorus | 0.32 | 0.20 |

## Artifact Prevention

The iterative processing is designed to prevent the artifacts caused by the current
cascading-filter approach:

| Problem | Current Approach | New Approach |
|---|---|---|
| Filter stacking | 10 cascaded biquads | Single combined filter per attempt |
| Phase accumulation | Unpredictable cascaded phase | Wide Q (0.7-1.2), one-pass correction |
| Gain buildup | No cumulative limit | Total gain capped at ±3dB per attempt |
| Over-correction | Keeps trying even when good | Bypass threshold (variance < 0.3) |
| Re-processing | Re-measures and re-applies | Verify-only after apply |
| Quality degradation | No stop condition | Stop immediately if quality degrades |

### Iteration Rules

- Each attempt: analyze → compute ALL corrections → apply as SINGLE combined filter
  → gain match to original level → verify
- Max 2-3 attempts for stems, 5 for mastering
- Each attempt REPLACES the previous (never stacks filters on top)
- If verification shows quality degraded, revert to previous best and stop
- Bypass entirely if spectral variance from target < 0.3

## LUFS Targets (Replaces Pink Noise)

| Role | Target LUFS |
|---|---|
| kick | -14 |
| snare | -16 |
| hat | -20 |
| bass | -18 |
| pad | -22 |
| melody | -20 |
| counter | -22 |
| chorus | -22 |

## Stereo Width Targets (Per Band)

| Band | Width |
|---|---|
| Sub (20-80Hz) | 0.0 (mono) |
| Bass (80-200Hz) | 0.5 (narrow) |
| Mid (200-2kHz) | 1.0 (normal) |
| High (2k-8kHz) | 1.3 (wide) |
| Air (8k-20kHz) | 1.4 (wide) |

## Mastering Targets

| Metric | Target |
|---|---|
| LUFS | -11 (reference is -10.2) |
| True Peak | -1.0 dBFS |
| Spectral tolerance | variance < 0.3 (64-band) |
| Match EQ iterations | max 5 |

## Dynamic EQ Bands

| Band | Frequency | Q | Direction | Use |
|---|---|---|---|---|
| mud | 275 Hz | 1.5 | cut | Reduce muddiness |
| harsh | 3.2 kHz | 2.0 | cut | Tame harshness |
| clarity | 5 kHz | 1.2 | boost | Add presence |

- Only activates when band energy exceeds threshold
- Attack/release for smooth activation
- Applied on stems AND master

## Output Compatibility

- Same `process_full_mix(stems, song_name, bpm)` interface as current ProductionEngine
- Same output directory: `output/<song>/mastered/`
- Same master file: `<song>_master.wav`
- New subdirectories: `reverb_returns/`, `delay_returns/`
- Sample pack generation (Step 4) — unchanged, independent of production
- Project consolidation (Step 5) — unchanged, same orchestrator
- `pipeline_orchestrator.py` — unchanged, calls new ProductionEngine via import swap

## Usage

### Standalone
```bash
python scripts/05042026_python_revamp/run_pipeline.py \
    --stems output/<song>/recordings/ \
    --reference output/reference/TheAlchemist_Tight_812814020637_1_5.mp3 \
    --song-name <song> \
    --bpm 90
```

### Via Orchestrator (import swap)
```python
# In pipeline_orchestrator.py, change:
from post_production import ProductionEngine
# To:
from scripts.05042026_python_revamp.production_engine import ProductionEngine
```

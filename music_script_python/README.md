# Full Pipeline 05102026

Portable autonomous music generation system: MIDI composition → Fantom recording → objective pink-noise arrangement/mix processing → preservation mastering.

Generates complete songs with melodies, bass, drums, pads, and effects — then records them through a Roland Fantom, processes the stems, and produces a mastered mix.

## Quick Start

```bash
# Full pipeline (MIDI → record → produce)
python Full_Pipeline_05102026/orchestrator.py --full

# MIDI generation only
python Full_Pipeline_05102026/orchestrator.py --midi-only

# Production only (existing stems)
python Full_Pipeline_05102026/orchestrator.py \
    --stems output/<song>/recordings/ \
    --song-name <song> --bpm 90 --workers 3

# Compatibility wrapper
python Full_Pipeline_05102026/run_pipeline.py \
    --stems output/<song>/recordings/ \
    --song-name <song> --bpm 90 --workers 3
```

The folder is self-contained by default. Outputs are written under
`Full_Pipeline_05102026/output/` unless `MUSICGEN_PROJECT_ROOT` or `--output-dir`
is provided.

The 2026-05-10 promoted path keeps the objective pink-noise staging, section
arrangement-density control, reduced wet returns, DnB/pad-bass-drum review
variants, full-song premaster, and full-song streaming master. See
`CHANGELOG_05102026.md` for the file-by-file change log and backups.

## Pipeline Overview

```
MIDI Generation (midi_orchestrator.py)
    ├── Scale/Key selection (75% major/minor, 25% other modes)
    ├── Time signature (4/4, 3/4, 5/4, 5/8)
    ├── Drum pattern families (12 families, 2 per song)
    ├── Melody, bass, pad, counter-melody, FX generation
    ├── Drum explosion into individual tracks
    └── Output: .mid file

Fantom Recording (audio_recorder.py)
    ├── Multi-pass recording (15 stems per pass)
    ├── Per-stem patch assignment
    ├── Trigger probability thinning (hi-hats 85%, kicks 91%, snares 92%)
    └── Output: individual WAV stems

Production (production_engine.py)
    ├── Per-stem gain staging + optimization
    ├── Dynamic soft clipping (drum stems + drum bus)
    ├── Bus summing (drums, bass, melody, FX)
    ├── Bass-drums unmasking + kick-bass sidechain
    ├── Transient shaping + presence EQ on drum bus
    ├── Automation effects with intensity ramping
    ├── Mix variants (dnb-mix-1, dnb-mix-2, bass1, bass2)
    └── Mastering with reference matching
```

## Key Files

### Entry Points

| File | Purpose |
|------|---------|
| `orchestrator.py` | Full pipeline: MIDI → Record → Produce → Sample Pack |
| `run_pipeline.py` | Production only: takes existing stems, runs production |
| `midi_orchestrator.py` | MIDI generation: composes the full MIDI sequence |

### MIDI Generation

| File | Purpose |
|------|---------|
| `midi_config.py` | Time signatures, bar lengths, swing values, LUFS targets |
| `midi_theory.py` | Music theory: modes, scales, chord voicings, Armenian Maqam |
| `midi_song_structure.py` | Song sections (intro/verse/chorus/fill/outro), chord progressions |
| `midi_composition.py` | Melody, bass, harmonic bass, counter-melody, pad generation |
| `midi_drum_sequences.py` | 12 drum pattern families with micro-techniques |
| `midi_engine.py` | MIDI utilities: swing, spatial, note writing |
| `midi_models.py` | Data classes: VoiceLeadingContext, TensionState, MelodyNote |
| `midi_analysis.py` | Melody interval analysis, voice leading analysis |

### Production

| File | Purpose |
|------|---------|
| `production_engine.py` | Main production orchestrator: stem processing, bus summing, mixing |
| `dsp_engine.py` | Audio processing: compression, EQ, reverb, delay, soft clip, sidechain |
| `iterative_processor.py` | iZotope-style feedback loops for stems, buses, and master |
| `optimizer.py` | Nelder-Mead optimization of soft clip + limiter parameters |
| `automation_engine.py` | Bus-level effects with intensity ramping at transitions |
| `gain_staging.py` | Per-stem loudness targeting |
| `dynamic_eq.py` | Frequency-dependent processing, unmasking between buses |
| `stereo_processor.py` | Stereo width control |
| `quality_assessor.py` | LUFS, crest factor, peak measurement |
| `reference_analyzer.py` | Reference track spectral profiling |
| `stem_context_analyzer.py` | Spectral collision detection between stems |
| `section_analyzer.py` | Busy section detection for optimizer evaluation |
| `sanity_checker.py` | Historical run comparison |
| `optimization_logger.py` | Optimization result logging |
| `config.py` | All configuration: effect depths, LUFS targets, compression presets |

## Drum Pattern Families

12 pattern families, 2 randomly selected per song (one for main sections, one for chorus/fill):

| Family | Character |
|--------|-----------|
| `boom_bap` | Classic 16th-note hats, snare on 2&4 |
| `lofi` | Ghost kicks, late snare, sparse asymmetric hats |
| `trap` | 32nd-note hat rolls, 808 kick flams |
| `mpc_soul` | Kick flams, rimshot ghosts, ride cymbal |
| `broken_beat` | Displaced kick/snare, velocity extremes |
| `drill` | Syncopated `x--x--x-x--x--x-` hat pattern, ghost hats |
| `memphis_phonk` | Cowbell-driven, heavy kick, snare+clap layer |
| `jazzhop` | Ride cymbal timekeeper, brush ghost snares |
| `chopped_break` | Flammed hits, break templates, vinyl bleed |
| `half_time` | Snare on 3, kick fills space, rimshot backbeat |
| `negative_space` | 3-4 hits per bar, silence as instrument |
| `polyrhythmic` | 3-over-4/3-over-5 hi-hats, displaced snare |

Every pattern adapts to the song's time signature (4/4, 3/4, 5/4, 5/8).

**Micro-techniques** (randomly injected per bar, any family):
- Ghost kick anticipation (20%)
- Snare flam (15%)
- Hi-hat choke (15%)
- Velocity crescendo (10%)
- Bar-end ghost roll (12%)
- Kick push (18%)
- Crash texture (8%)
- Rimshot counter-rhythm (10%)

## Drum Processing Chain

```
Drum stems:
  Gain stage (kick -12 LUFS, snare -14 LUFS)
  → Dynamic soft clip (5 dB headroom, 25ms blocks)
  → Optimizer (soft clip + limit, 5 evals max)

Drum bus (sum of all drum stems):
  Peak protect (-0.1 dBFS)
  → Parallel compression (10:1, 50% blend)
  → Transient shaping (+4 dB boost)
  → Presence EQ (3.5 kHz +2.5 dB, 70 Hz +1.5 dB)
  → Dynamic soft clip (4 dB headroom, 25ms blocks)
  → Automation effects with intensity ramping
```

## Automation Effects

Effects at transition points (verse transitions, chorus, fill, pre-chorus builds) with three onset types:

| Onset | Behavior |
|-------|----------|
| `quarter_note` | Builds over 1 beat (50% of transitions) |
| `rapid` | Builds in first 20% of segment (30%) |
| `instant` | Full intensity from beat 1 (20%) |
| `two_note` | Builds over 2 beats (pre-chorus only) |

Both the effect **depth** and the **dry/wet mix** ramp from 0% to 100% over the onset duration.

## Mix Variants

Each song produces multiple mix variants:

| Variant | Contents |
|---------|----------|
| `dnb-mix-1` | Bass + Drums (no harmonic bass) |
| `dnb-mix-2` | Drums + Harmonic Bass (bassline 2) |
| `bass1` | Everything except harmonic bass |
| `bass2` | Everything except bass |

## Sample Packs

Generated from the MIDI with individual drum and melody layers:

- Verse/chorus drum bus (all drums summed)
- Verse/chorus individual kick
- Verse/chorus individual snare/clap
- Verse/chorus melody layers
- Bass, harmonic bass, counter melody
- One-shot samples extracted from each stem

## MIDI Filename Format

```
{timestamp}_{bpm}bpm_{key}_{scale}_{time_sig}_{main_family}-{chorus_family}{_inv}.mid
```

Example: `05052026_143022_87bpm_G_Minor_5-8_drill-jazzhop_inv.mid`

## Dependencies

- `mido` — MIDI file I/O
- `numpy` — Audio processing
- `soundfile` — WAV I/O
- `pedalboard` — Audio effects (compressor, reverb, delay, EQ)
- `pyloudnorm` — LUFS measurement
- `scipy` — Optimization, signal processing

# Pipeline Walkthrough — Step by Step

How the Python Revamp Pipeline works at every stage.

---

## STEP 1: MIDI Generation (`midi_orchestrator.py`)

### 1.1 Song Parameters

```
BPM:           Random 75-95
Time Signature: Random from 4/4, 3/4, 5/4, 5/8
Scale/Key:     75% chance major/minor, 25% other modes (Armenian Maqam, etc.)
```

The time signature determines bar length in ticks:
- 4/4 = 1920 ticks/bar
- 3/4 = 1440 ticks/bar
- 5/4 = 2400 ticks/bar
- 5/8 = 1200 ticks/bar

### 1.2 Drum Family Selection

Two pattern families are randomly selected from 12 options:
- **Main family** — used for intro, verse, outro sections
- **Chorus family** — used for chorus and fill sections

10% chance of **inversion**: ONE bar in ONE section gets kick and snare swapped.

5% chance per bar of a **surprise bar**: a random family replaces the normal pattern.

### 1.3 Song Structure (72 bars fixed)

```
Bars 0-7:    Intro
Bars 8-23:   Verse 1
Bars 24-31:  Chorus 1
Bars 32-35:  Fill 1
Bars 36-51:  Verse 2
Bars 52-59:  Chorus 2
Bars 60-63:  Fill 2
Bars 64-71:  Outro
```

### 1.4 Chord Progressions

Each section type has its own progression pool. Progressions are in Roman numeral notation relative to the scale root. Passing chords connect sections.

### 1.5 Melody Generation

**4-bar loop** (`midi_composition.py`):
- Seed motif generated from scale intervals, then diversified to avoid overusing the same contour fingerprint
- 4 bars with ABAC phrase structure: statement, response, restatement, turnaround
- Each ABAC bar is stored as an explicit phrase cell, so rests and variable rhythm lengths do not blur bar boundaries
- Per-song melody persona selects sparse, swung, syncopated, hypnotic, or chorus-lift behavior
- Strong beats and cadences favor chord tones or guide tones from the shared `BarHarmony`
- Weak beats can use controlled passing tones, neighbor tones, anticipations, and rests when they resolve musically
- Voice leading prevents parallel perfects and keeps melodies snapped to the active chord progression
- Chorus melody uses the same strong-beat chord reinforcement as verse melody while following the chorus progression window

**Counter melody** — 2-bar phrases that respond to the main melody with more rests, register separation, and the active 2-bar harmony window.

**FX melody** — Echo taps derived from main melody notes.

### 1.6 Bass Generation

Time-signature-specific bass patterns:
- 4/4: whole, dotted_half, half_quarter, lofi_pocket, syncopated, standard, root_fifth, active
- 3/4: waltz, flowing, lofi_pocket, syncopated
- 5/4: money (K-S-K-S-K), dotted, standard, root_fifth
- 5/8: tight, bouncy, standard

Patterns scale proportionally to bar length.

Bass lines are written one octave higher than the earlier sub-heavy range because Fantom bass patches tend to contain strong low-end fundamentals. Main bass targets MIDI 45-64 and harmonic bass targets MIDI 52-72; Fantom calibration can still transpose down if a selected patch measures too high. Bass lines also read the next bar's harmony so final notes can approach the upcoming root or bass tone. Lofi pedal/ostinato behavior is used sparingly in stable sections.

### 1.7 Pad Chords

Pads use the shared `BarHarmony` chord tones, extensions, and suspensions. Voicings preserve common tones, choose nearby inversions in the 72-96 register, and resolve suspended tones intentionally instead of treating every pad chord as an isolated block.

### 1.8 Drum Pattern Generation

Each bar calls the appropriate pattern function with:
- `tpb`: ticks per beat (480)
- `variation_level`: 0 (simple) to 2 (complex)
- `is_chorus`: enables chorus-specific patterns
- `inverted`: swaps kick and snare
- `time_sig`: adapts pattern to meter

Pattern functions build notes, then `_finalize()` applies:
1. **Micro-techniques** — random ghost kicks, flams, chokes, crescendos, rolls
2. **Inversion** — kick/snare swap if enabled
3. **Deduplication** — removes duplicate note/time pairs

### 1.8.1 The 12 Drum Pattern Families

Each song gets 2 randomly selected families — one for main sections (intro/verse/outro), one for chorus/fill.

#### 1. Boom-Bap
Classic hip-hop. 16th-note closed hi-hats with swing, snare on beats 2 and 4, kick on 1 and 3 (or syncopated variants). Four base pattern IDs: Classic, Syncopated, 8thNoteHat, DoubleKick. Ghost snares at velocity 40-45 on offbeats. Extra kicks on random 16th positions.

**Hi-hats**: 16 hits per bar (4/4), velocity accents on downbeats (75-105) vs offbeats (60-90), 5% swing factor on offbeat 16ths.

**Chorus variant**: Open hats on the "and" of 2 and 4, busier kick pattern with syncopated hits.

#### 2. Lo-Fi
J Dilla / Nujabes style. Loose timing, ghost kicks that anticipate the downbeat, snare shifted 20-40 ticks late (the "drunk" feel). Only 3-6 sparse asymmetric hi-hat hits per bar. Kick on the "and" of 4 pushing into the next bar (40% chance).

**Key characteristic**: The late snare creates a dragging, behind-the-beat feel. Ghost kicks at velocity 30-45 on offbeat 16ths.

#### 3. Trap
32nd-note hi-hat rolls at 70% density (not every 32nd — creates natural variation). Snare + clap layer on every snare hit. Kick flams (two hits 1-2 ticks apart) for 808 slide effect. Open hat bleed on the last 16th note.

**Key characteristic**: The rapid hi-hat rolls create a galloping, energetic feel. The kick flam mimics the 808 bass slide common in trap production.

#### 4. MPC Soul
Ride cymbal as primary timekeeper instead of hi-hats. Kick flams (two hits 1-3 ticks apart) for MPC pad sensitivity. Rimshot ghost notes 16th before snare hits. Ghost snares at velocity 30-45 on random offbeat positions.

**Key characteristic**: The ride cymbal gives a warmer, jazzier texture. The kick flams create a "thump" that's distinct from clean kick hits.

#### 5. Broken Beat
Everything displaced. Kick shifted 20-50 ticks off the grid (randomly early or late). Snare on offbeat 16th positions. Only 4-6 asymmetric hi-hat hits with extreme velocity range (25-110). The gaps and displacements create a lopsided, experimental groove.

**Key characteristic**: The intentional timing displacement creates tension and a "broken" feel. Velocity extremes make some hits whisper-quiet and others punchy.

#### 6. Drill
Syncopated hi-hat pattern `x--x--x-x--x--x-` (positions 0, 3, 6, 8, 11, 14 of 16). Position 8 has 50% chance of open hat variant `x--x--x-t--x--x-`. Ghost hi-hats (velocity 30-50) fill remaining positions at 35% density. 32nd-note hat bursts at bar transitions when variation level > 0.

**Key characteristic**: The syncopated pattern is distinctive to UK/NY drill. The ghost hats add texture without cluttering the main pattern.

#### 7. Memphis Phonk
Cowbell (note 56) on 8th notes as primary rhythmic driver. Heavy kick on beat 1 only (velocity 127). Snare + clap layer on every snare hit. Tom fills (low tom 45, mid tom 47) as 16th-note rolls in variation bars.

**Key characteristic**: The cowbell replaces hi-hats as the timekeeper, giving an aggressive, minimal feel. Only 3-4 elements per bar — aggression comes from velocity and layering.

#### 8. Jazz-Hop
Ride cymbal (note 51) plays a jazz ride pattern (ding-ding-a-ding). Ghost snares everywhere — before and after every main snare hit at velocity 30-45. Kick is sparse (beat 1 only, or beat 1 and "and" of 3). Brush swirl: 32nd-note snare roll at velocity 20-35 at the start of every 4th bar.

**Key characteristic**: Mimics a live jazz drummer with brushes. The ghost snares create a constant soft snare undercurrent. Very relaxed, organic feel.

#### 9. Chopped Break
Mimics a chopped vinyl breakbeat. Flammed hits (two snare hits 1-3 ticks apart, second at 60% velocity). 3 break templates (Think Break, Apache, Funky Drummer rhythmic patterns). Heavy swing (0.60+). Vinyl bleed ghosts at velocity 20-30 on random 16th positions.

**Key characteristic**: The flammed hits simulate the "chop" artifact from sampling vinyl. The break templates give authentic boom-bap breakbeat rhythms.

#### 10. Half-Time
Snare on beat 3 only (half-time feel). Kick fills the space: beat 1, "and" of 2, and beat 3+. Rimshot (note 37) on beats 2 and 4 at velocity 50-60 as a subtle backbeat that implies the original tempo. Hi-hats at 8th-note pace with ghost 16ths at velocity 30-40 between them.

**Key characteristic**: The snare on 3 makes the pattern feel slower and heavier even at the same BPM. The rimshot backbeat creates a "double-time" illusion.

#### 11. Negative Space
Only 3-4 hits per bar. All hits placed on off-grid positions (16th-note offbeats like "e" and "a"). Long 2-3 beat stretches of complete silence. One "anchor" hit defines the bar's character. Everything at velocity 35-55.

**Key characteristic**: Silence is the instrument. The listener's brain fills in the missing rhythm. The sparse, quiet hits exist almost subliminally.

#### 12. Polyrhythmic
3-over-4 hi-hats (triplet groupings against 4/4 kick/snare). Kick in dotted quarter notes (every 3 8th notes). Two snare layers: quiet snare (velocity 40) on beats 2 and 4, loud snare (velocity 100) on the "and" of 3. In 5/4: 3-over-5 polyrhythm.

**Key characteristic**: The conflicting rhythmic feels create a floating, disorienting quality. The kick resolves every 3 bars instead of every bar.

### 1.8.2 Time Signature Adaptation

Each pattern family adapts to the song's time signature:

| Time Sig | Snare Position | Kick Pattern | Hi-Hat Density | Bar Length |
|----------|---------------|--------------|----------------|------------|
| **4/4** | Beats 2 & 4 | Beats 1 & 3 | 16 sixteenths | 1920 ticks |
| **3/4** | Beat 3 only | Beat 1 | 6 eighths | 1440 ticks |
| **5/4** | Beats 2 & 4 | Beats 1, 3, 5 (K-S-K-S-K) | 20 sixteenths | 2400 ticks |
| **5/8** | Beat 4 (2+3 grouping) | Beat 1 | 5 eighths | 1200 ticks |

The 5/4 kick pattern follows the Pink Floyd "Money" approach: kick-snare-kick-snare-kick, with syncopation layered on top.

### 1.8.3 Micro-Techniques

Randomly injected per bar, regardless of pattern family or variation level:

| Technique | Probability | Description |
|-----------|------------|-------------|
| Ghost kick anticipation | 20% | Ghost kick (vel 30-45) one 16th before each main kick |
| Snare flam | 15% | Two snare hits 3 ticks apart, second at 60% velocity |
| Hi-hat choke | 15% | Open hat immediately followed by closed hat 3 ticks later |
| Velocity crescendo | 10% | Gradual hi-hat velocity increase over the bar |
| Bar-end ghost roll | 12% | 32nd-note snare roll (vel 25-40) at the end of the bar |
| Kick push | 18% | Kick on the "and" of 4, pushing into next bar |
| Crash texture | 8% | Low-velocity crash cymbal (vel 40-60) on beat 1 |
| Rimshot counter-rhythm | 10% | Rimshot on "and" of 1 and "and" of 3 against snare |

### 1.8.4 Drum Inversion

10% of songs get **positional inversion**. When active:
1. A section type is chosen (verse, chorus, or fill)
2. A bar position within that section is chosen (0-7)
3. ONE bar at that position in ONE section gets kick and snare swapped

Example: If the chosen section is "verse" at position 3, then bar 11 (verse1 start 8 + position 3) gets inverted. Bar 43 (verse2 start 36 + position 3) does NOT — only one occurrence per song.

### 1.8.5 Surprise Bars

5% chance per bar of a **surprise bar**: a randomly selected pattern family replaces the normal pattern for that single bar. This creates unexpected rhythmic variation that keeps the listener's attention.

Additionally, 10% chance in verse/outro bars of using a random family instead of the song's main family.

### 1.8.6 Drum Explosion

After all bars are generated, the flat drum event list is split into individual MIDI tracks:
- `drum1_*` — intro/verse/outro events
- `drum2_*` — chorus/fill events
- `drum_aux_*` — auxiliary percussion

Each unique (prefix, note) pair becomes its own track:
- `drum1_Kick_n36`
- `drum2_Snare_n40`
- `drum_aux_Tambourine_n54`

This exploded format allows per-instrument stem recording on the Fantom.

### 1.8.7 GM Drum Note Map

| Note | Name | Note | Name |
|------|------|------|------|
| 35 | KickLow | 44 | PedalHat |
| 36 | Kick | 45 | LowTom |
| 37 | SideStick/Rimshot | 46 | OpenHat |
| 38 | Snare | 47 | MidTom |
| 39 | Clap | 49 | Crash |
| 40 | SnareAlt | 51 | Ride |
| 41 | KickAlt | 54 | Tambourine |
| 42 | ClosedHat | 56 | Cowbell |
| 43 | FloorTom | 70 | Maracas |

### 1.10 MIDI Output

Filename encodes all song parameters:
```
{timestamp}_{key}_{scale}_{time_sig}_{main_family}-{chorus_family}{_inv}.mid
```

Metadata returned: BPM, key, scale, time signature, drum families, inversion flag, section timings.

---

## STEP 2: Fantom Recording (`audio_recorder.py`)

### 2.1 Multi-Pass Recording

The Fantom records 15 stems per pass (Part 16 is sync click). Stems are grouped into passes based on track count.

### 2.2 Patch Assignment

Each track gets a Fantom patch based on its name:
- Kick/Snare/Hat → `drums` category
- Bass → `bass` category
- Melody → `lead`/`poly`/`brass` categories
- Pad → `pad`/`strings`/`choir` categories

### 2.3 Trigger Probability Thinning

Some stems have notes randomly dropped to create a more natural feel:
- **Hi-hats**: 85% keep rate (15% dropped)
- **Kicks**: 91% keep rate
- **Snares**: 92% keep rate

### 2.4 Octave Calibration Audit

Bass and melodic parts are octave-checked during Fantom calibration. The recorder builds a short dense audition snippet from the part's real notes and writes before/after audit MIDI snippets when a shift is considered:

```text
recordings/calibration_audit/<pass>/part03_Main_Melody_before.mid
recordings/calibration_audit/<pass>/part03_Main_Melody_after_plus12st.mid
```

Each pass manifest includes `octave_calibration` for every part, including note ranges, centroid measurements, bass fundamental estimates, expected MIDI fundamental energy, harmonic dominance, bright/rumble/usable-bass ratios, decision reason, settle delay, audit MIDI paths, and verification status. Bass octave choice is MIDI-register-first: the calibration snippet is transposed into the intended bass register before the first audible audition, so the Fantom is not asked to audition a known-too-high bass register and then correct it. Centroid and fundamental estimates are diagnostic for bass after that point; they reject patches that are too bright, too harmonic, or sub-rumble heavy instead of repeatedly chasing octave shifts. Octave transposition waits `0.75s` before the shifted MIDI is re-auditioned; gain staging keeps its shorter SysEx delay.

Patch audition retries are stricter for pitch-critical roles. Normal tracks try up to 4 patches, melodic tracks up to 8, and bass tracks up to 16. Rejected bass patches are marked bad for the current run so the selector keeps moving through the patch pool instead of reusing a tone that failed the register/spectrum check. The manifest stores `patch_attempts` with the accepted/rejected patch names and rejection reasons.

The exact post-calibration MIDI sent to the Fantom for each pass is also preserved as `<song>_<pass>_recording_pass.mid` and linked from the manifest as `recording_midi`.

### 2.5 Stem Splitting

After recording, the multi-channel WAV is split into individual stem WAVs based on the recorded track names.

---

## STEP 3: Production (`production_engine.py`)

### 3.1 Per-Stem Processing

For each stem:

**A. Gain Stage** (`gain_staging.py`)
- Measure current LUFS
- Apply gain to hit target LUFS for the role:
  - Kick: -12 LUFS
  - Snare: -14 LUFS
  - Hat: -18 LUFS
  - Bass: -18 LUFS
  - Melody: -20 LUFS

**B. Optimization** (`optimizer.py`)
- Nelder-Mead search over 2 params: soft_clip_ceiling + limiter_ceiling
- Evaluates on busiest sections (top 20%)
- 15 evals max for melodic stems, 5 for drum stems
- Skipped entirely for transient percussion (crash, ride, tambourine)

**C. Dynamic Soft Clip** (drum stems only)
- 25ms blocks, 5 dB headroom
- Ceiling follows local peak level
- Catches kick/snare transients without fixed threshold

**D. Context Analysis** (`stem_context_analyzer.py`)
- Detects spectral collisions between stems
- Generates EQ cut suggestions for lower-priority stems

### 3.2 Bus Summing

Stems are grouped into buses:
- `drums` — kick, snare, hat, clap, percussion
- `bass` — bass stems
- `melody` — melody, counter melody, pad, chord
- `fx` — everything else

### 3.3 Bus Processing

**Unmasking** (`dynamic_eq.py`):
- Melody bus: cut where it conflicts with drums (2200-3200 Hz) and bass (120-240 Hz)
- Bass bus: cut where it conflicts with kick (50-120 Hz)

**Kick-Bass Sidechain** (`dsp_engine.py`):
- Detects kick transients in drum bus
- Ducks bass frequencies (40-120 Hz) by 3 dB max
- 20ms release — tight ducking, no pumping
- Only affects low bass, high bass untouched

### 3.4 Automation Effects (`automation_engine.py`)

Transition effects applied at section boundaries:

**Verse transitions** (bars 4, 8, 12, 16 of each verse):
- 2-3 buses get effects simultaneously
- Onset: 50% quarter_note, 30% rapid, 20% instant

**Pre-chorus builds** (4 bars before each chorus):
- All buses get filter sweep effects
- Onset: two_note (builds over 2 beats)

**Chorus/Fill/Outro**:
- Section-wide effects
- Onset: 50% quarter_note, 30% rapid, 20% instant

**Intensity ramping**:
- Fixed effects (tape wobble, filter sweeps, etc.) get dual-ramp envelope
- Both depth and dry/wet mix ramp from 0% to 100%
- Ramping effects (reverb wash, delay swell, etc.) already build internally

**Effect depths** (very pronounced):
- Tape wobble: 0.020
- Vinyl crackle: 0.12
- Sidechain pump: 0.95
- Stereo widen: up to 2.5x
- Riser gain: +12 dB
- HPF sweep: up to 6000 Hz
- LPF sweep: down to 100 Hz

### 3.5 Drum Bus Processing

After automation effects:

**Parallel compression**:
- 10:1 ratio, 2ms attack, 40ms release
- 50% blend (NY-style)

**Transient shaping**:
- Split into transient + sustain components
- Boost transients by +4 dB

**Presence EQ**:
- 3.5 kHz +2.5 dB (snare/hat attack)
- 70 Hz +1.5 dB (kick thump)

**Dynamic soft clip**:
- 4 dB headroom, 25ms blocks
- Adapts to local peak level

### 3.6 Mix Variants

Four mix variants produced:
- `dnb-mix-1` — Bass + Drums (no harmonic bass)
- `dnb-mix-2` — Drums + Harmonic Bass
- `bass1` — Everything except harmonic bass
- `bass2` — Everything except bass

Each variant is independently mastered.

### 3.7 Mastering

- Iterative processing with reference track matching
- Compression + limiting + loudness matching
- Output: 24-bit PCM WAV

---

## STEP 4: Sample Pack Generation (`generate_sample_stems.py`)

Short clips recorded from the MIDI for reuse:

| Sample Set | Contents |
|------------|----------|
| `verse_8bars_melodic` | Bass, Harmonic Bass, Main Melody, Counter Melody |
| `chorus_8bars_melodic` | Bass, Harmonic Bass, Chorus Melody |
| `verse_8bars_drums` | All verse drum stems + drum bus |
| `chorus_8bars_drums` | All chorus drum stems + drum bus |
| `verse_8bars_kick` | Isolated verse kick |
| `verse_8bars_snare` | Isolated verse snare/clap |
| `chorus_8bars_kick` | Isolated chorus kick |
| `chorus_8bars_snare` | Isolated chorus snare/clap |
| `verse_8bars_melody_layers` | Main Melody + Counter Melody |
| `chorus_8bars_melody_layers` | Chorus Melody |

Each drum set also produces:
- Normalized drum bus
- One-shot samples (individual hits, normalized)

Each verse/chorus drum and melodic sample set also writes a matching MIDI excerpt:
- `sample_pack_build/<song>/<sample_set>/midi/<song>_<sample_set>.mid`
- Excerpts preserve tempo, time signature, count-in alignment, and the selected musical tracks.
- The internal sync click track used for Fantom recording is not included in the user-facing MIDI excerpt.

---

## STEP 5: Project Consolidation

Final project structure:
```
output/<song>/
├── midi/
│   └── <song>.mid
├── recordings/
│   └── <stems>.wav
├── mastered/
│   ├── final/
│   │   ├── <song>_master.wav
│   │   ├── <song>_streaming_master.wav
│   │   ├── <song>_drums-bass_master.wav
│   │   └── <song>_pads-drums-bass_master.wav
│   ├── <song>_premaster.wav
│   ├── buses/
│   │   ├── bus_drums.wav
│   │   ├── bus_bass.wav
│   │   ├── bus_melody.wav
│   │   └── bus_pads.wav
│   ├── section_automated_buses/
│   │   ├── auto_drums.wav
│   │   ├── auto_bass.wav
│   │   ├── auto_melody.wav
│   │   └── auto_pads.wav
│   ├── reverb_returns/
│   ├── delay_returns/
│   ├── section_calibrated_returns.wav
│   └── cleanup_manifest.json
├── sample_pack_build/
│   └── <sample_sets>/
└── DOCUMENTATION.md
```

Cleanup removes per-stem processed WAVs, old pre-section `mastered/automated/` buses, detector-only `sidechain_keys/`, `raw_summed_returns.wav`, temporary mix sums, golden-post audio candidates, raw multichannel pass WAVs, and checksum-verified duplicate parent masters. JSON/JSONL/MD/TXT diagnostics and logs are preserved.

---

## Resuming the Pipeline

The pipeline can be resumed from different steps if it fails or is interrupted.

### Resume from Step 2 (Recording)

If MIDI was already generated but recording failed or wasn't done:

```bash
# The MIDI file is in scripts/output/ — use --full to re-run from recording
python scripts/05042026_python_revamp/orchestrator.py --full

# Or use run_pipeline.py with existing stems directory
python scripts/05042026_python_revamp/run_pipeline.py \
    --stems output/05052026_162431_B_B_Mixolydian_5-8_boom_bap-trap/recordings/ \
    --song-name 05052026_162431_B_B_Mixolydian_5-8_boom_bap-trap \
    --bpm <bpm>
```

### Resume from Step 3 (Production)

If stems were recorded but production failed:

```bash
python scripts/05042026_python_revamp/orchestrator.py \
    --stems output/<song>/recordings/ \
    --song-name <song> \
    --bpm <bpm> \
    --resume-step 3
```

### Resume from Specific Production Sub-Steps

The production engine saves state to `pipeline_state.json`. Steps:
- **1**: Per-stem processing
- **2**: Bus summing
- **2.5**: Automation effects
- **3**: Mix variants
- **4**: Mastering

```bash
# Resume from bus summing
python scripts/05042026_python_revamp/orchestrator.py \
    --stems output/<song>/recordings/ \
    --song-name <song> --bpm <bpm> \
    --resume-step 2

# Resume from automation
python scripts/05042026_python_revamp/orchestrator.py \
    --stems output/<song>/recordings/ \
    --song-name <song> --bpm <bpm> \
    --resume-step 2.5
```

---

## File Dependency Graph

```
orchestrator.py
├── midi_orchestrator.py
│   ├── midi_config.py
│   ├── midi_theory.py
│   ├── midi_song_structure.py
│   ├── midi_composition.py
│   │   └── midi_models.py
│   ├── midi_drum_sequences.py
│   ├── midi_engine.py
│   └── midi_analysis.py
├── audio_recorder.py (scripts/audio_pipeline/)
│   └── fantom_midi_control.py
└── production_engine.py
    ├── dsp_engine.py
    ├── iterative_processor.py
    │   └── optimizer.py
    ├── gain_staging.py
    ├── dynamic_eq.py
    ├── stereo_processor.py
    ├── quality_assessor.py
    ├── reference_analyzer.py
    ├── stem_context_analyzer.py
    ├── section_analyzer.py
    ├── sanity_checker.py
    ├── optimization_logger.py
    ├── automation_engine.py
    └── config.py
```

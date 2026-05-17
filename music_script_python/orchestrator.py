#!/usr/bin/env python3
"""
Full Pipeline Orchestrator — MIDI → Recording → Production.

Integrates MIDI generation, Fantom recording, and the Python Revamp
production engine into a single unified pipeline.

Usage:
    # Full pipeline (MIDI → record → produce):
    python Full_Pipeline_05102026/orchestrator.py --full

    # Production only (existing stems):
    python Full_Pipeline_05102026/orchestrator.py \
        --stems output/<song>/recordings/ \
        --song-name <song> \
        --bpm 79

    # MIDI generation only:
    python Full_Pipeline_05102026/orchestrator.py --midi-only
"""

import argparse
import os
import sys
import glob
import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(os.environ.get("MUSICGEN_PROJECT_ROOT", str(SCRIPT_DIR))).resolve()

# Add this package's directory first (highest priority)
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

# NOTE: Do NOT add scripts/audio_pipeline to sys.path here — it would shadow
# our new gain_staging.py, dynamic_eq.py, etc. The Fantom imports are handled
# lazily inside step_record() where they're actually needed.

import mido
import sounddevice as sd
import production_engine as engine_module
try:
    import parallel_engine_patch
except Exception:
    parallel_engine_patch = None
from midi_orchestrator import main as generate_midi


def find_fantom_device() -> int:
    """Probe audio devices and return the index of the Roland Fantom."""
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        name = dev.get('name', '').lower()
        if 'fantom' in name:
            print(f"  Found Roland Fantom: device {i} — {dev['name']} "
                  f"({dev['max_input_channels']} in, {dev['max_output_channels']} out)")
            return i
    print("  WARNING: Roland Fantom not found among audio devices:")
    for i, dev in enumerate(devices):
        ch_in = dev['max_input_channels']
        ch_out = dev['max_output_channels']
        if ch_in > 0:
            print(f"    {i}: {dev['name']} ({ch_in} in, {ch_out} out)")
    raise RuntimeError("Roland Fantom audio device not connected")


def get_bpm_from_midi(midi_path: str) -> float:
    """Extract BPM from a MIDI file."""
    mid = mido.MidiFile(midi_path)
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                return round(60_000_000 / msg.tempo, 2)
    return 90.0


def find_stems(stems_dir: str, exclude: list = None) -> dict:
    """Find WAV stems in directory, optionally excluding by filename substring."""
    stems = {}
    exclude = [x.lower() for x in (exclude or [])]
    for path in sorted(glob.glob(os.path.join(stems_dir, "*.wav"))):
        name = os.path.basename(path)
        if not name.startswith('.'):
            if not any(ex in name.lower() for ex in exclude):
                stems[name] = path
    return stems


def find_midi_file(song_name: str) -> str:
    """Search for MIDI file in common locations."""
    search_dirs = [
        os.path.join(str(SCRIPT_DIR), "output"),
        os.path.join(str(PROJECT_ROOT), "output"),
        os.path.join(str(PROJECT_ROOT), "output", song_name, "midi"),
        os.path.join(str(PROJECT_ROOT), "midi"),
    ]
    for dir_path in search_dirs:
        matches = sorted(glob.glob(os.path.join(dir_path, f"{song_name}*.mid*")))
        if matches:
            return matches[-1]
    return None


def output_song_name(song_name: str, bpm: float = None) -> str:
    """Match ProductionEngine output naming without changing project folder names."""
    base = str(song_name or "song")
    if re.search(r'(?i)(^|[_-])\d+(?:\.\d+)?bpm($|[_-])', base):
        return base
    if bpm is None:
        return base
    return f"{base}_{int(round(float(bpm)))}bpm"


def audit_expected_variants(output_dir: str, song_name: str, bpm: float):
    """Warn when retained review variants were not copied into final/."""
    output_name = output_song_name(song_name, bpm)
    expected = [
        f"{output_name}_drums-bass_master.wav",
        f"{output_name}_pads-drums-bass_master.wav",
    ]
    final_dir = os.path.join(output_dir, "final")
    missing_final = [f for f in expected if not os.path.exists(os.path.join(final_dir, f))]

    if not missing_final:
        print("  Verified retained variants: drums-bass, pads-drums-bass")
        return

    print("  WARNING: Missing expected utility variant output(s).")
    if missing_final:
        print(f"    Missing in mastered/final/: {', '.join(missing_final)}")
    print("    Likely causes: Step 5 did not run, final copy failed,")
    print("    selected drum/bass/pad stems were absent, or variant mastering failed.")


def step_generate_midi() -> tuple:
    """Step 1: Generate MIDI sequence."""
    print("\n" + "=" * 70)
    print("[STEP 1] MIDI GENERATION")
    print("=" * 70)
    result = generate_midi()
    if isinstance(result, tuple):
        midi_path, metadata = result
    else:
        midi_path = result
        metadata = {}
    song_name = os.path.basename(midi_path).replace(".mid", "")
    bpm = metadata.get('bpm', get_bpm_from_midi(midi_path))
    print(f"  MIDI: {midi_path}")
    print(f"  Song: {song_name}")
    print(f"  BPM: {bpm}")

    # Copy MIDI to song folder
    project_dir = os.path.join(str(PROJECT_ROOT), "output", song_name)
    midi_dir = os.path.join(project_dir, "midi")
    os.makedirs(midi_dir, exist_ok=True)
    dest = os.path.join(midi_dir, os.path.basename(midi_path))
    shutil.copy2(midi_path, dest)
    print(f"  Copied to: {dest}")

    return midi_path, song_name, bpm, metadata


def step_record(midi_path: str, song_name: str, metadata: dict = None) -> dict:
    """Step 2: Record stems from Roland Fantom."""
    print("\n" + "=" * 70)
    print("[STEP 2] RECORDING FROM FANTOM")
    print("=" * 70)

    try:
        # Temporarily add audio_pipeline to path for Fantom imports
        audio_pipeline_dir = str(SCRIPT_DIR / "audio_pipeline")
        if audio_pipeline_dir not in sys.path:
            sys.path.insert(0, audio_pipeline_dir)
        from audio_recorder import AudioRecorder, MultiPassOrchestrator
        from fantom_midi_control import FantomController
    except ImportError as e:
        print(f"  Error: Could not import recording modules: {e}")
        print("  Make sure Full_Pipeline_05102026/audio_pipeline is in the path.")
        return {}

    project_dir = os.path.join(str(PROJECT_ROOT), "output", song_name)
    recordings_dir = os.path.join(project_dir, "recordings")
    os.makedirs(recordings_dir, exist_ok=True)

    controller = FantomController()
    if not controller.output:
        print("  Error: Fantom hardware not connected. Skipping recording.")
        return {}

    device_index = find_fantom_device()
    recorder = AudioRecorder(device_index=device_index, output_dir=recordings_dir)
    orch = MultiPassOrchestrator(recorder, controller)
    stems = orch.run_multi_pass(midi_path, song_name, metadata=metadata)
    print(f"  Recorded {len(stems)} stems")
    return stems


def step_produce(stems: dict, song_name: str, bpm: float,
                 output_dir: str = None, resume_step: float = None,
                 golden_post: bool = True,
                 golden_post_params: str = None,
                 golden_pan_seed: int = None,
                 section_aware_pink: bool = True,
                 workers: int = 3,
                 arrangement_seed: int = None) -> str:
    """Step 3: Production (mixing & mastering) with Python Revamp."""
    print("\n" + "=" * 70)
    print("[STEP 3] PRODUCTION — Python Revamp Pipeline")
    print("=" * 70)

    if output_dir is None:
        output_dir = os.path.join(str(PROJECT_ROOT), "output", song_name, "mastered")

    os.makedirs(output_dir, exist_ok=True)

    os.environ["GAIN_FLOW_TEST_LOG"] = os.path.join(output_dir, "pink_noise_stage_log.jsonl")
    os.environ["ARRANGEMENT_DENSITY_LOG"] = os.path.join(output_dir, "arrangement_density_log.jsonl")
    if arrangement_seed is None:
        arrangement_seed = int(datetime.now().strftime("%H%M%S"))
    os.environ["ARRANGEMENT_DENSITY_SEED"] = str(int(arrangement_seed))

    if parallel_engine_patch is not None:
        parallel_engine_patch.install(
            engine_module,
            copy_dir=str(SCRIPT_DIR),
            workers=workers,
            quiet_optimizer=True,
            run_metadata_path=os.path.join(output_dir, "parallel_stem_processing.jsonl"),
            gain_mode="pink",
        )

    engine = engine_module.ProductionEngine(
        output_dir=output_dir,
        golden_post_enabled=golden_post,
        golden_post_params_path=golden_post_params,
        golden_pan_seed=golden_pan_seed,
        section_aware_pink_enabled=section_aware_pink,
    )

    # Auto-resume: check for existing pipeline state
    state = engine._load_state()
    if state and resume_step is None:
        last_step = state.get('step', 0)
        # Determine next step based on completed step
        step_sequence = {0: 1, 1: 2, 2: 2.5, 2.5: 3, 3: 4, 4: 5, 5: 5}
        next_step = step_sequence.get(last_step, last_step + 1)
        if next_step <= 1:
            # Step 1 was incomplete — re-run full pipeline
            print(f"  Found incomplete state from Step {last_step}. Re-running Step 1...")
            master_path = engine.process_full_mix(stems, song_name, bpm=bpm)
        else:
            print(f"  Found existing state from Step {last_step}. Resuming from Step {next_step}...")
            master_path = engine.resume_from_step(next_step, song_name, bpm)
    elif resume_step is not None:
        # Explicit resume from a specific step
        if state and resume_step > 1:
            master_path = engine.resume_from_step(resume_step, song_name, bpm)
        else:
            # Step 1 resume or no state — re-run full pipeline
            if not state:
                print(f"  No saved state found. Running full pipeline...")
            else:
                print(f"  Step 1 resume requested. Re-running full pipeline...")
            master_path = engine.process_full_mix(stems, song_name, bpm=bpm)
    else:
        master_path = engine.process_full_mix(stems, song_name, bpm=bpm)

    audit_expected_variants(output_dir, song_name, bpm)
    return master_path


def step_sample_pack(midi_path: str, song_name: str) -> str:
    """Step 4: Generate companion sample pack from MIDI."""
    print("\n" + "=" * 70)
    print("[STEP 4] SAMPLE PACK GENERATION")
    print("=" * 70)

    try:
        # Temporarily add audio_pipeline to path for sample generation
        audio_pipeline_dir = str(SCRIPT_DIR / "audio_pipeline")
        if audio_pipeline_dir not in sys.path:
            sys.path.insert(0, audio_pipeline_dir)
        from generate_sample_stems import generate_sample_pack
    except ImportError as e:
        print(f"  Error: Could not import sample generation module: {e}")
        return None

    project_dir = os.path.join(str(PROJECT_ROOT), "output", song_name)
    sample_output = os.path.join(project_dir, "sample_pack_build")

    try:
        device_index = find_fantom_device()
        sample_dir = generate_sample_pack(
            midi_path,
            output_root=sample_output,
            device_index=device_index,
        )
        print(f"  Sample pack: {sample_dir}")
        return sample_dir
    except Exception as e:
        print(f"  Sample generation failed: {e}")
        return None


def step_consolidate(song_name: str, midi_path: str, master_path: str,
                     stems: dict, metadata: dict):
    """Step 5: Project consolidation — generate comprehensive documentation."""
    print("\n" + "=" * 70)
    print("[STEP 5] PROJECT CONSOLIDATION")
    print("=" * 70)

    project_dir = os.path.join(str(PROJECT_ROOT), "output", song_name)
    mastered_dir = os.path.join(project_dir, "mastered")
    recordings_dir = os.path.join(project_dir, "recordings")
    log_dir = os.path.join(project_dir, "log")

    # Copy MIDI to project
    midi_dir = os.path.join(project_dir, "midi")
    os.makedirs(midi_dir, exist_ok=True)
    if midi_path and os.path.exists(midi_path):
        dest = os.path.join(midi_dir, os.path.basename(midi_path))
        if not os.path.exists(dest):
            shutil.copy2(midi_path, dest)
        print(f"  MIDI: {dest}")

    # Gather data for documentation
    bpm = metadata.get('bpm', 'N/A')
    output_name = output_song_name(song_name, bpm if bpm != 'N/A' else None)
    key = metadata.get('key', 'N/A')
    scale = metadata.get('scale', 'N/A')
    time_sig = metadata.get('time_signature', '4-4')
    main_family = metadata.get('main_drum_family', 'N/A')
    chorus_family = metadata.get('chorus_drum_family', 'N/A')
    inverted = metadata.get('inverted', False)
    is_armenian = metadata.get('is_armenian', False)
    sections_meta = metadata.get('sections', {})

    # Read recording manifests
    manifests = []
    if os.path.isdir(recordings_dir):
        for f in sorted(os.listdir(recordings_dir)):
            if f.endswith('_manifest.json'):
                try:
                    with open(os.path.join(recordings_dir, f)) as mf:
                        manifests.append(json.load(mf))
                except Exception:
                    pass

    # Collect all parts from all manifests
    all_parts = []
    for m in manifests:
        all_parts.extend(m.get('parts', []))

    # Read automation plan
    auto_plan_path = os.path.join(log_dir, "automation_plan.json")
    auto_plan = None
    if os.path.exists(auto_plan_path):
        try:
            with open(auto_plan_path) as af:
                auto_plan = json.load(af)
        except Exception:
            pass

    # Find master/mix variant files
    master_files = {}
    if os.path.isdir(mastered_dir):
        for f in sorted(os.listdir(mastered_dir)):
            if f.endswith('_master.wav'):
                path = os.path.join(mastered_dir, f)
                if 'pads-drums-bass' in f:
                    master_files['Pads/Chords + Drums + Bass'] = f
                elif 'drums-bass' in f:
                    master_files['Drums + Bass'] = f
                elif 'bass1' in f:
                    master_files['Bass 1 (No Harmonic Bass)'] = f
                elif 'bass2' in f:
                    master_files['Bass 2 (No Bass)'] = f
                elif 'pristine' in f:
                    master_files['Pristine Mix'] = f
                elif f.replace('_master.wav', '') in {song_name, output_name} or '_inv' in f:
                    master_files['Final Master'] = f

    # Build send config lookup
    try:
        sys.path.insert(0, str(SCRIPT_DIR))
        import config as cfg
        stem_send_map = getattr(cfg, 'STEM_SEND_MAP', [])
        layer_presets = getattr(cfg, 'LAYER_PRESETS', {})
        reverb_cats = getattr(cfg, 'REVERB_CATEGORIES', {})
        delay_presets = getattr(cfg, 'DELAY_PRESETS', {})
        drum_parallel = getattr(cfg, 'DRUM_PARALLEL_COMP', {})
        drum_clip = getattr(cfg, 'DRUM_DYNAMIC_SOFT_CLIP', {})
        kick_sc = getattr(cfg, 'KICK_BASS_SIDECHAIN', {})
        effect_depth = getattr(cfg, 'EFFECT_DEPTH', {})
        lufs_targets = getattr(cfg, 'STEM_LUFS_TARGETS', {})
    except Exception:
        stem_send_map = []
        layer_presets = {}
        reverb_cats = {}
        delay_presets = {}
        drum_parallel = {}
        drum_clip = {}
        kick_sc = {}
        effect_depth = {}
        lufs_targets = {}

    def get_send_for_track(track_name):
        n = track_name.lower()
        for match, category, rev_send, dly_send in stem_send_map:
            if match in n:
                return category, rev_send, dly_send
        return None, 0.0, 0.0

    # Generate documentation
    doc_path = os.path.join(project_dir, "DOCUMENTATION.md")
    with open(doc_path, "w") as f:
        f.write(f"# Project: {song_name}\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"---\n\n")

        # === Musical Parameters ===
        f.write(f"## Musical Parameters\n\n")
        f.write(f"| Parameter | Value |\n")
        f.write(f"|-----------|-------|\n")
        f.write(f"| MIDI File | `{os.path.basename(midi_path)}` |\n")
        f.write(f"| BPM | {bpm} |\n")
        f.write(f"| Key | {key} |\n")
        f.write(f"| Scale/Mode | {scale} |\n")
        f.write(f"| Time Signature | {time_sig.replace('-', '/')} |\n")
        f.write(f"| Main Drum Family | {main_family} |\n")
        f.write(f"| Chorus Drum Family | {chorus_family} |\n")
        f.write(f"| Inversion | {'Yes' if inverted else 'No'} |\n")
        f.write(f"| Armenian/Maqam | {'Yes' if is_armenian else 'No'} |\n\n")

        # === Output Files ===
        f.write(f"## Output Files\n\n")
        f.write(f"| File | Description |\n")
        f.write(f"|------|-------------|\n")
        for desc, fname in master_files.items():
            f.write(f"| `{fname}` | {desc} |\n")
        f.write(f"\n")

        # === Roland Fantom Patches ===
        f.write(f"## Roland Fantom Patches\n\n")
        if all_parts:
            f.write(f"| Part | Track | Patch Name | MSB | LSB | PC |\n")
            f.write(f"|------|-------|------------|-----|-----|-----|\n")
            for part in all_parts:
                p_idx = part.get('part', '?')
                t_name = part.get('source_track_name', 'Unknown')
                patch = part.get('patch', {})
                f.write(f"| {p_idx} | {t_name} | {patch.get('name', 'Unknown')} | {patch.get('msb', '?')} | {patch.get('lsb', '?')} | {patch.get('pc', '?')} |\n")
            f.write(f"\n")
        else:
            f.write(f"No recording manifests found.\n\n")

        # === Sound Design ===
        f.write(f"## Sound Design\n\n")

        # LFO Modulations
        f.write(f"### LFO Modulations\n\n")
        lfo_parts = [p for p in all_parts if p.get('sound_design', {}).get('lfo_matrix')]
        if lfo_parts:
            f.write(f"| Part | Track | LFO Details |\n")
            f.write(f"|------|-------|-------------|\n")
            for part in lfo_parts:
                p_idx = part.get('part', '?')
                t_name = part.get('source_track_name', 'Unknown')
                lfo = part['sound_design']['lfo_matrix']
                f.write(f"| {p_idx} | {t_name} | {lfo} |\n")
            f.write(f"\n")
        else:
            f.write(f"No LFO modulations applied.\n\n")

        # MFX Applied
        f.write(f"### MFX Applied\n\n")
        mfx_parts = [p for p in all_parts if p.get('sound_design', {}).get('mfx')]
        if mfx_parts:
            f.write(f"| Part | Track | MFX |\n")
            f.write(f"|------|-------|-----|\n")
            for part in mfx_parts:
                p_idx = part.get('part', '?')
                t_name = part.get('source_track_name', 'Unknown')
                mfx = part['sound_design']['mfx']
                f.write(f"| {p_idx} | {t_name} | {mfx} |\n")
            f.write(f"\n")
        else:
            f.write(f"No MFX applied.\n\n")

        # Drum FXM
        f.write(f"### Drum FXM\n\n")
        fxm_parts = [p for p in all_parts if p.get('sound_design', {}).get('drum_fxm')]
        if fxm_parts:
            f.write(f"| Part | Track | FXM |\n")
            f.write(f"|------|-------|-----|\n")
            for part in fxm_parts:
                p_idx = part.get('part', '?')
                t_name = part.get('source_track_name', 'Unknown')
                fxm = part['sound_design']['drum_fxm']
                f.write(f"| {p_idx} | {t_name} | {fxm} |\n")
            f.write(f"\n")
        else:
            f.write(f"No Drum FXM applied.\n\n")

        # === Reverb & Delay Sends ===
        f.write(f"## Reverb & Delay Sends\n\n")
        f.write(f"| Track Pattern | Reverb Send | Reverb Category | Delay Send |\n")
        f.write(f"|---------------|-------------|-----------------|------------|\n")
        seen = set()
        for match, category, rev_send, dly_send in stem_send_map:
            if match not in seen:
                seen.add(match)
                cat_str = category or '—'
                f.write(f"| {match} | {rev_send:.2f} | {cat_str} | {dly_send:.2f} |\n")
        f.write(f"\n")

        # === Layer Processing ===
        f.write(f"## Layer Processing\n\n")
        if layer_presets:
            f.write(f"| Layer | LUFS Target | Comp Ratio | Trim dB | EQ Bands |\n")
            f.write(f"|-------|-------------|------------|---------|----------|\n")
            for name, preset in layer_presets.items():
                lufs = preset.get('lufs_target', '—')
                ratio = preset.get('comp_ratio', '—')
                trim = preset.get('trim_db', 0.0)
                eq_bands = preset.get('eq', [])
                eq_str = ', '.join([
                    f"{'HP' if b['type']=='highpass' else 'LP' if b['type']=='lowpass' else '+' if b.get('gain_db',0)>0 else ''}{abs(b.get('gain_db',0))}@{b['freq']}" if b['type'] == 'bell' else f"{b['type'].upper()}{b['freq']}"
                    for b in eq_bands
                ]) if eq_bands else '—'
                f.write(f"| {name} | {lufs} | {ratio} | {trim:+.1f} | {eq_str} |\n")
            f.write(f"\n")

        # === Post-Processing Chain ===
        f.write(f"## Post-Processing Chain\n\n")

        f.write(f"### Per-Stem Processing\n\n")
        f.write(f"- **Gain staging**: LUFS targets per role")
        if lufs_targets:
            parts = [f"{k} {v}" for k, v in lufs_targets.items() if k != 'default']
            f.write(f" ({', '.join(parts)})")
        f.write(f"\n")
        f.write(f"- **Optimizer**: Nelder-Mead over soft_clip_ceiling + limiter_ceiling (5 evals for drums, 15 for melodic)\n")
        if drum_clip:
            f.write(f"- **Dynamic soft clip** (drum stems): {drum_clip.get('stem_headroom_db', 5)} dB headroom, {drum_clip.get('block_ms', 25)}ms blocks\n")
        f.write(f"\n")

        f.write(f"### Bus Processing\n\n")
        if drum_parallel:
            f.write(f"- **Drum bus parallel compression**: {drum_parallel.get('ratio', 10):.0f}:1 ratio, {drum_parallel.get('attack_ms', 2):.0f}ms attack, {drum_parallel.get('release_ms', 40):.0f}ms release, {drum_parallel.get('blend', 0.5)*100:.0f}% blend\n")
        f.write(f"- **Drum bus transient shaping**: +4 dB boost\n")
        f.write(f"- **Drum bus presence EQ**: 3.5 kHz +2.5 dB (Q=1.0), 70 Hz +1.5 dB (Q=1.0)\n")
        if drum_clip:
            f.write(f"- **Drum bus dynamic soft clip**: {drum_clip.get('bus_headroom_db', 4)} dB headroom, {drum_clip.get('block_ms', 25)}ms blocks\n")
        f.write(f"- **Bass-drums unmasking**: -2 dB cut at 50-120 Hz\n")
        if kick_sc:
            f.write(f"- **Kick-bass sidechain**: {kick_sc.get('depth_db', 3)} dB depth, {kick_sc.get('release_ms', 20)}ms release, threshold {kick_sc.get('threshold_db', -30)} dBFS, {kick_sc.get('freq_range', (40,120))[0]}-{kick_sc.get('freq_range', (40,120))[1]} Hz\n")
        f.write(f"- **Melody-drums unmasking**: -1.5 dB cut at 2200-3200 Hz\n")
        f.write(f"- **Melody-bass unmasking**: -1 dB cut at 120-240 Hz\n")
        f.write(f"- **Bus peak protection**: -0.1 dBFS ceiling\n")
        f.write(f"\n")

        # === Automation Effects ===
        f.write(f"## Automation Effects\n\n")
        if auto_plan and auto_plan.get('events'):
            f.write(f"| Section | Bars | Bus | Effect | Onset |\n")
            f.write(f"|---------|------|-----|--------|-------|\n")
            for event in auto_plan['events']:
                name = event.get('name', '?')
                start = event.get('start_bar', 0)
                end = event.get('end_bar', 0)
                onset = event.get('onset', 'instant')
                effects = event.get('effects', {})
                for bus, effect in effects.items():
                    f.write(f"| {name} | {start}-{end} | {bus} | {effect} | {onset} |\n")
            f.write(f"\n")

            f.write(f"### Onset Types\n\n")
            f.write(f"| Onset | Behavior |\n")
            f.write(f"|-------|----------|\n")
            f.write(f"| `instant` | Full intensity from beat 1 |\n")
            f.write(f"| `quarter_note` | Builds over 1 beat |\n")
            f.write(f"| `rapid` | Builds in first 20% of segment |\n")
            f.write(f"| `two_note` | Builds over 2 beats (pre-chorus) |\n")
            f.write(f"\n")
        else:
            f.write(f"No automation plan logged.\n\n")

        # === Effect Depths ===
        f.write(f"## Effect Depth Settings\n\n")
        if effect_depth:
            f.write(f"| Parameter | Value |\n")
            f.write(f"|-----------|-------|\n")
            for k, v in effect_depth.items():
                f.write(f"| {k} | {v} |\n")
            f.write(f"\n")

    print(f"  Documentation: {doc_path}")
    print(f"\n  PROJECT COMPLETE: {project_dir}")


def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def remove_duplicate_final_masters(mastered_dir: str) -> tuple:
    """Remove parent mastered WAVs only when final/ has an identical copy."""
    final_dir = os.path.join(mastered_dir, "final")
    if not os.path.isdir(mastered_dir) or not os.path.isdir(final_dir):
        return [], []

    removed = []
    skipped = []
    for name in sorted(os.listdir(final_dir)):
        if not name.lower().endswith(".wav"):
            continue
        parent_path = os.path.join(mastered_dir, name)
        final_path = os.path.join(final_dir, name)
        if not os.path.isfile(parent_path) or not os.path.isfile(final_path):
            continue
        parent_size = os.path.getsize(parent_path)
        final_size = os.path.getsize(final_path)
        if parent_size != final_size:
            skipped.append((name, "size differs"))
            continue
        if _sha256_file(parent_path) != _sha256_file(final_path):
            skipped.append((name, "hash differs"))
            continue
        os.remove(parent_path)
        removed.append((name, parent_size))
    return removed, skipped


_CLEANUP_AUDIO_EXTENSIONS = (".wav", ".aif", ".aiff", ".flac")


def _is_audio_file(path: str) -> bool:
    return path.lower().endswith(_CLEANUP_AUDIO_EXTENSIONS)


def _safe_remove_empty_dirs(start_dir: str, stop_dir: str):
    """Remove empty directories from start_dir up to, but not including, stop_dir."""
    current = start_dir
    while current and os.path.abspath(current) != os.path.abspath(stop_dir):
        try:
            os.rmdir(current)
        except OSError:
            break
        current = os.path.dirname(current)


def _collect_cleanup_audio_candidates(mastered_dir: str, recordings_dir: str) -> list:
    """Return audio files that are intermediate under the current retention policy."""
    candidates = []

    def add(path: str, category: str, reason: str):
        if os.path.isfile(path) and _is_audio_file(path):
            candidates.append({
                "path": path,
                "category": category,
                "reason": reason,
                "size_bytes": os.path.getsize(path),
            })

    if os.path.isdir(mastered_dir):
        for subdir, category, reason in [
            ("processed", "processed_stem", "per-stem processed intermediate"),
            ("pristine_processed", "pristine_processed_stem", "duplicate pristine processing intermediate"),
            ("automated", "pre_section_automated_bus", "superseded by section_automated_buses"),
            ("sidechain_keys", "detector_key_bus", "detector-only sidechain key"),
            ("golden_post", "golden_post_audio", "candidate/intermediate golden-post render"),
        ]:
            root_dir = os.path.join(mastered_dir, subdir)
            if os.path.isdir(root_dir):
                for root, _, files in os.walk(root_dir):
                    for name in files:
                        add(os.path.join(root, name), category, reason)

        for name in os.listdir(mastered_dir):
            path = os.path.join(mastered_dir, name)
            if not os.path.isfile(path) or not _is_audio_file(path):
                continue
            if name.endswith("_mix.wav"):
                add(path, "temporary_mix", "temporary mix sum")
            elif name == "raw_summed_returns.wav":
                add(path, "raw_return_sum", "uncalibrated wet-return sum superseded by section_calibrated_returns.wav")

    if os.path.isdir(recordings_dir):
        for name in os.listdir(recordings_dir):
            path = os.path.join(recordings_dir, name)
            if name.endswith("_pass.wav") and "_pass0" in name:
                add(path, "raw_multichannel_pass", "raw multichannel pass capture superseded by split stem recordings")

    return candidates


def cleanup_intermediates(song_name: str, output_dir: str = None, recordings_dir: str = None,
                          dry_run: bool = False):
    """Delete intermediate WAV files after pipeline completion.
    
    PRESERVED (never deleted):
    - recordings/*.wav — individual stem WAVs (e.g. songname_pass01_part01_usb01-02_Bass.wav)
    - recordings/*.json — manifest files with patch/sound design data
    - midi/ — MIDI files
    - mastered/final/*.wav — final master variants
    - mastered/*_premaster.wav — full-song premaster reference
    - mastered/buses/ — dry bus sums for review
    - mastered/section_automated_buses/ — final-stage section-aware bus renders
    - mastered/reverb_returns/ — reverb return audio for review
    - mastered/delay_returns/ — delay return audio for review
    - mastered/section_calibrated_returns.wav — calibrated combined wet return
    - mastered/*.json / mastered/*.jsonl / mastered/*.md — production diagnostics
    - sample_pack_build/ — sample pack files
    
    DELETED:
    - mastered/processed/ — per-stem processed intermediates
    - mastered/pristine_processed/ — duplicate processing
    - mastered/automated/ — pre-section automated buses superseded by section_automated_buses/
    - mastered/sidechain_keys/ — detector-only sidechain keys
    - mastered/raw_summed_returns.wav — uncalibrated return sum
    - mastered/*_mix.wav — temporary mix sums
    - mastered/*.wav duplicated exactly in mastered/final/
    - mastered/golden_post/**/*.wav — post-audio intermediate renders
    - recordings/*_pass*_pass.wav — raw multi-pass recordings only
    """
    project_dir = os.path.join(str(PROJECT_ROOT), "output", song_name)
    mastered_dir = output_dir or os.path.join(project_dir, "mastered")
    recordings_dir = recordings_dir or os.path.join(project_dir, "recordings")

    deleted = []
    freed_bytes = 0
    skipped_duplicate_masters = []

    candidates = _collect_cleanup_audio_candidates(mastered_dir, recordings_dir)
    for item in candidates:
        path = item["path"]
        freed_bytes += item["size_bytes"]
        rel_base = recordings_dir if path.startswith(recordings_dir) else mastered_dir
        rel_path = os.path.relpath(path, rel_base)
        deleted.append({
            "path": f"recordings/{rel_path}" if rel_base == recordings_dir else rel_path,
            "category": item["category"],
            "reason": item["reason"],
            "size_bytes": item["size_bytes"],
        })
        if not dry_run:
            os.remove(path)
            _safe_remove_empty_dirs(os.path.dirname(path), mastered_dir if rel_base == mastered_dir else recordings_dir)

    duplicate_masters = []
    if not dry_run:
        duplicate_masters, skipped_duplicate_masters = remove_duplicate_final_masters(mastered_dir)
        for name, size_bytes in duplicate_masters:
            freed_bytes += size_bytes
            deleted.append({
                "path": f"duplicate_master/{name}",
                "category": "duplicate_parent_master",
                "reason": "identical copy exists in mastered/final",
                "size_bytes": size_bytes,
            })
        for name, reason in skipped_duplicate_masters:
            print(f"  Preserved parent master {name}: final copy {reason}")

    cleanup_manifest = {
        "song_name": song_name,
        "dry_run": dry_run,
        "freed_bytes": 0 if dry_run else freed_bytes,
        "candidate_bytes": freed_bytes,
        "deleted": deleted,
        "skipped_duplicate_masters": [
            {"name": name, "reason": reason}
            for name, reason in skipped_duplicate_masters
        ],
        "preserved_policy": [
            "recordings/*_part*_usb*.wav original split stems",
            "mastered/final/*.wav final masters",
            "mastered/*_premaster.wav full-song premaster",
            "mastered/buses/*.wav dry buses",
            "mastered/section_automated_buses/*.wav final-stage section-aware buses",
            "mastered/reverb_returns/*.wav and mastered/delay_returns/*.wav wet returns",
            "mastered/section_calibrated_returns.wav calibrated combined wet return",
        ],
    }
    manifest_path = os.path.join(mastered_dir, "cleanup_manifest.json")
    if os.path.isdir(mastered_dir) and not dry_run:
        with open(manifest_path, "w") as f:
            json.dump(cleanup_manifest, f, indent=2)

    if deleted:
        action = "Would clean up" if dry_run else "Cleaned up"
        bytes_label = "candidate" if dry_run else "freed"
        print(f"  {action} {len(deleted)} audio items, {bytes_label} {freed_bytes / 1024 / 1024:.1f} MB")
        if not dry_run:
            print(f"  Cleanup manifest: {manifest_path}")
    else:
        print("  No intermediate files to clean up")

    return cleanup_manifest


def run_full_pipeline(sample_pack: bool = False,
                      golden_post: bool = True,
                      golden_post_params: str = None,
                      golden_pan_seed: int = None,
                      section_aware_pink: bool = True,
                      workers: int = 3,
                      arrangement_seed: int = None):
    """Run the complete pipeline: MIDI → Record → Produce → Sample Pack."""
    print("=" * 70)
    print("FULL PIPELINE — MIDI → RECORD → PRODUCE")
    print("=" * 70)

    # Step 1: Generate MIDI
    midi_path, song_name, bpm, metadata = step_generate_midi()

    # Step 2: Record
    stems = step_record(midi_path, song_name, metadata)
    if not stems:
        print("  No stems recorded. Cannot proceed to production.")
        return

    # Step 3: Produce
    master_path = step_produce(
        stems, song_name, bpm,
        golden_post=golden_post,
        golden_post_params=golden_post_params,
        golden_pan_seed=golden_pan_seed,
        section_aware_pink=section_aware_pink,
        workers=workers,
        arrangement_seed=arrangement_seed,
    )

    # Step 4: Sample Pack (optional)
    sample_dir = None
    if sample_pack:
        sample_dir = step_sample_pack(midi_path, song_name)

    # Step 5: Consolidate
    step_consolidate(song_name, midi_path, master_path, stems, metadata)

    # Step 6: Cleanup intermediate files
    cleanup_intermediates(song_name)

    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETE: {song_name}")
    print(f"Master: {master_path}")
    if sample_dir:
        print(f"Sample Pack: {sample_dir}")
    print("=" * 70)


def run_production_only(stems_dir: str, song_name: str, bpm: float,
                        output_dir: str = None, sample_pack: bool = False,
                        midi_file: str = None,
                        resume_step: float = None,
                        exclude: list = None,
                        golden_post: bool = True,
                        golden_post_params: str = None,
                        golden_pan_seed: int = None,
                        section_aware_pink: bool = True,
                        workers: int = 3,
                        arrangement_seed: int = None):
    """Run production on existing stems, with optional sample pack."""
    stems = find_stems(stems_dir, exclude=exclude)
    if not stems:
        print(f"Error: No WAV files found in {stems_dir}")
        sys.exit(1)

    print(f"Found {len(stems)} stems in {stems_dir}")

    master_path = step_produce(
        stems, song_name, bpm, output_dir, resume_step,
        golden_post=golden_post,
        golden_post_params=golden_post_params,
        golden_pan_seed=golden_pan_seed,
        section_aware_pink=section_aware_pink,
        workers=workers,
        arrangement_seed=arrangement_seed,
    )

    # Sample pack (optional) — always generates fresh MIDI via midi_orchestrator
    sample_dir = None
    if sample_pack:
        print("\n  Generating fresh MIDI for sample pack...")
        try:
            fresh_midi, _, _, _ = step_generate_midi()
            sample_dir = step_sample_pack(fresh_midi, song_name)
        except Exception as e:
            print(f"  Sample pack failed: {e}")

    if master_path:
        # Cleanup intermediate files
        cleanup_intermediates(song_name, output_dir=output_dir, recordings_dir=stems_dir)

        print(f"\n{'='*70}")
        print(f"PRODUCTION COMPLETE: {song_name}")
        print(f"Master: {master_path}")
        if sample_dir:
            print(f"Sample Pack: {sample_dir}")
        print(f"{'='*70}")
    else:
        print("Production failed — no master produced.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Full Pipeline Orchestrator — MIDI → Recording → Production"
    )

    # Mode selection
    parser.add_argument("--full", action="store_true", default=False,
                        help="Run full pipeline (MIDI → record → produce)")
    parser.add_argument("--midi-only", action="store_true",
                        help="Generate MIDI only")
    parser.add_argument("--produce-only", action="store_true",
                        help="Run production only on existing stems")

    # Production options
    parser.add_argument("--stems", type=str, default=None,
                        help="Directory containing stem WAV files")
    parser.add_argument("--song-name", type=str, default=None,
                        help="Song name for output files")
    parser.add_argument("--bpm", type=float, default=None,
                        help="Beats per minute")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory")
    parser.add_argument("--resume-step", type=float, default=None,
                        help="Resume production from step (1, 2, 2.5, 3, 4, 5). Auto-detects if omitted.")
    parser.add_argument("--exclude-stem", type=str, action='append', default=[],
                        help="Exclude stems matching this substring (can be used multiple times)")
    parser.add_argument("--golden-post", action="store_true", default=True,
                        help="Use the promoted golden post-audio pathway (default)")
    parser.add_argument("--no-golden-post", action="store_true",
                        help="Disable the promoted golden post-audio pathway and use the older summing path")
    parser.add_argument("--golden-post-params", type=str, default=None,
                        help="Optional JSON parameter file for the golden post-audio pathway")
    parser.add_argument("--golden-pan-seed", type=int, default=None,
                        help="Optional fixed pan seed for repeatable dry stereo-wall placement")
    parser.add_argument("--no-section-aware-pink", action="store_true",
                        help="Disable post-automation section-aware pink staging and wet-return calibration")
    parser.add_argument("--workers", type=int, default=3,
                        help="Parallel stem workers for objective pink-noise processing (default: 3)")
    parser.add_argument("--arrangement-seed", type=int, default=None,
                        help="Optional fixed seed for repeatable bass ownership and layer-reveal choices")

    # Sample pack options
    parser.add_argument("--sample-pack", action="store_true",
                        help="Generate companion sample pack (requires Fantom connected)")
    parser.add_argument("--midi-file", type=str, default=None,
                        help="MIDI file for sample pack generation (auto-detected if not provided)")

    args = parser.parse_args()
    golden_post = bool(args.golden_post and not args.no_golden_post)
    section_aware_pink = not bool(args.no_section_aware_pink)

    # Default: run full pipeline with sample pack if no mode specified
    no_mode_selected = not any([args.full, args.midi_only, args.produce_only,
                                args.stems, args.sample_pack])

    if args.full or no_mode_selected:
        run_full_pipeline(
            sample_pack=True,
            golden_post=golden_post,
            golden_post_params=args.golden_post_params,
            golden_pan_seed=args.golden_pan_seed,
            section_aware_pink=section_aware_pink,
            workers=args.workers,
            arrangement_seed=args.arrangement_seed,
        )
    elif args.midi_only:
        midi_path, song_name, bpm, _ = step_generate_midi()
        print(f"\nMIDI generated: {midi_path}")
    elif args.sample_pack:
        # Sample pack only mode
        if not args.song_name:
            print("Error: --song-name required for sample pack generation")
            sys.exit(1)
        midi_path = args.midi_file or find_midi_file(args.song_name)
        if not midi_path:
            print(f"Error: MIDI file not found for '{args.song_name}'. Use --midi-file to specify.")
            sys.exit(1)
        sample_dir = step_sample_pack(midi_path, args.song_name)
        print(f"\nSample pack: {sample_dir}")
    elif args.produce_only or args.stems:
        if not args.stems:
            print("Error: --stems required for production mode")
            sys.exit(1)
        if not args.song_name:
            args.song_name = os.path.basename(os.path.normpath(args.stems))
        if not args.bpm:
            midi_path = find_midi_file(args.song_name)
            if midi_path:
                args.bpm = get_bpm_from_midi(midi_path)
                print(f"BPM from MIDI: {args.bpm}")
            else:
                args.bpm = 90.0
                print(f"BPM defaulting to: {args.bpm}")
        run_production_only(args.stems, args.song_name, args.bpm, args.output_dir,
                            sample_pack=args.sample_pack, midi_file=args.midi_file,
                            resume_step=args.resume_step,
                            exclude=args.exclude_stem,
                            golden_post=golden_post,
                            golden_post_params=args.golden_post_params,
                            golden_pan_seed=args.golden_pan_seed,
                            section_aware_pink=section_aware_pink,
                            workers=args.workers,
                            arrangement_seed=args.arrangement_seed)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

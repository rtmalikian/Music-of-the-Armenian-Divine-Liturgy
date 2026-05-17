#!/usr/bin/env python3
import mido
import random
import os
import sys
from datetime import datetime
from typing import List, Dict

# Add parent directory and current directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

from midi_config import (
    TOTAL_BARS, PROD_DIR, SCALES_FILE, SWING_VALUES, NOTE_NAMES, REGISTER_RANGES,
    TIME_SIGNATURES, get_bar_length_ticks, get_song_length_ticks
)
from midi_models import VoiceLeadingContext, TensionState, MelodyNote
from midi_theory import (
    ARMENIAN_MAQAM_SCALES, MODE_INTERVALS, get_chord_quality, get_chord_notes,
    plan_cadences, clamp_to_register, filter_scale_tones, get_modal_pad_chord,
    get_microtonal_offset_for_root, parse_chord_symbol, build_bar_harmony,
    nearest_chord_or_scale_tone
)
from midi_composition import (
    generate_4bar_loop, generate_euclidean, generate_bass,
    generate_harmonic_bass, generate_counter_melody_2bar
)
from midi_musical_devices import resolve_suspension_voicing, voice_lead_pad_chord
from midi_song_structure import (
    VERSE_PROGRESSIONS, CHORUS_PROGRESSIONS, INTRO_OUTRO_PROGRESSIONS,
    FILL_PROGRESSIONS, LOFI_PROGRESSIONS, get_bar_type, get_passing_chord,
    transform_loop
)
from midi_engine import (
    apply_swing, init_spatial, write_performance_to_track
)
from midi_analysis import analyze_melody_intervals, analyze_voice_leading

# Drum imports
from midi_drum_sequences import (
    get_pattern_funcs as get_drum_pattern_funcs,
    GM_DRUM_MAP, PATTERN_FAMILIES, PATTERN_FAMILY_MAP
)

def main():
    print("=" * 70)
    print("Music Generator v10.0.10 - Orchestrated Edition")
    print("=" * 70)

    # BPM Randomization (75-95 BPM)
    song_bpm = random.randint(75, 95)
    print(f"SONG BPM: {song_bpm}")

    # Time signature selection
    time_sig = random.choice(list(TIME_SIGNATURES.keys()))
    bar_length = get_bar_length_ticks(time_sig)
    song_length = get_song_length_ticks(time_sig)
    ts_info = TIME_SIGNATURES[time_sig]
    beats_per_bar = ts_info['beats_per_bar']
    print(f"TIME SIGNATURE: {ts_info['numerator']}/{ts_info['denominator']}")

    # Inversion: 10% of songs get ONE inverted bar in ONE section
    inverted = False
    inverted_section = None
    inverted_bar_pos = None
    inverted_section_idx = None
    if random.random() < 0.10:
        inverted = True
        inverted_section = random.choice(['verse', 'chorus', 'fill'])
        inverted_bar_pos = random.randint(0, 7)
        inverted_section_idx = random.choice([1, 2])
        print(f"INVERSION: {inverted_section}{inverted_section_idx} bar position {inverted_bar_pos}")

    mid = mido.MidiFile(type=1)
    tempo_tr = mido.MidiTrack()
    bass_tr = mido.MidiTrack()
    harm_bass_tr = mido.MidiTrack()
    main_mel_tr = mido.MidiTrack()
    counter_mel_tr = mido.MidiTrack()
    chorus_mel_tr = mido.MidiTrack()
    fx_tr = mido.MidiTrack()
    drums_main_tr = mido.MidiTrack()
    drums_chorus_tr = mido.MidiTrack()
    pad_tr = mido.MidiTrack()
    aux_tr = mido.MidiTrack()
    aux_tr.name = 'Aux Percussion'

    mid.tracks.extend([tempo_tr, bass_tr, harm_bass_tr, main_mel_tr, counter_mel_tr,
                       chorus_mel_tr, fx_tr, drums_main_tr, drums_chorus_tr, pad_tr, aux_tr])

    tempo_tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(song_bpm), time=0))
    tempo_tr.append(mido.MetaMessage('time_signature',
        numerator=ts_info['numerator'], denominator=ts_info['denominator'], time=0))
    tempo_tr.append(mido.MetaMessage('end_of_track', time=song_length))

    scales_map = {}
    try:
        with open(SCALES_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split(' ', 1)
                if len(parts) >= 2: scales_map[parts[0]] = [int(n) for n in parts[1].split()]
    except FileNotFoundError: pass

    for ro in range(12):
        for mn, iv in MODE_INTERVALS.items(): scales_map[f"{NOTE_NAMES[ro]} {mn}"] = [ro + i for i in iv]
        for mn, sc in ARMENIAN_MAQAM_SCALES.items(): scales_map[f"{NOTE_NAMES[ro]} {mn}"] = [ro + i for i in sc['intervals']]

    if random.random() < 0.75:
        major_minor_scales = [k for k in scales_map.keys()
                              if any(m in k for m in ("Major", "Minor"))]
        scale_name = random.choice(major_minor_scales)
    else:
        other_scales = [k for k in scales_map.keys()
                        if not any(m in k for m in ("Major", "Minor"))]
        scale_name = random.choice(other_scales)
    
    scale_notes = scales_map[scale_name]
    base = scale_notes[0]
    key = NOTE_NAMES[base % 12]
    is_armenian = any(m in scale_name for m in ARMENIAN_MAQAM_SCALES.keys())
    armenian_scale_name = next((m for m in ARMENIAN_MAQAM_SCALES if m in scale_name), None)

    verse_prog_discard = random.choice(list(LOFI_PROGRESSIONS.keys()))
    chorus_prog_discard = random.choice(list(LOFI_PROGRESSIONS.keys()))

    verse_prog_name = random.choice(list(VERSE_PROGRESSIONS.keys()))
    chorus_prog_name = random.choice(list(CHORUS_PROGRESSIONS.keys()))
    intro_prog_name = random.choice(list(INTRO_OUTRO_PROGRESSIONS.keys()))
    fill_prog_name = random.choice(list(FILL_PROGRESSIONS.keys()))
    
    verse_prog = VERSE_PROGRESSIONS[verse_prog_name]
    chorus_prog = CHORUS_PROGRESSIONS[chorus_prog_name]
    intro_prog = INTRO_OUTRO_PROGRESSIONS[intro_prog_name]
    fill_prog = FILL_PROGRESSIONS[fill_prog_name]

    print(f"\nScale: {key} {scale_name}")
    print(f"Armenian/Maqam: {'Yes (' + armenian_scale_name + ')' if is_armenian else 'No'}")
    print(f"Progressions: {verse_prog_discard} → {chorus_prog_discard}")
    
    print(f"\nChord Progressions:")
    print(f"  Intro: {intro_prog_name}")
    print(f"  Verse: {verse_prog_name}")
    print(f"  Chorus: {chorus_prog_name}")
    print(f"  Fill: {fill_prog_name}")

    cadences = plan_cadences(TOTAL_BARS)
    cadence_bars = {c.bar: c.cadence_type for c in cadences}

    harmony_plan = []
    def progression_for_section(section_type):
        if section_type in ['intro', 'outro']:
            return intro_prog
        if section_type.startswith('chorus'):
            return chorus_prog
        if section_type.startswith('fill'):
            return fill_prog
        return verse_prog

    def chord_degree(chord_token):
        return parse_chord_symbol(chord_token, scale_notes, base).root_offset

    for bar in range(TOTAL_BARS):
        bt = get_bar_type(bar)
        next_bt = get_bar_type(bar + 1) if bar + 1 < TOTAL_BARS else None
        is_last = (bt == 'intro' and bar == 7) or (bt == 'verse1' and bar == 23) or (bt == 'chorus1' and bar == 31) or \
                  (bt == 'fill1' and bar == 35) or (bt == 'verse2' and bar == 51) or (bt == 'chorus2' and bar == 59) or \
                  (bt == 'fill2' and bar == 63) or (bt == 'outro' and bar == 71)
        
        prog = progression_for_section(bt)
        chord_token = prog[bar % len(prog)]
        next_target_degree = None
        if is_last and next_bt:
            next_prog = progression_for_section(next_bt)
            next_target_degree = chord_degree(next_prog[(bar + 1) % len(next_prog)])
            chord_token = get_passing_chord(bt, next_bt, base, scale_notes, next_target_degree)
        harmony_plan.append(build_bar_harmony(
            bar, bt, chord_token, base, scale_notes, armenian_scale_name if is_armenian else scale_name
        ))

    bass_tr.name = 'Bass'
    bass_tr.append(mido.MetaMessage('track_name', name='Bass', time=0))
    harm_bass_tr.name = 'Harmonic Bass'
    harm_bass_tr.append(mido.MetaMessage('track_name', name='Harmonic Bass', time=0))
    main_mel_tr.name = 'Main Melody'
    main_mel_tr.append(mido.MetaMessage('track_name', name='Main Melody', time=0))
    counter_mel_tr.name = 'Counter Melody'
    counter_mel_tr.append(mido.MetaMessage('track_name', name='Counter Melody', time=0))
    chorus_mel_tr.name = 'Chorus Melody'
    chorus_mel_tr.append(mido.MetaMessage('track_name', name='Chorus Melody', time=0))
    fx_tr.name = 'Melody FX'
    fx_tr.append(mido.MetaMessage('track_name', name='Melody FX', time=0))
    pad_tr.name = 'Pad (Chords)'
    pad_tr.append(mido.MetaMessage('track_name', name='Pad (Chords)', time=0)) 

    # We skip naming drums_main_tr and drums_chorus_tr as they will be removed after explosion


    verse_loop = generate_4bar_loop(
        scale_notes, base, armenian_scale_name if is_armenian else 'western',
        False, bar_length, harmony_window=harmony_plan[8:12]
    )
    chorus_loop = generate_4bar_loop(
        scale_notes, base, armenian_scale_name if is_armenian else 'western',
        True, bar_length, harmony_window=harmony_plan[24:28]
    )
    print(f"  Melody personas: verse={verse_loop.get('persona', 'legacy')}, chorus={chorus_loop.get('persona', 'legacy')}")

    all_melody_notes, main_mel_analysis, chorus_mel_analysis, bass_analysis = [], [], [], []
    gvc, current_swing = VoiceLeadingContext(), SWING_VALUES['medium']
    bass_ev, harm_bass_ev, main_mel_ev, chorus_mel_ev, fx_ev, pad_ev, counter_mel_ev, aux_perc_ev = [], [], [], [], [], [], [], []
    section_high_notes = {}
    previous_pad_voicing = None
    drone_starts = {0: 8, 8: 16, 24: 8, 32: 4, 36: 16, 52: 8, 60: 4, 64: 8}

    def add_pitch_bend_event(events, time, cents):
        pitch = int(max(-8192, min(8191, (cents / 100.0) * 4096)))
        events.append({'time': max(0, time), 'type': 'pitchwheel', 'pitch': pitch})

    def add_melody_note(events, abs_t, note, vel, dur, scale_name_for_bend=None,
                        prev_note=None):
        if scale_name_for_bend in ARMENIAN_MAQAM_SCALES:
            ascending = True if prev_note is None else note >= prev_note
            cents = get_microtonal_offset_for_root(note, base, scale_name_for_bend, ascending)
            if cents:
                add_pitch_bend_event(events, abs_t, cents)
                events.extend([
                    {'time': abs_t, 'note': note, 'vel': vel},
                    {'time': abs_t + dur, 'note': note, 'vel': 0},
                ])
                add_pitch_bend_event(events, abs_t + dur, 0)
                return cents
        events.extend([
            {'time': abs_t, 'note': note, 'vel': vel},
            {'time': abs_t + dur, 'note': note, 'vel': 0},
        ])
        return 0

    def nearest_chord_tone(note, chord):
        pcs = [c % 12 for c in chord]
        candidates = [pc + 12 * octv for pc in pcs for octv in range(11)]
        candidates = [c for c in candidates if 48 <= c <= 86]
        return min(candidates, key=lambda n: abs(n - note)) if candidates else note

    def refine_major_minor_melody(note, tick, root, quality, chord, bar, dur):
        if not any(mode in scale_name for mode in ('Major', 'Minor')):
            return note
        strong_position = tick == 0 or tick % 480 == 0 or dur >= 720
        phrase_tail = tick >= int(bar_length * 0.72)
        if 'Minor' in scale_name and bar in cadence_bars and phrase_tail:
            raised_leading_pc = (base + 11) % 12
            natural_seventh_pc = (base + 10) % 12
            if note % 12 == natural_seventh_pc and random.random() < 0.65:
                return clamp_to_register(note + 1 if note + 1 <= 86 else note - 11, 'main_melody')
            if random.random() < 0.35:
                return clamp_to_register(nearest_chord_tone(note, [root, root + 3, root + 7]), 'main_melody')
        if strong_position and note % 12 not in [c % 12 for c in chord] and random.random() < (0.55 if phrase_tail else 0.35):
            return clamp_to_register(nearest_chord_tone(note, chord), 'main_melody')
        if 'Major' in scale_name and bt.startswith('chorus') and tick == 0 and random.random() < 0.15:
            sixth = (base + 9) % 12
            if sixth in {s % 12 for s in scale_notes} and sixth in {c % 12 for c in chord}:
                return clamp_to_register(min([sixth + 12 * octv for octv in range(11)], key=lambda n: abs(n - note)), 'chorus_melody')
        return note

    for bar in range(TOTAL_BARS):
        bt = get_bar_type(bar)
        harmony = harmony_plan[bar]
        root = harmony.root
        if bt == 'intro': energy = 0.3 + (bar / 8) * 0.3
        elif bt.startswith('verse'): energy = 0.6
        elif bt.startswith('chorus'): energy = 0.9
        elif bt.startswith('fill'): energy = 0.8
        else: energy = 0.7 - ((bar - 64) / 8) * 0.5
        
        dropout_active = (bar in [7, 23, 31, 35, 51, 59, 63]) and random.random() < 0.5
        qual = 'major' if (bar == 71 and is_armenian) else (
            'minor' if harmony.spec.quality in ['minor', 'min7', 'min9'] else
            'dom7' if harmony.spec.quality == 'dom7' else
            get_chord_quality(root, scale_notes)
        )
        bs = bar * bar_length

        if is_armenian and bar in drone_starts:
            drone_root = clamp_to_register(root, 'harmonic_bass')
            drone_fifth = clamp_to_register(root + 7, 'harmonic_bass')
            drone_dur = min(drone_starts[bar] * bar_length, song_length - bs)
            drone_vel = 34 if bt.startswith('verse') else 40 if bt.startswith('chorus') else 28
            for dn, dvel in [(drone_root, drone_vel), (drone_fifth, max(20, drone_vel - 8))]:
                harm_bass_ev.extend([
                    {'time': bs, 'note': dn, 'vel': dvel},
                    {'time': bs + drone_dur, 'note': dn, 'vel': 0},
                ])

        if bar > 4 and bt != 'outro':
            # Euclidean auxiliary percussion (Boom Bap friendly)
            # Standard Boom Bap percussion: Tambourine (54), Maracas (70)
            # Remove Bongos (60, 61) and Congas (62)
            e_steps = max(4, int(16 * beats_per_bar / 4))
            e_pattern = generate_euclidean(random.choice([2, 3, 4]), e_steps)
            perc_note = random.choice([54, 70])
            for i, pulse in enumerate(e_pattern):
                if pulse:
                    p_abs = bs + i * 120 + (random.randint(-20, 20) if current_swing > 0.5 else 0)
                    # Lower velocity for background percussion
                    aux_perc_ev.extend([{'time': p_abs, 'note': perc_note, 'vel': int(random.randint(30, 55) * energy)},
                                        {'time': p_abs + 60, 'note': perc_note, 'vel': 0}])

        current_loop = transform_loop(verse_loop, random.choice(['retrograde', 'inversion', 'original'])) if bt == 'verse2' else (chorus_loop if bt.startswith('chorus') else verse_loop)

        if bar < 71:
            styles = {'intro': 'dotted_half' if bar >= 4 else 'whole', 'verse1': ['root_fifth', 'standard', 'half_quarter', 'root_fifth'][bar % 4],
                      'chorus1': ['standard', 'active', 'root_fifth', 'standard'][bar % 4], 'fill1': 'active', 'outro': 'dotted_half' if bar < 68 else 'whole'}
            next_harmony = harmony_plan[bar + 1] if bar + 1 < len(harmony_plan) else None
            bcell = generate_bass(root, qual, scale_notes, gvc, None, styles.get(bt, 'standard'), bar, bar_length, time_sig, harmony=harmony, next_harmony=next_harmony)
            tick = 0
            for i, note in enumerate(bcell.notes):
                dur = bcell.rhythm[i]
                if tick + dur > bar_length: dur = bar_length - tick
                if note is not None:
                    vel = int((80 + (15 if bt.startswith('chorus') else 0)) * energy) + (10 if i == 0 and dur > 120 else 0)
                    if dur <= 120: vel = int(vel * 0.6)
                    abs_t = bs + tick + (apply_swing(0, (tick // 120) % 8, current_swing * 0.5) if current_swing > 0.5 else 0)
                    if abs_t + dur <= song_length:
                        fn = clamp_to_register(note, 'bass')
                        bass_ev.extend([{'time': abs_t, 'note': fn, 'vel': vel}, {'time': abs_t + dur, 'note': fn, 'vel': 0}])
                        bass_analysis.append(fn)
                tick += dur

        target_ev = main_mel_ev if bt in ['intro', 'verse1', 'verse2', 'outro'] else chorus_mel_ev
        source = 'main' if bt in ['intro', 'verse1', 'verse2', 'outro'] else 'chorus'
        base_vel = int((95 if source == 'main' else 108) * energy)
        phrase = None
        if current_loop.get('bars'):
            phrase = current_loop['bars'][bar % 4]
        else:
            start_idx = (bar % 4) * (len(current_loop['notes']) // 4)
            end_idx = min(start_idx + len(current_loop['notes']) // 4, len(current_loop['notes']))
            phrase = {
                'notes': current_loop['notes'][start_idx:end_idx],
                'rhythm': current_loop['rhythm'][start_idx:end_idx],
                'harmony_aware': current_loop.get('harmony_aware', False),
            }
        tick = 0
        for i in range(len(phrase['notes'])):
            if dropout_active and tick > 960: break
            note, dur = phrase['notes'][i], phrase['rhythm'][i]
            if note is None:
                tick += dur
                continue
            if phrase.get('harmony_aware'):
                fn = clamp_to_register(note, 'main_melody' if source == 'main' else 'chorus_melody')
            else:
                fn = clamp_to_register(note + (root - base), 'main_melody' if source == 'main' else 'chorus_melody')
            if not is_armenian:
                fn = refine_major_minor_melody(fn, tick, root, qual, harmony.chord_tones, bar, dur)
                fn = nearest_chord_or_scale_tone(fn, harmony, 'main_melody' if source == 'main' else 'chorus_melody', tick % 480 == 0)
                if source == 'chorus' and tick % 480 != 0 and fn % 12 not in {c % 12 for c in harmony.chord_tones}:
                    if random.random() < (0.75 if tick >= int(bar_length * 0.65) else 0.45):
                        fn = nearest_chord_or_scale_tone(fn, harmony, 'chorus_melody', True)
            if fn > 80:
                sid = bar // 8
                if section_high_notes.get(sid, 0) > 0: fn -= 12
                section_high_notes[sid] = section_high_notes.get(sid, 0) + 1
            if source == 'chorus' and tick % 480 == 0 and not is_armenian:
                fn = nearest_chord_or_scale_tone(fn, harmony, 'chorus_melody', True)
            vel = random.randint(base_vel - 8, base_vel + 8)
            if bar in [14, 22, 42, 50]: vel = int(vel * (1.0 - (tick / bar_length)))
            elif bar in [15, 23, 43, 51]: vel = 0
            abs_t = bs + tick + (apply_swing(0, (tick // 120) % 8, current_swing) if current_swing > 0.5 else 0)
            if is_armenian and random.random() < 0.25 and vel > 0:
                grace = fn - random.choice([1, 2])
                grace_t = max(bs, abs_t - 30)
                target_ev.extend([{'time': grace_t, 'note': grace, 'vel': int(vel*0.8)}, {'time': abs_t, 'note': grace, 'vel': 0}])
            if vel > 0:
                prev_note = all_melody_notes[-1].note if all_melody_notes else None
                cents = add_melody_note(target_ev, abs_t, fn, vel, dur,
                                        armenian_scale_name if is_armenian else None,
                                        prev_note)
                all_melody_notes.append(MelodyNote(abs_t, bar, fn, vel, source, cents))
                if source == 'main': main_mel_analysis.append(fn)
                else: chorus_mel_analysis.append(fn)
            tick += dur

        if bar < 71:
            hcell = generate_harmonic_bass(root, qual, scale_notes, VoiceLeadingContext(), None, 'standard', bar, bar_length, time_sig, harmony=harmony)
            tick = 0
            for i, note in enumerate(hcell.notes):
                dur = hcell.rhythm[i]
                if tick + dur > bar_length: dur = bar_length - tick
                if note is not None:
                    abs_t = bs + tick + (apply_swing(0, (tick // 120) % 8, current_swing * 0.5) if current_swing > 0.5 else 0)
                    if abs_t + dur <= song_length:
                        fn = clamp_to_register(note, 'harmonic_bass')
                        harm_bass_ev.extend([{'time': abs_t, 'note': fn, 'vel': random.randint(55, 70)}, {'time': abs_t + dur, 'note': fn, 'vel': 0}])
                tick += dur

        if bt not in ['fill1', 'fill2']:
            raw_chord = get_modal_pad_chord(root, qual, scale_notes, armenian_scale_name, energy) if is_armenian else list(harmony.chord_tones)
            has_explicit_color = bool(harmony.spec.extensions or harmony.spec.suspension or harmony.spec.quality in ['maj7', 'min7', 'min9', 'dom7'])
            if (not has_explicit_color) and random.random() < (0.15 if is_armenian else 0.3):
                ext = random.choice([root + 14, root + 17, root + 21])
                if ext not in raw_chord and (not is_armenian or ext % 12 in {n % 12 for n in scale_notes}):
                    raw_chord.append(ext)
            raw_chord = (filter_scale_tones(raw_chord, scale_notes) or raw_chord) if is_armenian else raw_chord
            pad_chord, is_susp = list(raw_chord), bool(harmony.spec.suspension)
            if (not harmony.spec.suspension) and random.random() < (0.55 if is_armenian else 0.4):
                third, fourth = root + (4 if qual == 'major' else 3), root + 5
                if third in pad_chord: pad_chord.remove(third); pad_chord.append(fourth); is_susp = True
            pad_chord = voice_lead_pad_chord([clamp_to_register(n, 'pad') for n in pad_chord], previous_pad_voicing)
            pad_vel = random.randint(45, 63) if is_armenian else random.randint(55, 75)
            if is_susp:
                for p in pad_chord: pad_ev.extend([{'time': bs, 'note': p, 'vel': pad_vel}, {'time': bs + 480, 'note': p, 'vel': 0}])
                resolved = resolve_suspension_voicing(pad_chord, [clamp_to_register(n, 'pad') for n in raw_chord])
                for r in resolved: pad_ev.extend([{'time': bs + 480, 'note': r, 'vel': pad_vel}, {'time': bs + bar_length, 'note': r, 'vel': 0}])
                previous_pad_voicing = resolved
            else:
                pdur = bar_length + (240 if bar in cadence_bars else random.randint(-60, 60))
                for p in sorted(list(set(pad_chord))): pad_ev.extend([{'time': bs, 'note': p, 'vel': pad_vel}, {'time': bs + pdur, 'note': p, 'vel': 0}])
                previous_pad_voicing = pad_chord
        
        if (not is_armenian) and ((bt == 'verse1' and bar - 8 in [6, 14]) or (bt == 'verse2' and bar - 36 in [6, 14])):
            cm_harmony = harmony_plan[bar:min(bar + 2, len(harmony_plan))]
            cm_data = generate_counter_melody_2bar(scale_notes, base, armenian_scale_name if is_armenian else 'western', root, qual, bar_length=bar_length, harmony=harmony, harmony_window=cm_harmony)
            tick = 0
            for i in range(len(cm_data['notes'])):
                cn, cd = cm_data['notes'][i], cm_data['rhythm'][i]
                if tick + cd > bar_length * 2: cd = (bar_length * 2) - tick
                if cd <= 0: break
                if cn is None:
                    tick += cd
                    continue
                cabs = bs + tick + (apply_swing(0, (tick // 120) % 8, current_swing) if current_swing > 0.5 else 0)
                if cabs + cd <= song_length:
                    harmony_for_counter = harmony_plan[min(len(harmony_plan) - 1, bar + int(tick // bar_length))]
                    fn = clamp_to_register(cn, 'counter_melody')
                    fn = nearest_chord_or_scale_tone(fn, harmony_for_counter, 'counter_melody', tick % bar_length in (0, 960))
                    counter_mel_ev.extend([{'time': cabs, 'note': fn, 'vel': random.randint(65, 80)}, {'time': cabs + cd, 'note': fn, 'vel': 0}])
                tick += cd

    if is_armenian:
        shadow_candidates = [mn for mn in all_melody_notes if mn.bar < 64 and mn.velocity > 0]
        for mn in shadow_candidates:
            if random.random() > 0.58:
                continue
            delay = random.choice([45, 60, 75])
            shadow_note = clamp_to_register(mn.note - 12 if mn.note > 66 else mn.note, 'counter_melody')
            shadow_vel = max(32, int(mn.velocity * random.uniform(0.45, 0.62)))
            dur = random.choice([180, 240, 300])
            st = mn.abs_time + delay
            if st + dur < song_length:
                counter_mel_ev.extend([
                    {'time': st, 'note': shadow_note, 'vel': shadow_vel},
                    {'time': st + dur, 'note': shadow_note, 'vel': 0},
                ])

    for mn in all_melody_notes:
        if mn.bar < 68 and random.random() < (0.2 + (mn.velocity / 127) * 0.2):
            fx_note = mn.note + 12
            if fx_note > 110: fx_note -= 12
            fx_note = nearest_chord_or_scale_tone(fx_note, harmony_plan[mn.bar], 'fx', True)
            for tap in range(3):
                dt = mn.abs_time + (tap * 360)
                if dt + 120 >= song_length: break
                tvel = int(mn.velocity * (0.8 / (tap + 1)))
                if tvel < 10: break
                fx_ev.extend([{'time': dt, 'note': fx_note, 'vel': tvel}, {'time': dt + 120, 'note': fx_note, 'vel': 0}])

    main_ev, chorus_ev = [], []
    bbA, bbB, bbC, bbD, main_family, chorus_family = get_drum_pattern_funcs()
    print(f"  Drum families: main={main_family}, chorus={chorus_family}")

    for bar in range(TOTAL_BARS):
        bt = get_bar_type(bar)
        bs = bar * bar_length
        is_lead = bar in [7, 23, 31, 35, 51, 59, 63]

        # Determine if THIS specific bar is inverted
        bar_inverted = False
        if inverted:
            section_key = f"{inverted_section}{inverted_section_idx}"
            if bt == section_key:
                section_start = {'verse1': 8, 'verse2': 36, 'chorus1': 24, 'chorus2': 52,
                                 'fill1': 32, 'fill2': 60}.get(bt, 0)
                phrase_pos = (bar - section_start) % 8
                if phrase_pos == inverted_bar_pos:
                    bar_inverted = True

        # Surprise bar (5%)
        if random.random() < 0.05:
            sf = random.choice(PATTERN_FAMILIES)
            dbar = PATTERN_FAMILY_MAP[sf](480, random.randint(0, 3), variation_level=1,
                                           is_chorus=bt.startswith('chorus'),
                                           inverted=bar_inverted, time_sig=time_sig)
        elif is_lead or bt.startswith('fill'):
            dbar = bbD(480, 2, bt.startswith('chorus'), inverted=bar_inverted, time_sig=time_sig)
        elif bt.startswith('chorus'):
            dbar = bbC(480, 1, True, inverted=bar_inverted, time_sig=time_sig)
        else:
            if random.random() < 0.10:
                sf = random.choice(PATTERN_FAMILIES)
                dbar = PATTERN_FAMILY_MAP[sf](480, random.randint(0, 3), variation_level=1,
                                               is_chorus=False, inverted=bar_inverted, time_sig=time_sig)
            else:
                p_id = random.randint(0, 3)
                dbar = bbA(480, p_id, False, inverted=bar_inverted, time_sig=time_sig) \
                    if bar % 2 == 0 \
                    else bbB(480, p_id, False, inverted=bar_inverted, time_sig=time_sig)

        # Map to specific drum sounds based on section intensity
        k_note, s_note = (36, 38) # Standard Boom Bap Kick/Snare
        if bt.startswith('chorus'):
            k_note, s_note = 36, 40 # Heavier snare/clap for chorus
            
        active_ev = chorus_ev if bt in ['chorus1','chorus2','fill1','fill2'] else main_ev
        last_hat = -100
        for n in sorted(dbar, key=lambda x: x['time']):
            msg = dict(n)
            # Re-map notes if necessary (bb patterns use 36 and 38 for kick/snare)
            if msg['note'] == 36: msg['note'] = k_note
            elif msg['note'] == 38: msg['note'] = s_note
            
            # Subtle chorus layer
            if bt.startswith('chorus') and msg['note'] == s_note and random.random() < 0.3: 
                active_ev.extend([{'time': bs + n['time'], 'note': 39, 'vel': int(msg['velocity'] * 0.8)}, {'time': bs + n['time'] + 60, 'note': 39, 'vel': 0}])
            
            if msg['note'] == 42 and abs(msg['time'] - last_hat) < 120: continue
            if msg['note'] == 46: last_hat = msg['time']
            
            abs_t = bs + msg['time'] + apply_swing(0, (msg['time'] // 120) % 8, current_swing)
            active_ev.extend([{'time': abs_t, 'note': msg['note'], 'vel': msg['velocity']}, {'time': abs_t + 60, 'note': msg['note'], 'vel': 0}])

    for ev_list in [main_ev, chorus_ev, bass_ev, harm_bass_ev, main_mel_ev, chorus_mel_ev, fx_ev, pad_ev, counter_mel_ev, aux_perc_ev]: ev_list.sort(key=lambda x: x['time'])
    
    # === ANALYZE OUTPUT ===
    main_analysis = analyze_melody_intervals(main_mel_analysis)
    chorus_analysis = analyze_melody_intervals(chorus_mel_analysis)
    vl_analysis = analyze_voice_leading(bass_analysis, main_mel_analysis)

    print(f"\n{'='*70}")
    print("MELODIC INTERVAL ANALYSIS")
    print(f"{'='*70}")
    print(f"Main Melody: {main_analysis['stepwise']:.1f}% Stepwise, {main_analysis['small_leap']:.1f}% Small Leaps, {main_analysis['large_leap']:.1f}% Large Leaps")
    print(f"Chorus Melody: {chorus_analysis['stepwise']:.1f}% Stepwise, {chorus_analysis['small_leap']:.1f}% Small Leaps, {chorus_analysis['large_leap']:.1f}% Large Leaps")
    
    print(f"\nVOICE LEADING ANALYSIS")
    print(f"{'='*70}")
    print(f"Contrary Motion: {vl_analysis['contrary']:.1f}% | Parallel: {vl_analysis['parallel']:.1f}%")
    print(f"{'='*70}\n")

    init_spatial(bass_tr, 64); init_spatial(main_mel_tr, 80); init_spatial(counter_mel_tr, 20)
    init_spatial(chorus_mel_tr, 64); init_spatial(pad_tr, 64); init_spatial(fx_tr, 40)
    
    # Non-drum tracks writing
    lt_b = write_performance_to_track(bass_tr, bass_ev, drums_main_tr, drums_chorus_tr)
    lt_hb = write_performance_to_track(harm_bass_tr, harm_bass_ev, drums_main_tr, drums_chorus_tr)
    lt_mm = write_performance_to_track(main_mel_tr, main_mel_ev, drums_main_tr, drums_chorus_tr, articulation='legato')
    lt_cm = write_performance_to_track(chorus_mel_tr, chorus_mel_ev, drums_main_tr, drums_chorus_tr, articulation='legato')
    lt_fx = write_performance_to_track(fx_tr, fx_ev, drums_main_tr, drums_chorus_tr)
    lt_p = write_performance_to_track(pad_tr, pad_ev, drums_main_tr, drums_chorus_tr)
    lt_ctr = write_performance_to_track(counter_mel_tr, counter_mel_ev, drums_main_tr, drums_chorus_tr, articulation='legato')
    
    # === EXPLODED DRUMS SYSTEM ===
    DRUM_NAME_MAP = {
        35: "KickLow", 36: "Kick", 41: "KickAlt",
        37: "SideStick", 38: "Snare", 39: "Clap", 40: "SnareAlt", 43: "FloorTom",
        42: "ClosedHat", 44: "PedalHat", 45: "LowTom", 46: "OpenHat", 47: "MidTom",
        49: "Crash", 51: "Ride", 54: "Tambourine", 70: "Maracas",
        60: "HighBongo", 61: "LowBongo", 62: "MuteConga"
    }

    # Group drum events by (Drum Set, Note)
    # drum1 = Main (intro/verse/outro), drum2 = Chorus/Fill
    drum_tracks_data = {} # (drum_set_name, note) -> list of events

    # Sort events for consistency
    main_ev.sort(key=lambda x: x['time'])
    chorus_ev.sort(key=lambda x: x['time'])
    aux_perc_ev.sort(key=lambda x: x['time'])

    def add_to_exploded(ev_list, prefix):
        for ev in ev_list:
            note = ev['note']
            key = (prefix, note)
            if key not in drum_tracks_data:
                drum_tracks_data[key] = []
            drum_tracks_data[key].append(ev)

    add_to_exploded(main_ev, "drum1")
    add_to_exploded(chorus_ev, "drum2")
    add_to_exploded(aux_perc_ev, "drum_aux")
    print(f"Exploding drums into individual instrument tracks...")
    
    # Remove original empty drum tracks and aux track from the MIDI file to prevent recording confusion
    tracks_to_keep = [tempo_tr, bass_tr, harm_bass_tr, main_mel_tr, counter_mel_tr, 
                      chorus_mel_tr, fx_tr, pad_tr]
    mid.tracks = tracks_to_keep

    # Keep track of the last times for end_of_track markers
    for (prefix, note) in sorted(drum_tracks_data.keys()):
        events = sorted(drum_tracks_data[(prefix, note)], key=lambda x: x['time'])
        instr_name = DRUM_NAME_MAP.get(note, "Instr")
        track_name = f"{prefix}_{instr_name}_n{note}"
        
        dtr = mido.MidiTrack()
        dtr.name = track_name # CRITICAL: Set the .name property for the recorder!
        dtr.append(mido.MetaMessage('track_name', name=track_name, time=0))
        mid.tracks.append(dtr)
        
        # Initialize spatial for drum tracks
        pan_val = random.randint(44, 84)
        init_spatial(dtr, pan=pan_val)
        
        # Write events to the new track
        lt = write_performance_to_track(dtr, events, None, None, force_drum=True)
        dtr.append(mido.MetaMessage('end_of_track', time=max(0, song_length - lt)))

    BASS_STOP = 71 * bar_length
    # Note: drums_main_tr and drums_chorus_tr are kept in mid.tracks but will be empty of notes 
    # if we wanted to replace them entirely. The user asked to label them as drum1 and drum2.
    # The exploded tracks above already use drum1 and drum2 prefixes.
    # To avoid confusion, let's remove the original empty drum tracks from the MIDI file
    # or just let them be. The original code added them to mid.tracks early.
    
    # Correct end_of_track for non-drum tracks
    bass_tr.append(mido.MetaMessage('end_of_track', time=max(0, BASS_STOP - lt_b)))
    harm_bass_tr.append(mido.MetaMessage('end_of_track', time=max(0, BASS_STOP - lt_hb)))
    main_mel_tr.append(mido.MetaMessage('end_of_track', time=max(0, song_length - lt_mm)))
    chorus_mel_tr.append(mido.MetaMessage('end_of_track', time=max(0, song_length - lt_cm)))
    fx_tr.append(mido.MetaMessage('end_of_track', time=max(0, song_length - lt_fx)))
    pad_tr.append(mido.MetaMessage('end_of_track', time=max(0, song_length - lt_p)))
    counter_mel_tr.append(mido.MetaMessage('end_of_track', time=max(0, song_length - lt_ctr)))

    ts = datetime.now().strftime("%m%d%Y_%H%M%S")
    ts_label = time_sig
    inv_label = "_inv" if inverted else ""
    out = os.path.join(PROD_DIR, f"{ts}_{song_bpm}bpm_{key}_{scale_name.replace(' ','_')}_{ts_label}_{main_family}-{chorus_family}{inv_label}.mid")
    mid.save(out)
    print(f"\n✓ Generated: {out}")

    # Return metadata for the audio pipeline
    metadata = {
        'bpm': song_bpm,
        'key': key,
        'scale': scale_name,
        'is_armenian': is_armenian,
        'time_signature': time_sig,
        'main_drum_family': main_family,
        'chorus_drum_family': chorus_family,
        'inverted': inverted,
        'sections': {}
    }
    for s_name, bar_idx in [('intro', 0), ('verse1', 8), ('chorus1', 24), ('fill1', 32),
                             ('verse2', 36), ('chorus2', 52), ('fill2', 60), ('outro', 64)]:
        metadata['sections'][s_name] = bar_idx * beats_per_bar * (60 / song_bpm)

    return out, metadata

if __name__ == "__main__":
    main()

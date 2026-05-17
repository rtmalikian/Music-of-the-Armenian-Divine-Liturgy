import random
from typing import List, Dict, Optional

# --- General MIDI (GM) Drum Map ---
GM_DRUM_MAP = {
    'KICK': 36, 'SNARE': 38, 'RIMSHOT': 37, 'CLOSED_HAT': 42,
    'OPEN_HAT': 46, 'LOW_TOM': 45, 'MID_TOM': 47, 'HIGH_TOM': 50,
    'CRASH_CYMBAL': 49, 'RIDE_CYMBAL': 51,
    'COWBELL': 56, 'CLAVES': 75, 'TAMBOURINE': 54, 'MARACAS': 70,
    'SIDE_STICK': 37, 'CLAP': 39, 'PEDAL_HAT': 44,
}

PATTERN_FAMILIES = [
    'boom_bap', 'lofi', 'trap', 'mpc_soul', 'broken_beat',
    'drill', 'memphis_phonk', 'jazzhop', 'chopped_break',
    'half_time', 'negative_space', 'polyrhythmic'
]

# ============================================================================
# HELPERS
# ============================================================================

def _get_drum_positions(time_sig, tpb):
    """Return (snare_times, kick_times, hat_count) for the time sig."""
    if time_sig == '3-4':
        return [2 * tpb], [0], 6
    elif time_sig == '5-4':
        return [1 * tpb, 3 * tpb], [0, 2 * tpb, 4 * tpb], 20
    elif time_sig == '5-8':
        half = tpb // 2
        return [3 * half], [0], 5
    else:  # 4-4
        return [1 * tpb, 3 * tpb], [0, 2 * tpb], 16


def invert_kick_snare(notes):
    """Swap kick (36) and snare (38) positions."""
    return [
        {'note': 38, 'velocity': n['velocity'], 'time': n['time']} if n['note'] == 36
        else {'note': 36, 'velocity': n['velocity'], 'time': n['time']} if n['note'] == 38
        else n for n in notes
    ]


def apply_micro_techniques(notes, tpb):
    """Randomly inject micro-techniques. Always available, not gated."""
    sixteenth = tpb // 4
    result = list(notes)

    # Ghost kick anticipation (20%)
    if random.random() < 0.20:
        for n in list(result):
            if n['note'] == 36 and n['velocity'] > 80 and n['time'] >= sixteenth:
                result.append({'note': 36, 'velocity': random.randint(30, 45),
                               'time': n['time'] - sixteenth})

    # Snare flam (15%)
    if random.random() < 0.15:
        for n in list(result):
            if n['note'] == 38 and n['velocity'] > 80:
                result.append({'note': 38, 'velocity': int(n['velocity'] * 0.6),
                               'time': n['time'] + 3})

    # Hi-hat choke (15%)
    if random.random() < 0.15:
        for n in list(result):
            if n['note'] == 46:
                result.append({'note': 42, 'velocity': 80, 'time': n['time'] + 3})

    # Velocity crescendo on hats (10%)
    if random.random() < 0.10:
        hats = sorted([n for n in result if n['note'] in (42, 44)], key=lambda x: x['time'])
        for i, h in enumerate(hats):
            h['velocity'] = max(30, min(127, int(40 + (i / max(len(hats), 1)) * 70)))

    # Bar-end ghost roll (12%)
    if random.random() < 0.12:
        bar_len = max(n['time'] for n in result) + sixteenth * 2 if result else tpb * 4
        roll_start = bar_len - sixteenth
        for i in range(3):
            result.append({'note': 38, 'velocity': random.randint(25, 40),
                           'time': roll_start + i * (sixteenth // 2)})

    # Kick push (18%)
    if random.random() < 0.18:
        bar_len = max(n['time'] for n in result) + sixteenth if result else tpb * 4
        push_time = bar_len - tpb // 2
        if push_time > 0:
            result.append({'note': 36, 'velocity': random.randint(70, 85), 'time': push_time})

    # Crash texture (8%)
    if random.random() < 0.08:
        result.append({'note': 49, 'velocity': random.randint(40, 60), 'time': 0})

    # Rimshot counter-rhythm (10%)
    if random.random() < 0.10:
        beats = tpb * 2
        result.append({'note': 37, 'velocity': random.randint(50, 65), 'time': tpb // 2})
        result.append({'note': 37, 'velocity': random.randint(50, 65), 'time': beats + tpb // 2})

    return result


def _finalize(notes, tpb, inverted, time_sig):
    """Apply micro-techniques, then invert if needed. Deduplicate."""
    notes = apply_micro_techniques(notes, tpb)
    if inverted:
        notes = invert_kick_snare(notes)
    # Deduplicate: remove exact duplicate (note, time) pairs
    seen = set()
    deduped = []
    for n in notes:
        key = (n['note'], n['time'])
        if key not in seen:
            seen.add(key)
            deduped.append(n)
    return deduped


# ============================================================================
# 1. BOOM BAP
# ============================================================================

def create_boom_bap_bar(tpb, base_pattern_id=0, variation_level=0,
                        is_chorus=False, inverted=False, time_sig='4-4'):
    notes = []
    sixteenth = tpb // 4
    eighth = tpb // 2
    snare_times, kick_times, hat_count = _get_drum_positions(time_sig, tpb)

    # Hi-hats
    if is_chorus and random.random() < 0.4:
        for i in range(hat_count):
            pos = i * (tpb * 4 // max(hat_count, 1))
            note = GM_DRUM_MAP['OPEN_HAT'] if i in [hat_count // 2 - 1, hat_count - 1] else GM_DRUM_MAP['CLOSED_HAT']
            vel = 100 if i % 2 == 0 else 80
            notes.append({'note': note, 'velocity': vel, 'time': pos})
    elif base_pattern_id == 2:
        for i in range(hat_count):
            pos = i * (tpb * 4 // max(hat_count, 1))
            notes.append({'note': GM_DRUM_MAP['CLOSED_HAT'], 'velocity': 90, 'time': pos})
    else:
        swing_factor = 0.05
        for i in range(hat_count):
            velocity = random.randint(75, 105) if i % 4 == 0 else random.randint(60, 90)
            on_time = i * sixteenth
            if i % 2 != 0:
                on_time += int(sixteenth * swing_factor)
            notes.append({'note': GM_DRUM_MAP['CLOSED_HAT'], 'velocity': velocity, 'time': on_time})

    # Snare
    snare_vel = 127 if is_chorus else 120
    for st in snare_times:
        notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': snare_vel, 'time': st})

    # Kick
    if is_chorus:
        for kt in kick_times:
            notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 125, 'time': kt})
        notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 110, 'time': eighth + sixteenth})
        if random.random() < 0.5:
            notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 105,
                          'time': kick_times[-1] + eighth + sixteenth if kick_times else eighth + sixteenth})
    else:
        if base_pattern_id == 0:
            for kt in kick_times:
                notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 120, 'time': kt})
        elif base_pattern_id == 1:
            if kick_times:
                notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 120, 'time': kick_times[0]})
                notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 100,
                              'time': kick_times[-1] + eighth})
        elif base_pattern_id == 3:
            if kick_times:
                notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 120, 'time': kick_times[0]})
                notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 90, 'time': sixteenth * 3})
                if len(kick_times) > 1:
                    notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 110, 'time': kick_times[1]})
        else:
            for kt in kick_times:
                notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 120, 'time': kt})

    # Variations
    if variation_level > 0:
        if random.random() < 0.4:
            bar_len = tpb * 4
            notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': 45, 'time': sixteenth * 7})
            if bar_len > sixteenth * 15:
                notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': 40, 'time': sixteenth * 15})
        if random.random() < 0.3:
            time = random.choice([3, 7, 11, 15]) * sixteenth
            notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': random.randint(80, 100), 'time': time})

    return _finalize(notes, tpb, inverted, time_sig)


# ============================================================================
# 2. LO-FI
# ============================================================================

def create_lofi_bar(tpb, base_pattern_id=0, variation_level=0,
                    is_chorus=False, inverted=False, time_sig='4-4'):
    notes = []
    sixteenth = tpb // 4
    bar_len = int(tpb * {'4-4': 4, '3-4': 3, '5-4': 5, '5-8': 2.5}.get(time_sig, 4))
    snare_times, kick_times, _ = _get_drum_positions(time_sig, tpb)

    # Sparse asymmetric hats (3-6 hits)
    hat_count = random.randint(3, 6)
    hat_positions = sorted(random.sample(range(0, bar_len, sixteenth), min(hat_count, bar_len // sixteenth)))
    for pos in hat_positions:
        notes.append({'note': GM_DRUM_MAP['CLOSED_HAT'], 'velocity': random.randint(40, 65), 'time': pos})

    # Late snare (shifted 20-40 ticks)
    late_offset = random.randint(20, 40)
    for st in snare_times:
        notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': random.randint(90, 110),
                      'time': st + late_offset})

    # Ghost kicks on offbeats
    for kt in kick_times:
        notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': random.randint(100, 120), 'time': kt})
        if random.random() < 0.4:
            ghost_time = kt + sixteenth * random.choice([2, 3])
            if ghost_time < bar_len:
                notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': random.randint(30, 45),
                              'time': ghost_time})

    # Kick push on "and" of last beat (40%)
    if random.random() < 0.4 and bar_len > sixteenth * 2:
        push_time = bar_len - sixteenth
        notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': random.randint(60, 80), 'time': push_time})

    return _finalize(notes, tpb, inverted, time_sig)


# ============================================================================
# 3. TRAP
# ============================================================================

def create_trap_bar(tpb, base_pattern_id=0, variation_level=0,
                    is_chorus=False, inverted=False, time_sig='4-4'):
    notes = []
    sixteenth = tpb // 4
    bar_len = int(tpb * {'4-4': 4, '3-4': 3, '5-4': 5, '5-8': 2.5}.get(time_sig, 4))
    snare_times, kick_times, _ = _get_drum_positions(time_sig, tpb)

    # 32nd-note hi-hat rolls
    thirty_second = max(sixteenth // 2, 60)
    roll_positions = list(range(0, bar_len, thirty_second))
    for i, pos in enumerate(roll_positions):
        if random.random() < 0.7:  # Not every 32nd, ~70% density
            vel = random.randint(70, 100) if i % 4 == 0 else random.randint(50, 80)
            note = GM_DRUM_MAP['CLOSED_HAT']
            # Occasional open hat
            if i > 0 and i % 8 == 7 and random.random() < 0.3:
                note = GM_DRUM_MAP['OPEN_HAT']
            notes.append({'note': note, 'velocity': vel, 'time': pos})

    # Snare
    snare_vel = 127 if is_chorus else 120
    for st in snare_times:
        notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': snare_vel, 'time': st})
        # Clap layer
        notes.append({'note': GM_DRUM_MAP['CLAP'], 'velocity': snare_vel - 10, 'time': st})

    # Kick flams
    for kt in kick_times:
        notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 125, 'time': kt})
        notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 100, 'time': kt + 2})

    # Open hat bleed on last beat
    if bar_len > sixteenth * 2:
        notes.append({'note': GM_DRUM_MAP['OPEN_HAT'], 'velocity': 90,
                      'time': bar_len - sixteenth})

    return _finalize(notes, tpb, inverted, time_sig)


# ============================================================================
# 4. MPC SOUL
# ============================================================================

def create_mpc_soul_bar(tpb, base_pattern_id=0, variation_level=0,
                        is_chorus=False, inverted=False, time_sig='4-4'):
    notes = []
    sixteenth = tpb // 4
    bar_len = int(tpb * {'4-4': 4, '3-4': 3, '5-4': 5, '5-8': 2.5}.get(time_sig, 4))
    snare_times, kick_times, _ = _get_drum_positions(time_sig, tpb)

    # Ride cymbal as primary timekeeper
    for i in range(bar_len // max(sixteenth, 1)):
        vel = random.randint(60, 90) if i % 2 == 0 else random.randint(45, 70)
        notes.append({'note': GM_DRUM_MAP['RIDE_CYMBAL'], 'velocity': vel, 'time': i * sixteenth})

    # Kick flams (two hits 1-3 ticks apart)
    for kt in kick_times:
        notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 120, 'time': kt})
        notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 85, 'time': kt + 3})

    # Snare with rimshot ghost
    for st in snare_times:
        notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': 115, 'time': st})
        if random.random() < 0.5:
            notes.append({'note': GM_DRUM_MAP['RIMSHOT'], 'velocity': 40, 'time': st - sixteenth})

    # Ghost snares
    if variation_level > 0:
        for i in range(2):
            ghost_pos = random.choice([sixteenth * 3, sixteenth * 7, sixteenth * 11])
            if ghost_pos < bar_len:
                notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': random.randint(30, 45),
                              'time': ghost_pos})

    return _finalize(notes, tpb, inverted, time_sig)


# ============================================================================
# 5. BROKEN BEAT
# ============================================================================

def create_broken_beat_bar(tpb, base_pattern_id=0, variation_level=0,
                           is_chorus=False, inverted=False, time_sig='4-4'):
    notes = []
    sixteenth = tpb // 4
    bar_len = int(tpb * {'4-4': 4, '3-4': 3, '5-4': 5, '5-8': 2.5}.get(time_sig, 4))
    snare_times, kick_times, _ = _get_drum_positions(time_sig, tpb)

    # Displaced kick (20-50 ticks off grid)
    for kt in kick_times:
        displacement = random.choice([-40, -30, -20, 20, 30, 40, 50])
        pos = max(0, kt + displacement)
        notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': random.randint(100, 120), 'time': pos})

    # Snare on offbeat position
    for st in snare_times:
        notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': random.randint(95, 115),
                      'time': st + sixteenth})

    # Sparse asymmetric hats (4-6 hits)
    hat_count = random.randint(4, 6)
    hat_positions = sorted(random.sample(range(0, bar_len, sixteenth), min(hat_count, max(1, bar_len // sixteenth))))
    for pos in hat_positions:
        notes.append({'note': GM_DRUM_MAP['CLOSED_HAT'], 'velocity': random.randint(25, 110), 'time': pos})

    # Velocity extremes
    if variation_level > 0:
        if random.random() < 0.3:
            notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': 25,
                          'time': random.choice([sixteenth * 5, sixteenth * 13])})

    return _finalize(notes, tpb, inverted, time_sig)


# ============================================================================
# 6. DRILL
# ============================================================================

def create_drill_bar(tpb, base_pattern_id=0, variation_level=0,
                     is_chorus=False, inverted=False, time_sig='4-4'):
    notes = []
    sixteenth = tpb // 4
    bar_len = int(tpb * {'4-4': 4, '3-4': 3, '5-4': 5, '5-8': 2.5}.get(time_sig, 4))
    snare_times, kick_times, _ = _get_drum_positions(time_sig, tpb)

    # Primary hi-hat pattern: x--x--x-x--x--x- (positions 0,3,6,8,11,14 of 16)
    # Scaled proportionally to bar length
    hat_positions_44 = [0, 3, 6, 8, 11, 14]  # 16th-note positions in 4/4
    scale = bar_len / (tpb * 4)
    for pos_16 in hat_positions_44:
        pos = int(pos_16 * sixteenth * scale)
        if pos < bar_len:
            # Position 8 gets open hat variant (50% chance)
            if pos_16 == 8 and random.random() < 0.5:
                notes.append({'note': GM_DRUM_MAP['OPEN_HAT'], 'velocity': random.randint(85, 100), 'time': pos})
            else:
                notes.append({'note': GM_DRUM_MAP['CLOSED_HAT'], 'velocity': random.randint(80, 100), 'time': pos})

    # Ghost hi-hats (secondary track — quiet hits between primary pattern)
    ghost_hat_positions = [1, 2, 4, 5, 7, 9, 10, 12, 13, 15]  # positions NOT in primary
    for pos_16 in ghost_hat_positions:
        if random.random() < 0.35:  # ~35% density for ghost hats
            pos = int(pos_16 * sixteenth * scale)
            if pos < bar_len:
                notes.append({'note': GM_DRUM_MAP['CLOSED_HAT'], 'velocity': random.randint(30, 50), 'time': pos})

    # Hi-hat rolls (secondary track — 32nd-note bursts at bar transitions)
    if variation_level > 0 and random.random() < 0.4:
        roll_start = bar_len - sixteenth * 2
        thirty_second = max(sixteenth // 2, 60)
        for i in range(6):
            pos = roll_start + i * thirty_second
            if 0 <= pos < bar_len:
                notes.append({'note': GM_DRUM_MAP['CLOSED_HAT'], 'velocity': random.randint(55, 75), 'time': pos})

    # Snare
    snare_vel = 127 if is_chorus else 120
    for st in snare_times:
        notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': snare_vel, 'time': st})

    # Kick
    for kt in kick_times:
        notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 125, 'time': kt})
        # Kick flam
        notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 95, 'time': kt + 2})

    return _finalize(notes, tpb, inverted, time_sig)


# ============================================================================
# 7. MEMPHIS PHONK
# ============================================================================

def create_memphis_phonk_bar(tpb, base_pattern_id=0, variation_level=0,
                             is_chorus=False, inverted=False, time_sig='4-4'):
    notes = []
    eighth = tpb // 2
    sixteenth = tpb // 4
    bar_len = int(tpb * {'4-4': 4, '3-4': 3, '5-4': 5, '5-8': 2.5}.get(time_sig, 4))
    snare_times, kick_times, _ = _get_drum_positions(time_sig, tpb)

    # Cowbell on 8th notes
    for i in range(bar_len // max(eighth, 1)):
        vel = 100 if i % 2 == 0 else 80
        notes.append({'note': GM_DRUM_MAP['COWBELL'], 'velocity': vel, 'time': i * eighth})

    # Heavy kick on beat 1
    notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 127, 'time': 0})

    # Snare + clap layer
    for st in snare_times:
        notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': 120, 'time': st})
        notes.append({'note': GM_DRUM_MAP['CLAP'], 'velocity': 110, 'time': st})

    # Tom fills (occasional)
    if variation_level > 0 and random.random() < 0.3:
        fill_start = bar_len - sixteenth * 4
        for i in range(4):
            pos = fill_start + i * sixteenth
            tom = random.choice([GM_DRUM_MAP['LOW_TOM'], GM_DRUM_MAP['MID_TOM']])
            notes.append({'note': tom, 'velocity': random.randint(80, 100), 'time': pos})

    return _finalize(notes, tpb, inverted, time_sig)


# ============================================================================
# 8. JAZZ-HOP
# ============================================================================

def create_jazzhop_bar(tpb, base_pattern_id=0, variation_level=0,
                       is_chorus=False, inverted=False, time_sig='4-4'):
    notes = []
    eighth = tpb // 2
    sixteenth = tpb // 4
    bar_len = int(tpb * {'4-4': 4, '3-4': 3, '5-4': 5, '5-8': 2.5}.get(time_sig, 4))
    snare_times, kick_times, _ = _get_drum_positions(time_sig, tpb)

    # Jazz ride pattern (ding-ding-a-ding)
    ride_pattern = [0, eighth, eighth + sixteenth, 2 * eighth]
    for beat_base in range(0, bar_len, tpb):
        for offset in ride_pattern:
            pos = beat_base + offset
            if pos < bar_len:
                vel = random.randint(65, 90) if offset == 0 else random.randint(50, 70)
                notes.append({'note': GM_DRUM_MAP['RIDE_CYMBAL'], 'velocity': vel, 'time': pos})

    # Ghost snares everywhere
    ghost_positions = [st - sixteenth for st in snare_times if st - sixteenth >= 0]
    ghost_positions += [st + sixteenth for st in snare_times if st + sixteenth < bar_len]
    for pos in ghost_positions:
        notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': random.randint(30, 45), 'time': pos})

    # Main snare
    for st in snare_times:
        notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': 100, 'time': st})

    # Kick (sparse)
    if kick_times:
        notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 100, 'time': kick_times[0]})

    # Brush swirl (32nd-note snare roll at start of every 4th bar concept)
    if variation_level > 0 and random.random() < 0.25:
        for i in range(6):
            pos = i * (sixteenth // 2)
            if pos < bar_len:
                notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': random.randint(20, 35),
                              'time': pos})

    return _finalize(notes, tpb, inverted, time_sig)


# ============================================================================
# 9. CHOPPED BREAK
# ============================================================================

def create_chopped_break_bar(tpb, base_pattern_id=0, variation_level=0,
                             is_chorus=False, inverted=False, time_sig='4-4'):
    notes = []
    eighth = tpb // 2
    sixteenth = tpb // 4
    bar_len = int(tpb * {'4-4': 4, '3-4': 3, '5-4': 5, '5-8': 2.5}.get(time_sig, 4))
    snare_times, kick_times, _ = _get_drum_positions(time_sig, tpb)

    # Break templates (rhythmic patterns from classic breaks)
    break_templates = [
        # Think Break style
        [(0, 36, 120), (sixteenth * 2, 38, 110), (sixteenth * 4, 36, 100),
         (sixteenth * 6, 38, 115), (eighth * 3, 36, 105)],
        # Apache style
        [(0, 36, 120), (eighth, 38, 115), (eighth * 2, 36, 100),
         (sixteenth * 6, 38, 110), (eighth * 3 + sixteenth, 36, 105)],
        # Funky Drummer style
        [(0, 36, 120), (eighth, 38, 110), (eighth + sixteenth, 38, 90),
         (eighth * 2, 36, 105), (eighth * 3, 38, 115)],
    ]
    template = random.choice(break_templates)

    # Apply template with scaling
    scale = bar_len / (tpb * 4)
    for time_offset, note_num, vel in template:
        pos = int(time_offset * scale)
        if pos < bar_len:
            notes.append({'note': note_num, 'velocity': vel, 'time': pos})

    # Heavy swing hats
    swing_factor = 0.15
    for i in range(bar_len // max(sixteenth, 1)):
        on_time = i * sixteenth
        if i % 2 != 0:
            on_time += int(sixteenth * swing_factor)
        if on_time < bar_len:
            notes.append({'note': GM_DRUM_MAP['CLOSED_HAT'], 'velocity': random.randint(55, 85),
                          'time': on_time})

    # Vinyl bleed ghosts
    if random.random() < 0.3:
        for _ in range(random.randint(1, 3)):
            pos = random.randint(0, max(0, bar_len - 1))
            notes.append({'note': random.choice([38, 37, 42]),
                          'velocity': random.randint(20, 30), 'time': pos})

    return _finalize(notes, tpb, inverted, time_sig)


# ============================================================================
# 10. HALF-TIME
# ============================================================================

def create_half_time_bar(tpb, base_pattern_id=0, variation_level=0,
                         is_chorus=False, inverted=False, time_sig='4-4'):
    notes = []
    eighth = tpb // 2
    sixteenth = tpb // 4
    bar_len = int(tpb * {'4-4': 4, '3-4': 3, '5-4': 5, '5-8': 2.5}.get(time_sig, 4))
    snare_times, kick_times, hat_count = _get_drum_positions(time_sig, tpb)

    # Snare on beat 3 (half-time feel)
    half_bar = bar_len // 2
    notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': 120, 'time': half_bar})

    # Kick fills the space
    notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 120, 'time': 0})
    notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 100, 'time': eighth + sixteenth})
    if half_bar + eighth < bar_len:
        notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 110, 'time': half_bar + eighth})

    # Rimshot on beats 2 and 4 as subtle backbeat
    for st in snare_times:
        notes.append({'note': GM_DRUM_MAP['RIMSHOT'], 'velocity': random.randint(50, 60), 'time': st})

    # Hi-hats at 8th-note pace with ghost 16ths
    for i in range(bar_len // max(eighth, 1)):
        pos = i * eighth
        notes.append({'note': GM_DRUM_MAP['CLOSED_HAT'], 'velocity': random.randint(70, 90), 'time': pos})
        # Ghost 16th between
        ghost_pos = pos + sixteenth
        if ghost_pos < bar_len:
            notes.append({'note': GM_DRUM_MAP['CLOSED_HAT'], 'velocity': random.randint(30, 40),
                          'time': ghost_pos})

    # Open hat on last beat
    if bar_len > eighth:
        notes.append({'note': GM_DRUM_MAP['OPEN_HAT'], 'velocity': 85,
                      'time': bar_len - eighth})

    return _finalize(notes, tpb, inverted, time_sig)


# ============================================================================
# 11. NEGATIVE SPACE
# ============================================================================

def create_negative_space_bar(tpb, base_pattern_id=0, variation_level=0,
                              is_chorus=False, inverted=False, time_sig='4-4'):
    notes = []
    sixteenth = tpb // 4
    bar_len = int(tpb * {'4-4': 4, '3-4': 3, '5-4': 5, '5-8': 2.5}.get(time_sig, 4))

    # 3-4 hits per bar total, on off-grid positions
    hit_count = random.randint(3, 4)
    # Use "e" and "a" positions (16th offbeats)
    offbeat_positions = [sixteenth + i * sixteenth * 2 for i in range(bar_len // (sixteenth * 2))]
    offbeat_positions += [sixteenth * 3 + i * sixteenth * 4 for i in range(bar_len // (sixteenth * 4))]
    offbeat_positions = sorted(set(p for p in offbeat_positions if 0 < p < bar_len))

    if len(offbeat_positions) >= hit_count:
        chosen = random.sample(offbeat_positions, hit_count)
    else:
        chosen = offbeat_positions

    for pos in sorted(chosen):
        note_type = random.choice([GM_DRUM_MAP['SNARE'], GM_DRUM_MAP['KICK'],
                                    GM_DRUM_MAP['RIMSHOT'], GM_DRUM_MAP['CLOSED_HAT']])
        notes.append({'note': note_type, 'velocity': random.randint(35, 55), 'time': pos})

    return _finalize(notes, tpb, inverted, time_sig)


# ============================================================================
# 12. POLYRHYTHMIC
# ============================================================================

def create_polyrhythmic_bar(tpb, base_pattern_id=0, variation_level=0,
                            is_chorus=False, inverted=False, time_sig='4-4'):
    notes = []
    eighth = tpb // 2
    sixteenth = tpb // 4
    bar_len = int(tpb * {'4-4': 4, '3-4': 3, '5-4': 5, '5-8': 2.5}.get(time_sig, 4))
    snare_times, kick_times, _ = _get_drum_positions(time_sig, tpb)

    # 3-over-4 (or 3-over-5 for 5/4) hi-hats
    if time_sig == '5-4':
        triplet_base = bar_len // 5
    else:
        triplet_base = bar_len // 4

    triplet_len = max(triplet_base // 3, 80)
    for i in range(bar_len // max(triplet_len, 1)):
        pos = i * triplet_len
        if pos < bar_len:
            vel = random.randint(65, 90) if i % 3 == 0 else random.randint(50, 70)
            notes.append({'note': GM_DRUM_MAP['CLOSED_HAT'], 'velocity': vel, 'time': pos})

    # Kick in dotted quarters
    dotted_quarter = int(tpb * 1.5)
    for pos in range(0, bar_len, dotted_quarter):
        notes.append({'note': GM_DRUM_MAP['KICK'], 'velocity': 110, 'time': pos})

    # Displaced snare layer
    notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': 40, 'time': snare_times[0] if snare_times else eighth})
    notes.append({'note': GM_DRUM_MAP['SNARE'], 'velocity': 100,
                  'time': (snare_times[-1] if snare_times else 3 * eighth) + sixteenth})

    return _finalize(notes, tpb, inverted, time_sig)


# ============================================================================
# PATTERN FAMILY MAP & GET_PATTERN_FUNCS
# ============================================================================

PATTERN_FAMILY_MAP = {
    'boom_bap': create_boom_bap_bar,
    'lofi': create_lofi_bar,
    'trap': create_trap_bar,
    'mpc_soul': create_mpc_soul_bar,
    'broken_beat': create_broken_beat_bar,
    'drill': create_drill_bar,
    'memphis_phonk': create_memphis_phonk_bar,
    'jazzhop': create_jazzhop_bar,
    'chopped_break': create_chopped_break_bar,
    'half_time': create_half_time_bar,
    'negative_space': create_negative_space_bar,
    'polyrhythmic': create_polyrhythmic_bar,
}


def get_pattern_funcs(args=None):
    """Select 2 random pattern families: one for main sections, one for chorus/fill."""
    main_family, chorus_family = random.sample(PATTERN_FAMILIES, 2)
    main_func = PATTERN_FAMILY_MAP[main_family]
    chorus_func = PATTERN_FAMILY_MAP[chorus_family]

    fA = lambda tpb, pid, is_ch, inverted=False, time_sig='4-4': \
        main_func(tpb, pid, variation_level=0, is_chorus=is_ch, inverted=inverted, time_sig=time_sig)
    fB = lambda tpb, pid, is_ch, inverted=False, time_sig='4-4': \
        main_func(tpb, pid, variation_level=1, is_chorus=is_ch, inverted=inverted, time_sig=time_sig)
    fC = lambda tpb, pid, is_ch, inverted=False, time_sig='4-4': \
        chorus_func(tpb, pid, variation_level=1, is_chorus=True, inverted=inverted, time_sig=time_sig)
    fD = lambda tpb, pid, is_ch, inverted=False, time_sig='4-4': \
        chorus_func(tpb, pid, variation_level=2, is_chorus=is_ch, inverted=inverted, time_sig=time_sig)

    return fA, fB, fC, fD, main_family, chorus_family

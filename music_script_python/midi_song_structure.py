import random
from typing import List, Dict, Optional, Union

ChordToken = Union[int, str]

# ============================================================================
# CHORD PROGRESSIONS
# ============================================================================

VERSE_PROGRESSIONS = {
    "I-vi-IV-V": [0, 9, 5, 7], "I-V-vi-IV": [0, 7, 9, 5], "vi-IV-I-V": [9, 5, 0, 7],
    "I-IV-V-IV": [0, 5, 7, 5], "I-vi-ii-V": [0, 9, 2, 7], "IV-I-V-vi": [5, 0, 7, 9],
    "I-bVII-IV-I": [0, 10, 5, 0], "I-V-bVII-IV": [0, 7, 10, 5],
    "i-bVII-bVI-bVII": [0, 10, 8, 10], "i-bVI-bIII-bVII": [0, 8, 3, 10],
    "I-bIII-IV-I": [0, 3, 5, 0], "vi-IV-ii-V": [9, 5, 2, 7],
    "I-iii-IV-V": [0, 4, 5, 7], "vi-V-IV-I": [9, 7, 5, 0],
    "i-bVII-IV-bVI": [0, 10, 5, 8], "I-bVI-IV-V": [0, 8, 5, 7],
    "I-ii-IV-V": [0, 2, 5, 7], "vi-ii-V-I": [9, 2, 7, 0],
    "I-IV-ii-V": [0, 5, 2, 7], "I-V-ii-IV": [0, 7, 2, 5],
    "Iadd9-vi7-IVmaj7-Vsus4": ["Iadd9", "vi7", "IVmaj7", "Vsus4"],
    "iadd9-bVIIadd9-bVImaj7-V7": ["iadd9", "bVIIadd9", "bVImaj7", "V7"],
    "Imaj7-iii7-IVadd9-V7": ["Imaj7", "iii7", "IVadd9", "V7"],
    "vi9-IVmaj7-ii7-V7": ["vi9", "IVmaj7", "ii7", "V7"],
}

CHORUS_PROGRESSIONS = {
    "I-V-vi-IV": [0, 7, 9, 5], "IV-V-iii-vi": [5, 7, 4, 9], "vi-V-IV-V": [9, 7, 5, 7],
    "I-IV-bVII-IV": [0, 5, 10, 5], "iii-vi-IV-V": [4, 9, 5, 7], "I-bVI-bVII-I": [0, 8, 10, 0],
    "IV-V-I-I": [5, 7, 0, 0], "I-V-IV-I": [0, 7, 5, 0],
    "I-IV-vi-V": [0, 5, 9, 7], "vi-IV-I-V": [9, 5, 0, 7],
    "bVI-bVII-I-I": [8, 10, 0, 0], "I-bVII-bVI-bVII": [0, 10, 8, 10],
    "I-bIII-bVII-IV": [0, 3, 10, 5], "bIII-bVII-IV-I": [3, 10, 5, 0],
    "I-V-bVII-IV": [0, 7, 10, 5], "I-ii-V-I": [0, 2, 7, 0],
    "IV-I-V-I": [5, 0, 7, 0], "bVII-IV-I-V": [10, 5, 0, 7],
    "I-bVII-IV-bVI": [0, 10, 5, 8], "vi-bVII-IV-I": [9, 10, 5, 0],
    "Imaj7-Vsus4-vi9-IVadd9": ["Imaj7", "Vsus4", "vi9", "IVadd9"],
    "IVmaj7-V7-Iadd9-I6": ["IVmaj7", "V7", "Iadd9", "I6"],
    "bVImaj7-bVII7-Iadd9-I": ["bVImaj7", "bVII7", "Iadd9", "I"],
    "Iadd9-bIIImaj7-bVII7-IVadd9": ["Iadd9", "bIIImaj7", "bVII7", "IVadd9"],
}

INTRO_OUTRO_PROGRESSIONS = {
    "I-IV-I-V": [0, 5, 0, 7], "vi-IV-I-V": [9, 5, 0, 7], "I-add9-IV-I": ["Iadd9", "IV", "I"],
    "I-V-I": [0, 7, 0], "I-V-vi-IV": [0, 7, 9, 5], "I-bVII-IV-I": [0, 10, 5, 0],
    "I-bVI-bVII-I": [0, 8, 10, 0], "vi-V-IV-I": [9, 7, 5, 0],
    "i-bVII-bVI-V": [0, 10, 8, 7], "I-IV-bVII-I": [0, 5, 10, 0],
    "I-ii-V-I": [0, 2, 7, 0], "bVII-IV-I": [10, 5, 0],
    "Iadd9-IVmaj7-I6-Vsus4": ["Iadd9", "IVmaj7", "I6", "Vsus4"],
    "iadd9-bVIIadd9-bVImaj7-V7": ["iadd9", "bVIIadd9", "bVImaj7", "V7"],
}

FILL_PROGRESSIONS = {
    "V/vi-vi": [7, 9], "V/V-V": [2, 7], "IV-V": [5, 7], "ii-V": [2, 7],
    "bVII-V": [10, 7], "bVI-bVII": [8, 10], "ii-V-I-V": [2, 7, 0, 7],
    "iii-vi-ii-V": [4, 9, 2, 7], "bII-V": [1, 7], "V-bVI-V": [7, 8, 7],
    "I-bVII-V": [0, 10, 7], "V-IV": [7, 5], "bVII-IV-V": [10, 5, 7],
    "vi-bVI-V": [9, 8, 7], "ii-bII-I": [2, 1, 0], "IV-bVII-I": [5, 10, 0],
    "V7/vi-vi7": ["V7/vi", "vi7"], "V7/V-V7": ["V7/V", "V7"],
    "ii7-V7-Iadd9": ["ii7", "V7", "Iadd9"], "bII7-V7": ["bII7", "V7"],
}

PASSING_CHORDS = {
    ('intro', 'verse1'): [0, 7, 10],
    ('verse1', 'chorus1'): [7, 10, 8, 2], ('verse2', 'chorus2'): [7, 10, 8, 2],
    ('chorus1', 'fill1'): [0, 7, 2, 9], ('chorus2', 'fill2'): [0, 7, 2, 9],
    ('fill1', 'verse2'): [7, 10, 4], ('fill2', 'outro'): [0, 7, 10, 8],
    ('outro', None): [0],
}

LOFI_PROGRESSIONS = {**VERSE_PROGRESSIONS, **CHORUS_PROGRESSIONS}

def get_section_progression(section_type: str) -> Dict[str, List[ChordToken]]:
    if section_type.startswith('verse'): return VERSE_PROGRESSIONS
    elif section_type.startswith('chorus'): return CHORUS_PROGRESSIONS
    elif section_type in ['intro', 'outro']: return INTRO_OUTRO_PROGRESSIONS
    elif section_type.startswith('fill'): return FILL_PROGRESSIONS
    return VERSE_PROGRESSIONS

def _dominant_of(target_degree: int) -> int:
    return (target_degree + 7) % 12

def _upper_modal_neighbor(target_degree: int) -> int:
    return (target_degree + 10) % 12

def _lower_chromatic_neighbor(target_degree: int) -> int:
    return (target_degree - 1) % 12

def _target_symbol(target_degree: int) -> str:
    return {0: 'I', 1: 'bII', 2: 'ii', 3: 'bIII', 4: 'iii', 5: 'IV',
            6: 'bV', 7: 'V', 8: 'bVI', 9: 'vi', 10: 'bVII', 11: 'vii'}.get(target_degree % 12, 'I')

def get_passing_chord(from_section: str, to_section: str, root: int, scale: List[int],
                      target_degree: Optional[int] = None) -> ChordToken:
    if to_section is None:
        return random.choice(PASSING_CHORDS.get((from_section, to_section), [0]))

    target = 0 if target_degree is None else target_degree % 12
    context_pool = list(PASSING_CHORDS.get((from_section, to_section), []))

    if to_section.startswith('chorus') and not from_section.startswith('chorus'):
        context_pool += [_dominant_of(target), _upper_modal_neighbor(target), 8]
    elif from_section.startswith('chorus') and to_section.startswith('fill'):
        context_pool += [0, 2, _dominant_of(target), 9]
    elif from_section.startswith('fill') and to_section.startswith('verse'):
        context_pool += [_dominant_of(target), _upper_modal_neighbor(target), 4]
    elif from_section.startswith('fill') and to_section == 'outro':
        context_pool += [0, 7, 10, 8, _dominant_of(target)]
    elif from_section == 'intro' and to_section.startswith('verse'):
        context_pool += [0, _dominant_of(target), _upper_modal_neighbor(target)]

    if target not in (0, 7):
        context_pool += [f"V7/{_target_symbol(target)}", _lower_chromatic_neighbor(target)]

    if not context_pool:
        if to_section.startswith('chorus') and not from_section.startswith('chorus'): return _dominant_of(target)
        if from_section.startswith('chorus') and not to_section.startswith('chorus'): return random.choice([0, _dominant_of(target)])
        if to_section.startswith('verse') and not from_section.startswith('verse'): return random.choice([_dominant_of(target), _upper_modal_neighbor(target)])
        return 0

    return random.choice(context_pool)

def transform_loop(loop: Dict, mode: str) -> Dict:
    new_loop = {
        'notes': list(loop['notes']),
        'rhythm': list(loop['rhythm']),
        'bars': [
            {
                'notes': list(bar.get('notes', [])),
                'rhythm': list(bar.get('rhythm', [])),
                'role': bar.get('role'),
                'persona': bar.get('persona'),
                'harmony_aware': bar.get('harmony_aware', loop.get('harmony_aware', False)),
            }
            for bar in loop.get('bars', [])
        ],
        'is_chorus': loop.get('is_chorus', False),
        'motif': loop.get('motif'),
        'persona': loop.get('persona'),
        'harmony_aware': loop.get('harmony_aware', False),
    }
    if mode == 'retrograde':
        new_loop['notes'].reverse()
        new_loop['rhythm'].reverse()
        for bar in new_loop['bars']:
            bar['notes'].reverse()
            bar['rhythm'].reverse()
    elif mode == 'inversion':
        center = next((n for n in loop['notes'] if n is not None), None)
        if center is not None:
            new_loop['notes'] = [None if n is None else center - (n - center) for n in loop['notes']]
            for bar in new_loop['bars']:
                bar['notes'] = [None if n is None else center - (n - center) for n in bar['notes']]
    elif mode == 'augmentation':
        new_loop['rhythm'] = [r * 2 for r in loop['rhythm']]
        for bar in new_loop['bars']:
            bar['rhythm'] = [r * 2 for r in bar['rhythm']]
    if new_loop['bars']:
        new_loop['notes'] = [n for bar in new_loop['bars'] for n in bar['notes']]
        new_loop['rhythm'] = [r for bar in new_loop['bars'] for r in bar['rhythm']]
    return new_loop

def get_bar_type(bar: int) -> str:
    if bar < 8: return 'intro'
    elif bar < 24: return 'verse1'
    elif bar < 32: return 'chorus1'
    elif bar < 36: return 'fill1'
    elif bar < 52: return 'verse2'
    elif bar < 60: return 'chorus2'
    elif bar < 64: return 'fill2'
    return 'outro'

def get_phrase_position(bar: int) -> int:
    bt = get_bar_type(bar)
    offsets = {'intro': 0, 'verse1': 8, 'chorus1': 24, 'fill1': 32, 'verse2': 36, 'chorus2': 52, 'fill2': 60, 'outro': 64}
    return (bar - offsets.get(bt, 0)) % 8

def get_abac_position(bar: int, bar_type: str) -> str:
    if bar_type.startswith('verse'): phrase_bar = (bar - 8) % 4 if bar_type == 'verse1' else (bar - 36) % 4
    elif bar_type.startswith('chorus'): phrase_bar = (bar - 24) % 4 if bar_type == 'chorus1' else (bar - 52) % 4
    elif bar_type == 'intro': phrase_bar = bar % 4
    elif bar_type == 'outro': phrase_bar = (bar - 64) % 4
    else: phrase_bar = bar % 4
    return {0: 'A', 1: 'B', 2: 'A', 3: 'C'}.get(phrase_bar, 'A')

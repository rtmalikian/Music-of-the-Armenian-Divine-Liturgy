import random
from typing import Dict, List, Optional, Sequence, Tuple

from midi_models import BarHarmony
from midi_theory import clamp_to_register, nearest_pitch_for_pc


MELODY_PERSONAS: Dict[str, Dict] = {
    "sparse_sleepy": {
        "rest_chance": 0.28,
        "nct_chance": 0.22,
        "repeat_chance": 0.26,
        "pickup_chance": 0.18,
        "contours": ["descending", "wave", "arch"],
    },
    "swung_hook": {
        "rest_chance": 0.16,
        "nct_chance": 0.28,
        "repeat_chance": 0.34,
        "pickup_chance": 0.32,
        "contours": ["wave", "arch", "ascending"],
    },
    "syncopated_pocket": {
        "rest_chance": 0.22,
        "nct_chance": 0.30,
        "repeat_chance": 0.22,
        "pickup_chance": 0.38,
        "contours": ["wave", "ascending", "descending"],
    },
    "narrow_hypnotic": {
        "rest_chance": 0.20,
        "nct_chance": 0.18,
        "repeat_chance": 0.44,
        "pickup_chance": 0.20,
        "contours": ["wave", "arch"],
    },
    "chorus_lift": {
        "rest_chance": 0.10,
        "nct_chance": 0.24,
        "repeat_chance": 0.20,
        "pickup_chance": 0.30,
        "contours": ["ascending", "arch", "wave"],
    },
}

ABAC_ROLES = {
    0: "statement",
    1: "response",
    2: "restatement",
    3: "turnaround",
}


def choose_melody_persona(is_chorus: bool) -> Dict:
    pool = ["chorus_lift", "swung_hook", "syncopated_pocket"] if is_chorus else [
        "sparse_sleepy",
        "swung_hook",
        "syncopated_pocket",
        "narrow_hypnotic",
    ]
    name = random.choice(pool)
    persona = dict(MELODY_PERSONAS[name])
    persona["name"] = name
    return persona


def phrase_role(bar_in_loop: int) -> str:
    return ABAC_ROLES.get(bar_in_loop % 4, "statement")


def motif_fingerprint(motif: Sequence[int], rhythm: Sequence[int]) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    intervals = tuple((motif[i] - motif[i - 1]) for i in range(1, len(motif)))
    rhythm_shape = tuple(0 if r <= 240 else 1 if r <= 480 else 2 for r in rhythm[:8])
    return intervals, rhythm_shape


def diversify_motif(motif: List[int], rhythm: List[int], is_chorus: bool) -> List[int]:
    stock_fingerprints = {
        ((1, 1, -1, -1, -1, 2, -1), (1, 1, 1, 1)),
        ((2, 2, 1, 2, -2, -1, -2, -2), (1, 0, 0, 1)),
    }
    if motif_fingerprint(motif, rhythm)[0] not in {fp[0] for fp in stock_fingerprints}:
        return motif
    out = motif[:]
    if len(out) > 3:
        out[random.randint(1, len(out) - 2)] += random.choice([-3, -2, 2, 3])
    if is_chorus and len(out) > 2:
        out[-1] += random.choice([2, 4, 5])
    return out


def theory_rhythm(is_chorus: bool, bar_in_loop: int, bar_length: int, persona: Dict) -> Tuple[List[int], List[bool]]:
    q, e, dq, h = 480, 240, 720, 960
    role = phrase_role(bar_in_loop)
    if is_chorus:
        templates = {
            "statement": [[q, e, e, q, q], [e, e, q, e, e, q, q], [dq, e, q, q]],
            "response": [[e, e, q, dq, e, e], [q, q, e, e, q], [q, e, e, h]],
            "restatement": [[q, e, e, q, q], [e, e, q, q, e, e], [dq, e, q, q]],
            "turnaround": [[e, e, q, q, h], [q, e, e, dq, e], [q, q, h]],
        }
    else:
        templates = {
            "statement": [[q, q, q, q], [q, e, e, q, q], [dq, e, q, q]],
            "response": [[e, e, q, q, h], [q, q, e, e, q], [q, h, q]],
            "restatement": [[q, q, q, q], [q, e, e, q, q], [dq, e, q, q]],
            "turnaround": [[q, e, e, h], [e, e, q, dq, e], [h, q, q]],
        }
    rhythm = random.choice(templates[role]).copy()
    if random.random() < persona.get("pickup_chance", 0.2):
        rhythm = [e] + rhythm
    rhythm = _scale_rhythm(rhythm, bar_length)
    rests = []
    tick = 0
    for idx, dur in enumerate(rhythm):
        strong = tick == 0 or tick % 480 == 0 or idx == len(rhythm) - 1
        can_rest = not strong and role != "turnaround"
        rests.append(can_rest and random.random() < persona.get("rest_chance", 0.15))
        tick += dur
    return rhythm, rests


def apply_melodic_devices(notes: List[int], rhythm: List[int], harmony: BarHarmony,
                          next_harmony: Optional[BarHarmony], scale: List[int],
                          voice: str, persona: Dict, role: str,
                          rests: Optional[List[bool]] = None) -> List[Optional[int]]:
    out: List[Optional[int]] = [clamp_to_register(n, voice) for n in notes]
    rests = rests or [False] * len(out)
    chord_pcs = {n % 12 for n in harmony.chord_tones}
    guide_pool = harmony.guide_tones or harmony.chord_tones
    tick = 0
    for i, note in enumerate(list(out)):
        if note is None:
            tick += rhythm[i]
            continue
        strong = tick == 0 or tick % 480 == 0 or i == len(out) - 1
        cadence_slot = role == "turnaround" and i >= max(0, len(out) - 2)
        if rests[i] and not cadence_slot:
            out[i] = None
            tick += rhythm[i]
            continue
        if i > 0 and out[i - 1] is not None and random.random() < persona.get("repeat_chance", 0.2):
            out[i] = out[i - 1]
        elif strong or cadence_slot:
            pool = guide_pool if cadence_slot and guide_pool else harmony.chord_tones
            out[i] = _nearest_from_pool(note, pool, voice)
        elif random.random() < persona.get("nct_chance", 0.22):
            out[i] = _controlled_non_chord_tone(out, i, rhythm, harmony, next_harmony, scale, voice)
        if out[i] is not None and strong and out[i] % 12 not in chord_pcs:
            out[i] = _nearest_from_pool(out[i], harmony.chord_tones, voice)
        tick += rhythm[i]
    if role == "turnaround" and out:
        cadence_pool = (next_harmony.guide_tones or next_harmony.chord_tones) if next_harmony else harmony.chord_tones
        last_idx = next((idx for idx in range(len(out) - 1, -1, -1) if out[idx] is not None), None)
        if last_idx is not None:
            out[last_idx] = _nearest_from_pool(out[last_idx], cadence_pool, voice)
    return out


def bass_approach_note(current_note: int, next_harmony: Optional[BarHarmony],
                       scale: List[int]) -> Optional[int]:
    if not next_harmony:
        return None
    target_pc = next_harmony.root % 12
    candidates = []
    scale_pcs = {n % 12 for n in scale}
    for semitone in (-2, -1, 1, 2, 5, 7):
        pc = (target_pc + semitone) % 12
        if abs(semitone) == 1 or pc in scale_pcs:
            candidates.append(nearest_pitch_for_pc(current_note, pc, 45, 64))
    if not candidates:
        return None
    return min(candidates, key=lambda n: abs(n - current_note))


def should_use_pedal(section: str, bar: int) -> bool:
    if section.startswith("fill"):
        return False
    return bar % 8 in (0, 1, 4, 5) and random.random() < 0.18


def voice_lead_pad_chord(chord: List[int], previous: Optional[List[int]],
                         voice: str = "pad", max_notes: int = 5) -> List[int]:
    pcs = []
    for note in chord:
        if note % 12 not in pcs:
            pcs.append(note % 12)
    if previous:
        previous_pcs = {n % 12: n for n in previous}
        ordered = [pc for pc in pcs if pc in previous_pcs] + [pc for pc in pcs if pc not in previous_pcs]
    else:
        ordered = pcs
    voiced = []
    for idx, pc in enumerate(ordered[:max_notes]):
        reference = previous[min(idx, len(previous) - 1)] if previous else 82 + idx * 2
        candidate = nearest_pitch_for_pc(reference, pc, 72, 96)
        if candidate not in voiced:
            voiced.append(candidate)
    return sorted(voiced)


def resolve_suspension_voicing(suspended: List[int], resolved_chord: List[int],
                               voice: str = "pad") -> List[int]:
    return voice_lead_pad_chord(resolved_chord, suspended, voice=voice, max_notes=len(suspended) or 5)


def _scale_rhythm(rhythm: List[int], bar_length: int) -> List[int]:
    total = sum(rhythm)
    if total <= 0:
        return rhythm
    scaled = [max(120, int(r * bar_length / total)) for r in rhythm]
    diff = bar_length - sum(scaled)
    if scaled:
        scaled[-1] += diff
    return scaled


def _nearest_from_pool(note: int, pool: Sequence[int], voice: str) -> int:
    if not pool:
        return clamp_to_register(note, voice)
    candidates = [nearest_pitch_for_pc(note, p % 12, 0, 127) for p in pool]
    candidates = [clamp_to_register(c, voice) for c in candidates]
    return min(candidates, key=lambda n: abs(n - note))


def _controlled_non_chord_tone(notes: List[Optional[int]], idx: int, rhythm: List[int],
                               harmony: BarHarmony, next_harmony: Optional[BarHarmony],
                               scale: List[int], voice: str) -> int:
    current = notes[idx] if notes[idx] is not None else _nearest_from_pool(harmony.root + 36, harmony.chord_tones, voice)
    prev_note = next((notes[j] for j in range(idx - 1, -1, -1) if notes[j] is not None), None)
    next_note = next((notes[j] for j in range(idx + 1, len(notes)) if notes[j] is not None), None)
    scale_pcs = sorted({n % 12 for n in scale})
    if prev_note is not None and next_note is not None:
        gap = next_note - prev_note
        if 3 <= abs(gap) <= 5:
            direction = 1 if gap > 0 else -1
            return _step_in_scale(prev_note, direction, scale_pcs, voice)
        if random.random() < 0.45:
            direction = random.choice([-1, 1])
            neighbor = _step_in_scale(prev_note, direction, scale_pcs, voice)
            if idx + 1 < len(notes):
                notes[idx + 1] = _nearest_from_pool(prev_note, harmony.chord_tones, voice)
            return neighbor
    if next_harmony and random.random() < 0.35:
        return _nearest_from_pool(current, next_harmony.chord_tones, voice)
    return _step_in_scale(current, random.choice([-1, 1]), scale_pcs, voice)


def _step_in_scale(note: int, direction: int, scale_pcs: Sequence[int], voice: str) -> int:
    candidates = []
    for pc in scale_pcs:
        p = nearest_pitch_for_pc(note, pc, 0, 127)
        if direction > 0 and p > note:
            candidates.append(p)
        elif direction < 0 and p < note:
            candidates.append(p)
    if not candidates:
        return clamp_to_register(note + (2 * direction), voice)
    return clamp_to_register(min(candidates, key=lambda n: abs(n - note)), voice)

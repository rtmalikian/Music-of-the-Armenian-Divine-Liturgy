import os

# ============================================================================
# CONFIGURATION
# ============================================================================

TICKS_PER_BEAT = 480  # MIDI standard
TOTAL_BARS = 72

TIME_SIGNATURES = {
    '4-4': {'numerator': 4, 'denominator': 4, 'beats_per_bar': 4},
    '3-4': {'numerator': 3, 'denominator': 4, 'beats_per_bar': 3},
    '5-4': {'numerator': 5, 'denominator': 4, 'beats_per_bar': 5},
    '5-8': {'numerator': 5, 'denominator': 8, 'beats_per_bar': 2.5},
}

def get_bar_length_ticks(ts_key):
    return int(TICKS_PER_BEAT * TIME_SIGNATURES[ts_key]['beats_per_bar'])

def get_song_length_ticks(ts_key):
    return get_bar_length_ticks(ts_key) * TOTAL_BARS

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROD_DIR = os.path.join(SCRIPT_DIR, "output")
os.makedirs(PROD_DIR, exist_ok=True)

SCALES_FILE = os.path.join(PROD_DIR, "scales.txt")

# Priority 3: MPC Swing values
SWING_VALUES = {
    'none': 0.50,      # No swing (straight)
    'light': 0.54,     # Light swing
    'medium': 0.58,    # Classic MPC swing (J Dilla, Premier)
    'heavy': 0.62,     # Heavy swing (Dilla-style "drunk" feel)
}

# Priority 3: Humanization settings
HUMANIZATION = {
    'timing_lofi': (-30, 40),    # Asymmetric (J Dilla: some early, some late)
    'timing_jazz': (-20, 20),     # More balanced
    'timing_subtle': (-10, 10),   # Subtle
    'velocity_lofi': (-25, 15),   # More quiet than loud
    'velocity_jazz': (-15, 15),   # Balanced
    'velocity_subtle': (-8, 8),   # Subtle
}

# Priority 1: Stepwise motion weighting
INTERVAL_WEIGHTS = {
    'stepwise': 0.60,
    'small_leap': 0.30,
    'large_leap': 0.10,
}

# Register ranges for different instruments
REGISTER_RANGES = {
    'bass': (45, 64), 'harmonic_bass': (52, 72), 'main_melody': (48, 84),
    'counter_melody': (54, 78), 'chorus_melody': (52, 86), 'pad': (72, 96),
}

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

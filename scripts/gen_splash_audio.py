"""Synthesize a 3-second cinematic splash sound: radar ping → scanner sweep →
cannon boom → galloping percussion. Saved as WAV in src/assets.

Pure numpy/scipy — no API. Runs locally.
"""
import numpy as np
from scipy.io import wavfile
from pathlib import Path

SR = 44100
DURATION = 3.0  # seconds
t = np.linspace(0, DURATION, int(SR * DURATION), endpoint=False)
mix = np.zeros_like(t)


def envelope(start, attack, release, exp_decay=None):
    """Trapezoidal envelope, optionally with exponential decay during release."""
    env = np.zeros_like(t)
    s = int(start * SR)
    a = int(attack * SR)
    r = int(release * SR)
    if s + a >= len(env): return env
    # attack ramp
    env[s:s + a] = np.linspace(0, 1, a)
    end = s + a + r
    if end > len(env): end = len(env)
    if exp_decay is not None:
        local = np.arange(end - (s + a)) / SR
        env[s + a:end] = np.exp(-local * exp_decay)
    else:
        env[s + a:end] = np.linspace(1, 0, end - (s + a))
    return env


# === RADAR PING (0 - 0.6s) ===
ping = np.sin(2 * np.pi * 880 * t) * envelope(0.0, 0.01, 0.55, exp_decay=10)
mix += ping * 0.55

# === ECHO OF PING (0.4 - 1.0s) ===
echo = np.sin(2 * np.pi * 880 * t) * envelope(0.4, 0.01, 0.55, exp_decay=14) * 0.35
mix += echo

# === SECOND RADAR PING (0.85 - 1.3s) — confirms a contact ===
ping2 = np.sin(2 * np.pi * 1320 * t) * envelope(0.85, 0.005, 0.40, exp_decay=12) * 0.30
mix += ping2

# === SCANNER SWEEP (1.0 - 1.7s) — frequency sweep 350Hz → 1400Hz ===
sweep_start, sweep_dur = 1.0, 0.7
sweep_mask = (t >= sweep_start) & (t < sweep_start + sweep_dur)
sweep_progress = np.zeros_like(t)
sweep_progress[sweep_mask] = (t[sweep_mask] - sweep_start) / sweep_dur
sweep_freq = 350 + 1050 * sweep_progress
phase = np.cumsum(2 * np.pi * sweep_freq / SR)
sweep_env = np.zeros_like(t)
sweep_env[sweep_mask] = np.sin(np.pi * sweep_progress[sweep_mask]) ** 1.5
mix += np.sin(phase) * sweep_env * 0.35

# === CANNON BOOM (1.6 - 2.4s) — deep low-freq impact ===
boom_env = envelope(1.6, 0.005, 0.80, exp_decay=4.5)
boom_sine_low = np.sin(2 * np.pi * 55 * t) * boom_env
boom_sine_mid = np.sin(2 * np.pi * 90 * t) * boom_env * 0.5
rng = np.random.default_rng(seed=42)
noise = (rng.random(len(t)) * 2 - 1) * boom_env * 0.55
# Crude low-pass via cumulative average to take the edge off the noise
noise_lp = np.convolve(noise, np.ones(48) / 48, mode='same')
mix += boom_sine_low * 0.8 + boom_sine_mid * 0.3 + noise_lp * 0.55

# === GALLOPING HORSE HOOVES (2.2 - 3.0s) — rhythmic noise bursts ===
hoof_times = [2.20, 2.32, 2.46, 2.59, 2.71, 2.83]
hoof_pattern = np.zeros_like(t)
for ht in hoof_times:
    hoof_t = t - ht
    pulse = np.where((hoof_t >= 0) & (hoof_t < 0.06),
                     np.exp(-hoof_t * 60), 0)
    hoof_pattern += pulse
hoof_noise = (rng.random(len(t)) * 2 - 1) * hoof_pattern * 0.55
# Add a soft low thump synced with hooves
hoof_thump = np.sin(2 * np.pi * 140 * t) * hoof_pattern * 0.35
mix += hoof_noise + hoof_thump

# === TANK-TRACK CLANK (continuous low rumble, 1.2 - 3.0s) ===
rumble_env = envelope(1.2, 0.4, 1.4, exp_decay=1.0)
rumble = (rng.random(len(t)) * 2 - 1) * rumble_env * 0.12
# Heavy low-pass for a metallic-grind feel
rumble_lp = np.convolve(rumble, np.ones(160) / 160, mode='same')
mix += rumble_lp * 0.8

# === FINAL HORN/CHARGE ACCENT (2.7 - 3.0s) — a brass-like fanfare hint ===
charge_env = envelope(2.70, 0.04, 0.26, exp_decay=6)
# 3-note ascending fanfare: E5, G5, C6
fanfare_t = t - 2.70
fanfare = np.zeros_like(t)
for i, (freq, off, dur) in enumerate([(659, 0.0, 0.09), (784, 0.09, 0.09), (1047, 0.18, 0.12)]):
    note_mask = (fanfare_t >= off) & (fanfare_t < off + dur)
    fanfare[note_mask] = np.sin(2 * np.pi * freq * fanfare_t[note_mask])
mix += fanfare * charge_env * 0.30

# === NORMALIZE + SOFT MASTER GAIN ===
peak = np.max(np.abs(mix))
if peak > 0:
    mix = mix / peak * 0.88  # leave a touch of headroom
mix_int = (mix * 32767).astype(np.int16)

# === SAVE ===
out = Path("/app/frontend/src/assets/splash-radar.wav")
out.parent.mkdir(parents=True, exist_ok=True)
wavfile.write(out, SR, mix_int)
size_kb = out.stat().st_size // 1024
print(f"Saved → {out} ({size_kb} KB, {DURATION}s @ {SR}Hz)")

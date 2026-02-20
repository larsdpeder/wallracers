import pygame
import numpy as np
import math

SAMPLE_RATE = 44100


def _fade(samples, fade_in=500, fade_out=500):
    n = len(samples)
    fi = min(fade_in, n // 4)
    fo = min(fade_out, n // 4)
    if fi > 0:
        samples[:fi] *= np.linspace(0, 1, fi)
    if fo > 0:
        samples[-fo:] *= np.linspace(1, 0, fo)
    return samples


def _to_sound(samples, volume=0.3):
    samples = np.nan_to_num(samples, nan=0.0)
    samples = np.clip(samples, -1, 1)
    pcm = (samples * volume * 32767).astype(np.int16)
    stereo = np.column_stack((pcm, pcm))
    return pygame.sndarray.make_sound(stereo)


def _bandpass_noise(n, low_freq, high_freq):
    """Generate band-limited noise using FFT filtering."""
    noise = np.random.randn(n).astype(np.float32)
    fft = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(n, 1.0 / SAMPLE_RATE)
    mask = (freqs >= low_freq) & (freqs <= high_freq)
    fft[~mask] = 0
    return np.fft.irfft(fft, n).astype(np.float32)


def _distort(samples, drive=2.0):
    """Soft-clip distortion for gritty engine tone."""
    return np.tanh(samples * drive) / np.tanh(drive)


def _engine_loop(duration=6.0):
    """V6 turbo-hybrid F1 engine — cylinder pulses, turbo whine, exhaust crackle."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)
    s = np.zeros(n, dtype=np.float32)

    # --- Layer 1: Cylinder firing pulses (low, rumbly) ---
    base_rpm = 5500
    rpm_drift = base_rpm + 400 * np.sin(2 * math.pi * 0.3 * t) + \
                200 * np.sin(2 * math.pi * 0.9 * t)
    firing_freq = rpm_drift / 60.0 * 3
    phase = np.cumsum(firing_freq / SAMPLE_RATE) * 2 * math.pi

    pulse = np.sin(phase)
    pulse = np.sign(pulse) * (np.abs(pulse) ** 0.7)
    s += 0.30 * pulse

    # Keep lower harmonics only — no high scream
    s += 0.20 * np.sin(phase * 2)
    s += 0.10 * np.sin(phase * 3)

    # --- Layer 2: Exhaust resonance (bassy) ---
    exhaust_freq = firing_freq * 0.5
    exhaust_phase = np.cumsum(exhaust_freq / SAMPLE_RATE) * 2 * math.pi
    exhaust = 0.18 * np.sin(exhaust_phase)
    exhaust = _distort(exhaust, 2.5)
    s += 0.15 * exhaust

    # --- Layer 3: Exhaust crackle (subtle) ---
    crackle = np.random.randn(n).astype(np.float32)
    burst_times = np.random.choice(n, size=int(duration * 4), replace=False)
    crackle_env = np.zeros(n, dtype=np.float32)
    for bt in burst_times:
        burst_len = np.random.randint(300, 1000)
        end = min(bt + burst_len, n)
        burst = np.exp(-np.linspace(0, 6, end - bt))
        crackle_env[bt:end] = np.maximum(crackle_env[bt:end], burst)
    s += 0.04 * crackle * crackle_env

    # --- Layer 4: Low-end rumble ---
    rumble = 0.12 * np.sin(2 * math.pi * 50 * t)
    rumble += 0.08 * np.sin(2 * math.pi * 75 * t)
    rumble *= (0.8 + 0.2 * np.sin(2 * math.pi * 0.4 * t))
    s += rumble

    s = _distort(s, 1.5)

    # Crossfade for seamless loop
    xf = int(SAMPLE_RATE * 0.15)
    s[-xf:] = s[-xf:] * np.linspace(1, 0, xf) + s[:xf] * np.linspace(0, 1, xf)

    return _to_sound(s, 0.07)


def _engine_rev(duration=2.0):
    """Dramatic RPM climb — turbo spool, gear shift feel."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)
    s = np.zeros(n, dtype=np.float32)

    # RPM sweeps from 8000 to 15000
    rpm = 8000 + 7000 * (t / duration) ** 1.2
    firing_freq = rpm / 60.0 * 3
    phase = np.cumsum(firing_freq / SAMPLE_RATE) * 2 * math.pi

    # Sharper pulse wave at higher RPM
    pulse = np.sin(phase)
    pulse = np.sign(pulse) * (np.abs(pulse) ** 0.5)
    s += 0.35 * pulse
    s += 0.25 * np.sin(phase * 2)
    s += 0.20 * np.sin(phase * 3)
    s += 0.12 * np.sin(phase * 4)
    s += 0.08 * np.sin(phase * 6)

    # Turbo spool — rising whistle
    turbo_freq = 1500 + 3500 * (t / duration) ** 0.8
    turbo_phase = np.cumsum(turbo_freq / SAMPLE_RATE) * 2 * math.pi
    turbo = 0.08 * np.sin(turbo_phase)
    # Turbo gets louder as RPM climbs
    turbo *= np.linspace(0.3, 1.0, n)
    s += turbo

    # Exhaust bark gets more intense
    exhaust_noise = _bandpass_noise(n, 100, 2000)
    exhaust_env = np.linspace(0.3, 1.0, n) ** 2
    s += 0.12 * exhaust_noise * exhaust_env

    # High RPM scream
    scream = _bandpass_noise(n, 3000, 8000)
    scream_env = np.linspace(0, 0.8, n) ** 3
    s += 0.06 * scream * scream_env

    s = _distort(s, 2.0)
    s = _fade(s, 500, 1000)
    return _to_sound(s, 0.22)


def _boost_whoosh(duration=0.6):
    """Turbo dump valve + wastegate whoosh on boost."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)
    s = np.zeros(n, dtype=np.float32)

    # Turbo dump valve "pshhh" — filtered noise falling in pitch
    noise = np.random.randn(n).astype(np.float32)
    # Falling resonance
    center_freq = 4000 - 3000 * (t / duration)
    for i in range(3):
        freq_i = center_freq * (1 + i * 0.3)
        mod = np.sin(np.cumsum(freq_i / SAMPLE_RATE) * 2 * math.pi)
        s += (0.15 / (i + 1)) * noise * np.abs(mod)

    # Pressure release envelope — sharp attack, slow decay
    env = np.exp(-3.0 * t / duration)
    env[:int(n * 0.05)] *= np.linspace(0, 1, int(n * 0.05))
    s *= env

    # Turbo flutter (the "stututu" sound)
    flutter_freq = 40 + 20 * np.sin(2 * math.pi * 3 * t)
    flutter = 0.3 * np.sin(np.cumsum(flutter_freq / SAMPLE_RATE) * 2 * math.pi)
    flutter_env = np.exp(-4 * t / duration)
    flutter_env[:int(n * 0.1)] = 0  # flutter starts after initial dump
    s += flutter * flutter_env * noise * 0.3

    # Sub bass thump
    s += 0.2 * np.sin(2 * math.pi * 50 * t) * np.exp(-8 * t / duration)

    s = _fade(s, 100, 300)
    return _to_sound(s, 0.28)


def _countdown_beep(duration=0.15):
    """F1 lights-style beep — the five red lights tone."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)
    # Classic F1 countdown is a pure-ish tone around 1000Hz
    s = 0.6 * np.sin(2 * math.pi * 1000 * t)
    s += 0.2 * np.sin(2 * math.pi * 2000 * t)
    s += 0.1 * np.sin(2 * math.pi * 3000 * t)
    s = _fade(s, 80, 150)
    return _to_sound(s, 0.35)


def _go_signal(duration=0.6):
    """Lights out and away we go! Dramatic ascending burst."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)
    s = np.zeros(n, dtype=np.float32)

    # Ascending sweep
    freq = 800 + 600 * (t / duration)
    phase = np.cumsum(freq / SAMPLE_RATE) * 2 * math.pi
    s += 0.4 * np.sin(phase)
    s += 0.3 * np.sin(phase * 1.5)
    s += 0.2 * np.sin(phase * 2)

    # Crowd roar (bandpass noise)
    crowd = _bandpass_noise(n, 200, 3000)
    crowd_env = np.linspace(0, 1, n) ** 0.5
    s += 0.25 * crowd * crowd_env

    # Grid start revs (short engine burst)
    rev_freq = 300 + 500 * (t / duration) ** 2
    rev_phase = np.cumsum(rev_freq / SAMPLE_RATE) * 2 * math.pi
    s += 0.15 * _distort(np.sin(rev_phase) + 0.5 * np.sin(rev_phase * 2), 2.0)

    s = _fade(s, 100, 400)
    return _to_sound(s, 0.35)


def _pickup_chime(duration=0.15):
    """Quick bright radio chirp for item pickup."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)
    # Ascending chirp
    freq = 1200 + 2000 * (t / duration)
    phase = np.cumsum(freq / SAMPLE_RATE) * 2 * math.pi
    s = 0.5 * np.sin(phase)
    s += 0.3 * np.sin(phase * 1.5)
    env = np.exp(-3 * t / duration)
    s *= env
    s = _fade(s, 50, 100)
    return _to_sound(s, 0.25)


def _oil_splat(duration=0.5):
    """Tire lock-up screech + gravel trap feel."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)
    s = np.zeros(n, dtype=np.float32)

    # Tire lock-up screech — harsh, falling pitch
    screech_freq = 1800 - 1200 * (t / duration)
    screech_phase = np.cumsum(screech_freq / SAMPLE_RATE) * 2 * math.pi
    screech = np.sign(np.sin(screech_phase))  # square wave = harsh
    screech += 0.5 * np.sin(screech_phase * 3)
    screech_env = np.exp(-3 * t / duration)
    s += 0.2 * _distort(screech, 2.5) * screech_env

    # Impact thud
    s += 0.4 * np.sin(2 * math.pi * 60 * t) * np.exp(-10 * t / duration)
    s += 0.2 * np.sin(2 * math.pi * 120 * t) * np.exp(-8 * t / duration)

    # Gravel/debris spray
    debris = _bandpass_noise(n, 1000, 8000)
    debris_env = np.sin(math.pi * t / duration) * np.exp(-2 * t / duration)
    s += 0.15 * debris * debris_env

    s = _fade(s, 100, 300)
    return _to_sound(s, 0.22)


def _honk(base_freq, duration=0.35):
    """Stadium air horn — big and brassy."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)

    # Main horn tone with slight vibrato
    vib = 1.0 + 0.015 * np.sin(2 * math.pi * 8 * t)
    freq = base_freq * vib
    phase = np.cumsum(freq / SAMPLE_RATE) * 2 * math.pi

    # Rich brass harmonics
    s = 0.40 * np.sin(phase)
    s += 0.35 * np.sin(phase * 2)
    s += 0.20 * np.sin(phase * 3)
    s += 0.10 * np.sin(phase * 4)
    s += 0.05 * np.sin(phase * 5)

    # Add some "blat" — distorted low end
    blat = 0.15 * np.sin(phase * 0.5)
    s += _distort(blat, 3.0)

    # Slight noise for air pressure
    s += 0.03 * np.random.randn(n).astype(np.float32)

    # Envelope: quick attack, sustain, release
    env = np.ones(n, dtype=np.float32)
    attack = min(int(n * 0.03), 400)
    release = min(int(n * 0.2), 3000)
    if attack > 0:
        env[:attack] = np.linspace(0, 1, attack) ** 0.5
    if release > 0:
        env[-release:] = np.linspace(1, 0, release) ** 0.5
    s *= env

    return _to_sound(s, 0.28)


def _finish_fanfare(duration=2.0):
    """Checkered flag — engine cooldown + victory horn + crowd."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)
    s = np.zeros(n, dtype=np.float32)

    # Engine winding down (high to low RPM)
    rpm = 14000 - 10000 * (t / duration) ** 0.5
    firing_freq = rpm / 60.0 * 3
    phase = np.cumsum(firing_freq / SAMPLE_RATE) * 2 * math.pi
    engine = 0.15 * np.sin(phase) + 0.10 * np.sin(phase * 2)
    engine *= np.exp(-2 * t / duration)
    s += engine

    # Victory horn — triumphant two-note (like the podium ceremony)
    horn_start = int(0.3 * SAMPLE_RATE)
    horn_n = n - horn_start
    horn_t = np.linspace(0, duration - 0.3, horn_n, dtype=np.float32)
    # Major chord: C5 E5 G5
    horn = 0.20 * np.sin(2 * math.pi * 523 * horn_t)
    horn += 0.18 * np.sin(2 * math.pi * 659 * horn_t)
    horn += 0.22 * np.sin(2 * math.pi * 784 * horn_t)
    # Add warmth
    horn += 0.08 * np.sin(2 * math.pi * 1046 * horn_t)
    horn *= (1.0 - np.exp(-5 * horn_t)) * np.exp(-0.8 * horn_t / (duration - 0.3))
    s[horn_start:] += horn

    # Crowd roar
    crowd = _bandpass_noise(n, 200, 4000)
    crowd_env = np.sqrt(np.clip(np.sin(math.pi * t / duration), 0, 1))
    crowd_env *= np.linspace(0, 1, n) ** 0.3
    s += 0.18 * crowd * crowd_env

    # Exhaust pops during cooldown
    pop_noise = np.random.randn(n).astype(np.float32)
    pop_times = np.random.choice(n // 2, size=6, replace=False)
    pop_env = np.zeros(n, dtype=np.float32)
    for pt in pop_times:
        burst_len = np.random.randint(300, 1200)
        end = min(pt + burst_len, n)
        pop_env[pt:end] = np.exp(-np.linspace(0, 8, end - pt))
    s += 0.10 * pop_noise * pop_env

    s = _fade(s, 200, 1500)
    return _to_sound(s, 0.28)


def _lane_switch(duration=0.08):
    """Quick tire chirp for lane changes."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)
    noise = _bandpass_noise(n, 2000, 6000)
    env = np.exp(-20 * t / duration)
    s = 0.5 * noise * env
    # Tiny suspension thunk
    s += 0.3 * np.sin(2 * math.pi * 150 * t) * np.exp(-30 * t / duration)
    s = _fade(s, 30, 50)
    return _to_sound(s, 0.12)


class SoundManager:
    def __init__(self):
        self.sounds = {}
        self._engine_channel = None

    def init(self):
        pygame.mixer.set_num_channels(16)
        self._engine_channel = pygame.mixer.Channel(15)

        self.sounds["countdown"] = _countdown_beep()
        self.sounds["go"] = _go_signal()
        self.sounds["boost"] = _boost_whoosh()
        self.sounds["pickup"] = _pickup_chime()
        self.sounds["oil"] = _oil_splat()
        self.sounds["finish"] = _finish_fanfare()
        self.sounds["engine_rev"] = _engine_rev()
        self.sounds["engine_loop"] = _engine_loop()
        self.sounds["lane_switch"] = _lane_switch()

        # Honks — different pitch per player, stadium air horn
        honk_freqs = [320, 400, 260, 480]
        for i, freq in enumerate(honk_freqs):
            self.sounds[f"honk_{i}"] = _honk(freq)

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def start_engine(self):
        """Start looping engine sound during racing."""
        if self._engine_channel and "engine_loop" in self.sounds:
            self._engine_channel.play(self.sounds["engine_loop"], loops=-1)

    def stop_engine(self):
        """Stop the engine loop."""
        if self._engine_channel:
            self._engine_channel.fadeout(800)

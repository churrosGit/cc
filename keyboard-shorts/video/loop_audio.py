"""Seamless loop audio (loop length from events.json): original BGM (120 BPM, 4 bars = 8 s) + ratchet clicks + spanner taps.
Rendered over three loop periods and the middle one is kept, so tails wrap across the seam.
Usage: python3 loop_audio.py events.json out.wav"""
import json, sys, wave
import numpy as np
SR = 44100; ev = json.load(open(sys.argv[1])); P = ev['duration']; N = int(SR * P)
rng = np.random.default_rng(3); T = 3 * N; buf = np.zeros(T); sfx = np.zeros(T)
t_ = lambda n: np.arange(n) / SR
def add(b, x, at, g=1.0):
    i = int(at * SR); j = min(len(b), i + len(x))
    if 0 <= i < len(b): b[i:j] += x[:j - i] * g
def hp(x, lo):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); return np.fft.irfft(X / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4), len(x))
note = lambda m: 440 * 2 ** ((m - 69) / 12)
beat = 0.5; PROG = [([57, 60, 64, 67], 45), ([53, 57, 60, 64], 41), ([48, 55, 60, 64], 36), ([55, 59, 62, 67], 43)]
for rep in range(3):
    t0 = rep * P
    for b in range(int(round(P / (4 * beat)))):            # fill the whole loop with 4-bar progressions
        ch, root = PROG[b % 4]; tb = t0 + b * 4 * beat
        n = int(4 * beat * SR * 1.15); tt = t_(n); e = np.minimum(1, tt / 0.25) * np.exp(-tt * 0.9)
        add(buf, sum(np.sin(2 * np.pi * note(m) * tt) + 0.5 * np.sin(2 * np.pi * note(m) * 1.003 * tt) for m in ch) * e / 9, tb)
        for k in range(16):                       # soft 16th pluck
            m = ch[[0, 2, 1, 3][k % 4]] + 12; nn = int(0.3 * SR); tt2 = t_(nn)
            add(buf, np.sin(2 * np.pi * note(m) * tt2) * np.exp(-tt2 * 14) * (0.5 if k % 4 else 0.8) * 0.35, tb + k * beat / 4)
        for k in range(8):                        # bass 8ths
            nn = int(beat / 2 * SR * 0.9); tt2 = t_(nn)
            add(buf, np.tanh(1.6 * np.sin(2 * np.pi * note(root - 12) * tt2)) * np.minimum(1, tt2 / 0.005) * np.exp(-tt2 * 3) * 0.45, tb + k * beat / 2)
        for k in range(8):                        # kick on beats, hat on off-beats
            tt2 = t_(int(0.3 * SR))
            if k % 2 == 0: add(buf, np.sin(2 * np.pi * np.cumsum(48 + 80 * np.exp(-tt2 * 30)) / SR) * np.exp(-tt2 * 10) * 0.6, tb + k * beat / 2)
            else: hh = t_(int(0.05 * SR)); add(buf, hp(rng.standard_normal(len(hh)), 7000) * np.exp(-hh * 80) * 0.12, tb + k * beat / 2)
    def click():
        n = int(0.09 * SR); tt = t_(n)
        ring = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, a, d in [(3150, 1, 90), (5070, .7, 120), (7400, .45, 160), (1850, .5, 70)])
        return 0.55 * ring + 0.8 * hp(rng.standard_normal(n), 2500) * np.exp(-tt * 400) + 0.5 * np.sin(2 * np.pi * 210 * tt) * np.exp(-tt * 60)
    def tap():
        n = int(0.35 * SR); tt = t_(n)
        ring = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, a, d in [(1120, 1, 14), (2310, .6, 18), (3730, .4, 24), (5200, .25, 30)])
        return 0.5 * ring + 0.6 * hp(rng.standard_normal(n), 1500) * np.exp(-tt * 120)
    for c in ev['clicks']: add(sfx, click(), t0 + c, 1.0)
    for c in ev['taps']: add(sfx, tap(), t0 + c, 0.7)
mid = slice(N, 2 * N)
m = buf[mid] / np.max(np.abs(buf[mid])); s = sfx[mid] / np.max(np.abs(sfx[mid]))
mix = 0.45 * m + 0.6 * s; mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix = mix / np.max(np.abs(mix)) * 0.89
st = (np.stack([mix, np.roll(mix, 12)], 1) * 32767).astype(np.int16)
with wave.open(sys.argv[2], 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
print('wrote', sys.argv[2], P, 's')

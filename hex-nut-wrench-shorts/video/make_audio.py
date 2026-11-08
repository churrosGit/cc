"""Original BGM + SFX, synthesized from scratch with numpy (no samples, no third-party audio).
Usage: python3 make_audio.py events.json audio.wav [narration_44k_mono.wav]
With a narration file the BGM is ducked under the voice and the voice leads the mix."""
import json, sys, wave
import numpy as np

SR = 44100
ev = json.load(open(sys.argv[1]))
DUR = ev['duration']
N = int(SR * DUR) + SR
rng = np.random.default_rng(7)

def t_(n): return np.arange(n) / SR
def env_adsr(n, a, d, s, r, hold=None):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    hold = n - a - d - r if hold is None else int(hold * SR)
    e = np.concatenate([np.linspace(0, 1, max(a, 1)), np.linspace(1, s, max(d, 1)), np.full(max(hold, 0), s), np.linspace(s, 0, max(r, 1))])
    return np.pad(e, (0, max(0, n - len(e))))[:n]
def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); g = np.ones_like(f)
    if hi: g *= 1 / np.sqrt(1 + (f / hi) ** 4)
    if lo: g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4)
    return np.fft.irfft(X * g, len(x))
def add(buf, x, at, gain=1.0):
    i = int(at * SR); j = min(len(buf), i + len(x))
    if j > i: buf[i:j] += x[:j - i] * gain
def note(m): return 440 * 2 ** ((m - 69) / 12)

BPM = 104; beat = 60 / BPM; bar = 4 * beat
# A minor: Am9 | Fmaj7 | C(add9) | G6  (2 bars each), MIDI voicings
PROG = [([57, 60, 64, 67, 71], 45), ([53, 57, 60, 64, 67], 41), ([48, 55, 60, 62, 64], 36), ([55, 59, 62, 64, 67], 43)]
pad = np.zeros(N); pluck = np.zeros(N); bass = np.zeros(N); drums = np.zeros(N)

nbars = int(DUR / bar) + 2
for b in range(0, nbars, 2):
    chord, root = PROG[(b // 2) % 4]; t0 = b * bar; n = int(2 * bar * SR)
    tt = t_(n); e = env_adsr(n, 0.6, 0.4, 0.8, 0.9)
    s = sum(np.sin(2 * np.pi * note(m) * tt * (1 + dt)) for m in chord for dt in (-0.0025, 0.0025))
    s += 0.25 * sum(np.sign(np.sin(2 * np.pi * note(m) * tt)) for m in chord[:3])
    add(pad, s * e / 10, t0)
    # pluck arpeggio, 16ths
    pat = [0, 2, 1, 3, 4, 3, 1, 2]
    for k in range(32):
        m = chord[pat[k % 8]] + 12; nn = int(0.4 * SR); tt2 = t_(nn)
        x = (np.sin(2 * np.pi * note(m) * tt2) + 0.3 * np.sin(4 * np.pi * note(m) * tt2)) * np.exp(-tt2 * 11)
        add(pluck, x * (0.9 if k % 4 == 0 else 0.6), t0 + k * beat / 4)
    # bass: 8ths on the root with octave hop
    for k in range(16):
        m = root - 12 + (12 if k % 8 == 6 else 0); nn = int(beat / 2 * SR * 0.95); tt2 = t_(nn)
        x = np.tanh(1.8 * np.sin(2 * np.pi * note(m) * tt2)) * env_adsr(nn, 0.005, 0.05, 0.7, 0.04)
        add(bass, x, t0 + k * beat / 2)

def kick():
    n = int(0.35 * SR); tt = t_(n); f = 48 + 90 * np.exp(-tt * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9)
def hat(): n = int(0.06 * SR); return fft_filter(rng.standard_normal(n), lo=7000) * np.exp(-t_(n) * 70)
def snare():
    n = int(0.2 * SR); tt = t_(n)
    return (0.5 * fft_filter(rng.standard_normal(n), lo=1500, hi=9000) + 0.3 * np.sin(2 * np.pi * 190 * tt)) * np.exp(-tt * 22)
K, Hh, Sn = kick(), hat(), snare()
DRUM_IN, DRUM_OUT = 4.5, 45.5
for i in range(int(DUR / (beat / 2)) + 1):
    t = i * beat / 2
    if not (DRUM_IN <= t < DRUM_OUT): continue
    if i % 4 == 0: add(drums, K, t, 1.0)
    if i % 8 == 4: add(drums, Sn, t, 0.55)
    if i % 2 == 1: add(drums, Hh, t, 0.35)

pluck = pluck + 0.35 * np.roll(pluck, int(beat * 0.75 * SR))      # dotted-8th echo
pad = fft_filter(pad, hi=2200); pluck = fft_filter(pluck, hi=6000); bass = fft_filter(bass, hi=900)
# arrangement envelope: soft intro, full body, outro fade
tt = t_(N)
body = np.clip((tt - 4.2) / 0.6, 0, 1)
master = np.clip(tt / min(0.8, DUR * 0.1), 0, 1) * np.clip((DUR - tt) / min(2.5, DUR * 0.12), 0, 1)
music = 0.55 * pad + 0.32 * pluck * (0.6 + 0.4 * body) + 0.45 * bass * body + 0.5 * drums
music *= master

# ---------- SFX ----------
sfx = np.zeros(N)
def click():
    n = int(0.09 * SR); tt = t_(n)
    ring = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, a, d in [(3150, 1, 90), (5070, .7, 120), (7400, .45, 160), (1850, .5, 70)])
    tr = fft_filter(rng.standard_normal(n), lo=2500) * np.exp(-tt * 400)
    thunk = np.sin(2 * np.pi * 210 * tt) * np.exp(-tt * 60)
    return 0.55 * ring + 0.8 * tr + 0.5 * thunk
def tap():
    n = int(0.35 * SR); tt = t_(n)
    ring = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, a, d in [(1120, 1, 14), (2310, .6, 18), (3730, .4, 24), (5200, .25, 30)])
    return 0.5 * ring + 0.6 * fft_filter(rng.standard_normal(n), lo=1500) * np.exp(-tt * 120)
def whoosh(L=0.7):
    n = int(L * SR); tt = t_(n); x = fft_filter(rng.standard_normal(n), lo=300, hi=4000)
    return x * np.sin(np.pi * tt / L) ** 2
C, Tp = click(), tap()
for c in ev['clicks']: add(sfx, C, c, 0.9 * (1.3 if 33 < c < 38 else 1))
for c in ev['taps']: add(sfx, Tp, c, 0.6)
for c in (4.15, 14.65): add(sfx, whoosh(0.7), c, 0.25)
add(sfx, whoosh(1.2), 15.5, 0.18)

music = music / (np.max(np.abs(music)) + 1e-9)
sfx = sfx / (np.max(np.abs(sfx)) + 1e-9)
if len(sys.argv) > 3:
    with wave.open(sys.argv[3]) as w:
        assert w.getframerate() == SR and w.getnchannels() == 1
        v = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768.0
    voice = np.zeros(N); voice[:min(N, len(v))] = v[:N]
    voice /= np.max(np.abs(voice)) + 1e-9
    # sidechain: smoothed voice envelope -> duck music by up to ~11 dB
    k = int(0.25 * SR); c = np.concatenate([[0], np.cumsum(np.abs(voice))]); env = np.zeros(N); lo = np.clip(np.arange(N) - k // 2, 0, N); hi = np.clip(np.arange(N) + k // 2, 0, N); env = (c[hi] - c[lo]) / k
    env = np.clip(env / (np.percentile(env[env > 1e-4], 60) + 1e-9), 0, 1)
    duck = 1 - 0.72 * env
    mix = 0.88 * voice + 0.30 * music * duck + 0.42 * sfx
else:
    mix = music * 0.5 + sfx * 0.62
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix = mix[:int(SR * DUR)]
mix = mix / np.max(np.abs(mix)) * 0.89
# light stereo: pluck echo offset gives width; here just duplicate with tiny delay on the right
L = mix; R = np.concatenate([np.zeros(12), mix[:-12]])
st = (np.stack([L, R], 1) * 32767).astype(np.int16)
with wave.open(sys.argv[2], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
print('wrote', sys.argv[2], f'{DUR}s')

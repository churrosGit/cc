import numpy as np, wave, sys
SR = 44100; DUR = 30.0; N = int(SR * DUR)
rng = np.random.default_rng(5)
L = np.zeros(N); Rch = np.zeros(N)
BEAT = 0.5
TRANS = [3, 7, 11, 15, 19, 23, 27]

def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR); j = min(N, i + len(sig))
    if i >= N or j <= i: return
    s = sig[:j - i] * gain
    L[i:j] += s * np.sqrt(0.5 * (1 - pan)) * 1.414 / 1.414
    Rch[i:j] += s * np.sqrt(0.5 * (1 + pan)) * 1.414 / 1.414

def env_exp(n, tau): return np.exp(-np.arange(n) / (tau * SR))
def tt(d): return np.arange(int(d * SR)) / SR
def note(m): return 440.0 * 2 ** ((m - 69) / 12)

def kick(gain=1.0):
    t = tt(0.45); f = 42 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 7.5)
    click = rng.standard_normal(len(t)) * np.exp(-t * 300) * 0.25
    return np.tanh((s + click) * 1.6) * gain

def hat(open_=False):
    d = 0.25 if open_ else 0.06
    n = rng.standard_normal(int(d * SR))
    n = np.diff(np.concatenate([[0], n]))  # crude highpass
    return n * env_exp(len(n), 0.05 if open_ else 0.012) * 0.35

def clap():
    t = tt(0.3); n = rng.standard_normal(len(t))
    e = np.zeros(len(t))
    for k, o in enumerate([0, 0.011, 0.022]):
        i = int(o * SR); e[i:] += np.exp(-(t[: len(t) - i]) * (90 if k < 2 else 18))
    # bandpass-ish: difference of smoothed
    sm = np.convolve(n, np.ones(6) / 6, 'same')
    return (n - sm) * e * 0.5

def saw(f, d, detune=0.0):
    t = tt(d); out = 0
    for dt in (-detune, 0, detune):
        ph = (t * f * (1 + dt)) % 1.0
        out = out + (2 * ph - 1)
    return out / 3

def lowpass(x, a):  # one-pole, a in (0,1): higher = brighter
    y = np.zeros_like(x); acc = 0.0
    # vectorized via scipy-free recursive filter using cumulative trick is hard; do chunked python loop on downsampled? keep simple
    for i in range(len(x)):
        acc += a * (x[i] - acc); y[i] = acc
    return y

def lp_fast(x, cutoff):
    # FFT brickwall-ish smooth lowpass
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))

# ---- chords ----
# segment chord roots (MIDI): Am, F, C, G, Am, F, (intro Am, outro Am)
CH = {
    'Am': [57, 60, 64, 69], 'F': [53, 57, 60, 65], 'C': [55, 60, 64, 67], 'G': [55, 59, 62, 67], 'Fmaj7': [53, 57, 60, 64],
}
sections = [(0, 3, 'Am'), (3, 7, 'Am'), (7, 11, 'F'), (11, 15, 'C'), (15, 19, 'G'), (19, 23, 'Am'), (23, 27, 'Fmaj7'), (27, 30, 'Am')]
bass_root = {'Am': 33, 'F': 29, 'C': 36, 'G': 31, 'Fmaj7': 29}

# pads
for a, b, c in sections:
    d = b - a + 0.6
    pad = sum(saw(note(m), d, 0.004) for m in CH[c]) / 4
    pad = lp_fast(pad, 1400 if a >= 3 else 700)
    t = tt(d); e = np.minimum(1, t / 0.25) * np.minimum(1, (d - t) / 0.5)
    if a == 0: e = np.minimum(1, t / 2.5) * np.minimum(1, (d - t) / 0.4)
    if a == 27: e = np.minimum(1, t / 0.05) * np.exp(-t * 0.6)
    add(pad * e, a, 0.16, -0.25); add(pad * e, a + 0.012, 0.16, 0.25)

# drums
for i in range(int(DUR / (BEAT / 2))):
    t = i * BEAT / 2
    beat_i = i // 2
    if 3 <= t < 29:
        if i % 2 == 0:
            add(kick(1.0 if 19 <= t < 23 else 0.85), t, 0.9)
        else:
            add(hat(open_=(beat_i % 4 == 3)), t, 0.5, 0.3)
        if t >= 7 and i % 2 == 0 and beat_i % 2 == 1:
            add(clap(), t, 0.55, -0.1)
    if 11 <= t < 27 and i % 2 == 1:  # 16th shuffle hats
        add(hat(), t + BEAT / 4, 0.22, -0.35)

# bass (8th notes, sidechain feel)
for a, b, c in sections:
    if a < 3 or a >= 27: continue
    r = bass_root[c]
    for k in range(int((b - a) / (BEAT / 2))):
        t0 = a + k * BEAT / 2
        m = r + (12 if k % 4 == 3 else 0)
        t = tt(BEAT / 2)
        s = np.sin(2 * np.pi * note(m) * t) + 0.3 * np.sin(2 * np.pi * note(m) * 2 * t)
        e = np.minimum(1, t / 0.02) * np.exp(-t * 5) if k % 2 == 1 else np.minimum(1, np.maximum(0, (t - 0.06) / 0.04)) * np.exp(-t * 4)
        add(np.tanh(s * 1.4) * e, t0, 0.32)
# outro sub hit
add(np.sin(2 * np.pi * note(33) * tt(3)) * np.exp(-tt(3) * 1.2), 27, 0.5)

# arp (16ths) from 11s
for a, b, c in sections:
    if a < 11 or a >= 27: continue
    notes = CH[c] + [CH[c][1] + 12]
    for k in range(int((b - a) / (BEAT / 4))):
        t0 = a + k * BEAT / 4
        m = notes[(k * 3) % len(notes)] + 12
        t = tt(0.22)
        s = saw(note(m), 0.22, 0.002) * np.exp(-t * 18)
        s = lp_fast(s, 2600)
        add(s, t0, 0.07, 0.5 if k % 2 else -0.5)

# whooshes + impacts at transitions
for b in TRANS:
    d = 0.6; t = tt(d); n = rng.standard_normal(len(t))
    # rising bandpass sweep via varying lowpass of noise: approximate with crossfade between filtered versions
    lo = lp_fast(n, 600); hi = lp_fast(n, 5000) - lp_fast(n, 900)
    k = (t / d) ** 2
    sw = (lo * (1 - k) + hi * k) * k * 1.2
    add(sw, b - d, 0.35, -0.4); add(sw[::-1] * 0 + sw, b - d + 0.01, 0.35, 0.4)
    # impact
    ti = tt(1.2)
    boom = np.sin(2 * np.pi * (50 + 40 * np.exp(-ti * 8)) * ti) * np.exp(-ti * 3.5)
    crash = (rng.standard_normal(len(ti))) * np.exp(-ti * 4.5)
    crash = crash - lp_fast(crash, 3000)
    add(boom, b, 0.55 if b != 27 else 0.8); add(crash, b, 0.12 if b != 27 else 0.2)

# intro riser (0-3)
t = tt(3.0); n = rng.standard_normal(len(t))
f = 200 + 3000 * (t / 3) ** 2
ris = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.15 + (n - lp_fast(n, 1500)) * 0.4
add(ris * (t / 3) ** 2.5, 0.0, 0.25)

# typing clicks (prompt segment): chars typed between 23.9 and 26.0
PLEN = len('cinematic portrait, soft rim light, 35mm film grain, shallow depth of field --style raw')
for i in range(PLEN):
    tc = 23 + 0.9 + 2.1 * i / PLEN
    c = rng.standard_normal(int(0.02 * SR)); c = (c - lp_fast(c, 2500)) * env_exp(len(c), 0.003)
    add(c, tc, 0.25, rng.uniform(-0.4, 0.4))

# ---- simple reverb (FFT convolution with decaying noise IR) ----
ir_t = tt(1.6); ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 3.2); ir[:int(0.01 * SR)] = 0
ir = lp_fast(ir, 6000); ir /= np.sqrt(np.sum(ir ** 2))
def conv(x, h):
    n = len(x) + len(h); nf = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, nf) * np.fft.rfft(h, nf), nf)[:len(x)]
L2 = L + conv(L, ir) * 0.18; R2 = Rch + conv(Rch, ir[::-1][::-1] * 1.0) * 0.18

mix = np.stack([L2, R2], 1)
# master: fade out, soft clip, normalize
fade = np.ones(N); fo = int(0.8 * SR); fade[-fo:] = np.linspace(1, 0, fo)
mix *= fade[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(mix * 1.5) / np.tanh(1.5) * 0.89
out = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('ok', out.shape)

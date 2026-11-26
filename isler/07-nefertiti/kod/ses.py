"""Filmin sesi: tamamı numpy ile sentez (örnek/kayıt yok). -> ../test/ses.wav"""
import numpy as np, wave, os
SR = 48000; DUR = 28.0; N = int(SR * DUR); rng = np.random.default_rng(3)
T = np.arange(N) / SR
def buf(): return np.zeros((N, 2))
def fft_filt(x, lo=None, hi=None, w=.25):
    X = np.fft.rfft(x, axis=0); f = np.fft.rfftfreq(len(x), 1 / SR); lf = np.log2(np.maximum(f, 1)); g = np.ones_like(f)
    if lo: g *= 1 / (1 + np.exp(-(lf - np.log2(lo)) / w * 2))
    if hi: g *= 1 / (1 + np.exp((lf - np.log2(hi)) / w * 2))
    return np.fft.irfft(X * (g[:, None] if x.ndim == 2 else g), n=len(x), axis=0)
def add(b, x, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR); x = np.asarray(x)
    if x.ndim == 1: x = np.stack([x * np.cos((pan + 1) * np.pi / 4), x * np.sin((pan + 1) * np.pi / 4)], 1) * 1.2
    a, e = max(i, 0), min(i + len(x), N)
    if e > a: b[a:e] += gain * x[a - i:e - i]
def ss(a, b, t): u = np.clip((t - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
# Re hicaz: D Eb F# G A Bb C
D, Eb, Fs, G, A, Bb, C_ = 62, 63, 66, 67, 69, 70, 72
# ---------- yankı
def reverb(x, sec=4.2, bright=5200, pre=.03, seed=1):
    r = np.random.default_rng(seed); n = int(sec * SR); t = np.arange(n) / SR
    ir = r.normal(size=(n, 2)) * np.exp(-t * 6.9 / sec)[:, None]
    dark = fft_filt(ir, 140, 1500); bri = fft_filt(ir, 140, bright); k = np.exp(-t / .5)[:, None]
    ir = bri * k + dark * (1 - k); ir = np.vstack([np.zeros((int(pre * SR), 2)), ir]); ir /= np.sqrt((ir ** 2).sum(0))
    L = len(x) + len(ir); M = 1 << int(np.ceil(np.log2(L)))
    return np.fft.irfft(np.fft.rfft(x, M, axis=0) * np.fft.rfft(ir, M, axis=0), M, axis=0)[:len(x)]
# ---------- sesler
def pluck(f, sec=3.0, bright=.6, damp=.996):
    P = max(int(round(SR / f - .5)), 4); n = int(sec * SR); e = rng.uniform(-1, 1, P)
    k = int(P * .13) or 1; e = e - np.roll(e, k) * .7                          # tezene yeri
    for _ in range(int((1 - bright) * 4)): e = (e + np.roll(e, 1)) / 2
    out = [e]; cur = e
    for _ in range(n // P):
        cur = damp * .5 * (cur + np.concatenate([[cur[-1]], cur[:-1]])); out.append(cur)
    y = np.concatenate(out)[:n]; t = np.arange(len(y)) / SR
    return y * np.minimum(1, t / .0015) * np.exp(-t * .5) * .5
def pluck2(f, sec=3.0, **k):                                                    # çift telli
    a, b = pluck(f * 1.0015, sec, **k), pluck(f * .9985, sec, **k); m = min(len(a), len(b)); return np.stack([a[:m] * .8 + b[:m] * .35, a[:m] * .35 + b[:m] * .8], 1)
def ney(notes, gl=.09):
    """notes: [(t, süre, midi, şiddet)]"""
    t0 = notes[0][0]; t1 = notes[-1][0] + notes[-1][1] + .5; n = int((t1 - t0) * SR); t = np.arange(n) / SR + t0
    pit = np.full(n, notes[0][2], float); amp = np.zeros(n)
    for i, (a, d, m, v) in enumerate(notes):
        w = ss(a - gl / 2, a + gl / 2, t); pit = pit * (1 - w) + m * w
        amp = np.maximum(amp, v * ss(a, a + .16, t) * (1 - ss(a + d - .18, a + d + .22, t)))
    vib = .22 * np.sin(2 * np.pi * 5.1 * t + .6 * np.sin(t * 2)) * ss(0, 1, (np.sin(t * 1.1) + 1) / 2)
    f = hz(pit + vib + .05 * np.cumsum(rng.normal(size=n)) / np.sqrt(np.arange(1, n + 1) * 60 + 1)); ph = 2 * np.pi * np.cumsum(f) / SR
    y = sum(g * np.sin(k * ph + k) for k, g in ((1, 1), (2, .42), (3, .30), (4, .10), (5, .07), (6, .03)))
    br = fft_filt(rng.normal(size=n), 700, 4200) * .55 + fft_filt(rng.normal(size=n), 250, 900) * .4
    return (y * .30 * amp ** 1.2 + br * .20 * amp ** .7 * (1 + .5 * np.sin(ph))) * .6
def pad(midis, t0, t1, at, rel, bright=1.0, formant=True):
    n = int((t1 - t0) * SR); t = np.arange(n) / SR; out = np.zeros((n, 2))
    for m in midis:
        f0 = hz(m)
        for dt in (-.07, 0.0, .06):
            f = hz(m + dt); pan = rng.uniform(-.8, .8); y = np.zeros(n); drift = .0015 * np.sin(2 * np.pi * rng.uniform(.08, .25) * t + rng.uniform(0, 6))
            ph = 2 * np.pi * f * (t + np.cumsum(drift) / SR)
            for h in range(1, int(min(22, 5200 / f0)) + 1):
                fh = f * h; g = h ** -1.25
                if formant: g *= .25 + 1.2 * np.exp(-((fh - 620) / 240) ** 2) + .9 * np.exp(-((fh - 1080) / 260) ** 2) + .25 * np.exp(-((fh - 2600) / 500) ** 2)
                y += g * bright ** (h - 1) * np.sin(h * ph + rng.uniform(0, 6))
            out += np.stack([y * np.cos((pan + 1) * np.pi / 4), y * np.sin((pan + 1) * np.pi / 4)], 1)
    env = ss(0, at, t) * (1 - ss(t1 - t0 - rel, t1 - t0, t)); return out * env[:, None] / (3 * len(midis))
def dum(v=1.0, f0=118, f1=58, dec=5.0):
    n = int(1.4 * SR); t = np.arange(n) / SR; ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-t * 26)) / SR
    y = np.sin(ph) * np.exp(-t * dec) + .35 * np.sin(1.59 * ph) * np.exp(-t * 11)
    return v * (y + fft_filt(rng.normal(size=n), 120, 900) * np.exp(-t * 42) * 1.6) * np.minimum(1, t / .002)
def tek(v=1.0, hi=1.0):
    n = int(.35 * SR); t = np.arange(n) / SR
    return v * (fft_filt(rng.normal(size=n), 1100 * hi, 6500) * np.exp(-t * 48) * 1.5 + .35 * np.sin(2 * np.pi * 372 * hi * t) * np.exp(-t * 34) + .2 * np.sin(2 * np.pi * 611 * hi * t) * np.exp(-t * 40))
def boom(v=1.0):
    n = int(4.5 * SR); t = np.arange(n) / SR; ph = 2 * np.pi * np.cumsum(38 + 55 * np.exp(-t * 16)) / SR
    return v * (np.tanh(1.5 * np.sin(ph) * np.exp(-t * 1.5)) + fft_filt(rng.normal(size=n), 40, 420) * np.exp(-t * 4.5) * 1.1)
def swell(sec, v=1.0):
    n = int(sec * SR); t = np.arange(n) / SR; e = (t / sec) ** 3.2
    x = fft_filt(rng.normal(size=(n, 2)), 500, 7500) * e[:, None] * .8
    s = sum(np.sin(2 * np.pi * hz(m) * t + 3 * np.sin(2 * np.pi * .7 * t)) for m in (86, 93, 98)) * e * .06
    return v * (x + s[:, None]) * (1 - ss(sec - .02, sec, t))[:, None]
def clunk(v=1.0, p=1.0):
    n = int(1.6 * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for f, d, g in ((148, 10, .8), (211, 14, .6), (417, 20, .55), (668, 26, .40), (1139, 34, .28), (2184, 52, .18), (3420, 70, .10)): y += g * np.sin(2 * np.pi * f * p * t + f) * np.exp(-t * d)
    y += fft_filt(rng.normal(size=n), 900, 9000) * np.exp(-t * 130) * 1.4
    k = int(.052 * SR); y[k:] += .35 * fft_filt(rng.normal(size=n), 1500, 8000)[:n - k] * np.exp(-t[:n - k] * 160)
    y += .9 * np.sin(2 * np.pi * np.cumsum(46 + 60 * np.exp(-t * 30)) / SR) * np.exp(-t * 6); return v * y
# ================= düzen
dry, wet = buf(), buf()
def both(x, t0, g, w, pan=0.0): add(dry, x, t0, g, pan); add(wet, x, t0, g * w, pan)
BT = .65
# taban uğultu
dr = np.zeros(N)
for f, g in ((hz(26), .9), (hz(38), .55), (hz(38) * 1.003, .4), (hz(45), .16), (hz(50), .10)): dr += g * np.sin(2 * np.pi * f * T + .25 * np.sin(2 * np.pi * .11 * T * (1 + g)) + g * 9)
de = ss(0, 3.5, T) * (.55 + .45 * ss(5.8, 13.8, T)) * (1 - ss(18.45, 18.75, T)) + .75 * ss(19.4, 22.2, T) * (1 - ss(26.0, 28.0, T))
dry += (dr * de * .12)[:, None]
air = fft_filt(rng.normal(size=(N, 2)), 180, 1300) * (.5 + .5 * np.sin(2 * np.pi * .09 * T + np.array([[0], [1.3]])).T) if False else fft_filt(rng.normal(size=(N, 2)), 180, 1300) * (.6 + .4 * np.sin(2 * np.pi * .09 * T))[:, None]
dry += air * (ss(0, 2.5, T) * (1 - ss(6.2, 9.0, T)) + .35 * ss(19.4, 21, T) * (1 - ss(26, 27.8, T)))[:, None] * .035
# taş fısıltısı: ışık yüzeyde gezerken kum taneleri
for _ in range(130):
    a = rng.uniform(.6, 5.6); n = int(.03 * SR); x = fft_filt(rng.normal(size=n), 2200, 9000) * np.exp(-np.arange(n) / SR * rng.uniform(120, 260)); both(x, a, rng.uniform(.012, .05) * ss(.4, 2, a), 1.5, rng.uniform(-.9, .9))
# giriş neyi
both(ney([(1.5, 1.25, D, .75), (2.75, .30, Eb, .6), (3.05, 1.25, D, .8), (4.30, .34, Fs, .65), (4.64, .30, Eb, .7), (4.94, .95, D, .65)]), 1.5, .34, 2.3, -.15)
for a, m, v in ((.9, 38, .5), (3.6, 45, .4), (5.0, 50, .35)): both(pluck2(hz(m), 4.0, bright=.35), a, .45 * v, 2.0)
# tutuşma
both(swell(1.35), 4.45, .34, 1.0)
both(boom(.55), 5.8, .42, .5)
for k, m in enumerate((86, 93, 98, 102)):
    n = int(4 * SR); t = np.arange(n) / SR; x = sum(g * np.sin(2 * np.pi * hz(m) * r * t) * np.exp(-t * d) for r, g, d in ((1, 1, 1.3), (2.76, .4, 2.6), (5.4, .18, 5))) * np.minimum(1, t / .004); both(x, 5.8 + k * .035, .05, 2.6, (-.6, .5, -.2, .7)[k])
# boya dalgası: koro + parıltı + kanun + davul
both(pad([50, 57, 62], 5.8, 14.9, 3.5, 1.2, .95), 5.8, .30, .9)
both(pad([54, 62, 66], 8.2, 14.9, 3.5, 1.0, .97), 8.2, .30, .9)
both(pad([69, 74], 10.8, 14.9, 3.0, .9, .98), 10.8, .26, .9)
SC = [74, 75, 78, 79, 81, 82, 84, 86, 87, 90, 91, 93, 94, 98]
for _ in range(330):
    a = 5.8 + 8.4 * rng.beta(2.3, 1.5); m = SC[rng.integers(len(SC))] + 12; n = int(.7 * SR); t = np.arange(n) / SR
    both(np.sin(2 * np.pi * hz(m) * t) * np.exp(-t * rng.uniform(6, 14)) * np.minimum(1, t / .003), a, rng.uniform(.004, .016), 2.4, rng.uniform(-1, 1))
mot = [50, 57, 62, 63, 66, 63, 62, 57]
g0 = 14.4 - 11 * BT
for b in range(11 * 2):                                   # sekizlikler, son 4 vuruşta onaltılık
    a = g0 + b * BT / 2; lv = .30 + .5 * (b / 22)
    both(pluck2(hz(mot[b % 8] + (12 if b >= 14 else 0)), 2.2, bright=.55), a, .34 * lv, 1.0, 0)
    if b >= 14: both(pluck2(hz(mot[(b * 3 + 2) % 8] + 24), 1.4, bright=.75), a + BT / 4, .22 * lv, 1.2)
pat = [(0, 'D'), (.5, 't'), (1.5, 't'), (2, 'D'), (3, 't'), (3.5, 't')]
for bar in range(2, 11, 4):
    for o, k in pat:
        a = g0 + (bar - 3 + o) * BT + BT; lv = .25 + .75 * ss(7.6, 14, a)
        if 7.5 < a < 14.35: both(dum(1.0) if k == 'D' else tek(.8, rng.uniform(.95, 1.08)), a, (.50 if k == 'D' else .26) * lv, .8, 0 if k == 'D' else rng.uniform(-.4, .4))
for k in range(8): both(tek(.8, 1.0 + .02 * k), 14.4 - (8 - k) * BT / 8, .10 + .035 * k, .9, (-1) ** k * .35)
both(swell(1.7, 1.0), 12.7, .40, .8)
# üç vuruş
for i, a in enumerate((14.4, 15.7, 17.0)):
    both(boom(1.0), a, .62, .45); both(dum(1.2), a, .60, .7); both(tek(1.0), a, .3, .9)
    for m, o in ((38, 0), (50, .0), ((62, 63, 66)[i], .0), ((69, 70, 74)[i], .02)): both(pluck2(hz(m), 3.0, bright=.6), a + o, .5, 1.1)
    for o, v in ((.325, .5), (.4875, .35), (.65, .7), (.975, .5), (1.1375, .4)): both(tek(.8) if v < .6 else dum(.6), a + o, .30 * v, .9, rng.uniform(-.4, .4))
    run = ([74, 75, 78, 79], [79, 78, 75, 74], [81, 82, 81, 78])[i]
    for k, m in enumerate(run): both(pluck2(hz(m), 1.6, bright=.7), a + .65 + k * .1625, .24, 1.2)
both(pad([38, 50, 57], 14.4, 18.7, .05, .25, .92), 14.4, .26, .6)
both(pad([62, 66], 17.0, 18.7, .3, .25, .96), 17.0, .26, .8)
both(swell(1.1, 1.0), 17.5, .34, .4)
# ışıklar
for a, v, p in ((19.4, .75, 1.0), (20.2, .8, 1.09), (21.4, 1.0, .88)):
    both(clunk(v, p), a, .46, 1.0, (-.35, .35, 0)[[19.4, 20.2, 21.4].index(a)])
    h = np.zeros(N); e = ss(a, a + .25, T) * (1 - ss(a + .6, a + 2.4, T)); h = (np.sin(2 * np.pi * 100 * T) + .5 * np.sin(2 * np.pi * 200 * T) + .25 * np.sin(2 * np.pi * 300 * T)) * e; dry += (h * .010)[:, None]
both(boom(1.0), 21.4, .50, .5)
# çözülme
both(pad([38, 50, 57, 62], 21.4, 28.0, 1.6, 3.4, .95), 21.4, .34, .8)
both(pad([66, 69, 74], 22.0, 28.0, 2.2, 3.2, .97), 22.0, .30, .9)
both(ney([(22.3, 1.5, A, .8), (23.8, .32, Bb, .65), (24.12, .8, A, .8), (24.92, .32, G, .65), (25.24, .40, Fs, .75), (25.64, .30, Eb, .65), (25.94, 1.5, D, .75)]), 22.3, .38, 2.2, .12)
for a, m, v in ((21.4, 38, .9), (21.4, 50, .8), (21.44, 57, .6), (21.48, 66, .55), (22.7, 62, .4), (23.35, 69, .4), (24.0, 66, .4), (24.65, 57, .4), (25.3, 62, .4), (25.94, 50, .6), (25.96, 57, .5), (25.98, 62, .5), (26.0, 66, .45)):
    both(pluck2(hz(m), 4.0, bright=.5), a, .40 * v, 1.2)
# ================= miks
mx = dry + .42 * reverb(wet)
mx = fft_filt(mx, 26, 15000, .12)
sil = 1 - .985 * ss(18.62, 18.80, T) * (1 - ss(19.36, 19.40, T))            # karanlık: nefes
mx *= sil[:, None]
mx *= (1 - ss(26.6, 28.0, T))[:, None] * ss(0, .4, T)[:, None]
pk = np.abs(mx).max(); mx = np.tanh(mx / pk * 1.7) / np.tanh(1.7) * .93
w = wave.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'test', 'ses.wav'), 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(mx, -1, 1) * 32767).astype('<i2').tobytes()); w.close()
# ölçüm
for a in np.arange(0, 28, 1.0):
    s = mx[int(a * SR):int((a + 1) * SR)]; print(f'{a:4.0f}s rms {20*np.log10(np.sqrt((s**2).mean())+1e-6):6.1f} dB  tepe {np.abs(s).max():.2f}')

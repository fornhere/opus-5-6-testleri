"""Filmin sesi: tamamı numpy ile sentez. Çıktı film/ses.wav (48 kHz stereo)."""
import numpy as np, wave, os
SR = 48000; DUR = 14.9; N = int(SR * DUR); rg = np.random.default_rng(5); T = np.arange(N) / SR
T1, T2, T3, T4 = 0.0, 56 / 24, 112 / 24, 172 / 24; W_OUT = (T4 + 1.95, T4 + 3.90); W_IN = (T4 + 4.35, T4 + 6.25); END = 348 / 24
def bp(x, lo, hi, sl=2):            # FFT bant süzgeci (yumuşak kenar)
    f = np.fft.rfftfreq(len(x), 1 / SR) + 1e-6; g = 1 / (1 + (lo / f) ** (2 * sl)) / (1 + (f / hi) ** (2 * sl)); return np.fft.irfft(np.fft.rfft(x) * g, len(x))
def pink(n):
    f = np.fft.rfftfreq(n, 1 / SR); s = rg.normal(size=len(f)) + 1j * rg.normal(size=len(f)); s /= np.sqrt(np.maximum(f, 20)); x = np.fft.irfft(s, n); return x / np.abs(x).max()
def env(pts): return np.interp(T, [p[0] for p in pts], [p[1] for p in pts])
def smooth(x, ms): k = int(SR * ms / 1000); w = np.hanning(k); w /= w.sum(); return np.convolve(x, w, 'same')
L = np.zeros(N); R = np.zeros(N); RV = np.zeros((2, N)); MU = np.zeros((2, N))
def put(buf, sig, t, pan=0.0, g=1.0):
    i = int(t * SR); n = min(len(sig), N - i)
    if n <= 0 or i < 0: return
    buf[0, i:i + n] += sig[:n] * g * np.cos((pan + 1) * np.pi / 4); buf[1, i:i + n] += sig[:n] * g * np.sin((pan + 1) * np.pi / 4)
# ---- keçeli piyano
def piano(f, d=4.0, v=1.0):
    n = int(SR * d); t = np.arange(n) / SR; y = np.zeros(n); B = .00035
    for k in range(1, 11):
        fk = f * k * np.sqrt(1 + B * k * k)
        if fk > 9000: break
        a = (1 / k ** 1.55) * np.exp(-((k - 1) / (3.2 + 3.5 * v)) ** 1.3); dec = np.exp(-t * (.55 + .32 * k) * (f / 260) ** .35)
        y += a * dec * (np.sin(2 * np.pi * fk * t + rg.uniform(0, 6)) + .55 * np.sin(2 * np.pi * fk * 1.0007 * t + rg.uniform(0, 6)))
    th = bp(rg.normal(size=n), 90, 700) * np.exp(-t * 55) * .9; y = y * (1 - np.exp(-t * 320)) + th * .35 * v
    return y * np.minimum(1, (d - t) / .4) * v * .22
def pad(notes, t0, t1, g, br=900):
    n = int(SR * (t1 - t0)); t = np.arange(n) / SR; e = np.minimum(1, t / ((t1 - t0) * .38)) * np.minimum(1, (t1 - t0 - t) / ((t1 - t0) * .30)); e = np.clip(e, 0, 1) ** 1.4
    for c in (0, 1):
        y = np.zeros(n)
        for f in notes:
            for dt in (-.0035, 0, .0031):
                ph = rg.uniform(0, 6.28); y += np.sin(2 * np.pi * f * (1 + dt) * t + ph + .25 * np.sin(2 * np.pi * .21 * t + c)) + .30 * np.sin(4 * np.pi * f * (1 + dt) * t + ph) + .10 * np.sin(6 * np.pi * f * (1 + dt) * t)
        i = int(t0 * SR); m = min(n, N - i); MU[c, i:i + m] += bp(y, 60, br)[:m] * e[:m] * g
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
pad([hz(m) for m in (38, 50, 57, 64)], 0.0, 3.4, .020); pad([hz(m) for m in (43, 50, 59, 66)], 2.3, 5.6, .022); pad([hz(m) for m in (40, 52, 59, 67)], 4.5, 7.4, .024, 1100)
pad([hz(m) for m in (38, 50, 57, 62, 66, 69)], 6.0, 10.2, .026, 1700); pad([hz(m) for m in (35, 47)], 9.0, 12.4, .034, 320); pad([hz(m) for m in (43, 50, 59, 62, 66)], 11.6, 14.9, .026, 1500); pad([hz(m) for m in (38, 50, 57, 66, 69)], 13.0, 14.9, .018, 1800)
for (t, m, v) in ((.55, 69, .42), (1.45, 66, .36), (T2 + .05, 71, .45), (T2 + .95, 74, .40), (T2 + 1.7, 69, .34), (T3 + .10, 64, .42), (T3 + .75, 67, .46), (T3 + 1.35, 71, .56), (T3 + 1.85, 74, .62),
                  (T4, 38, .85), (T4, 50, .7), (T4 + .02, 66, .72), (T4 + .05, 74, .78), (T4 + .62, 78, .55), (T4 + 1.2, 76, .5), (T4 + 1.75, 74, .42),
                  (W_IN[0] + .95, 67, .42), (W_IN[0] + 1.3, 71, .50), (W_IN[0] + 1.62, 74, .58), (13.35, 38, .75), (13.37, 57, .55), (13.39, 66, .62), (13.42, 74, .7), (13.9, 81, .34)):
    put(MU, piano(hz(m), 4.2, v), t, pan=(m - 62) / 34)
# tarama sırasında müzik boğulur, sonra açılır
lp = np.stack([bp(MU[c], 30, 420, 1) for c in (0, 1)]); k = smooth(env([(0, 0), (W_OUT[0], 0), (W_OUT[0] + 1.5, 1), (W_IN[0] + .2, 1), (W_IN[1] - .5, 0), (15, 0)]), 200); MU = MU * (1 - k) + lp * k * .9
# ---- cam / kaşık tınısı (kipsel sentez)
def ting(f0, d=1.8, hard=1.0):
    n = int(SR * d); t = np.arange(n) / SR; y = np.zeros(n)
    for r, a, q in ((1, 1, 3.2), (1.006, .5, 3.0), (2.32, .62, 4.6), (4.25, .38, 7.5), (6.63, .22, 12), (9.38, .12, 19)):
        if f0 * r < 18000: y += a * np.exp(-t * q * 1.25) * np.sin(2 * np.pi * f0 * r * t + rg.uniform(0, 6))
    return (y * (1 - np.exp(-t * 2600)) + hard * .5 * bp(rg.normal(size=n), 3000, 12000) * np.exp(-t * 420)) * .10
for (t, f, g, p) in ((T2 + .22, 2480, .50, .25), (T2 + .40, 2510, .26, .3), (T3 + .5, 2440, .14, .1), (13.62, 2480, .46, .15), (13.80, 2525, .20, .2)): put(RV, ting(f), t, p, g * .5); put(MU, ting(f), t, p, g * .6)
# ---- şeker çıtırtısı
for _ in range(95):
    t = rg.uniform(.1, 2.2); n = int(SR * rg.uniform(.004, .013)); c = bp(rg.normal(size=n + 400), rg.uniform(2500, 5000), rg.uniform(8000, 14000))[:n] * np.exp(-np.arange(n) / n * 5); put(MU, c, t, rg.uniform(-.5, .6), .035 * rg.uniform(.2, 1) ** 2)
# ---- oda tonu
for c in (0, 1):
    MU[c] += bp(pink(N), 60, 700, 1) * .020 * env([(0, 0), (.5, 1), (W_OUT[0] + .5, 1), (W_OUT[1], .12), (W_IN[0] + .6, .12), (W_IN[1], 1), (END, 1), (DUR, 0)]); MU[c] += bp(pink(N), 1500, 6000, 1) * .010 * env([(0, 0), (.5, .7), (T3, .7), (T3 + 1.6, 1.2), (W_OUT[0], 1), (W_OUT[1], 0), (W_IN[0] + 1, 0), (W_IN[1], 1), (END, .8), (DUR, 0)])
# ---- güneş kabarması
for c in (0, 1): MU[c] += bp(pink(N), 200, 2600, 1) * .05 * smooth(env([(0, 0), (T3 + .4, 0), (T3 + 2.35, 1), (T4 + .12, 0), (15, 0)]) ** 2, 60)
# ---- tarama süpürmesi
def sweep(t0, t1, up):
    n = int(SR * (t1 - t0)); t = np.arange(n) / n; e = np.sin(np.pi * np.clip(t, 0, 1)) ** 1.3; out = np.zeros((2, n)); x = [rg.normal(size=n) for _ in (0, 1)]; B = 40; hop = n // B
    for b in range(B):
        i0 = max(0, b * hop - hop); i1 = min(n, b * hop + 2 * hop); w = np.hanning(i1 - i0); u = (b + .5) / B; u = u if up else 1 - u; fc = 220 * (26 ** u)
        for c in (0, 1): out[c, i0:i1] += bp(x[c][i0:i1], fc * .62, fc * 1.6) * w
    out *= e; pan = np.linspace(-.55, .55, n) * (1 if up else -1); out[0] *= np.cos((pan + 1) * np.pi / 4); out[1] *= np.sin((pan + 1) * np.pi / 4); return out / np.abs(out).max()
def add2(sig, t, g): i = int(t * SR); n = min(sig.shape[1], N - i); MU[:, i:i + n] += sig[:, :n] * g; RV[:, i:i + n] += sig[:, :n] * g * .5
add2(sweep(W_OUT[0] - .1, W_OUT[1], True), W_OUT[0] - .1, .16); add2(sweep(W_IN[0], W_IN[1] + .1, False), W_IN[0], .16)
for _ in range(150):      # dalga kenarındaki kıvılcım
    t = rg.choice([rg.uniform(W_OUT[0] + .35, W_OUT[1] - .2), rg.uniform(W_IN[0] + .25, W_IN[1] - .3)]); n = int(SR * .05); f = rg.uniform(2600, 8200); s = np.sin(2 * np.pi * f * np.arange(n) / SR) * np.exp(-np.arange(n) / SR * rg.uniform(90, 200)); put(RV, s, t, rg.uniform(-.8, .8), .010 * rg.uniform(.2, 1)); put(MU, s, t, rg.uniform(-.8, .8), .008 * rg.uniform(.2, 1))
sub = np.sin(2 * np.pi * np.cumsum(env([(0, 52), (W_OUT[0] + 1.35, 52), (W_OUT[0] + 2.6, 34), (15, 34)])) / SR) * smooth(env([(0, 0), (W_OUT[0] + 1.30, 0), (W_OUT[0] + 1.36, 1), (W_OUT[0] + 2.7, 0), (15, 0)]), 12); MU += sub * .16
# ---- yankı
def rev(x, rt=2.4, seed=1):
    r = np.random.default_rng(seed); n = int(SR * rt * 1.1); t = np.arange(n) / SR; h = r.normal(size=n) * np.exp(-6.9 * t / rt) * (1 - np.exp(-t * 60)); h = bp(h, 180, 5200, 1); h /= np.sqrt((h ** 2).sum()); m = len(x) + n; return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(h, m), m)[:len(x)]
OUT = np.stack([MU[c] + .34 * rev(MU[c], 2.4, 11 + c) + .8 * rev(RV[c], 2.0, 21 + c) for c in (0, 1)])
OUT *= env([(0, 0), (.25, 1), (END - .7, 1), (END + .15, 0), (DUR, 0)])
OUT = OUT / np.abs(OUT).max(); OUT = np.tanh(OUT * 1.7) / np.tanh(1.7) * .84
OUT = OUT[:, :int(SR * END)]; pcm = (OUT.T * 32767).astype('<i2'); os.makedirs('film', exist_ok=True)
w = wave.open('film/ses.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close(); print('ses', OUT.shape[1] / SR, 'sn')

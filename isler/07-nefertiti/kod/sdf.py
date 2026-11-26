"""Küçük SDF kitaplığı (numpy). Koordinatlar: x = heykelin solu, f = öne, z = yukarı, birim cm."""
import numpy as np
F = np.float32

def smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25

def smax(a, b, k):
    return -smin(-a, -b, k)

def ell(x, f, z, c, r):
    px, pf, pz = x - c[0], f - c[1], z - c[2]
    k0 = np.sqrt((px / r[0])**2 + (pf / r[1])**2 + (pz / r[2])**2)
    k1 = np.sqrt((px / r[0]**2)**2 + (pf / r[1]**2)**2 + (pz / r[2]**2)**2) + 1e-6
    return k0 * (k0 - 1.0) / k1

def ell_yaw(x, f, z, c, r, yaw):
    """x-f düzleminde döndürülmüş elipsoit (yaw radyan; + => dış taraf geriye)."""
    px, pf, pz = x - c[0], f - c[1], z - c[2]
    ca, sa = np.cos(yaw), np.sin(yaw)
    u = px * ca - pf * sa
    v = px * sa + pf * ca
    return ell(u, v, pz, (0, 0, 0), r)

def cap(x, f, z, a, b, r1, r2=None):
    if r2 is None: r2 = r1
    a = np.asarray(a, F); b = np.asarray(b, F)
    ba = b - a
    px, pf, pz = x - a[0], f - a[1], z - a[2]
    h = np.clip((px * ba[0] + pf * ba[1] + pz * ba[2]) / float(ba @ ba), 0, 1)
    d = np.sqrt((px - ba[0] * h)**2 + (pf - ba[1] * h)**2 + (pz - ba[2] * h)**2)
    return d - (r1 + (r2 - r1) * h)

def chain(x, f, z, pts, rs, k=0.0):
    d = None
    for i in range(len(pts) - 1):
        e = cap(x, f, z, pts[i], pts[i + 1], rs[i], rs[i + 1])
        d = e if d is None else (smin(d, e, k) if k > 0 else np.minimum(d, e))
    return d

class Spline:
    """Doğal kübik eğri -> sık tablo -> np.interp."""
    def __init__(self, xs, ys, n=4000):
        xs = np.asarray(xs, float); ys = np.asarray(ys, float)
        o = np.argsort(xs); xs, ys = xs[o], ys[o]
        # pchip benzeri (aşım yapmayan) teğetler
        h = np.diff(xs); dl = np.diff(ys) / h
        m = np.zeros_like(xs)
        m[0], m[-1] = dl[0], dl[-1]
        for i in range(1, len(xs) - 1):
            if dl[i - 1] * dl[i] > 0:
                w1 = 2 * h[i] + h[i - 1]; w2 = h[i] + 2 * h[i - 1]
                m[i] = (w1 + w2) / (w1 / dl[i - 1] + w2 / dl[i])
        X = np.linspace(xs[0], xs[-1], n)
        i = np.clip(np.searchsorted(xs, X) - 1, 0, len(xs) - 2)
        t = (X - xs[i]) / h[i]
        Y = ((2*t**3 - 3*t**2 + 1) * ys[i] + (t**3 - 2*t**2 + t) * h[i] * m[i]
             + (-2*t**3 + 3*t**2) * ys[i + 1] + (t**3 - t**2) * h[i] * m[i + 1])
        # hafif yumuşatma
        ker = np.hanning(max(3, n // 40) | 1); ker /= ker.sum()
        p = len(ker) // 2
        Yp = np.concatenate([2*Y[0] - Y[p:0:-1], Y, 2*Y[-1] - Y[-2:-p-2:-1]])
        self.X, self.Y = X.astype(F), np.convolve(Yp, ker, 'valid').astype(F)
    def __call__(self, v):
        return np.interp(v, self.X, self.Y).astype(F)

def gauss(u, v=0.0):
    return np.exp(-(u * u + v * v))

# ---------- gürültü ----------
def _hash(i, j, k, seed):
    n = (i.astype(np.int64) * 374761393 + j.astype(np.int64) * 668265263
         + k.astype(np.int64) * 2147483647 + seed * 1274126177) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n = ((n ^ (n >> 16)) * 2246822519) & 0xFFFFFFFF
    return ((n ^ (n >> 15)) & 0xFFFF).astype(F) / 65535.0

def vnoise(x, y, z, seed=0):
    xi, yi, zi = np.floor(x), np.floor(y), np.floor(z)
    fx, fy, fz = (x - xi).astype(F), (y - yi).astype(F), (z - zi).astype(F)
    xi, yi, zi = xi.astype(np.int64), yi.astype(np.int64), zi.astype(np.int64)
    u = fx**3 * (fx * (fx * 6 - 15) + 10); v = fy**3 * (fy * (fy * 6 - 15) + 10); w = fz**3 * (fz * (fz * 6 - 15) + 10)
    def H(a, b, c): return _hash(xi + a, yi + b, zi + c, seed)
    x00 = H(0,0,0) * (1-u) + H(1,0,0) * u
    x10 = H(0,1,0) * (1-u) + H(1,1,0) * u
    x01 = H(0,0,1) * (1-u) + H(1,0,1) * u
    x11 = H(0,1,1) * (1-u) + H(1,1,1) * u
    return ((x00 * (1-v) + x10 * v) * (1-w) + (x01 * (1-v) + x11 * v) * w) * 2 - 1

def fbm(x, y, z, oct=4, seed=0, gain=0.5):
    a, s, n = 1.0, 0.0, 0.0
    fr = 1.0
    for o in range(oct):
        s = s + a * vnoise(x * fr, y * fr, z * fr, seed + o * 17)
        n += a; a *= gain; fr *= 2.03
    return s / n

# ---------- örgü çıkarma (OpenVDB, Blender ile gelir) ----------
def mesh(fn, lo, hi, vox, T=48, threads=8, verbose=''):
    import openvdb as vdb, time
    from concurrent.futures import ThreadPoolExecutor
    t0 = time.time()
    lo = np.asarray(lo, float); hi = np.asarray(hi, float)
    n = np.ceil((hi - lo) / (vox * T)).astype(int)
    st = 6
    bg = 6 * vox
    grid = vdb.FloatGrid(float(bg))
    cs = np.arange(0, T + 1, st) * vox
    act, ins = [], []
    for i in range(n[0]):
        # bir dilim karo birden
        X0 = lo + np.array([i, 0, 0]) * vox * T
        ox = lo[0] + i * T * vox + cs
        of = lo[1] + np.arange(0, n[1] * T + 1, st) * vox
        oz = lo[2] + np.arange(0, n[2] * T + 1, st) * vox
        gx, gf, gz = np.meshgrid(ox.astype(F), of.astype(F), oz.astype(F), indexing='ij')
        d = fn(gx, gf, gz)
        q = T // st
        for j in range(n[1]):
            for k in range(n[2]):
                s = d[:, j*q:j*q+q+1, k*q:k*q+q+1]
                if s.min() < st * vox * 1.8 and s.max() > -st * vox * 1.8:
                    act.append((i, j, k))
                elif s.max() < 0:
                    ins.append((i, j, k))
    def ev(t):
        o = lo + np.array(t) * T * vox
        a = [(o[m] + np.arange(T) * vox).astype(F) for m in range(3)]
        gx, gf, gz = np.meshgrid(*a, indexing='ij')
        return t, np.clip(fn(gx, gf, gz), -bg, bg).astype(F)
    for t in ins:
        a = np.array(t) * T
        grid.fill(tuple(int(v) for v in a), tuple(int(v) for v in a + T - 1), -float(bg), False)
    with ThreadPoolExecutor(threads) as ex:
        for t, arr in ex.map(ev, act):
            grid.copyFromArray(arr, ijk=tuple(int(v) * T for v in t))
    pts, quads = grid.convertToQuads(0.0)
    pts = pts.astype(np.float64) * vox + lo
    print(f'[mesh {verbose}] karo={len(act)} nokta={len(pts)} yuz={len(quads)} {time.time()-t0:.1f}s', flush=True)
    return pts.astype(F), quads

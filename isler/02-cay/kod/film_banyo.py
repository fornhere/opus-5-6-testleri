"""Final kareler: zamansal süzgeç (yalnız gürültü seviyesindeki farkta) -> 1080p Lanczos -> objektif + gren + makine eğrisi."""
import bpy, sys, os, glob, numpy as np
arg = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:])
D = arg['dir']; O = arg['out']; os.makedirs(O, exist_ok=True); pi, pn = (int(v) for v in arg.get('part', '0/1').split('/'))
EV = float(arg.get('ev', -1.8)); GREN = float(arg.get('gren', .5)); WB = np.array([1.03, .992, .965], np.float32); W2, H2 = 1920, 1080; S = W2 / 2000
TS = float(arg.get('ts', .030)); only = [x for x in arg.get('only', '').split(',') if x]
def load(f):
    im = bpy.data.images.load(f); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); bpy.data.images.remove(im); return a.reshape(h, w, 4)[..., :3].copy()
def blur(x, s):
    p = int(3 * s) + 1; y = np.pad(x, ((p, p), (p, p), (0, 0)), 'reflect'); fy = np.fft.fftfreq(y.shape[0])[:, None]; fx = np.fft.rfftfreq(y.shape[1])[None]
    k = np.exp(-2 * (np.pi * s) ** 2 * (fx ** 2 + fy ** 2))[..., None].astype(np.float32); return np.fft.irfft2(np.fft.rfft2(y, axes=(0, 1)) * k, s=y.shape[:2], axes=(0, 1))[p:-p, p:-p].astype(np.float32)
def box3(x):
    y = np.pad(x, ((2, 2), (2, 2)), 'edge'); c = y.cumsum(0); y = (c[4:] - np.concatenate([np.zeros((1, c.shape[1]), c.dtype), c[:-5]])) ; c = y.cumsum(1); return (c[:, 4:] - np.concatenate([np.zeros((c.shape[0], 1), c.dtype), c[:, :-5]], 1)) / 25
def lanc(n, m):
    s = n / m; M = np.zeros((m, n), np.float32)
    for i in range(m):
        c = (i + .5) * s - .5; l = int(np.floor(c)) - 2
        for j in range(l, l + 6):
            t = c - j; w = 1.0 if abs(t) < 1e-9 else (np.sinc(t) * np.sinc(t / 3) if abs(t) < 3 else 0); M[i, min(max(j, 0), n - 1)] += w
    return M / M.sum(1, keepdims=True)
yy, xx = np.mgrid[0:H2, 0:W2].astype(np.float32); u = (xx - W2 / 2) / (H2 / 2); v = (yy - H2 / 2) / (H2 / 2); r2 = u * u + v * v
def warp(c, k):
    X = np.clip((u * (1 + k * r2)) * H2 / 2 + W2 / 2, 0, W2 - 1.001); Y = np.clip((v * (1 + k * r2)) * H2 / 2 + H2 / 2, 0, H2 - 1.001); x0 = X.astype(int); y0 = Y.astype(int); fx = X - x0; fy = Y - y0
    return (c[y0, x0] * (1 - fx) + c[y0, x0 + 1] * fx) * (1 - fy) + (c[y0 + 1, x0] * (1 - fx) + c[y0 + 1, x0 + 1] * fx) * fy
def develop(a, seed):
    a = a * 2 ** EV
    hm = np.clip(a.mean(-1, keepdims=True) - 1.2, 0, 3); a = a + np.clip(blur(hm, 1.6 * S) - hm, 0, None) * np.array([.10, .015, .16], np.float32)
    hi = np.minimum(a, 12); a = a * .955 + blur(hi, 2.2 * S) * .022 + blur(hi, 14 * S) * .013 + blur(hi, 70 * S) * .010
    a = a * (1 / (1 + .03 * r2) ** 2)[..., None]
    a[..., 0] = warp(a[..., 0], .0006); a[..., 2] = warp(a[..., 2], -.0006)
    rg = np.random.default_rng(seed); Lm = np.maximum(a, 1e-5); n = rg.normal(size=a.shape).astype(np.float32); nl = rg.normal(size=a.shape[:2] + (1,)).astype(np.float32)
    n = .62 * n + .78 * blur(n, .75) * 2.1; nl = .5 * nl + blur(nl, .8) * 1.6; a = np.maximum(a + np.sqrt(Lm * .0011 + .0000045) * GREN * (.45 * n + .75 * nl), 0)
    a = a * WB; cr = np.array([[.93, .05, .02], [.03, .93, .04], [.02, .06, .92]], np.float32); a = a @ cr.T
    x = np.maximum(a, 0) * .92; t = (x * (2.40 * x + .05)) / (x * (2.30 * x + .62) + .13); t = np.clip(t * 1.035, 0, 1)
    d = np.where(t <= .0031308, 12.92 * t, 1.055 * np.power(np.maximum(t, 1e-8), 1 / 2.4) - .055); d = d + (d - blur(d, 1.1 * S)) * .30
    return np.clip(d + rg.uniform(-.5, .5, d.shape) / 255, 0, 1)
MY, MX = lanc(900, H2), lanc(1600, W2); idx = 0; k5 = (-2, -1, 0, 1, 2)
for shot in arg.get('shots', '1234'):
    fs = [f for f in sorted(glob.glob(f'{D}/s{shot}_*.exr')) if '.tmp.' not in f]; n = len(fs); cache = {}
    a0, a1 = n * pi // pn, n * (pi + 1) // pn
    for i in range(a0, a1):
        o = f'{O}/s{shot}_{i:04d}.png'
        if (only and f's{shot}_{i:04d}' not in only) or (os.path.exists(o) and not only): continue
        for k in [k for k in cache if k < i - 2]: del cache[k]
        for k in k5:
            if 0 <= i + k < n and i + k not in cache: cache[i + k] = load(fs[i + k])
        c = cache[i]; num = c.copy(); den = np.ones(c.shape[:2] + (1,), np.float32); lc = np.log(c.mean(-1) + .01)
        for k in k5:
            if k and 0 <= i + k < n:
                b = cache[i + k]; d = np.abs(np.log(b.mean(-1) + .01) - lc); d = np.maximum(box3(d) * .9, d * .55); w = (np.exp(-(d / TS) ** 2) * (.8 if abs(k) == 1 else .5)).astype(np.float32)[..., None]; num += b * w; den += w
        a = num / den; a = np.tensordot(MY, a, (1, 0)); a = np.tensordot(a, MX, (1, 1)).transpose(0, 2, 1); a = np.maximum(a, 0)
        d = develop(a.astype(np.float32), int(shot) * 1000 + i)
        im = bpy.data.images.new('o', W2, H2); px = np.ones((H2, W2, 4), np.float32); px[..., :3] = d; im.pixels.foreach_set(px.ravel()); im.filepath_raw = os.path.abspath(o); im.file_format = 'PNG'; im.save(); bpy.data.images.remove(im)
print('FILM BANYO BITTI', pi)

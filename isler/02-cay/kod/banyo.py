"""Karanlık oda: EXR -> bloom, vinyet, CA, gren, AgX -> PNG. Yalnız numpy."""
import bpy, sys, os, numpy as np
arg = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:])
src, dst = os.path.abspath(arg['in']), os.path.abspath(arg['out']); ev = float(arg.get('ev', 0)); gren = float(arg.get('gren', 1)); raw = int(arg.get('raw', 0))
im = bpy.data.images.load(src); w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); a = a.reshape(h, w, 4)[..., :3] * 2 ** ev
def blur(x, s):
    fy = np.fft.fftfreq(x.shape[0] + 2 * int(3 * s))[:, None]; fx = np.fft.rfftfreq(x.shape[1] + 2 * int(3 * s))[None]
    p = int(3 * s); y = np.pad(x, ((p, p), (p, p), (0, 0)), 'reflect' if p < min(x.shape[:2]) else 'edge'); k = np.exp(-2 * (np.pi * s) ** 2 * (fx ** 2 + fy ** 2))[..., None]
    r = np.fft.irfft2(np.fft.rfft2(y, axes=(0, 1)) * k, s=y.shape[:2], axes=(0, 1)); return r[p:-p, p:-p].astype(np.float32)
S = w / 1500
if not raw:
    hi = np.minimum(a, 12)
    hm = np.clip(a.mean(-1, keepdims=True) - 1.2, 0, 3); a = a + np.clip(blur(hm, 1.6 * S) - hm, 0, None) * np.array([.10, .015, .16], np.float32)      # boyuna renk saçağı
    a = a * .955 + blur(hi, 2.2 * S) * .022 + blur(hi, 14 * S) * .013 + blur(hi, 90 * S) * .010          # lens saçılması
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); u = (xx - w / 2) / (h / 2); v = (yy - h / 2) / (h / 2); r2 = u * u + v * v
    a = a * (1 / (1 + .03 * r2) ** 2)[..., None]
    def warp(c, k):
        X = np.clip((u * (1 + k * r2)) * h / 2 + w / 2, 0, w - 1.001); Y = np.clip((v * (1 + k * r2)) * h / 2 + h / 2, 0, h - 1.001); x0 = X.astype(int); y0 = Y.astype(int); fx = X - x0; fy = Y - y0
        return (c[y0, x0] * (1 - fx) + c[y0, x0 + 1] * fx) * (1 - fy) + (c[y0 + 1, x0] * (1 - fx) + c[y0 + 1, x0 + 1] * fx) * fy
    a[..., 0] = warp(a[..., 0], .0010); a[..., 2] = warp(a[..., 2], -.0010)
    if gren:
        rg = np.random.default_rng(3); L = np.maximum(a, 1e-5)
        n = rg.normal(size=a.shape).astype(np.float32); nl = rg.normal(size=a.shape[:2] + (1,)).astype(np.float32)
        n = .62 * n + .78 * blur(n, .75 * max(S, .6)) * 2.1; nl = .5 * nl + blur(nl, .8 * max(S, .6)) * 1.6
        sg = np.sqrt(L * .0011 + .0000045) * gren
        a = np.maximum(a + sg * (.45 * n + .75 * nl), 0)
# makine JPEG eğrisi: kanal başına S, sert kırpan parlaklar, hafif kanal sızması
wb = np.array([float(v) for v in arg.get('wb', '1.0,1.0,1.0').split(',')], np.float32); a = a * wb
cr = np.array([[.93, .05, .02], [.03, .93, .04], [.02, .06, .92]], np.float32); a = a @ cr.T
x = np.maximum(a, 0) * float(arg.get('k', .92)); t = (x * (2.40 * x + .05)) / (x * (2.30 * x + .62) + .13)
t = np.clip(t * 1.035, 0, 1); d = np.where(t <= .0031308, 12.92 * t, 1.055 * np.power(np.maximum(t, 1e-8), 1 / 2.4) - .055)
L_ = d.mean(-1, keepdims=True); d = np.clip(L_ + (d - L_) * float(arg.get('sat', 1.0)), 0, 1)
d = d + (d - blur(d, 1.1 * S)) * float(arg.get('kes', .35))                                  # makine içi keskinleştirme
d = np.clip(d + (np.random.default_rng(9).uniform(-.5, .5, d.shape) / 255), 0, 1)
o = bpy.data.images.new('o', w, h); b = np.ones((h, w, 4), np.float32); b[..., :3] = d; o.pixels.foreach_set(b.ravel()); o.filepath_raw = dst; o.file_format = 'PNG'; o.save()

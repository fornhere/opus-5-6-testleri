"""Boyalar: hepsi burada sayısal olarak çizilir (indirilmiş doku yok)."""
import numpy as np
import geo
from sdf import *

def C(r, g, b): return np.array([r, g, b], F) / 255.0
def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return (t * t * (3 - 2 * t)).astype(F)
def mix(img, col, a):
    a = np.clip(a, 0, 1)[..., None]
    return img * (1 - a) + col * a
def _par(fn, H):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(6) as ex: list(ex.map(fn, range(0, H, 96)))
def ink(d, w=.018):        # d<0 içerisi
    return ss(w, -w, d)
def rbox(x, y, hx, hy, r):
    qx, qy = np.abs(x) - hx + r, np.abs(y) - hy + r
    return np.minimum(np.maximum(qx, qy), 0) + np.sqrt(np.maximum(qx, 0)**2 + np.maximum(qy, 0)**2) - r

RED = C(146, 74, 50); BLUE = C(84, 102, 106); GREEN = C(124, 130, 90); TAN = C(194, 160, 110); PLASTER = C(220, 201, 168)
GOLD = C(196, 165, 112); GOLDL = C(216, 193, 148); LINE = C(128, 66, 42)

# ------------------------------------------------ YÜZ (ön izdüşüm)  x[-8,8]  z[16,34]
def face_all(ppc=150):
    n = 23; H = int(11.5 * ppc); ed = [H * i // n for i in range(n + 1)]
    R = [face(ppc, ed[i], ed[i + 1]) for i in range(n)]
    return np.concatenate([r[0] for r in R]), np.concatenate([r[1] for r in R])
def face(ppc, h0, h1):
    W, H = 12 * ppc, h1 - h0
    x = (np.arange(W) + .5) / ppc - 6; z = (np.arange(h0, h1) + .5) / ppc + 19
    X, Z = np.meshgrid(x.astype(F), z.astype(F))
    ax = np.abs(X)
    img = np.zeros((H, W, 3), F); al = np.zeros((H, W), F)
    nz = fbm(X * 3, Z * 3, 0 * X, 4, 101); nf = fbm(X * 16, Z * 16, 0 * X, 3, 102)
    def lay(col, a):
        nonlocal img, al
        a = np.clip(a, 0, 1)
        out = a + al * (1 - a)
        img[...] = np.where(out[..., None] > 1e-4, (col * a[..., None] + img * (al * (1 - a))[..., None]) / np.maximum(out, 1e-4)[..., None], img)
        al = out
    blk = C(34, 29, 27)
    # --- kaş
    s = np.clip((ax - .88) / (5.45 - .88), 0, 1)
    top = Spline([0, .12, .3, .5, .7, .85, 1], [29.16, 29.50, 29.93, 30.05, 29.74, 29.18, 28.44])(s)
    bot = Spline([0, .12, .3, .5, .7, .85, 1], [28.56, 28.80, 29.24, 29.44, 29.27, 28.90, 28.36])(s)
    mid, h = (top + bot) / 2, (top - bot) / 2
    d = np.abs(Z - mid) - h
    endin = np.sqrt(np.maximum(.88 + .26 - ax, 0)**2 + np.maximum(np.abs(Z - 28.93) - .06, 0)**2) - .28
    d = np.where(ax < 1.10, np.maximum(d, np.maximum(.86 - ax, endin * .9)), d)
    d = np.maximum(d, ax - 5.45)
    a = ink(d + .02 * nf, .025)
    wear = ss(.25, .95, nz + .35 * nf)
    lay(C(58, 48, 41), a * (1 - .40 * wear * ss(.0, .2, -d + .1)) * (1 - .45 * ss(.80, 1.0, s)))
    # --- göz
    up, lo = geo.eye_curves(ax)
    ad = geo.almond(ax, Z)
    n2 = fbm(X * 9, Z * 9, 0 * X, 3, 103)
    # göz akı
    sc = np.empty((H, W, 3), F); sc[...] = C(134, 118, 97)
    sc = mix(sc, C(104, 90, 73), .5 * ss(-.1, .6, n2)); sc = mix(sc, C(88, 76, 62), .55 * ss(26.75, 27.1, Z))
    red = np.maximum(gauss((ax - 1.85) / .22, (Z - 26.45) / .2), .7 * gauss((ax - 4.5) / .2, (Z - 26.8) / .2))
    sc = mix(sc, C(140, 74, 54), .55 * red)
    ir = np.sqrt((ax - 3.02)**2 + (Z - 26.90)**2)
    sc = np.where((X < 0)[..., None], mix(mix(sc, C(40, 28, 22), ink(ir - .66, .016)), C(18, 14, 12), ink(ir - .50, .08)), sc)
    lay(sc, ink(ad + .02, .012))
    # sürme
    s_ = np.clip((ax - geo.EX0) / 3.1, 0, 1)
    upper = .10 + .062 * ss(-.06, .22, Z - (up + lo) * .5) * ss(geo.EX0 - .05, geo.EX0 + .6, ax)
    k = np.maximum(ad - upper * (1 - .0 * s_), -(ad + .035))
    inr = cap(ax, Z, 0 * ax, (1.86, 26.48, 0), (1.47, 26.35, 0), .10, .012)
    ext = cap(ax, Z, 0 * ax, (4.60, 26.86, 0), (5.60, 26.76, 0), .10, .015)
    k = smin(k, ext, .06)
    kw = ss(.45, .7, nz + .5 * nf)
    k = smin(k, inr, .10)
    lay(blk, ink(k + .005 * nf, .011) * (1 - .12 * kw) * (1 - .55 * ss(4.8, 5.6, ax)))
    # --- dudak
    zm, zu, zl = geo.mouth_curves(ax)
    ld = np.maximum(np.maximum(Z - zu, zl - Z) * .9, ax - geo.LW)
    lip = np.empty((H, W, 3), F); lip[...] = C(122, 62, 48)
    lip = mix(lip, C(138, 78, 62), .55 * ss(-.2, .7, nz)); lip = mix(lip, C(86, 42, 33), .75 * gauss((Z - zm) / .10))
    lay(lip, ink(ld + .01 * nf, .02) * .95)
    lay(C(88, 40, 30), .55 * ink(np.abs(ld) - .018, .016) * (ax < 2.5))
    # --- küçük dökülmeler
    sp = fbm(X * 11, Z * 11, 0 * X, 2, 105); reg = fbm(X * .9, Z * .9, 0 * X, 2, 106)
    m = ss(.84, .90, sp + .36 * reg) * (ax < 6) * .8 * (1 - ink(ad - .25, .05)) * (1 - ink(ld - .05, .05)) * (Z < 26)
    lay(C(224, 192, 152), m * .85)
    return img, al

# ------------------------------------------------ TAÇ (theta, t)
def crown(W=6144, H=2304, t0=-.04, t1=1.02):
    th = ((np.arange(W) + .5) / W * 2 - 1) * np.pi
    t = t0 + (np.arange(H) + .5) / H * (t1 - t0)
    img = np.empty((H, W, 3), F); hgt = np.zeros((H, W), F); rgh = np.full((H, W), .62, F)
    def _row(a):
        TH, T = np.meshgrid(th.astype(F), t[a:a + 96].astype(F))
        Rr = 6.6 + 5.4 * np.clip(T, 0, 1)
        # dikişsiz gürültü koordinatları
        cx, cy = np.cos(TH) * Rr, np.sin(TH) * Rr
        Zs = T * 22.0
        b = geo.blue_sd(TH, T)
        n_l = fbm(cx * .35, cy * .35, Zs * .5, 4, 201)
        n_m = fbm(cx * 1.6, cy * 1.6, Zs * 2.2, 3, 202)
        st = fbm(cx * .9, cy * .9, Zs * 5.0, 4, 203)          # yatay fırça
        st2 = fbm(cx * 2.2, cy * 2.2, Zs * 13.0, 3, 204)
        fine = fbm(cx * 9, cy * 9, Zs * 9, 2, 205)
        blue = np.empty(TH.shape + (3,), F); blue[...] = C(66, 77, 86)
        blue = mix(blue, C(42, 53, 66), .55 * ss(-.20, .60, st + .5 * n_l))
        blue = mix(blue, C(84, 100, 114), .38 * ss(.05, .60, -st + .4 * st2))
        blue = mix(blue, C(92, 84, 70), .60 * ss(-.05, .50, n_l + .4 * n_m))
        blue = mix(blue, C(70, 62, 50), .35 * ss(.20, .6, st2 + .5 * n_m))
        s = np.degrees(TH)
        pale = np.maximum(gauss((np.abs(s) - 38) / 13, (T - .36) / .075), .6 * gauss((s + 62) / 12, (T - .40) / .07))
        blue = mix(blue, C(150, 168, 186), .85 * pale * ss(.02, .40, n_m + .4 * fine))
        pale2 = ss(.45, .7, n_l) * ss(.25, .5, n_m)
        blue = mix(blue, C(120, 138, 150), .4 * pale2)
        hh = .15 * st + .10 * st2 + .12 * fine + .16 * n_m
        # kurdele
        def ribbon(img, hh, dd, arc, half, gate):
            g = ink(np.abs(dd) - half, .025) * gate
            inner = half - .17
            U = 6.15
            q = np.mod(arc, U)
            col = np.empty(img.shape, F); col[...] = C(176, 142, 92)
            def seg(c, w):   # merkez, yarı genişlik
                return ink(rbox(q - c, dd, w, inner, .03), .02)
            r_ = C(138, 70, 50); g_ = C(122, 126, 84); bl_ = C(74, 84, 86)
            vv = fbm(arc * 2.1, dd * 2.1, 0 * dd, 3, 211)
            rcol = np.empty(img.shape, F); rcol[...] = r_; rcol = mix(rcol, C(164, 98, 70), .55 * ss(-.1, .5, vv)); rcol = mix(rcol, C(110, 50, 36), .4 * ss(.1, .6, -vv))
            gcol = np.empty(img.shape, F); gcol[...] = g_; gcol = mix(gcol, C(158, 154, 112), .6 * ss(-.1, .5, vv)); gcol = mix(gcol, C(90, 92, 66), .4 * ss(.1, .6, -vv))
            for c_, w_, k_ in [(1.15, 1.15, 0), (2.68, .22, 2), (4.02, .95, 1), (5.40, .22, 2)]:
                sg = seg(c_, w_)[..., None]
                cc = rcol if k_ == 0 else gcol if k_ == 1 else bl_
                col = col * (1 - sg) + cc * sg
            # kontur
            edge = np.minimum(np.abs(np.abs(dd) - half + .02), np.abs(np.abs(dd) - inner))
            col = mix(col, C(104, 66, 42), .55 * ink(edge - .016, .015))
            wr = ss(.35, .62, fine * .5 + n_m * .7)
            col = mix(col, C(205, 180, 135), .55 * wr)
            hh = hh * (1 - .6 * g) + g * (.35 * ink(np.abs(np.abs(dd) - (half + inner) / 2) - .085, .03) + .1 * fine)
            return img * (1 - g[..., None]) + col * g[..., None], hh
        arc = TH * Rr * 1.02 + 1.15
        bd_ = geo.band_d(TH, T)
        blue, hh = ribbon(blue, hh, bd_, np.abs(TH) * Rr * 1.02 + 2.2 + .25 * bd_ * np.sin(np.abs(TH)), 1.13, 1.0)
        dd, si = geo.strip_d(TH, T)
        blue, hh = ribbon(blue, hh, dd, si - .12, 1.02, ink(-si + .0, .03) * (geo.band_d(TH, T) < -1.15))
        # arka dikey kurdele
        dk = (np.abs(TH) - np.pi) * Rr
        gate = ink(np.abs(dk) - .95, .02) * (bd_ < -1.1) * (b > .1)
        vr = mix(np.broadcast_to(C(170, 130, 74), blue.shape).copy(), RED, ink(np.abs(np.mod(T * 22, 1.3) - .65) - .42, .03) * ink(np.abs(dk) - .72, .02))
        blue = blue * (1 - gate[..., None]) + vr * gate[..., None]
        # dökülme ve kırık
        m = geo.chip(TH, T); r = geo.rubdots(TH, T)
        crack = PLASTER * (1 - .10 * ss(-.3, .5, n_m)[..., None]) * (1 - .14 * ss(.1, .6, fine)[..., None])
        blue = blue * (1 - (r * .85)[..., None]) + (crack * .92) * (r * .85)[..., None]
        sp = ss(.70, .80, fbm(cx * 3.0, cy * 3.0, Zs * 4.0, 3, 221) + .45 * n_l)
        blue = blue * (1 - .75 * sp[..., None]) + C(186, 164, 126) * .75 * sp[..., None]
        blue = blue * (1 - m[..., None]) + crack * m[..., None]
        hh = hh * (1 - m) + m * (.5 * fine + .6 * n_m)
        # altın alınlık
        gold = np.empty(TH.shape + (3,), F); gold[...] = GOLD
        gold = mix(gold, GOLDL, .75 * ss(-.05, .45, n_m + .4 * fine))
        gold = mix(gold, C(158, 120, 72), .45 * ss(.1, .6, -n_m + .3 * n_l))
        gold = mix(gold, C(150, 110, 68), .4 * ss(.50, .70, fbm(cx * 4, cy * 4, Zs * 4, 3, 231)))
        gs = geo.gold_sd(TH, T)
        gold = mix(gold, C(112, 74, 46), .55 * ink(gs - .06, .03))
        k = ss(-.015, .015, b)
        out = gold * (1 - k[..., None]) + blue * k[..., None]
        hh = hh * k + (1 - k) * (.10 * n_m + .12 * fine)
        mol = gauss((b - .06) / .085)
        out = mix(out, C(166, 130, 82), .92 * ss(.25, .6, mol) * (1 - m * .9))
        out = mix(out, C(74, 52, 36), .55 * gauss((b + .06) / .03)); out = mix(out, C(50, 44, 38), .5 * gauss((b - .19) / .03))
        img[a:a + 96] = out; hgt[a:a + 96] = hh
        rgh[a:a + 96] = np.clip(.60 + .16 * n_m + .10 * m - .12 * (1 - k), .3, .95)
    _par(_row, H)
    return img, hgt, rgh

# ------------------------------------------------ GERDANLIK (s, rho)  s: 0 arka orta -> .5 ön orta
def collar(Lc, W=8192, R=8.4, H=1536, A=None):
    s = (np.arange(W) + .5) / W
    rho = (np.arange(H) + .5) / H * R
    img = np.empty((H, W, 3), F); hgt = np.zeros((H, W), F)
    def _row(a):
        SS, RH = np.meshgrid(s.astype(F), rho[a:a + 96].astype(F))
        ri = RH / R * (A.shape[0] - 1); i0 = np.clip(ri.astype(int), 0, A.shape[0] - 2); fi_ = (ri - i0).astype(F)
        si = np.clip(SS * A.shape[1], 0, A.shape[1] - 1.001); j0 = si.astype(int); fj = (si - j0).astype(F); j1 = np.minimum(j0 + 1, A.shape[1] - 1)
        # sıra ortasındaki yay uzunluğunu kullan ki birimler radyal olarak düz insin
        u = xs = (A[i0, j0] * (1 - fi_) * (1 - fj) + A[i0 + 1, j0] * fi_ * (1 - fj) + A[i0, j1] * (1 - fi_) * fj + A[i0 + 1, j1] * fi_ * fj)
        def rowx(rc):
            ii = min(int(rc / R * (A.shape[0] - 1)), A.shape[0] - 2)
            return A[ii, j0] * (1 - fj) + A[ii, j1] * fj
        n_l = fbm(xs * .30, RH * .30, 0 * u, 4, 301); n_m = fbm(xs * 1.3, RH * 1.3, 0 * u + 5, 4, 302); fine = fbm(xs * 7, RH * 7, 0 * u + 9, 3, 303)
        wob = .05 * fbm(xs * 1.1, RH * 1.1, 0 * u + 13, 2, 304)
        rr = RH + wob
        img_ = np.empty(u.shape + (3,), F); img_[...] = TAN
        img_ = mix(img_, C(214, 184, 134), .6 * ss(-.1, .5, n_m)); img_ = mix(img_, C(172, 134, 84), .4 * ss(.1, .6, -n_m + .3 * fine))
        h_ = np.zeros(u.shape, F)
        def put(col, cov, hv=.0):
            nonlocal img_, h_
            img_ = mix(img_, col, cov); h_ = h_ * (1 - cov) + hv * cov
        def cell(w0, seed, rc):
            """sıra ortası rc'de w0 cm adımlı hücre; q yerel, gerçek cm (rho ile genişler)"""
            xr = rowx(rc); k = np.round(xr / w0)
            sc_ = np.clip(xs / np.where(np.abs(xr) < .05, 1e9, xr), .55, 1.8); sc_ = np.where(np.abs(xr) < .05, 1.0, sc_)
            w = w0; q = (xr / w0 - k) * w0
            rnd = _rnd(k, seed)
            return q, w, k, rnd
        def _rnd(k, seed): return np.mod(np.sin(k * 127.1 + seed * 311.7) * 43758.5453, 1).astype(F)
        # --- sıra 1: fıçı boncuklar 0.05–0.95
        q, w, k, rnd = cell(1.42, 1, .5)
        pal = np.stack([BLUE, GREEN * .95, RED, BLUE, C(150, 140, 96), C(64, 84, 98)])
        ci = (np.mod(k + (k < 0), 6)).astype(int)
        cols = pal[np.clip(ci, 0, 5)]
        inrow = ink(np.abs(rr - .50) - .47, .02)
        sh = rbox(q + .10, rr - .50, w * .33, .40, .14)
        put(C(206, 174, 120), inrow, .12)
        put(cols, ink(sh, .02), .5)
        put(LINE, .55 * ink(np.abs(sh) - .02, .02), .1)
        # --- çizgi
        def rule(r0, r1):
            put(C(204, 168, 112), ink(np.abs(rr - (r0 + r1) / 2) - (r1 - r0) / 2, .015), .38)
            for e in (r0, r1): put(LINE, .8 * ink(np.abs(rr - e) - .022, .018), -.05)
        rule(.97, 1.12)
        # --- petal sıraları
        def petals(r0, r1, N, seed):
            q, w, k, rnd = cell(N, seed, (r0 + r1) / 2)
            v = np.clip((rr - r0) / (r1 - r0), 0, 1)
            inn = ink(np.abs(rr - (r0 + r1) / 2) - (r1 - r0) / 2, .015)
            # zemin: kırmızı; üstte yeşil başlık, altta mavi
            put(RED * (.92 + .2 * rnd)[..., None], inn * .92, .10)
            put(C(150, 80, 50), inn * .5 * ss(.0, .5, n_m), .10)
            gap = np.abs(np.abs(q) - w * .5)                                # hücre kenarına uzaklık
            put(GREEN, inn * ink(v - .24, .03) * ink(gap - w * .20, .02), .40)
            put(C(200, 172, 124), inn * ink(np.abs(v - .64) - .035, .02) * ink(gap - w * .30, .02), .20)
            put(BLUE, inn * ink(.70 - v - .10 * (gap / (w * .5)), .02), .42)
            # petal gövdesi
            hw = w * Spline([0, .18, .45, .68, .86, 1.0], [.20, .25, .31, .30, .17, .02])(v)
            pd = np.abs(q) - hw
            pc = np.empty(u.shape + (3,), F); pc[...] = C(202, 168, 112); pc = mix(pc, C(184, 142, 90), .5 * rnd)
            put(pc, inn * ink(pd, .018), .62)
            put(LINE, inn * .62 * ink(np.abs(pd) - .016, .016), .05)
        petals(1.14, 3.18, .60, 3)
        rule(3.22, 3.42)
        # --- meyve sırası 3.45–4.75
        q, w, k, rnd = cell(1.06, 5, 4.1)
        inn = ink(np.abs(rr - 4.10) - .66, .015)
        put(C(188, 150, 98), inn, .10)
        gap = np.abs(np.abs(q) - w * .5)
        put(RED, inn * ink(rr - 3.84 + gap * .55, .02) * .9, .20)
        put(BLUE, inn * ink(4.34 - rr + gap * 1.0, .02), .42)
        fd = np.sqrt((q / 1.02)**2 + ((rr - 4.06) / .98)**2) - w * .40
        fd = smin(fd, np.maximum(np.abs(q) - .16 + (rr - 4.3) * .25, np.abs(rr - 4.38) - .26), .12)
        fc = np.empty(u.shape + (3,), F); fc[...] = C(200, 164, 106); fc = mix(fc, C(150, 146, 92), .7 * (rnd > .55) + 0 * rnd)
        fc = mix(fc, C(216, 190, 140), .6 * gauss((q + .1) / .2, (rr - 3.92) / .2))
        put(fc, inn * ink(fd, .02), .66)
        put(LINE, inn * .6 * ink(np.abs(fd) - .017, .016), .05)
        put(C(120, 70, 44), inn * .6 * ink(np.sqrt((q)**2 + (rr - 4.0)**2) - .045, .02), .4)
        rule(4.78, 4.96)
        petals(4.98, 6.75, .66, 7)
        rule(6.78, 6.96)
        # damla sırası
        q, w, k, rnd = cell(.95, 9, 7.4)
        inn = ink(np.abs(rr - 7.45) - .48, .015)
        dr = np.sqrt((q / .9)**2 + ((rr - 7.42) / 1.5)**2) - w * .36
        put(C(190, 152, 100), inn, .1); put(np.where((np.mod(k, 2) == 0)[..., None], BLUE, RED).astype(F), inn * ink(dr, .02), .5)
        # --- aşınma: plaster
        edge_w = .34 * ss(3.5, 8.0, RH)
        wr = ss(.30, .56, n_l * .62 + n_m * .52 + .26 * fine + edge_w * .60 - .04)
        img_ = mix(img_, PLASTER * (1 - .12 * ss(-.2, .5, fine)[..., None]), .88 * wr)
        wr2 = ss(.36, .60, n_m * .6 + fine * .6)
        img_ = mix(img_, C(212, 184, 138), .60 * wr2)
        img_ = mix(img_, C(196, 166, 120), .24 * np.ones_like(wr2))
        img_ = mix(img_, C(120, 92, 62), .16 * ss(.0, .6, fine + .4 * n_m))
        h_ = h_ * (1 - .8 * wr) + .10 * fine - .12 * wr
        put(LINE, .75 * ink(np.abs(RH - .03) - .035, .02), 0)
        img[a:a + 96] = img_; hgt[a:a + 96] = h_
    _par(_row, H)
    return img, hgt

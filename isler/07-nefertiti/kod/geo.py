"""Nefertiti büstü geometrisi. Bütün sayılar profil ve ön görünüşten okunan cm ölçüleridir."""
import numpy as np
from sdf import *

# ------------------------------------------------ TAÇ (çizgisel yüzey)
F0 = np.array([12.75, 32.05]); F1 = np.array([5.39, 48.5])
B0 = np.array([0.56, 20.2]);   B1 = np.array([-18.4, 40.0])
CW0, CW1 = 6.62, 12.0
dF_ = F1 - F0; D0_ = B0 - F0; dD_ = (B1 - B0) - dF_
def _cr(a, b0, b1): return a[0] * b1 - a[1] * b0
_a = -(dD_[0] * dF_[1] - dD_[1] * dF_[0])
_b0 = -(D0_[0] * dF_[1] - D0_[1] * dF_[0])

def crown_param(x, f, z):
    """(t, u, v): t kesit, u ön-arka (-1..1), v yan (-1..1)"""
    qf, qz = f - F0[0], z - F0[1]
    b = _cr(dD_, qf, qz) + _b0
    c = _cr(D0_, qf, qz)
    disc = np.sqrt(np.maximum(b * b - 4 * _a * c, 0))
    t1 = (-b + disc) / (2 * _a); t2 = (-b - disc) / (2 * _a)
    t = np.where(np.abs(t1 - 0.5) < np.abs(t2 - 0.5), t1, t2)
    tc = np.clip(t, -0.6, 1.4)
    Ff, Fz = F0[0] + dF_[0] * tc, F0[1] + dF_[1] * tc
    Df, Dz = D0_[0] + dD_[0] * tc, D0_[1] + dD_[1] * tc
    L = np.sqrt(Df * Df + Dz * Dz)
    s = ((f - Ff) * Df + (z - Fz) * Dz) / (L * L)
    u = 1 - 2 * s
    w = CW0 + (CW1 - CW0) * tc
    return t.astype(F), u.astype(F), (x / w).astype(F), (L * 0.5).astype(F), w.astype(F)

def crown_r(t, u, v, hl, w):
    n = 2.32 - 0.27 * np.clip(t * 1.3, 0, 1)
    au, av = np.abs(u) + 1e-5, np.abs(v) + 1e-5
    r = (au**n + av**n)**(1 / n)
    gu = r**(1 - n) * au**(n - 1) / hl
    gv = r**(1 - n) * av**(n - 1) / w
    g = np.sqrt(gu * gu + gv * gv) + 1e-4
    return (r - 1) / g * 0.93       # 0.93: yüzeyin yana açılması

def crown_theta(u, v, t):
    n = 2.32 - 0.27 * np.clip(t * 1.3, 0, 1)
    return np.arctan2(np.sign(v) * np.abs(v)**(n / 2), np.sign(u) * np.abs(u)**(n / 2)).astype(F)

def crown_shell(x, f, z):
    t, u, v, hl, w = crown_param(x, f, z)
    return crown_r(t, u, v, hl, w), t, crown_theta(u, v, t)

# mavi tacın alt sınırı  t = blue_lo(|theta| derece)
_bl = Spline([0, 20, 40, 56, 60.5, 62.5, 64, 67, 72, 78, 85, 95, 104, 125, 150, 180],
             [.205, .205, .208, .213, .212, .195, .165, .125, .086, .068, .066, .100, .128, .132, .128, .125], n=8000)
_gl = Spline([0, 30, 60, 75, 80, 95, 104, 115, 140, 180],
             [0.0, .004, .030, .056, .075, .105, .128, .098, .035, 0.0])
def blue_lo(adeg): return _bl(adeg)
def gold_lo(adeg): return _gl(adeg)

# ------------------------------------------------ BAŞ
_front = Spline([13, 15.5, 17, 17.6, 18.05, 18.67, 19.39, 20.7, 22, 23.4, 25, 26.5, 27.9, 29.42, 30.67, 32.05, 34, 36, 40],
                [14.0, 14.7, 15.2, 15.48, 15.56, 15.42, 15.14, 15.22, 15.28, 15.02, 14.62, 14.35, 14.2, 14.0, 13.38, 12.75, 11.8, 10.7, 8.0])
_w = Spline([13, 17, 18, 19, 20.7, 22.4, 24, 26.5, 28.5, 30, 32, 36, 40],
            [4.6, 4.75, 4.9, 5.12, 5.62, 6.12, 6.48, 6.68, 6.62, 6.5, 6.3, 5.6, 4.5])
_fc = Spline([13, 17, 20, 22, 24, 27, 30, 40], [6.6, 6.6, 6.5, 6.1, 5.6, 5.0, 4.5, 3.0])
_n = Spline([13, 18, 19.5, 21, 23, 25, 26.9, 28.3, 31, 40], [2.12, 2.10, 2.02, 1.95, 2.0, 2.2, 2.32, 2.34, 2.3, 2.2])
_back = Spline([13, 20, 24, 30, 40], [1.2, 0.9, 0.2, -3, -6])

def loft(x, f, z):
    w, fc, n = _w(z), _fc(z), _n(z)
    df = _front(z) - fc; db = fc - _back(z)
    d = np.where(f >= fc, df, db)
    au, av = np.abs((f - fc) / d) + 1e-5, np.abs(x / w) + 1e-5
    r = (au**n + av**n)**(1 / n)
    g = np.sqrt((r**(1 - n) * au**(n - 1) / d)**2 + (r**(1 - n) * av**(n - 1) / w)**2) + 1e-4
    return (r - 1) / g

# --- göz
EYE_C = (2.90, 12.02, 26.86); EYE_R = (2.12, 1.16, 1.30); EYE_YAW = np.radians(23)
EX0, EX1 = 1.62, 4.72
def eye_curves(ax):
    s = np.clip((ax - EX0) / (EX1 - EX0), 0, 1)
    zb = 26.42 + 0.42 * s
    up = zb + 0.74 * np.maximum(np.sin(np.pi * s**0.86), 0)**0.86 * (1 - 0.10 * s)
    lo = zb - 0.31 * np.maximum(np.sin(np.pi * s**0.92), 0)**0.95
    return up, lo
def almond(ax, z):
    up, lo = eye_curves(ax)
    d = np.maximum(z - up, lo - z) * 0.86
    d = np.where(ax < EX0, np.sqrt((EX0 - ax)**2 + (z - 26.42)**2), d)
    return np.where(ax > EX1, np.sqrt((ax - EX1)**2 + (z - 26.84)**2), d)

# --- ağız
_mzc = Spline([18.6, 19.15, 19.42, 19.62, 19.85, 20.16, 20.48, 20.64, 20.72, 20.80, 20.98, 21.25, 21.42, 21.5, 21.87, 22.35, 22.9],
              [0.0, 0.0, 0.01, 0.16, 0.42, 0.55, 0.49, 0.36, 0.27, 0.34, 0.47, 0.56, 0.585, 0.54, 0.34, 0.16, 0.0], n=6000)
LW = 2.60
def mouth_curves(ax):
    e = np.clip(ax / LW, 0, 1)
    zm = 20.66 + 0.07 * np.sin(np.clip(ax / 1.7, 0, 1) * np.pi) + 0.08 * e**3
    zu = zm + (0.66 + 0.11 * gauss((ax - 0.58) / 0.36)) * np.maximum(1 - e**1.95, 0)
    zl = zm - 1.18 * np.maximum(1 - e**2.4, 0)**0.9
    return zm, zu, zl
def mouth_disp(ax, z):
    zm, zu, zl = mouth_curves(ax)
    a = np.where(z > zu, 21.42 + (z - zu), np.where(z > zm, 20.72 + (z - zm) / np.maximum(zu - zm, .08) * 0.70,
        np.where(z > zl, 20.72 - (zm - z) / np.maximum(zm - zl, .10) * 1.10, 19.62 - (zl - z))))
    e = np.clip(ax / (LW + .05), 0, 1)
    A = np.maximum(1 - e**2.3, 0)**0.85
    A2 = np.clip(1 - (ax / 2.2)**2, 0, 1)
    k = np.maximum(gauss((z - zu) / .10) * (z > zu), gauss((z - zl) / .10) * (z < zl))
    amp = np.where((z > zu) | (z < zl), k * A + (1 - k) * (0.3 * A + 0.7 * A2), A)
    d = amp * _mzc(a)
    d = d - 0.10 * gauss((z - zm) / 0.065) * np.clip(1 - (ax / 2.66)**8, 0, 1)
    d = d - 0.13 * gauss((ax - 2.64) / 0.34, (z - 20.74) / 0.40)     # köşe çukuru
    d = d + 0.035 * gauss((ax - 3.25) / 0.4, (z - 20.7) / 0.6)       # köşe dışı dolgunluk
    d = d - 0.035 * gauss(ax / 0.30, (z - 21.95) / 0.35)              # filtrum
    d = d + 0.0 * ax
    return d

def head(x, f, z, vn=None):
    ax = np.abs(x)
    d = loft(x, f, z)
    # çene altı yüzeyi
    zb = 16.93 + 0.036 * ax**2 + 0.0015 * ax**4 + 0.13 * np.maximum(9.5 - f, 0)
    d = smax(d, (zb - z) * 0.93, 1.15)
    front = np.clip((f - 8.0) / 2.0, 0, 1)
    disp = 0
    # elmacık, yanak çukuru, şakak
    disp = disp + 0.26 * gauss((ax - 4.4) / 1.35, (z - 25.1 - 0.15 * (ax - 4.4)) / 0.85)
    disp = disp - 0.30 * gauss((ax - 4.4) / 1.45, (z - 22.1) / 1.6)
    disp = disp - 0.12 * gauss((ax - 6.2) / 1.2, (z - 29.0) / 1.6)
    # kaş kemeri (yumuşak)
    zbrow = 29.45 - 0.085 * (ax - 3.0)**2
    disp = disp + 0.07 * gauss((z - zbrow) / 0.45) * np.clip((ax - 0.2) / 1.0, 0, 1) * np.clip((6.3 - ax) / 1.2, 0, 1)
    # göz çukuru: genel basen + kaş altı derin oyuk
    disp = disp - 0.42 * gauss((ax - 3.2) / 1.9, (z - 27.1) / 1.25)
    zs = 28.22 - 0.10 * (ax - 3.0)**2
    disp = disp - 0.60 * gauss((ax - 3.5) / 1.75, (z - zs) / 0.58)
    disp = disp - 0.16 * gauss((ax - 4.4) / 0.9, (z - 27.95) / 0.5)
    disp = disp - 0.40 * gauss((ax - 1.60) / 0.62, (z - 27.2) / 1.05)
    # göz altı, burun kenarı
    disp = disp - 0.10 * gauss((ax - 2.4) / 1.0, (z - 25.55) / 0.45)
    disp = disp - 0.07 * gauss((ax - 2.45) / 0.55, (z - 22.7) / 0.9)
    # ağız ve çene
    disp = disp + mouth_disp(ax, z)
    disp = disp + 0.10 * gauss(ax / 1.6, (z - 18.0) / 0.7)
    disp = disp - 0.12 * gauss((ax - 3.0) / 0.9, (z - 19.2) / 0.9)
    d = d - disp * front

    # --- burun
    n1 = cap(ax, f, z, (0.20, 13.50, 28.95), (0.06, 15.98, 24.32), 0.56, 0.70)
    n2 = cap(ax, f, z, (0.42, 13.10, 27.8), (1.08, 14.60, 23.85), 0.52, 0.82)
    nose = smin(n1, n2, 1.0)
    tip = ell(ax, f, z, (0, 15.97, 23.74), (0.98, 0.88, 0.80))
    nose = smin(nose, tip, 0.55)
    ala = cap(ax, f, z, (0.70, 15.64, 23.50), (1.24, 15.04, 23.42), 0.52, 0.57)
    nose = smin(nose, ala, 0.40)
    nose = smin(nose, cap(ax, f, z, (0.98, 14.42, 24.75), (1.26, 14.86, 23.75), 0.54, 0.52), 0.55)
    col = cap(ax, f, z, (0, 16.12, 23.30), (0, 15.22, 22.66), 0.40, 0.36)
    nose = smin(nose, col, 0.35)
    nos = ell_yaw(ax, f, z, (0.74, 15.42, 22.86), (0.32, 0.58, 0.34), np.radians(26))
    d = smin(d, nose, 0.50)
    # kanat oluğu
    d = d + 0.05 * gauss((ax - 1.86) / 0.20, (z - 23.5) / 0.45) * (f > 13.5)
    d = smax(d, -nos, 0.14)

    # --- göz kapağı ve göz
    e = ell_yaw(ax, f, z, EYE_C, EYE_R, EYE_YAW)
    lid = ell_yaw(ax, f, z, (EYE_C[0] + .05, EYE_C[1], EYE_C[2] + .10), (EYE_R[0] + .34, EYE_R[1] + .17, EYE_R[2] + .22), EYE_YAW)
    zl_ = 26.78 - 0.05 * (ax - 3.2)                        # üst kapak yalnız göz çizgisinin üstünde kabarır
    lu = smax(lid, (zl_ - z) * 0.9, 0.45)
    kk = 0.06 + 0.45 * np.clip((ax - 4.45) / 0.7, 0, 1)
    d = smin(d, lu, kk)
    d = smin(d, e - 0.11, 0.45)
    al = almond(ax, z)
    fr = 11.0 - f
    carve = np.maximum(al, fr)
    d = smax(d, -carve, 0.06)
    d = np.minimum(d, e)
    d = d + 0.02 * gauss((al - 0.17) / 0.05) * (f > 11) * (z > 26.9)     # kirpik çizgisi
    return d

# ------------------------------------------------ KULAK
def _cat(P, R, m):
    P = np.array([list(a) + [r] for a, r in zip(P, R)]); P = np.vstack([2*P[0]-P[1], P, 2*P[-1]-P[-2]]); O = []
    for i in range(1, len(P) - 2):
        for t in np.arange(m) / m:
            a, b, c, d_ = P[i-1], P[i], P[i+1], P[i+2]
            O.append(.5 * (2*b + (c-a)*t + (2*a-5*b+4*c-d_)*t*t + (3*b-a-3*c+d_)*t**3))
    O.append(P[-2]); O = np.array(O)
    return [tuple(o[:3]) for o in O], list(O[:, 3])

def ear(x, f, z, side, broken=True):
    """side=+1: heykelin sol kulağı (x>0)"""
    X = x * side
    Of, Oz, Ox = 4.75, 24.75, 7.30
    U = np.array([-0.342, 0.940]); V = np.array([0.940, 0.342])
    a = np.radians(33)
    dx, df, dz = X - Ox, f - Of, z - Oz
    q = df * U[0] + dz * U[1]
    pv = df * V[0] + dz * V[1]
    p = pv * np.cos(a) - dx * np.sin(a)
    n = dx * np.cos(a) + pv * np.sin(a)
    S = 0.98
    p, q, n = p / S, q / S, n / S
    hel = [(.30, .05, -.10), (.80, .55, .02), (1.10, 1.35, .05), (1.0, 2.15, .08), (.45, 2.66, .10), (-.35, 2.74, .12), (-1.05, 2.32, .14),
           (-1.48, 1.55, .15), (-1.60, .65, .14), (-1.48, -.25, .10), (-1.18, -1.05, .04), (-.80, -1.60, 0.0)]
    rr = [.16, .22, .25, .26, .27, .28, .28, .28, .27, .25, .23, .20]
    hel, rr = _cat(hel, rr, 4)
    d = chain(p, q, n, hel, rr, .04)
    # iç levha
    plate = np.sqrt(((p + .22) / 1.42)**2 + ((q - .45) / 2.25)**2)
    pl = np.maximum((plate - 1) * 1.2, np.abs(n + .12 + 0.10 * (1 - plate**2)) - 0.13)
    d = smin(d, pl, .22)
    anti = chain(p, q, n, [(-.35, -1.25, .04), (-.78, -.6, .10), (-.92, .2, .12), (-.72, .95, .10), (-.15, 1.75, .02)], [.22, .24, .25, .24, .16], .1)
    anti = np.minimum(anti, cap(p, q, n, (-.80, .75, .10), (-.65, 1.9, .04), .22, .15))
    d = smin(d, anti, .16)
    d = smin(d, ell(p, q, n, (.02, -1.30, .06), (.34, .24, .24)), .18)
    d = smin(d, ell(p, q, n, (.92, -.42, .10), (.27, .44, .22)), .22)
    d = smin(d, ell(p, q, n, (.10, -2.05, -.02), (.72, .80, .27)), .30)
    # konka çukuru
    d = smax(d, -ell(p, q, n, (.12, -.30, .22), (.62, .86, .42)), .14)
    d = smax(d, -ell(p, q, n, (.66, -.42, -.15), (.24, .26, .5)), .10)
    d = smax(d, -ell(p, q, n, (.20, 1.35, .22), (.48, .62, .26)), .14)
    d = smax(d, -ell(p, q, n, (.14, -1.95, .28), (.11, .11, .30)), .08)   # küpe deliği
    if not broken: return d * S
    if side < 0:   # sağ kulak: arka kenarda kopuk + çatlak
        cs_ = [ell(p, q, n, (-1.80, .75, .25), (.46, 1.10, .62)) + 0.12 * fbm(p * 3.1, q * 3.1, n * 3.1, 5, 5, .62),
               cap(p, q, n, (-1.8, -.85, .1), (-.3, -1.02, .35), .06)]
    else:          # sol kulak: heliks ve lob kırık
        cs_ = [ell(p, q, n, (-1.80, -1.0, .1), (.80, 1.30, 1.2)) + 0.10 * fbm(p * 2.8, q * 2.8, n * 2.8, 5, 9, .62),
               ell(p, q, n, (.15, -3.05, 0), (1.7, 1.15, 1.1)) + 0.10 * fbm(p * 2.8, q * 2.8, n * 2.8, 5, 19, .62),
               ell(p, q, n, (1.05, 1.1, .3), (.42, .9, .5)) + 0.12 * fbm(p * 2.8, q * 2.8, n * 2.8, 5, 29, .62)]
    cm = np.minimum.reduce(cs_)
    if broken == 'kesik': return cm * S
    d = np.maximum(d, -cm)
    return d * S

# ------------------------------------------------ BOYUN + GÖĞÜS
_nf = Spline([2, 4, 6, 7.3, 8.06, 10.28, 11.7, 13.06, 14.2, 15.2, 16.2, 17.2, 20, 24], [4.2, 4.8, 5.2, 5.28, 5.30, 5.55, 5.95, 6.75, 7.70, 8.70, 9.55, 10.0, 10.2, 10.0])
_nb = Spline([2, 5.83, 9.72, 12.78, 15.83, 18.06, 20, 24], [-6.0, -5.6, -4.3, -2.75, -.83, .28, .60, 0.9])
_nw = Spline([2, 8, 11, 13, 14.5, 16, 18, 21, 24], [5.0, 4.6, 4.35, 4.22, 4.15, 4.12, 4.22, 4.85, 5.4])
_nn = Spline([2, 15.5, 17.5, 20.5, 24], [2.0, 2.0, 2.15, 2.9, 3.0])

def neck(x, f, z):
    fr, bk, w = _nf(z), _nb(z), _nw(z)
    c = (fr + bk) * 0.5; h = (fr - bk) * 0.5
    n = np.where(f < c, _nn(z), 2.0)
    au, av = np.abs((f - c) / h) + 1e-5, np.abs(x / w) + 1e-5
    r = (au**n + av**n)**(1 / n)
    g = np.sqrt((r**(1 - n) * au**(n - 1) / h)**2 + (r**(1 - n) * av**(n - 1) / w)**2) + 1e-4
    d = (r - 1) / g * 0.86
    d = smin(d, ell(np.abs(x), f, z, (3.0, 3.6, 22.9), (3.0, 2.9, 2.5)), 1.2)
    return smax(d, z - 25.0, 1.0)

def bust(x, f, z):
    ax = np.abs(x)
    fc = -0.9 + 0.10 * z
    d = ell(x, f - fc, z, (0, 0, 0), (17.0, 7.35, 12.4))
    d = smin(d, cap(ax, f, z, (2.6, 0.2, 14.0), (9.2, -0.9, 9.5), 1.5, 1.1), 2.2)
    return d

def body_soft(x, f, z):
    """kesilmemiş gövde + boyun + baş"""
    ax = np.abs(x)
    nk = neck(x, f, z)
    scm = chain(ax, f, z, [(4.2, 3.6, 21.0), (3.55, 4.2, 16.5), (2.5, 4.85, 11.6), (1.05, 4.75, 7.9)], [.75, .80, .72, .55], .4)
    nk = smin(nk, scm, 0.9)
    b = bust(x, f, z)
    clav = chain(ax, f, z, [(.75, 5.05, 6.9), (3.0, 4.75, 7.9), (6.0, 3.1, 9.0), (9, 1.2, 9.6)], [.42, .40, .40, .45], .3)
    b = smin(b, clav, 0.9)
    d = smin(nk, b, 1.5)
    d = d + 0.42 * gauss(np.sqrt((ax - 2.9)**2 + (f - 4.3)**2 + (z - 9.2)**2) / 1.25)
    d = d + 0.22 * gauss(np.sqrt(ax**2 + (f - 5.4)**2 + (z - 7.9)**2) / 0.75)
    # boyun ön çizgisi (gırtlak)
    d = d + 0.16 * gauss((ax - 1.9) / 0.8) * np.clip((f - 3) / 3, 0, 1) * np.clip((15.5 - z) / 2, 0, 1) * np.clip((z - 8.5) / 2, 0, 1)
    return d

def body(x, f, z, detail=True):
    ax = np.abs(x)
    d = body_soft(x, f, z)
    # alt/yan kesimler
    if detail:
        n1 = fbm(x * .45, f * .45, z * .45, 3, 3)
        n2 = fbm(x * 1.9, f * 1.9, z * 1.9, 3, 4)
    else:
        n1 = n2 = 0.0
    side = ax - (10.15 - 0.018 * np.maximum(z - 6, 0)**1.5) + 0.12 * n1 + 0.018 * n2
    bot = -z + 0.04 * n1
    d2 = smax(d, side, 0.75)
    d2 = smax(d2, bot + 0.0, 0.9)
    if detail:
        n3 = fbm(x * .9, f * .9, z * .9, 5, 7, .62)
        edge = np.maximum(gauss((side + .15) / .55) * gauss((d + .1) / .6), gauss((z - .25) / .5) * gauss((d + .1) / .7))
        d2 = d2 + edge * (np.clip((n3 - .10) * .95, 0, .28) + .06 * np.clip(n2 + .2, 0, 1))
    h = head(x, f, z)
    # taç altında kalan deriyi taca göm
    t, u, v, hl, w = crown_param(x, f, z)
    cs = crown_r(t, u, v, hl, w)
    gl = gold_lo(np.degrees(np.abs(crown_theta(u, v, t))))
    d2 = smin(d2, h, 0.85)
    d2 = np.where((t > gl - 0.004) & (z > 19.0), np.maximum(d2, cs + 0.02), d2)
    for s in (1, -1):
        near = (x * s > 5.2) & (np.abs(z - 24.7) < 4.2) & (f > 0.5) & (f < 9)
        if near.any():
            e = np.full_like(d2, 9.0)
            e[near] = ear(x[near], f[near], z[near], s)
            d2 = smin(d2, e, 0.30)
    return d2


# ------------------------------------------------ TAÇ KATI MODELİ
def _L(th):      # dP/dt boyu (cm) ~ açıya göre
    c = (1 + np.cos(th)) * .5
    return 18.02 * c + 27.4 * (1 - c)

def crown_pos(th, t, off=0.0):
    n = 2.32 - 0.27 * np.clip(t * 1.3, 0, 1)
    c = np.sign(np.cos(th)) * np.abs(np.cos(th))**(2 / n); s = np.sign(np.sin(th)) * np.abs(np.sin(th))**(2 / n)
    Fp = F0 + (F1 - F0) * t; Bp = B0 + (B1 - B0) * t
    C = (Fp + Bp) / 2; H = (Fp - Bp) / 2; w = CW0 + (CW1 - CW0) * t
    p = np.array([s * w, C[0] + c * H[0], C[1] + c * H[1]])
    if off:
        e = 1e-3
        a = crown_pos(th + e, t) - crown_pos(th - e, t); b = crown_pos(th, t + e) - crown_pos(th, t - e)
        nn = np.cross(a, b); nn /= np.linalg.norm(nn)
        if nn @ (p - np.array([0, C[0], C[1]])) < 0: nn = -nn
        p = p + nn * off
    return p

# (theta,t) uzayında sınır eğrilerine işaretli uzaklık haritası
_NT, _NP = 720, 520
_TT = np.linspace(-.12, 1.02, _NP)
def _sdmap(curve):
    A = np.linspace(0, 180, _NT // 2 + 1)
    ad = np.linspace(0, 180, 1801); tc = curve(ad.astype(F))
    out = np.empty((_NT // 2 + 1, _NP), F)
    for i, a in enumerate(A):
        R = 6.5 + 5.0 * np.clip(_TT, 0, 1)            # yerel yarıçap
        L = float(_L(np.radians(a)))
        dth = np.radians(ad - a)
        k = np.abs(ad - a) < 45
        dd = np.sqrt((dth[k][None] * R[:, None] * 1.05)**2 + ((_TT[:, None] - tc[k][None]) * L)**2).min(1)
        sg = np.where(_TT > np.interp(a, ad, tc), 1, -1)
        out[i] = dd * sg
    return out
_BMAP = _sdmap(_bl); _GMAP = _sdmap(_gl)
def _look(M, th, t):
    a = np.abs(th) * (180 / np.pi) / 180 * (M.shape[0] - 1)
    b = np.clip((t - _TT[0]) / (_TT[-1] - _TT[0]), 0, 1) * (_NP - 1)
    i = np.clip(a.astype(np.int32), 0, M.shape[0] - 2); j = np.clip(b.astype(np.int32), 0, _NP - 2)
    fa, fb = (a - i).astype(F), (b - j).astype(F)
    return (M[i, j] * (1 - fa) * (1 - fb) + M[i + 1, j] * fa * (1 - fb) + M[i, j + 1] * (1 - fa) * fb + M[i + 1, j + 1] * fa * fb)
def blue_sd(th, t): return _look(_BMAP, th, t)
def gold_sd(th, t): return _look(_GMAP, th, t)

def band_c(th):  return .520 + (.635 - .520) * (1 - np.cos(th)) * .5
def band_d(th, t):               # kurdele orta çizgisine cm uzaklık
    return (t - band_c(th)) * _L(th)
# alt kurdele: arkadan (180°, .575) -> yana (88°, .205)
def strip_d(th, t):
    a = np.abs(th)
    s = (np.pi - a) / (np.pi - np.radians(84))
    tc = .585 + (.200 - .585) * s + .035 * np.sin(np.pi * np.clip(s, 0, 1))
    dd = (t - tc) * _L(th) * .82
    return dd, (1 - s) * 13.5 + .72 * dd         # (enine cm, uçtan içeri cm)

def chip(th, t, x=None, f=None, z=None):
    """0..1 kırık/dökülme maskesi (sol yanda büyük plaster yaması + kenar kopukları)"""
    s = np.degrees(th)
    n = fbm(th * 9.0, t * 26.0, 0 * t, 4, 41)
    n2 = fbm(th * 30.0, t * 80.0, 0 * t, 3, 43)
    # büyük yama
    e = np.sqrt(((s - 116 - 10 * (t - .33) * 4) / 15.0)**2 + ((t - .325) / .165)**2)
    m = np.clip((1.0 - e + .42 * n + .12 * n2) * 6, 0, 1)
    # üst arka kenar kopukları
    for (c, wd, dp) in [(-158, 15, .050), (-140, 6, .018), (176, 10, .035), (150, 9, .040), (60, 3, .012), (97, 4, .014), (-80, 3, .010), (25, 2, .008), (-35, 2.5, .008)]:
        dd = np.abs((s - c + 180) % 360 - 180)
        m = np.maximum(m, np.clip(((t - 1 + dp * (1 + n * .7) * np.clip(1.3 - dd / wd, 0, 1)) / .012), 0, 1) * (dd < wd * 1.3))
    return m

def rubdots(th, t):
    """küçük dökülmeler"""
    n = fbm(th * 42.0, t * 105.0, 0 * t, 2, 51); g = fbm(th * 4.0, t * 7.0, 0 * t, 3, 52)
    return np.clip((n + .42 * g - .74) * 9, 0, 1)

def crown_solid(x, f, z):
    t, u, v, hl, w = crown_param(x, f, z)
    sh = crown_r(t, u, v, hl, w)
    th = crown_theta(u, v, t)
    near = np.abs(sh) < 1.2
    out = np.where(sh > 0, sh, sh).astype(F)
    tt, hh = t[near], th[near]
    if near.any():
        b = blue_sd(hh, tt); g_ = gold_sd(hh, tt)
        sm = np.clip(b / .10 + .5, 0, 1); sm = sm * sm * (3 - 2 * sm)
        raise_ = .05 + .10 * sm + .080 * np.exp(-((b - .06) / .12)**2)
        bd = np.abs(band_d(hh, tt))
        raise_ = raise_ + .03 * np.clip((1.16 - bd) / .05, 0, 1)
        sd_, si = strip_d(hh, tt)
        raise_ = raise_ + .03 * np.clip((1.05 - np.abs(sd_)) / .05, 0, 1) * np.clip(si / .05, 0, 1) * (b > .15)
        m = chip(hh, tt)
        px, pf, pz = x[near], f[near], z[near]
        raise_ = raise_ - m * (.16 + .07 * fbm(px * 2.2, pf * 2.2, pz * 2.2, 3, 61))
        raise_ = raise_ - .035 * rubdots(hh, tt) * sm * (1 - m)
        # fırça izi / düzgün olmayan yüzey
        raise_ = raise_ + sm * .012 * fbm(hh * 3.0, tt * 34.0, 0 * tt, 3, 63) + .02 * fbm(px * .35, pf * .35, pz * .35, 2, 64)
        rim = (tt - 1.0) * 17.0 + .05 * fbm(hh * 6, tt * 0, 0 * tt, 3, 65)
        # kenar kopuğu: rim aşağı iner
        rim = rim + m * np.clip((tt - .90) / .05, 0, 1) * .75
        s2 = sh[near] - raise_
        s2 = smax(s2, rim, .22)
        s2 = smax(s2, -g_ * .9, .07)
        out[near] = s2
    far = ~near
    out[far] = np.maximum(sh[far], (t[far] - 1.0) * 17.0)
    out = np.maximum(out, (-.10 - t) * 12.0)
    return out

# ------------------------------------------------ URAEUS
def _upx(px, y):
    t = (367 - y) / 228.0
    xcm = (px - 370) / 15.15
    w = CW0 + (CW1 - CW0) * t
    n = 2.32 - 0.27 * min(max(t * 1.3, 0), 1)
    th = np.arcsin(np.sign(xcm) * min(abs(xcm / w), 1)**(n / 2))
    return th, t
def _upts(L, off):
    return [tuple(crown_pos(*_upx(a, b), off)) for a, b in L]
def _sm(L, m=4):
    P, _ = _cat([tuple(p) + (0,) if len(p) == 2 else tuple(p) for p in L], [0] * len(L), m)
    return [tuple(p[:2]) for p in P]
_U_cord = _upts(_sm([(373, 134), (372.5, 150), (370, 168), (368.5, 184), (371, 204), (370, 226), (369, 240)]), .24)
_U_l = _upts(_sm([(369, 236), (358, 232), (343, 234), (327, 242), (319, 254), (325, 265), (341, 268), (356, 264), (366, 254)]), .22)
_U_r = _upts(_sm([(370, 212), (376, 227), (390, 234), (411, 239), (424, 250), (424, 263), (411, 271), (395, 270), (381, 261), (372, 250)]), .22)
_U_top = [tuple(crown_pos(0.0, 1.0, .20) + np.array([0, -a, b])) for a, b in [(0, 0), (.25, .14), (1.2, -.18), (2.6, -.72), (4.0, -1.25)]]
def uraeus(x, f, z):
    d = chain(x, f, z, _U_cord, np.linspace(.20, .27, len(_U_cord)))
    d = np.minimum(d, chain(x, f, z, _U_top, [.22, .24, .24, .22, .18]))
    d = smin(d, chain(x, f, z, _U_l, [.29] * len(_U_l)), .12)
    d = smin(d, chain(x, f, z, _U_r, [.29] * len(_U_r)), .12)
    # gövde kütüğü (kırık kobra başlığı)
    P = [crown_pos(*_upx(a, b), o) for a, b, o in [(369, 222, .18), (369, 244, .34), (370, 280, .40), (371, 313, .46)]]
    W = [(.30, .26), (.52, .46), (.55, .52), (.80, .62)]
    for i in range(3):
        a, b = P[i], P[i + 1]
        ba = b - a; L2 = float(ba @ ba)
        h = np.clip(((x - a[0]) * ba[0] + (f - a[1]) * ba[1] + (z - a[2]) * ba[2]) / L2, 0, 1)
        rx = x - a[0] - ba[0] * h; rf = f - a[1] - ba[1] * h; rz = z - a[2] - ba[2] * h
        rn = np.sqrt(rf * rf + rz * rz)
        wx = W[i][0] + (W[i + 1][0] - W[i][0]) * h; wn = W[i][1] + (W[i + 1][1] - W[i][1]) * h
        e = (((np.abs(rx) / wx)**3.2 + (rn / wn)**3.2)**(1 / 3.2) - 1) * np.minimum(wx, wn)
        d = smin(d, e, .10)
    # kırık yüzey
    d = d + .035 * fbm(x * 3.2, f * 3.2, z * 3.2, 3, 71) * np.clip((38.5 - z) / 2, .15, 1)
    b0 = crown_pos(*_upx(371, 306), 0)
    cut = (b0[2] - z) * .80 + (f - b0[1] - .25) * .60 - .10 + .10 * fbm(x * 2.4, f * 2.4, z * 2.4, 3, 72)
    d = np.maximum(d, np.where(z < b0[2] + 3.4, cut, -9))
    return d

# ------------------------------------------------ GERDANLIK PARAMETRESİ
def collar_curve(n=720):
    half = [(0, -4.6, 10.1), (2.6, -4.0, 11.3), (4.6, -2.4, 12.3), (5.5, -.6, 12.2), (5.5, 1.2, 11.0), (4.9, 2.7, 9.6), (3.7, 4.0, 8.2), (2.2, 4.9, 7.2), (0.9, 5.3, 6.75), (0, 5.35, 6.65)]
    pts = half + [(-a, b, c) for a, b, c in half[-2:0:-1]]
    P = np.array(pts + pts[:1] + pts[1:3], float); P = np.vstack([np.array(pts[-1]), P])
    O = []
    m = 60
    for i in range(1, len(pts) + 1):
        a, b, c, d_ = P[i-1], P[i], P[i+1], P[i+2]
        for t in np.arange(m) / m:
            O.append(.5 * (2*b + (c-a)*t + (2*a-5*b+4*c-d_)*t*t + (3*b-a-3*c+d_)*t**3))
    O = np.array(O)
    # yüzeye oturt
    for _ in range(12):
        e = .02
        def S(p): return body_soft(p[:, 0].astype(F), p[:, 1].astype(F), p[:, 2].astype(F)).astype(float)
        d0 = S(O); G = np.stack([(S(O + np.eye(3)[k] * e) - S(O - np.eye(3)[k] * e)) / (2 * e) for k in range(3)], 1)
        O = O - (d0 / np.maximum((G * G).sum(1), .2))[:, None] * G * .8
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(np.vstack([O, O[:1]]), axis=0), axis=1))])
    T = np.linspace(0, s[-1], n + 1)[:-1]
    C = np.stack([np.interp(T, s, np.append(O[:, k], O[0, k])) for k in range(3)], 1)
    for _ in range(90): C = (np.roll(C, 1, 0) + 2 * C + np.roll(C, -1, 0)) / 4
    return C, s[-1]

def collar_param(P, chunk=15000):
    """P (N,3) x,f,z -> (s [0..1), rho cm; rho<0 boyun tarafı)"""
    C, L = collar_curve()
    n = len(C); D = np.roll(C, -1, 0) - C; DD = (D * D).sum(1)
    nout = C - np.array([0, .8, 15.0]); nout /= np.linalg.norm(nout, axis=1)[:, None]
    S = np.empty(len(P), F); R = np.empty(len(P), F)
    C32 = C.astype(F)
    for a in range(0, len(P), chunk):
        p = P[a:a + chunk].astype(F)
        d2 = ((p[:, None, :] - C32[None])**2).sum(2)
        i = d2.argmin(1)
        best = None
        for k in (-1, 0):
            j = (i + k) % n
            h = np.clip(((p - C[j]) * D[j]).sum(1) / DD[j], 0, 1)
            q = C[j] + D[j] * h[:, None]
            dist = np.linalg.norm(p - q, axis=1)
            if best is None: best = (dist, j, h, q)
            else:
                m = dist < best[0]
                best = tuple(np.where(m if v.ndim == 1 else m[:, None], w, v) for v, w in zip(best, (dist, j, h, q)))
        dist, j, h, q = best
        sg = np.sign(((p - q) * nout[j]).sum(1))
        S[a:a + chunk] = ((j + h) / n) % 1.0; R[a:a + chunk] = dist * sg
    return S, R, L


def collar_arc(R=8.4, nr=43):
    """Her rho için yüzey üstündeki eş uzaklık eğrisinin ön ortadan işaretli yay uzunluğu: A[nr, n]"""
    C, L = collar_curve(); n = len(C)
    T = np.roll(C, -1, 0) - np.roll(C, 1, 0); T /= np.linalg.norm(T, axis=1)[:, None]
    e1 = C - np.array([0, .8, 15.0]); e1 -= (e1 * T).sum(1)[:, None] * T; e1 /= np.linalg.norm(e1, axis=1)[:, None]
    e2 = np.cross(T, e1)
    def Sf(p): return body_soft(p[:, 0].astype(F), p[:, 1].astype(F), p[:, 2].astype(F)).astype(float)
    m = Sf(C + e2 * .6) < Sf(C - e2 * .6); e2[m] *= -1
    rs = np.linspace(0, R, nr); A = np.zeros((nr, n)); mid = n // 2
    for i, r in enumerate(rs):
        rr = max(r, .02)
        lo = np.full(n, -1.9); hi = np.full(n, 1.5)
        for _ in range(26):
            md = (lo + hi) / 2
            p = C + rr * (np.cos(md)[:, None] * e1 + np.sin(md)[:, None] * e2)
            out = Sf(p) > 0
            hi = np.where(out, md, hi); lo = np.where(out, lo, md)
        for _ in range(int(2 + r * 3)):                        # kıvrım gürültüsünü yumuşat
            md = (np.roll(md, 1) + 2 * md + np.roll(md, -1)) / 4
        p = C + rr * (np.cos(md)[:, None] * e1 + np.sin(md)[:, None] * e2)
        sg = np.linalg.norm(np.diff(p, axis=0), axis=1)
        a = np.concatenate([[0], np.cumsum(sg)])
        A[i] = a - a[mid]
    return A.astype(F), L

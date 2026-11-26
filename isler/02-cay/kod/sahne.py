import bpy, sys, math, random, os
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, sahne_kit; importlib.reload(sahne_kit)
from sahne_kit import *

arg = dict(a.split('=', 1) for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []))
OUT = arg.get('out', 'render/test'); SPP = int(arg.get('spp', 128)); W = int(arg.get('w', 750))
CROP = arg.get('crop')          # x0,y0,x1,y1 (0..1, sol alt)
DEN = int(arg.get('den', 1))
rng = random.Random(7); nr = np.random.default_rng(7)

for c in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for x in list(c): c.remove(x)
sc = bpy.context.scene

# =================================================================== MALZEME
def m_glass(inner=False):
    m, g = mat('cam_ic' if inner else 'cam')
    o = g.obj()
    sm = g.noise(g.map(o, scale=(1, 1, .7)), 70, 5, .6, 1.2)
    smear = g.mr(sm, .52, .72, 0, 1, True)
    fine = g.noise(g.map(o, scale=(1, 1, .25)), 900, 3, .6)
    r = g.mul(smear, g.mr(fine, .35, .7, .0, .085))
    nrm = None
    if not inner:
        for (th, zc, rad, rot, st) in ((-2.02, .0685, .0235, .25, 1.0), (-1.72, .0640, .0215, .35, .7), (-.95, .030, .0252, -.3, .8)):
            cx_, cy_ = rad * math.cos(th), rad * math.sin(th)
            dv_ = g.vm('SUBTRACT', o, (cx_, cy_, zc))
            uu = g.vm('DOT_PRODUCT', dv_, (-math.sin(th) * math.cos(rot), math.cos(th) * math.cos(rot), math.sin(rot)))
            vv = g.vm('DOT_PRODUCT', dv_, (math.sin(th) * math.sin(rot), -math.cos(th) * math.sin(rot), math.cos(rot)))
            nn = g.vm('DOT_PRODUCT', dv_, (math.cos(th), math.sin(th), 0))
            e2 = g.math('SQRT', g.add(g.math('POWER', g.math('DIVIDE', uu, .0062), 2.0), g.math('POWER', g.math('DIVIDE', vv, .0088), 2.0)))
            msk = g.mul(g.mr(g.add(e2, g.mul(g.sub(g.noise(o, 260, 4), .5), .9)), .75, 1.05, 1, 0, True), g.mr(nn, -.008, -.006))
            rd = g.math('SQRT', g.add(g.mul(g.mul(uu, uu), 1.5), g.math('POWER', g.sub(vv, .0015), 2.0)))
            rd = g.add(rd, g.mul(g.sub(g.noise(o, 190, 3), .5), .0022))
            ridge = g.mr(g.math('SINE', g.mul(rd, 2 * math.pi / .00048)), -.2, .6)
            r = g.add(r, g.mul(g.mul(msk, g.add(g.mul(g.mul(ridge, g.mr(g.noise(o, 420, 4, .65), .40, .60)), .055), .022)), st))
    if inner:
        fog = g.attr('bugu'); r = g.add(r, g.mul(fog, g.mr(g.noise(o, 2600, 3), .3, .7, .10, .26)))
    b = g.n('BsdfGlass', Color=(.985, .995, .99), Roughness=r, IOR=1.517, Normal=nrm).outputs[0]
    g.out(b); return m

def m_tea(k=1.0):
    m, g = mat('cay')
    ior = g.mixf(g.attr('iface'), 1.333, 1.333 / 1.517)
    b = g.n('BsdfGlass', Color=(1, 1, 1), Roughness=0.0, IOR=ior).outputs[0]
    vol = g.n('VolumeCoefficients')
    vol.inputs['Absorption Coefficients'].default_value = (14 * k, 43 * k, 130 * k)
    g.out(b, vol.outputs[0]); return m

def m_drop(k):
    m, g = mat('damla'); vol = None
    if k:
        vol = g.n('VolumeCoefficients'); vol.inputs['Absorption Coefficients'].default_value = (14 * k, 43 * k, 130 * k); vol = vol.outputs[0]
    g.out(g.n('BsdfGlass', Color=(1, 1, 1), Roughness=0.0, IOR=1.333).outputs[0], vol); return m

def m_bubble():
    m, g = mat('kabarcik')
    fr = g.n('Fresnel', IOR=1.33).outputs[0]
    fr = g.math('MINIMUM', g.mul(fr, 1.8), 1.0)
    g.out(g.mixsh(fr, g.n('BsdfTransparent', Color=(.99, .97, .95)).outputs[0], g.n('BsdfGlossy', Color=(1, 1, 1), Roughness=.02).outputs[0])); return m

def m_porcelain(pattern=True):
    m, g = mat('porselen')
    o = g.obj(); x, y, z = g.sep(o)
    rr = g.math('SQRT', g.add(g.mul(x, x), g.mul(y, y)))
    wob = g.mul(g.sub(g.noise(o, 60, 3), .5), .0007)
    r = g.add(rr, wob)
    th = g.math('ARCTAN2', y, x)
    base = g.mix(g.mr(g.noise(o, 35, 4), .35, .7), (.83, .815, .775), (.80, .78, .735))
    col = base
    if pattern:
        edge = lambda a, b: g.mul(g.mr(r, a - .00012, a + .00012), g.mr(r, b - .00012, b + .00012, 1, 0))
        u = g.sub(g.math('FRACT', g.mul(g.add(th, math.pi), 32 / (2 * math.pi))), .5)
        aL = g.mul(r, 2 * math.pi / 32); sL = g.math('ABSOLUTE', g.mul(u, aL)); hw = g.mul(aL, .255)
        dz = g.math('MAXIMUM', g.sub(.0435, r), 0.0)
        dd = g.sub(g.math('SQRT', g.add(g.mul(sL, sL), g.mul(dz, dz))), hw)
        petal = g.mul(g.mr(dd, -.00007, .00007, 1, 0), g.mr(r, .05275, .0529, 1, 0))
        band = g.math('MAXIMUM', edge(.0543, .0552), edge(.0378, .0382))
        mask = g.math('MAXIMUM', petal, band)
        up = g.mr(g.sep(g.n('NewGeometry').outputs['Normal'])[2], .05, .2)
        wear = g.mr(g.noise(o, 900, 5, .7), .27, .36, .45, 1)
        wear2 = g.mr(g.noise(o, 140, 4, .65), .34, .5, .86, 1)
        mask = g.mul(g.mul(mask, up), g.mul(wear, wear2))
        red = g.mix(g.noise(o, 300, 3), (.42, .012, .010), (.50, .025, .016))
        col = g.mix(g.mul(mask, .97), base, red)
        # çay lekesi: oyukta ve kenara doğru hafif kahverengi iz
        stain = g.mul(g.mr(r, .0185, .0225), g.mr(r, .0225, .029, 1, 0))
        stain = g.mul(stain, g.mr(g.noise(o, 130, 5, .65, .8), .42, .68))
        col = g.mix(g.mul(stain, .55), col, (.36, .17, .06))
    mk = None
    for k_, (rt_, sx_) in enumerate(((.5, 150), (1.7, 190), (-.8, 170))):
        e_ = g.mr(g.noise(g.map(o, loc=(k_ * 3, 1, 0), rot=(0, 0, rt_), scale=(1, sx_ / 12, 1)), 120, 2, .5), .70, .74); mk = e_ if mk is None else g.math('MAXIMUM', mk, e_)
    mk = g.mul(mk, g.mr(rr, .050, .030, 0, 1)); col = g.mix(g.mul(mk, .30), col, (.40, .40, .39))
    sp_ = g.mul(g.mr(g.voro(g.map(o, loc=(3, 8, 1)), 210), .05, .08, 1, 0), g.mr(g.noise(o, 45, 3), .55, .62)); col = g.mix(g.mul(sp_, .6), col, (.45, .26, .12))
    rough = g.add(.055, g.mul(g.mr(g.noise(o, 120, 5, .62, 1), .42, .72), .17)); rough = g.add(rough, g.mul(mk, .15))
    if pattern:
        th0 = -2.02; c0 = (.0560 * math.cos(th0), .0560 * math.sin(th0), .0163)
        dc_ = g.vm('LENGTH', g.vm('SUBTRACT', o, c0)); chip = g.mr(g.add(dc_, g.mul(g.sub(g.noise(o, 700, 4), .5), .0011)), .00165, .00185, 1, 0)
        col = g.mix(chip, col, g.mix(g.noise(o, 1500, 4), (.55, .47, .37), (.36, .28, .20))); rough = g.add(rough, g.mul(chip, .6))
        # çentikten içeri uzanan çay emmiş kılcal çatlak
        t_ = (-math.sin(th0), math.cos(th0), 0); rd_ = (math.cos(th0), math.sin(th0), 0)
        ac = g.add(g.vm('DOT_PRODUCT', o, t_), g.add(g.mul(g.sub(g.noise(o, 70, 4, .6), .5), .0075), g.mul(g.sub(g.noise(o, 420, 3, .6), .5), .0016))); rad_ = g.vm('DOT_PRODUCT', o, rd_)
        crk = g.mul(g.mr(g.math('ABSOLUTE', ac), .00004, .00013, 1, 0), g.mul(g.mr(rad_, .030, .036), g.mr(rad_, .0562, .0566, 1, 0))); col = g.mix(g.mul(crk, .62), col, (.22, .12, .06))
    n = g.bump(g.noise(o, 55, 2, .5), .00035, .35)
    n = g.bump(g.mr(g.voro(o, 420), .0, .035, 1, 0), .00012, .5, n)        # tek tük sır iğne deliği
    b = principled(g, Base_Color=col, Roughness=rough, IOR=1.52, Normal=n, Subsurface_Weight=.22,
                   Subsurface_Radius=(1, .8, .6), Subsurface_Scale=.0012)
    if pattern:
        pass
    g.out(b); return m

def m_steel():
    m, g = mat('celik')
    o = g.obj()
    sc1 = g.noise(g.map(o, rot=(0, 0, .35), scale=(1, 30, 1)), 260, 3, .6)
    sc2 = g.noise(g.map(o, rot=(0, 0, -.9), scale=(1, 34, 1)), 300, 2, .5)
    sc3 = g.noise(g.map(o, rot=(0, 0, 1.9), scale=(1, 40, 1)), 260, 2, .5)
    scr = g.math('MAXIMUM', g.math('MAXIMUM', g.mr(sc1, .64, .76), g.mr(sc2, .66, .78)), g.mr(sc3, .66, .78))
    sm = g.mr(g.noise(o, 95, 5, .6, 1.5), .42, .72)
    vd = g.voro(o, 150); vr = g.sep(g.voro(o, 150, out='Color'))[0]; vsz = g.mr(vr, .55, 1, 0, .30)
    spot = g.mul(g.mr(g.math('ABSOLUTE', g.sub(vd, vsz)), .012, .04, 1, 0), g.mr(vr, .55, .6)); spotf = g.mul(g.mr(g.sub(vd, vsz), -.03, .0, 1, 0), g.mr(vr, .55, .6))
    rough = g.add(g.add(.060, g.mul(sm, .16)), g.mul(scr, .13)); rough = g.add(rough, g.mul(g.mr(g.noise(g.map(o, scale=(.35, 1, 1)), 240, 5, .6), .5, .62), .06)); rough = g.add(rough, g.mul(g.mr(g.noise(o, 520, 5, .65), .56, .70), .05))
    n = g.bump(scr, .000009, .20)
    n = g.bump(g.noise(o, 160, 3, .5), .00022, .25, n)
    col = g.mix(sm, (.645, .65, .66), (.58, .585, .595))
    g.out(principled(g, Base_Color=col, Metallic=1.0, Roughness=rough, Normal=n)); return m

def m_sugar(core=False, loose=False):
    m, g = mat('seker_oz' if core else ('seker_tek' if loose else 'seker'))
    o = g.obj(); z = g.sep(o)[2]
    ob_rand = g.n('ObjectInfo').outputs['Random']
    edge = g.add(z, g.mul(g.sub(g.noise(o, 260, 3), .5), .004))
    stain = g.mr(edge, -.0052, -.0035, 1, 0, True)
    col = g.mix(g.mul(stain, g.attr('islak')), (.985, .983, .975), (.62, .34, .13))
    if core:
        b = principled(g, Base_Color=g.mix(g.mul(stain, g.attr('islak')), (.90, .895, .875), (.62, .34, .13)), Roughness=.13, Subsurface_Weight=1.0, Subsurface_Radius=(1, .93, .85), Subsurface_Scale=.0009, IOR=1.54)
    else:
        gl = g.n('BsdfGlass', Color=col, Roughness=.06, IOR=1.54).outputs[0]
        df = principled(g, Base_Color=col, Roughness=.10, IOR=1.56)
        tr = g.n('BsdfTranslucent', Color=col).outputs[0]
        b = g.mixsh(.62 if loose else .55, g.mixsh(.35 if loose else .4, df, tr), gl)
    g.out(b); return m

def m_marble():
    """Marmara mermeri: beyaz-gri zemin, yönlü gri bantlar, yıpranmış cila."""
    m, g = mat('mermer')
    o = g.obj()
    warp = g.vm('SCALE', g.vm('SUBTRACT', g.noise(o, 4.5, 5, .55, color=True), (.5, .5, .5)), scale=.16)
    p = g.map(g.vm('ADD', o, warp), rot=(0, 0, .62))
    fw = g.vm('SCALE', g.vm('SUBTRACT', g.noise(o, 38, 4, .6, color=True), (.5, .5, .5)), scale=.011)
    p2 = g.vm('ADD', p, fw)
    bands = g.noise(g.map(p2, scale=(1.0, 5.5, 1)), 5.2, 8, .64)
    soft = g.noise(g.map(p2, loc=(3, 1, 0), scale=(1, 3.0, 1)), 2.4, 5, .55)
    thin = g.math('ABSOLUTE', g.sub(g.noise(g.map(p2, loc=(1.3, 7, 0), scale=(1, 4.2, 1)), 5.0, 6, .6), .5))
    col = g.ramp(bands, [(.33, (.135, .137, .138)), (.43, (.25, .25, .247)), (.51, (.46, .457, .447)), (.60, (.60, .597, .582)), (.72, (.67, .667, .65))])
    col = g.mix(g.mul(g.mr(soft, .40, .60, 1, 0, True), .45), col, (.30, .302, .30))
    vein = g.mul(g.mr(thin, .0, .020, 1, 0, True), g.mr(g.noise(o, 9, 4), .42, .62))
    col = g.mix(g.mul(vein, .75), col, (.13, .128, .122))
    # kristal dokusu
    cr = g.voro(o, 850, out='Color'); cr_v = g.sep(cr)[0]
    col = g.mix(g.mul(g.mr(cr_v, .2, 1), .18), col, (.84, .83, .81))
    col = g.mix(g.mul(g.mr(g.voro(g.map(o, loc=(2, 2, 2)), 1500), .0, .5), .05), col, (.3, .3, .3))
    # yaşlanma: sarımsı ton, halka lekeler
    col = g.mix(g.mul(g.mr(g.noise(o, 7, 6, .65), .45, .72), .30), col, (.50, .43, .33), 'MULTIPLY')
    x, y, z = g.sep(o)
    ring_r, ring_c = 0, 0
    for (cx, cy, R, w, s) in ((-.092, -.055, .0182, .0010, .9), (.135, .045, .0288, .0012, .6), (-.105, -.040, .0184, .0008, .5)):
        dx, dy = g.sub(x, cx), g.sub(y, cy)
        rr = g.math('SQRT', g.add(g.mul(dx, dx), g.mul(dy, dy)))
        rr = g.add(rr, g.mul(g.sub(g.noise(o, 90, 3), .5), .0012))
        a = g.mr(g.math('ABSOLUTE', g.sub(rr, R)), w * .3, w, 1, 0, True)
        a = g.mul(g.mul(a, s), g.mr(g.noise(g.map(o, loc=(cx * 50, 0, 0)), 75, 4, .6), .40, .60))
        ring_r = g.math('MAXIMUM', ring_r, a) if ring_r != 0 else a
    col = g.mix(g.mul(ring_r, .42), col, (.34, .22, .12))
    # cila: çizik, silme izi, parmak lekesi
    wipe = g.noise(g.map(o, rot=(0, 0, .25), scale=(1, 5, 1)), 16, 6, .68, .6)
    smud = g.noise(o, 46, 5, .62, 1.4)
    scr = None
    for k, (rot, sx, th) in enumerate(((.2, 210, .70), (1.1, 260, .71), (-.6, 240, .705), (2.3, 300, .715), (.75, 330, .715), (-1.2, 280, .715), (.02, 240, .70))):
        s = g.mr(g.noise(g.map(o, loc=(k, k * 2, 0), rot=(0, 0, rot), scale=(1, sx, 1)), 13 + 4 * k, 2, .5), th, th + .05)
        scr = s if scr is None else g.math('MAXIMUM', scr, s)
    etch = g.mul(g.mr(g.noise(o, 34, 5, .55, .9), .555, .575), g.mr(g.noise(o, 11, 3), .45, .55))
    rough = g.add(.105, g.mul(g.mr(wipe, .38, .70), .15)); rough = g.add(rough, g.mul(etch, .15))
    rough = g.add(rough, g.mul(g.mr(smud, .48, .74), .14))
    rough = g.add(rough, g.mul(g.sub(g.sep(cr)[1], .5), .10)); rough = g.add(rough, g.mul(scr, .20)); rough = g.add(rough, g.mul(ring_r, .22))
    rough = g.add(rough, g.mul(g.mr(g.noise(o, 1300, 2), .4, .7), .06))
    pit = g.mul(g.mr(g.voro(o, 330), .03, .10, 1, 0), g.mr(g.noise(o, 22, 4), .52, .66))
    n = g.bump(g.noise(o, 26, 3, .5), .0009, .16)
    n = g.bump(g.noise(o, 210, 4, .6), .00007, .30, n)
    n = g.bump(g.mul(g.sep(cr)[2], g.mr(g.voro(o, 850, 'DISTANCE_TO_EDGE'), 0, .08)), .000012, .45, n)
    n = g.bump(g.math('SUBTRACT', g.mul(scr, -.5), pit), .00009, .7, n)
    col = g.mix(g.mul(scr, .22), col, (.74, .73, .71))
    dust = g.mul(g.mr(g.voro(g.map(o, loc=(5, 3, 0)), 340), .055, .085, 1, 0), g.mr(g.noise(g.map(o, loc=(9, 1, 0)), 30, 4), .50, .60))
    col = g.mix(g.mul(dust, .55), col, (.42, .37, .30)); rough = g.add(rough, g.mul(dust, .4))
    b = principled(g, Base_Color=g.mix(g.mul(pit, .5), col, (.22, .19, .15)), Roughness=rough, IOR=1.5, Normal=n,
                   Subsurface_Weight=.06, Subsurface_Radius=(1, .95, .9), Subsurface_Scale=.002)
    g.out(b); return m

def m_flat(name, col, rough=.6, nscale=None, col2=None, bump=0, **k):
    m, g = mat(name); o = g.obj(); c = col; n = None
    if nscale:
        f = g.noise(o, nscale, 5, .6); c = g.mix(g.mr(f, .35, .68), col, col2 or tuple(v * .7 for v in col))
        if bump: n = g.bump(g.noise(o, nscale * 6, 5, .6), bump, .6)
    g.out(principled(g, Base_Color=c, Roughness=rough, Normal=n, **k)); return m

def m_simit():
    m, g = mat('simit'); o = g.obj()
    z = g.sep(o)[2]
    f = g.noise(o, 60, 6, .62); f2 = g.noise(o, 260, 4, .6)
    t = g.add(g.mr(z, .006, .030, 0, .68), g.mul(g.sub(f, .5), .85))
    c = g.ramp(t, [(.02, (.46, .25, .085)), (.25, (.34, .135, .032)), (.52, (.20, .062, .015)), (.80, (.115, .034, .009)), (1, (.06, .02, .007))])
    n = g.bump(g.add(g.mul(f, .8), g.mul(f2, .25)), .0007, .6)
    g.out(principled(g, Base_Color=c, Roughness=g.mr(f2, .3, .7, .5, .75), Normal=n, Specular_IOR_Level=.10)); return m

def m_base():
    m, g = mat('cam_alt'); o = g.obj()
    n = g.bump(g.add(g.voro(o, 900), g.mul(g.noise(o, 300, 4), .6)), .00030, .55)
    g.out(g.n('BsdfGlass', Color=(.985, .995, .99), Roughness=.20, IOR=1.517, Normal=n).outputs[0]); return m
M = dict(cam_alt=m_base(), cam=m_glass(), cam_ic=m_glass(True), cay=m_tea(1.25), cay2=m_tea(1.2), kab=m_bubble(), pors=m_porcelain(), pors0=m_porcelain(False),
         celik=m_steel(), seker=m_sugar(), seker_oz=m_sugar(True), seker_tek=m_sugar(False, True), mermer=m_marble(), damla=m_drop(1.6), damla_koyu=m_drop(3.2),
         su=m_drop(0), susam=m_flat('susam', (.76, .57, .32), .5, 900, (.60, .39, .17), Specular_IOR_Level=.2, Subsurface_Weight=.35, Subsurface_Scale=.0007),
         kirinti=m_flat('kirinti', (.45, .22, .08), .7, 900, (.62, .42, .2)), simit=m_simit())

# =================================================================== BARDAK
OUTER = [(0, 1.3), (9, 1.25), (15.2, 1.0), (16.6, .35), (17.5, 0), (18.4, .12), (19.2, .75), (19.9, 2.2), (20.8, 5), (22.2, 9), (24.1, 14.5), (25.35, 20), (25.6, 25),
         (24.9, 31), (23.3, 38), (21.4, 46), (20.55, 53), (20.9, 60), (22.4, 68), (24.6, 76), (26.5, 82.5), (27.15, 85.0)]
RIM = [(27.22, 85.6), (27.1, 86.05), (26.7, 86.32), (26.25, 86.2), (25.95, 85.8)]
INNER_UP = [(0, 8.4), (6, 8.5), (12, 9.1), (17, 11.2), (20.4, 14.6), (22.7, 19.5), (23.35, 25), (22.9, 31), (21.4, 38), (19.6, 46), (18.8, 53), (19.2, 60), (20.75, 68),
            (23.0, 76), (25.0, 82.5), (25.75, 85.2)]
def pert_factory(seed, amp):
    q = random.Random(seed)
    C = [(q.choice((1, 2, 2, 3, 4, 5)), q.uniform(0, 6.28), q.uniform(.06, .28), q.uniform(0, 6.28), q.uniform(.4, 1)) for _ in range(9)]
    def d(th, zmm):
        s = 0
        for (n, p, kz, pz, a) in C: s = s + a * np.cos(n * th + p + .02 * zmm) * np.cos(kz * zmm + pz)
        return s * amp / 3
    return d
dO, dI = pert_factory(3, .085 * MM), pert_factory(5, .11 * MM)

def fnoise(x, y, seed, oct=4):
    rq = np.random.default_rng(seed); out = 0; amp = 1; f = 1.0
    for _ in range(oct):
        for _ in range(5):
            a = rq.uniform(0, 6.283); k = f * rq.uniform(.6, 1.5); out = out + amp * np.sin(k * (x * math.cos(a) + y * math.sin(a)) + rq.uniform(0, 6.283)) / 5
        f *= 2.1; amp *= .62
    return out
def dry_wall(name, loc, inn, z_c, seg=1700, nz=170):
    q = np.random.default_rng(21); R0 = 24.0; zt = inn[-1, 1] / MM; th = np.linspace(0, 2 * np.pi, seg, endpoint=False); zz = np.linspace(zt, z_c, nz)
    S, Z = np.meshgrid(th * R0, zz); H = np.zeros((nz, seg)); L = 2 * math.pi * R0; ds = L / seg; dz = (zt - z_c) / (nz - 1)
    cx, sx = np.cos(th) * 1.0, np.sin(th) * 1.0
    patch = fnoise(np.tile(th * R0 * .22, (nz, 1)), Z * .35, 3, 4)                       # yamalı yoğunluk
    up = (Z - z_c) / (zt - z_c); reach = .55 + .30 * fnoise(np.tile(th * 5, (nz, 1)), Z * 0, 8, 3)  # buğunun çıktığı yükseklik değişken
    dens = np.clip(1.15 - up / np.clip(reach, .15, 1.2), 0, 1) * np.clip(.65 + .9 * patch, .05, 1.3)
    track = np.zeros((nz, seg)); beads = []
    for k in range(13):                                                              # akma izleri
        s0 = q.uniform(0, L); z1 = z_c + (zt - z_c) * q.uniform(.45, .95); z0 = z_c + (zt - z_c) * max(0, q.uniform(-.5, .35)); w = q.uniform(.35, .75)
        path = s0 + .35 * np.sin(zz * q.uniform(.6, 1.6) + q.uniform(0, 6)) + .12 * np.sin(zz * 4 + k)
        d = np.abs((S - path[:, None] + L / 2) % L - L / 2); on = (Z < z1) & (Z > z0); track = np.maximum(track, np.where(on, np.clip(1.4 - d / w, 0, 1), 0))
        if z0 > z_c + .6: beads.append((np.interp(z0, zz[::-1], path[::-1]), z0, w * 1.15, 1.45))
    th_sp = math.radians(24); d = np.abs((S - th_sp * R0 + L / 2) % L - L / 2); track = np.maximum(track, np.clip(1.5 - d / 2.1 + .4 * patch, 0, 1) * .93)   # kaşığın sildiği yer
    cand = [(q.uniform(0, L), z_c + (zt - z_c) * q.uniform(0, 1) ** 1.25) for _ in range(26000)]
    rad = np.sort(.065 * q.uniform(0, 1, len(cand)) ** (-1 / 2.15))[::-1]; rad = np.minimum(rad, .95); rad[rad > .6] *= q.uniform(.6, 1, (rad > .6).sum())
    placed = np.zeros((0, 3)); occ = np.full((nz, seg), False); drops = list(beads); fogmask = np.ones((nz, seg))
    for (s0, z0), r_ in zip(cand, rad):
        i = int(round((zt - z0) / dz)); j = int(s0 / ds) % seg; i = min(max(i, 0), nz - 1)
        if q.uniform() > dens[i, j] * (1.0 if r_ < .25 else .75): continue
        if q.uniform() < track[i, j] * .992: continue
        if occ[i, j] and q.uniform() > .10: continue
        drops.append((s0, z0, r_, 1 + max(0, r_ - .25) * q.uniform(0, .7)))
        rr = r_ * 1.12; ii = int(rr / dz) + 1; jj = int(rr / ds) + 1; occ[max(0, i - ii):i + ii + 1, np.arange(j - jj, j + jj + 1) % seg] = True
    for (s0, z0, r_, el) in drops:
        ii = int(1.6 * r_ * el / dz) + 2; jj = int(1.4 * r_ / ds) + 2; i = int(round((zt - z0) / dz)); j = int(s0 / ds)
        I = np.arange(max(0, i - ii), min(nz, i + ii + 1)); J = np.arange(j - jj, j + jj + 1); JJ = J % seg
        if len(I) == 0: continue
        X, Y = np.meshgrid(J * ds - s0, zz[I] - z0); Y = np.where(Y > 0, Y / (el * 1.08), Y / el); an = np.arctan2(Y, X); p1, p2 = q.uniform(0, 6.28, 2); irr = .07 + .12 * min(1, r_ / .5)
        dd = np.hypot(X, Y) / (r_ * (1 + irr * np.sin(2 * an + p1) + irr * .7 * np.sin(3 * an + p2)))
        h = r_ * .40 * np.clip(1 - dd ** 2, 0, 1) ** .72; sub = H[np.ix_(I, JJ)]; H[np.ix_(I, JJ)] = np.maximum(sub, h)
        fm = fogmask[np.ix_(I, JJ)]; fogmask[np.ix_(I, JJ)] = np.minimum(fm, np.clip((dd - .9) / (.45 if r_ > .2 else .2), 0, 1))
    H *= np.clip((zt - Z) / .4, 0, 1) * np.clip((Z - z_c) / .12, 0, 1)
    fog = np.clip(dens * 1.7 - .05, 0, 1) * (1 - track) * fogmask
    base = np.interp(zz * MM, inn[:, 1], inn[:, 0])[:, None] + np.stack([dI(th, z_) for z_ in zz]) - H * MM
    V = np.stack([base * np.cos(th)[None], base * np.sin(th)[None], np.repeat(zz[:, None] * MM, seg, 1)], -1).reshape(-1, 3)
    i0 = (np.arange(nz - 1)[:, None] * seg + np.arange(seg)[None]).ravel(); j2 = (np.arange(nz - 1)[:, None] * seg + (np.arange(seg) + 1)[None] % seg).ravel()
    F = np.stack([i0, j2, j2 + seg, i0 + seg], 1)
    ob = mesh_obj(name, V, F.tolist(), (M['cam_ic'],), loc=loc); at = ob.data.attributes.new('bugu', 'FLOAT', 'POINT'); at.data.foreach_set('value', fog.ravel().astype(np.float32))
    print('bugu damla', len(drops)); return ob

def build_glass(name, loc, z_t=71.5, seg=256, tea='cay', bubbles=0, rot=0.0, wet=False):
    men = 1.5; z_c = z_t + men
    out = crspline(OUTER, 7) * MM
    rim = crspline([OUTER[-1]] + RIM + [INNER_UP[-1]], 4)[1:-1] * MM
    inn = crspline(INNER_UP, 9) * MM
    rc = np.interp(z_c * MM, inn[:, 1], inn[:, 0])
    dry = inn[inn[:, 1] > z_c * MM + 1e-5][::-1]
    prof = np.vstack([out, rim, dry, [[rc, z_c * MM]]])
    kin = len(out) + len(rim)
    nO = len(out)
    if wet: prof = np.vstack([out, rim, inn[-1:]]); dry_wall(name + '_ic', loc, inn, z_c)
    def pert(th, r, z, k):
        zmm = z / MM; w = min(1, r / (18 * MM))
        if k < nO: return r + dO(th, zmm) * w
        if k < kin:
            t = (k - nO + 1) / (len(rim) + 1); return r + (1 - t) * dO(th, zmm) + t * dI(th, zmm)
        return r + dI(th, zmm)
    mi = [0] * (kin - 1) + [1] * (len(prof) - kin)
    mi = [2 if (k < nO - 1 and prof[k + 1][0] < 16.4 * MM and prof[k + 1][1] < 1.6 * MM) else v_ for k, v_ in enumerate(mi)]
    gl = lathe(name, prof, seg, (M['cam'], M['cam_ic'], M['cam_alt']), pert, mi, loc)
    wet = inn[inn[:, 1] <= z_c * MM - 1e-5]
    d = np.array([.12, .28, .5, .8, 1.2, 1.7, 2.4, 3.4, 4.8, 6.6, 9, 12, 15.5]) * MM
    top = [(rc - q, (z_t + men * math.exp(-(q / MM) / 1.45)) * MM) for q in d if rc - q > 1e-3] + [(0, z_t * MM)]
    lp = np.vstack([wet, [[rc, z_c * MM]], top]); nw = len(wet) + 1
    def pl(th, r, z, k):
        zmm = min(z / MM, z_c) if k < nw else z_c
        w = min(1, r / (18 * MM)) if k < nw else r / rc
        return r + dI(th, zmm) * w
    # cam iç yüzeyi ile aynı çarpım: dipte w=r/18mm, kuru cidarda w=1
    lq = lathe(name + '_cay', lp, seg, (M[tea],), pl, None, loc)
    at = lq.data.attributes.new('iface', 'FLOAT', 'FACE')
    v = np.zeros(len(lq.data.polygons), np.float32); v[:(nw - 1) * seg] = 1; at.data.foreach_set('value', v)
    lq.data.polygons.foreach_set('use_smooth', [True] * len(lq.data.polygons))
    # temas çizgisini keskin tut
    lq.data.update()
    e_sharp = lq.data.attributes.new('sharp_edge', 'BOOLEAN', 'EDGE')
    zs = np.array([vv.co.z for vv in lq.data.vertices]); rs = np.array([math.hypot(vv.co.x, vv.co.y) for vv in lq.data.vertices])
    start = 1 + (nw - 2) * seg; ringset = set(range(start, start + seg))
    e_sharp.data.foreach_set('value', [(e.vertices[0] in ringset and e.vertices[1] in ringset) for e in lq.data.edges])
    for q in (gl, lq): q.rotation_euler[2] = rot
    # kabarcıklar: cidara yaslanmış küme
    if bubbles:
        q = random.Random(11); placed = []
        for i in range(bubbles * 30):
            if len(placed) >= bubbles: break
            R = q.choice((.4, .5, .6, .8, 1.0, 1.4, 1.9)) * MM
            a = q.choice((q.gauss(2.5, .35), q.gauss(-2.2, .4), q.gauss(.7, .25))); rad = rc - R * 1.02 - abs(q.gauss(0, 1.0)) * MM
            px, py = rad * math.cos(a), rad * math.sin(a)
            if all(math.hypot(px - x, py - y) > (R + s) * .97 for x, y, s in placed): placed.append((px, py, R))
        for i, (px, py, R) in enumerate(placed):
            pf = [(R * 1.0 * math.sin(t), -0.0001 + R * math.cos(t) * .92) for t in np.linspace(math.pi / 2, 0, 12)]
            pf[-1] = (0, pf[-1][1])
            dd = (rc - math.hypot(px, py)) / MM
            zz = (z_t + men * math.exp(-dd / 1.45)) * MM
            lathe(f'{name}_kab{i}', pf, 24, (M['kab'],), loc=(loc[0] + px, loc[1] + py, loc[2] + zz))
    return gl

# =================================================================== TABAK
STOP = [(0, 4.2), (10, 4.2), (18, 4.2), (20.2, 4.25), (21.6, 4.7), (22.8, 5.35), (24.4, 5.6), (28, 5.9), (34, 7.1), (40, 9.0), (46, 11.5), (51, 14.0), (54.5, 16.0), (55.8, 16.75)]
SRIM = [(56.4, 16.95), (56.9, 16.6), (56.95, 16.0)]
SBOT = [(56.3, 15.3), (53.5, 13.4), (47, 9.4), (40, 6.4), (34, 4.4), (31.2, 3.2), (30.4, 1.2), (30.0, .25), (29.3, 0), (28.3, 0), (27.5, .3), (27.1, 1.4), (26, 2.1), (14, 2.3), (0, 2.4)]
def build_saucer(name, loc, m, scale=1.0, rot=0.0):
    t = crspline(STOP, 8); r_ = crspline([STOP[-1]] + SRIM + [SBOT[0]], 5)[1:-1]; b = crspline(SBOT, 6)
    prof = np.vstack([t, r_, b])[::-1] * MM * scale
    q = random.Random(int(abs(loc[0]) * 1e4) + 2); p1, p2, p3 = (q.uniform(0, 6.28) for _ in range(3))
    def pert(th, r, z, k): return r * (1 + .0016 * np.cos(2 * th + p1) + .0009 * np.cos(3 * th + p2) * (r > .04))
    ob = lathe(name, prof, 900 if name == 'tabak' else 256, (m,), pert, loc=loc); ob.rotation_euler[2] = rot
    if name == 'tabak':
        c0 = Vector((.0566 * math.cos(-2.02), .0566 * math.sin(-2.02), .0166))
        for v in ob.data.vertices:
            d_ = (v.co - c0).length + .0005 * noise.noise(v.co * 900)
            if d_ < .0018:
                k_ = (.0018 - d_) * .75; dr = Vector((-v.co.x, -v.co.y, 0)).normalized(); v.co += dr * k_ * .9 + Vector((0, 0, -k_ * .55)); v.co += Vector((noise.noise(v.co * 2500), noise.noise(v.co * 2500 + Vector((9, 0, 0))), noise.noise(v.co * 2500 + Vector((0, 9, 0))))) * .00009
        ob.data.update()
    return ob
_t = crspline(STOP, 8); _tr = np.vstack([_t, [[56.4, 16.95], [56.9, 16.3]]])
def H_sauc(px, py, cx=0.0, cy=0.0):
    r = np.hypot(np.asarray(px) - cx, np.asarray(py) - cy) / MM
    return np.where(r > 56.95, 0.0, np.interp(r, _tr[:, 0], _tr[:, 1])) * MM
SZ = 4.2 * MM

build_saucer('tabak', (0, 0, 0), M['pors'], rot=.17)
build_glass('bardak', (0.0006, -0.0004, SZ), 71.5, bubbles=34, wet=True)

mb, gb = mat('hava'); gb.out(gb.n('BsdfGlass', Color=(1, 1, 1), Roughness=0.0, IOR=1 / 1.517).outputs[0])
for i, (bx_, by_, bz_, br_) in enumerate(((-.0095, -.0062, .0046, .00022), (.0072, -.0100, .0040, .00016), (.0025, -.0135, .0052, .00030), (-.0020, .0060, .0050, .00020), (.0122, .0030, .0056, .00014))):
    pf = [(br_ * math.sin(t), br_ * 1.25 * math.cos(t)) for t in np.linspace(math.pi, 0, 16)]; pf[0] = (0, pf[0][1]); pf[-1] = (0, pf[-1][1])
    lathe(f'hava{i}', pf, 24, (mb,), loc=(bx_, by_, SZ + bz_))
# tabaktaki ince çay birikintisi + damlalar
hs = lambda x, y: float(H_sauc(x, y))
def puddle():
    """Oyuğu dolduran çay: cam dibi çevresinde halka, düzensiz dış sınır, menisküs kenarı."""
    seg = 220; V, F = [], []; R0 = 15.0; fr = np.array([0, .3, .55, .72, .84, .92, .97, 1.0])
    for j in range(seg):
        t = 2 * math.pi * j / seg
        Rm = 20.4 + 1.25 * math.sin(t + 2.4) + .55 * math.sin(2 * t + .4) + .3 * math.sin(5 * t + 1) + .16 * math.sin(9 * t)
        for k, f in enumerate(fr):
            r = R0 + (Rm - R0) * f
            edge = 1 - f; th = .55 * (1 - math.exp(-edge * (Rm - R0) / .9))
            z = max(float(np.interp(r, _tr[:, 0], _tr[:, 1])) - .03 + (0 if k == len(fr) - 1 else 0), 4.2 - .03)
            zt = 4.2 + .62 - .62 * math.exp(-edge * (Rm - R0) / .8)
            zz = max(zt, z) if k < len(fr) - 1 else z
            V.append((r * MM * math.cos(t), r * MM * math.sin(t), zz * MM))
    n = len(fr)
    for j in range(seg):
        j2 = (j + 1) % seg
        for k in range(n - 1): F.append((j * n + k, j * n + k + 1, j2 * n + k + 1, j2 * n + k))
    # alt kapak
    b0 = len(V)
    for j in range(seg):
        t = 2 * math.pi * j / seg
        V.append((V[j * n][0], V[j * n][1], 4.1 * MM)); 
    b1 = len(V)
    for j in range(seg):
        v = V[j * n + n - 1]; V.append((v[0], v[1], v[2] - .25 * MM))
    for j in range(seg):
        j2 = (j + 1) % seg
        F.append((j * n, j2 * n, b0 + j2, b0 + j)); F.append((b0 + j, b0 + j2, b1 + j2, b1 + j)); F.append((b1 + j, b1 + j2, j2 * n + n - 1, j * n + n - 1))
    ob = mesh_obj('birikinti', V, F, (M['damla_koyu'],))
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
puddle()
for i, (x, y, R, h) in enumerate(((-.0215, -.0235, .0017, .00040), (-.0245, -.0185, .0007, .00025), (.0270, -.0125, .0010, .0003))):
    drop_dome(f'tdamla{i}', x, y, hs, R, h, rng, (M['damla'],), lumps=.14, elong=1.08, rot=rng.uniform(0, 3))
flat0 = lambda x, y: 0.0
for i, (x, y, R, h) in enumerate(((-.0515, -.0640, .0036, .00060), (-.0590, -.0590, .0015, .00040), (-.0460, -.0690, .0008, .0003), (.052, .095, .0026, .0007), (-.083, .03, .0020, .0006))):
    drop_dome(f'mdamla{i}', x, y, flat0, R, h, rng, (M['damla' if i < 4 else 'su'],), lumps=.20, elong=1.12, rot=rng.uniform(0, 3))

# =================================================================== KAŞIK
def build_spoon(yaw, roll):
    L = 116.0; NU, NV = 190, 49
    u = np.concatenate([(1 - np.cos(np.linspace(0, math.pi / 2, 26)[:-1])) * 12, np.linspace(12, L - 4, NU - 40), L - 4 + 4 * np.sin(np.linspace(0, math.pi / 2, 16)[1:])])
    def halfw(s):
        bowl = 11.3 * np.sqrt(np.clip(1 - ((s - 17.5) / 17.5) ** 2, 0, 1)) * np.where(s < 17.5, 1.0, 1.0)
        bowl = np.where(s < 35, bowl, 0); bowl = np.where((s > 17.5), 11.3 * np.clip(np.cos(np.clip((s - 17.5) / 23.0, 0, 1) * math.pi / 2), 0, 1) ** .9, bowl)
        hand = np.interp(s, [36, 41, 50, 64, 80, 96, 106, 112, 116], [2.15, 1.95, 1.9, 2.2, 3.1, 4.5, 5.1, 5.0, 4.6])
        sm = 1 / (1 + np.exp(-(s - 36.5) / 1.1))
        w = np.maximum(bowl, hand * sm) if False else (bowl ** 3 + (hand * sm) ** 3) ** (1 / 3)
        end = np.sqrt(np.clip(1 - ((s - (L - 4.6)) / 4.6) ** 2, 0, 1)); w = np.where(s > L - 4.6, w * end, w)
        return np.maximum(w, 0.02)
    def cz(s): return np.interp(s, [0, 6, 17, 28, 36, 42, 55, 75, 95, 108, 116], [1.2, .55, 0, .2, 1.3, 3.1, 6.2, 8.6, 8.4, 7.1, 6.0])
    ss = np.linspace(0, L, 600); kz = cz(ss); ker = np.hanning(60); ker /= ker.sum()
    kz = np.convolve(np.pad(kz, 30, 'edge'), ker, 'same')[30:-30]
    w = halfw(u); z0 = np.interp(u, ss, kz)
    depth = 5.0 * np.clip(1 - ((u - 17) / 19.5) ** 2, 0, 1) ** .85
    crown = np.interp(u, [0, 36, 44, 60, 90, 116], [0, 0, .75, .70, .55, .25])
    thick = np.interp(u, [0, 5, 17, 30, 38, 46, 70, 108, 116], [.75, .95, 1.1, 1.25, 1.9, 2.0, 1.6, 1.35, 1.1])
    v = np.sin(np.linspace(-math.pi / 2, math.pi / 2, NV))
    T, B = [], []
    for i in range(len(u)):
        groove = 0
        edge = np.sqrt(np.clip(1 - np.abs(v) ** 11, 0, 1))
        zt = z0[i] - depth[i] * (1 - np.abs(v) ** 2.1) + crown[i] * (1 - v ** 2)
        if u[i] > 56:
            fa = min(1, (u[i] - 56) / 14) * np.clip((112.5 - u[i]) / 3.5, 0, 1); av = np.abs(v)
            zt = zt + fa * (.10 * np.exp(-((av - .86) / .07) ** 2) - .13 * np.exp(-((av - .72) / .05) ** 2))
        zb = zt - thick[i] * edge * np.where(w[i] > 1, 1, w[i])
        T.append(np.stack([np.full(NV, u[i]), v * w[i], zt], 1)); B.append(np.stack([np.full(NV, u[i]), v * w[i], zb], 1))
    T = np.array(T); B = np.array(B); n = len(u)
    V = [tuple(p) for p in T.reshape(-1, 3)]; off = len(V); bi = {}
    for i in range(n):
        for j in range(1, NV - 1): bi[(i, j)] = len(V); V.append(tuple(B[i, j]))
        bi[(i, 0)] = i * NV; bi[(i, NV - 1)] = i * NV + NV - 1
    F = []
    for i in range(n - 1):
        for j in range(NV - 1):
            F.append((i * NV + j, (i + 1) * NV + j, (i + 1) * NV + j + 1, i * NV + j + 1))
            F.append((bi[i, j], bi[i, j + 1], bi[i + 1, j + 1], bi[i + 1, j]))
    for e, rev in ((0, False), (n - 1, True)):
        for j in range(NV - 1):
            q = [e * NV + j, e * NV + j + 1, bi[e, j + 1], bi[e, j]]; q = list(dict.fromkeys(q))
            if len(q) > 2: F.append(tuple(reversed(q) if rev else q))
    V = np.array(V) * MM; wgt = np.gradient(u) * w * thick; cxm = (wgt * u).sum() / wgt.sum(); czm = (wgt * (z0 - depth * .55 - thick / 2)).sum() / wgt.sum()
    com = np.array([cxm, 0, czm]) * MM; print('kasik AM', cxm, czm); V = V - com
    ip = crspline(INNER_UP, 12)
    lowm = ip[:, 1] <= 25.0; fl_r, fl_z = ip[lowm, 0], ip[lowm, 1]
    best = None; VM = V / MM; gx, gy = .6, -.4
    for al in np.radians(np.linspace(16, 40, 49)):
        X = np.array([math.sin(al) * math.cos(yaw), math.sin(al) * math.sin(yaw), math.cos(al)]); Zz = np.array([-math.cos(al) * math.cos(yaw), -math.cos(al) * math.sin(yaw), math.sin(al)])
        Yy = np.cross(Zz, X); cr_, sr_ = math.cos(roll), math.sin(roll); Z1 = cr_ * Zz + sr_ * Yy; Y1 = cr_ * Yy - sr_ * Zz
        Rm = np.stack([X, Y1, Z1], 1); Wd = VM @ Rm.T
        for du in np.linspace(-22, 12, 69):
            for dv in np.linspace(-4, 4, 9):
                P = Wd + np.array([du * math.cos(yaw) - dv * math.sin(yaw), du * math.sin(yaw) + dv * math.cos(yaw), 0])
                rr_ = np.hypot(P[:, 0], P[:, 1]); low = P[:, 2] < P[:, 2].min() + 22
                if rr_[low].max() > 23.0: continue
                lift = np.max(np.interp(rr_[low], fl_r, fl_z) - P[low, 2]) + .12
                z_ = P[:, 2] + lift; mid = (z_ > 8) & (z_ < 85.2)
                if np.any(rr_[mid] > np.interp(z_[mid], ip[:, 1], ip[:, 0]) - .12): continue
                if best is None or lift < best[0]: best = (lift, Rm, du, dv, al)
    lift, R, du, dv, al = best; print('kasik egim', math.degrees(al), 'du', du, 'dv', dv, 'lift', lift)
    x = (gx + du * math.cos(yaw) - dv * math.sin(yaw)) * MM; y = (gy + du * math.sin(yaw) + dv * math.cos(yaw)) * MM; lift = lift * MM + SZ
    ob = mesh_obj('kasik', V, F, (M['celik'],))
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    ob.matrix_world = Matrix.Translation((x, y, lift)) @ Matrix(R.tolist()).to_4x4()
    md = ob.modifiers.new('s', 'SUBSURF'); md.levels = md.render_levels = 1
    return ob
build_spoon(math.radians(24), math.radians(-58))

# =================================================================== ŞEKER
def grain_shapes(k=8):
    S = []
    base = np.array([(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float) * .5
    for i in range(k):
        v = base * nr.uniform([.75, .65, .8], [1.15, 1.0, 1.35]); v += nr.uniform(-.13, .13, v.shape); S.append(v)
    return S
CUBE_F = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
def randrot(n):
    q = nr.normal(size=(n, 4)); q /= np.linalg.norm(q, axis=1)[:, None]; w, x, y, z = q.T
    return np.stack([np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], -1), np.stack([2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], -1),
                     np.stack([2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1)], 1)
def grains_mesh(name, P, sizes, mats):
    S = np.array(grain_shapes()); n = len(P); idx = nr.integers(0, len(S), n); R = randrot(n)
    V = np.einsum('nij,nkj->nki', R, S[idx] * sizes[:, None, None]) + P[:, None, :]
    F = (np.array(CUBE_F)[None] + (np.arange(n) * 8)[:, None, None]).reshape(-1, 4)
    ob = mesh_obj(name, V.reshape(-1, 3), F.tolist(), mats, smooth=False); return ob
from mathutils import kdtree
def build_sugar(name, x, y, yaw, dims, H, wet=0.0, seed=1, pitch=None, corner=(1, -1, 1)):
    q = np.random.default_rng(seed); D = np.array(dims) / 2; st = .105; V, F = [], []; rd = .45
    for ax in range(3):
        a1, a2 = [k for k in range(3) if k != ax]; n1 = int(2 * D[a1] / st); n2 = int(2 * D[a2] / st)
        for sg in (-1, 1):
            g1, g2 = np.meshgrid(np.linspace(-D[a1], D[a1], n1 + 1), np.linspace(-D[a2], D[a2], n2 + 1), indexing='ij'); P = np.zeros((n1 + 1, n2 + 1, 3)); P[..., a1] = g1; P[..., a2] = g2; P[..., ax] = sg * D[ax]
            b0 = sum(len(v) for v in V); V.append(P.reshape(-1, 3)); i0 = (np.arange(n1)[:, None] * (n2 + 1) + np.arange(n2)[None]).ravel() + b0
            fc = np.stack([i0, i0 + 1, i0 + n2 + 2, i0 + n2 + 1], 1); F.append(fc if (sg > 0) == (ax == 1) else fc[:, ::-1])
    V = np.concatenate(V); F = np.concatenate(F); key = np.round(V, 4); _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.ravel(); V = V[first]; F = inv[F]
    C = np.clip(V, -(D - rd), D - rd); N = V - C; N /= np.maximum(np.linalg.norm(N, axis=1), 1e-9)[:, None]; Bp = C + N * rd
    # kristal tohumları (geniş boy dağılımı)
    gr = np.concatenate([np.mgrid[-D[0] - .5:D[0] + .5:.53, -D[1] - .5:D[1] + .5:.53, -D[2] - .5:D[2] + .5:.53].reshape(3, -1).T + 0]); gr = gr + q.uniform(-.30, .30, gr.shape)
    qd = np.abs(gr) - D; inside = qd.max(1); gr = gr[(inside > -.75) & (inside < .35)]; gr = gr[q.uniform(0, 1, len(gr)) < .80]
    kd = kdtree.KDTree(len(gr))
    for i, g_ in enumerate(gr): kd.insert(Vector(g_), i)
    kd.balance(); tilt = q.normal(0, .44, gr.shape); off = q.normal(0, .085, len(gr)); off[q.uniform(0, 1, len(gr)) < .06] -= .22
    h = np.empty(len(Bp))
    for i, b in enumerate(Bp):
        (c1, i1, d1), (c2, i2, d2) = kd.find_n(Vector(b), 2); e = d2 - d1
        h[i] = off[i1] + float(np.dot(tilt[i1], b - gr[i1])) - .13 * max(0, 1 - e / .10)
    face = np.argmax(np.abs(N), axis=1); press = np.where(face == 2, .55, np.where(face == 0, 1.0, .85)); h *= press
    nz1 = np.array([noise.noise(Vector((b[0] * .28 + seed * 3, b[1] * .28, b[2] * .28))) for b in Bp]); nz2 = np.array([noise.noise(Vector((b[0] * .9 + seed, b[1] * .9, b[2] * .9 + 7))) for b in Bp])
    ed = np.sort(D - np.abs(Bp), axis=1)[:, 1]; ef = np.clip(1 - ed / 1.5, 0, 1)                 # kenara yakınlık
    h -= ef * np.clip(nz2 + .12, 0, 1) * 1.15 + np.clip(nz1 - .18, 0, 1) * .55 + .05 * nz2
    Pn = Bp + N * h[:, None]
    cc = D * np.array(corner); dc = np.linalg.norm(Bp - cc, axis=1) + 1.1 * nz2; cd = np.clip(3.4 - dc, 0, 3.4); dirc = -np.array(corner) / math.sqrt(3); Pn = Pn + dirc[None] * (cd * .55)[:, None]
    ob = mesh_obj(name, Pn * MM, F.tolist(), (M['seker_oz'],), smooth=False); ob.data.update()
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    # yüzeyde cam kristaller
    pick = q.choice(len(Pn), 3600, replace=False); sz = np.clip(.24 * q.uniform(0, 1, len(pick)) ** -.46, .2, 1.0) * MM
    gm = grains_mesh(name + '_kr', (Pn[pick] - N[pick] * .10) * MM, sz, (M['seker'],))
    VV = np.array([v.co[:] for v in ob.data.vertices])
    if pitch is None: p, r, lift = settle(VV[::37], np.zeros(3), x, y, yaw, H, (-.5, .5), (-.5, .5), 25, 4)
    else: p, r = pitch
    Rm = rotm(p, r, yaw); Wd = VV @ Rm.T; lift = np.max(H(Wd[:, 0] + x, Wd[:, 1] + y) - Wd[:, 2]) - .00012
    for o_ in (ob, gm):
        o_.matrix_world = Matrix.Translation((x, y, lift)) @ Matrix(Rm.tolist()).to_4x4()
        at = o_.data.attributes.new('islak', 'FLOAT', 'POINT'); at.data.foreach_set('value', np.full(len(o_.data.vertices), wet, np.float32))
    print(name, 'tepe', len(VV), 'pitch/roll', round(p, 2), round(r, 2)); return ob
build_sugar('seker1', -.0375, .0060, math.radians(64), (17.6, 12.4, 10.9), H_sauc, wet=0, seed=4, corner=(-1, 1, 1))
build_sugar('seker2', -.0700, -.0200, math.radians(-24), (17.0, 12.2, 10.6), lambda px, py: np.zeros_like(np.asarray(px)), wet=0, seed=9, corner=(1, -1, 1))
# dökülen taneler
def clump(x, y, R_, seed):
    import bmesh
    q = np.random.default_rng(seed); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1); oo = Vector(q.uniform(0, 40, 3))
    for v in bm.verts: v.co = v.co * R_ * (1 + .45 * noise.noise(v.co * 1.3 + oo) + .28 * noise.noise(v.co * 4 + oo) + .14 * noise.noise(v.co * 9 + oo)); v.co.z *= .8
    me = bpy.data.meshes.new('topak'); bm.to_mesh(me); P = np.array([v.co[:] for v in bm.verts]); bm.free(); me.materials.append(M['seker_oz']); ob = bpy.data.objects.new('topak', me); sc.collection.objects.link(ob); zl = -P[:, 2].min(); ob.location = (x, y, zl)
    pk = q.choice(len(P), int(60 * (R_ / .001) ** 2), replace=False); gm = grains_mesh('topak_kr', P[pk] * .95, q.uniform(.00022, .00055, len(pk)), (M['seker'],)); gm.location = (x, y, zl)
clump(-.0575, -.0290, .0016, 3); clump(-.0548, -.0345, .0008, 5); clump(-.0815, -.0300, .0005, 6)
def loose(n, cx, cy, sx, sy, H, name):
    P = np.stack([cx + sx * nr.standard_t(3, n), cy + sy * nr.standard_t(3, n)], 1); sz = np.clip(.10 * nr.uniform(0, 1, n) ** -.62, .10, .80) * MM
    gm = grains_mesh(name, np.column_stack([P, np.zeros(n)]), sz, (M['seker_tek'],)); co_ = np.array([v.co[:] for v in gm.data.vertices]).reshape(n, 8, 3)
    co_[:, :, 2] += (H(P[:, 0], P[:, 1]) - co_[:, :, 2].min(1) - .00002)[:, None]; gm.data.vertices.foreach_set('co', co_.reshape(-1)); gm.data.update()
Z0 = lambda px, py: np.zeros_like(np.asarray(px))
for k_, (cx_, cy_, sp_, n_) in enumerate(((-.0700, -.0290, .0045, 150), (-.0620, -.0215, .0035, 110), (-.0570, -.0330, .0065, 120), (-.072, -.044, .012, 90), (-.045, -.070, .028, 70), (-.0800, -.0200, .003, 50))): loose(n_, cx_, cy_, sp_, sp_ * .8, Z0, f'tane{k_}')
loose(60, -.0365, -.0030, .004, .003, H_sauc, 'tane8'); loose(30, -.033, .004, .008, .008, H_sauc, 'tane9')
for o_ in [o for o in sc.objects if o.name.startswith('tane')]:
    at = o_.data.attributes.new('islak', 'FLOAT', 'POINT'); at.data.foreach_set('value', np.zeros(len(o_.data.vertices), np.float32))

# =================================================================== SİMİT
def ell(n_u=10, n_v=7):
    V, F = [], []
    for i in range(n_v + 1):
        ph = math.pi * i / n_v
        for j in range(n_u):
            t = 2 * math.pi * j / n_u; V.append((math.sin(ph) * math.cos(t), math.sin(ph) * math.sin(t), math.cos(ph)))
    for i in range(n_v):
        for j in range(n_u): F.append((i * n_u + j, (i + 1) * n_u + j, (i + 1) * n_u + (j + 1) % n_u, i * n_u + (j + 1) % n_u))
    return np.array(V), np.array(F)
EV, EF = ell(14, 10)
def seed_shape():
    v = EV.copy(); t = v[:, 0]; tap = np.where(t > 0, 1 - .55 * t, 1.0); v[:, 1] *= tap; v[:, 2] *= tap
    return v * np.array([1.65, 1.0, .48]) * MM
def seeds_mesh(name, P, Nn, tl=1.0, floor=False):
    n = len(P); ang = nr.uniform(0, 6.28, n); Vs = []
    for i in range(n):
        v = EV.copy(); t = v[:, 0]; tp = nr.uniform(.30, .68); v[:, 1] *= np.where(t > 0, 1 - tp * t ** nr.uniform(.8, 1.6), 1 - .06 * t * t); v[:, 2] *= np.where(t > 0, 1 - tp * .8 * t, 1.0)
        v[:, 2] *= np.where(v[:, 2] > 0, nr.uniform(.75, 1.15), nr.uniform(.6, 1.1)); v[:, 2] += nr.uniform(-.25, .25) * (v[:, 0] ** 2 - .4); v[:, 1] += nr.uniform(-.16, .16) * v[:, 0] ** 2
        o3 = nr.uniform(0, 60, 3); dn = np.array([noise.noise(Vector(q_ * 1.9 + o3)) for q_ in v]); v *= (1 + .10 * dn)[:, None]
        base = v * np.array([1.62, 1.0, .52]) * nr.uniform(.82, 1.15, 3) * nr.uniform(.85, 1.1) * MM
        z = Vector(Nn[i]).normalized(); tilt = Vector(nr.normal(0, .18, 3)); z = (z + tilt * tl).normalized()
        x = z.orthogonal().normalized(); x.rotate(Matrix.Rotation(ang[i], 3, z)); y = z.cross(x)
        Rm = np.array([x[:], y[:], z[:]]).T; W_ = base @ Rm.T + P[i]
        if floor: W_[:, 2] -= W_[:, 2].min() + .00002
        Vs.append(W_)
    F = (EF[None] + (np.arange(n) * len(EV))[:, None, None]).reshape(-1, 4)
    return mesh_obj(name, np.concatenate(Vs), F.tolist(), (M['susam'],))
def build_simit(cx, cy, z0, R=.066, yaw=.3):
    nu, nv, NT = 520, 34, 13; Cs, obs = [], []
    ph = np.linspace(0, 2 * np.pi, nu, endpoint=False); a_, b_ = .0058, .0112
    for k in (0, 1):
        t = NT * ph + .75 * np.sin(ph + 1.1) + .42 * np.sin(3 * ph + .4) + .26 * np.sin(5 * ph + 2) + k * math.pi; Rr = R * (1 + .025 * np.sin(2 * ph + .7) + .012 * np.sin(5 * ph)); Cs.append(np.stack([Rr + a_ * np.cos(t), .78 * a_ * np.sin(t)], 1))
    allV, allF, allN = [], [], []
    for k in (0, 1):
        V = np.zeros((nu, nv, 3)); be = np.linspace(0, 2 * np.pi, nv, endpoint=False)
        for i in range(nu):
            rad = b_ * (1 + .10 * math.sin(2 * ph[i] + k * 2) + .08 * math.sin(5 * ph[i] + 2 * k) + .05 * math.sin(11 * ph[i] + 3 * k))
            w_ = np.array([noise.noise(Vector((14 * math.cos(ph[i]) + 9 * k, 14 * math.sin(ph[i]), 1.4 * math.sin(b)))) for b in be]); w2 = np.array([noise.noise(Vector((45 * math.cos(ph[i]) + 9 * k, 45 * math.sin(ph[i]), 4 * math.sin(b)))) for b in be])
            rr = rad * (1 + .10 * w_ + .03 * w2); rx = Cs[k][i, 0] + rr * np.cos(be); rz = Cs[k][i, 1] + rr * np.sin(be) * .92; rz = np.where(rz < -.0125, -.0125 + (rz + .0125) * .25, rz)
            V[i, :, 0] = rx * math.cos(ph[i]); V[i, :, 1] = rx * math.sin(ph[i]); V[i, :, 2] = rz
        allV.append(V.reshape(-1, 3))
        i0 = (np.arange(nu)[:, None] * nv + np.arange(nv)[None]); i1 = ((np.arange(nu) + 1) % nu)[:, None] * nv + np.arange(nv)[None]; jn = (np.arange(nv) + 1) % nv
        F = np.stack([i0.ravel(), i1.ravel(), i1[:, jn].ravel(), i0[:, jn].ravel()], 1)[:, ::-1]; allF.append(F + k * nu * nv)
    V = np.concatenate(allV); F = np.concatenate(allF); zmin = V[:, 2].min(); V[:, 2] -= zmin
    z0 = float(np.max(H_sauc(V[:, 0] / 1.62, V[:, 1] / 1.62) * 1.62 - V[:, 2])) - .0012
    ob = mesh_obj('simit', V, F.tolist(), (M['simit'],), loc=(cx, cy, z0)); ob.rotation_euler[2] = yaw; ob.data.update()
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free(); ob.data.update()
    pol = ob.data.polygons; ce = np.array([p_.center[:] for p_ in pol]); no = np.array([p_.normal[:] for p_ in pol]); ar = np.array([p_.area for p_ in pol])
    ang = np.arctan2(ce[:, 1], ce[:, 0]) % (2 * np.pi); ii = np.round(ang / (2 * np.pi) * nu).astype(int) % nu; rho = np.hypot(ce[:, 0], ce[:, 1]); kk = np.arange(len(pol)) // (nu * nv)
    other = np.where(kk[:, None] == 0, Cs[1][ii], Cs[0][ii]); dist = np.hypot(rho - other[:, 0], ce[:, 2] + zmin - other[:, 1])
    out_ = dist > b_ * .98; wt = ar * out_ * np.clip(no[:, 2] + .75, 0, 1.2) * np.clip(.75 + .7 * fnoise(ce[:, 0] * 260, ce[:, 1] * 260, 5, 3), .06, 1.5); wt /= wt.sum()
    Pk = nr.choice(len(pol), 2300, p=wt); P = ce[Pk] + no[Pk] * .0003 + nr.normal(0, .0004, (len(Pk), 3)) * .6
    sd = seeds_mesh('simit_susam', P, no[Pk]); sd.location = ob.location; sd.rotation_euler = ob.rotation_euler
PLC = (.118, .195)
build_saucer('tabak_simit', (*PLC, 0), M['pors0'], 1.62, .4)
build_simit(PLC[0], PLC[1], .0115)
# masaya düşen susam ve kırıntı
n = 26; P = np.column_stack([nr.normal(.085, .028, n), nr.normal(.075, .035, n), np.full(n, .0005)]); seeds_mesh('susamlar', P, np.tile((0, 0, 1.), (n, 1)), .22, True)
n = 7; P = np.column_stack([nr.uniform(.060, .10, n), nr.uniform(-.075, .0, n), np.full(n, .00062)]); seeds_mesh('susamlar2', P, np.tile((0, 0, 1.), (n, 1)), .22, True)
def crumbs(n, cx, cy, sx, sy):
    import bmesh
    for i in range(n):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1); R = nr.choice([.25, .35, .5, .7, .95], p=[.30, .3, .22, .13, .05]) * MM
        o3 = nr.uniform(0, 50, 3)
        for v in bm.verts:
            d = 1 + .55 * noise.noise(v.co * 1.2 + Vector(o3)) + .30 * noise.noise(v.co * 3.1 + Vector(o3)) - .35 * max(0, noise.noise(v.co * 6.5 + Vector(o3))); v.co = v.co * d * R; v.co.z *= .75
        me = bpy.data.meshes.new('k'); bm.to_mesh(me); bm.free(); me.materials.append(M['kirinti']); me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        ob = bpy.data.objects.new(f'kirinti{i}', me); sc.collection.objects.link(ob); ob.rotation_euler = nr.uniform(0, 6, 3); mr_ = ob.rotation_euler.to_matrix(); zm_ = min((mr_ @ v.co).z for v in me.vertices); ob.location = (nr.normal(cx, sx), nr.normal(cy, sy), -zm_ - .00003)
crumbs(34, .085, .06, .03, .045)
def fiber(x, y, L, seed):
    q = random.Random(seed); a = q.uniform(0, 6.28); V, F = [], []; px, py = x, y; n = 26; r = .000018
    for k in range(n):
        a += q.gauss(0, .16) + .05; px += math.cos(a) * L / n; py += math.sin(a) * L / n; z = .00012 + .0005 * abs(math.sin(k * .21 + seed)) * q.uniform(.8, 1)
        for j in range(5): V.append((px - math.sin(a) * r * math.cos(j * 1.2566), py + math.cos(a) * r * math.cos(j * 1.2566), z + r * math.sin(j * 1.2566)))
    for k in range(n - 1):
        for j in range(5): F.append((k * 5 + j, k * 5 + (j + 1) % 5, (k + 1) * 5 + (j + 1) % 5, (k + 1) * 5 + j))
    mesh_obj(f'lif{seed}', V, F, (lif,))
lif = m_flat('lif', (.10, .11, .15), .8)
fiber(.085, -.052, .009, 1)
# ikinci bardak (karşıdaki kişinin)
build_saucer('tabak2', (-.150, .235, 0), M['pors'], rot=1.0)
build_glass('bardak2', (-.150, .235, SZ), 38, 128, 'cay2')

# =================================================================== MASA + ODA
def box(name, a, b, m, bevel=0.0, seg=3):
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts: v.co = Vector([(a[i] + b[i]) / 2 + v.co[i] * (b[i] - a[i]) for i in range(3)])
    if bevel: bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=seg, affect='EDGES', profile=.5)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob); me.materials.append(m)
    if bevel: me.polygons.foreach_set('use_smooth', [True] * len(me.polygons)); 
    return ob
box('masa', (-.55, -.36, -.028), (.60, .43, 0), M['mermer'], .004, 4)
duvar = m_flat('duvar', (.70, .66, .57), .8, 5, (.62, .58, .49), .0015); lambri = m_flat('lambri', (.085, .155, .13), .38, 12, (.06, .11, .09), .0006)
pervaz = m_flat('pervaz', (.66, .63, .56), .45, 14, (.52, .48, .41), .0006); zemin = m_flat('zemin', (.16, .09, .05), .5, 8); tavan = m_flat('tavan', (.80, .80, .79), .9)
XL, XR, YB, YF, ZB, ZT = -1.5, 2.0, -3.0, .62, -.74, 2.0; T = .22
WX = (-.80, .62); WZ = (.055, 1.45)
box('db_alt', (XL, YF, ZB), (XR, YF + T, WZ[0]), lambri); box('db_ust', (XL, YF, WZ[1]), (XR, YF + T, ZT), duvar)
box('db_sol', (XL, YF, WZ[0]), (WX[0], YF + T, WZ[1]), duvar); box('db_sag', (WX[1], YF, WZ[0]), (XR, YF + T, WZ[1]), duvar)
lam2, gl2 = mat('lambri2'); ol = gl2.obj(); sc_l = gl2.mr(gl2.noise(gl2.map(ol, scale=(1, 1, 6)), 9, 6, .7, 1), .54, .68); cl = gl2.mix(gl2.mul(sc_l, .55), gl2.mix(gl2.noise(ol, 6, 4), (.065, .125, .105), (.105, .18, .15)), (.22, .25, .21))
gl2.out(principled(gl2, Base_Color=cl, Roughness=gl2.mr(gl2.noise(ol, 18, 4), .3, .7, .28, .55)))
xb = -1.2; kb = 0
while xb < 1.2:
    wb = .086 + .004 * math.sin(kb * 2.3); box(f'lam{kb}', (xb, YF - .016, ZB), (xb + wb - .004, YF + .002, WZ[0] - .045), lam2, .006); xb += wb; kb += 1
box('pervaz_alt', (XL, YF - .03, WZ[0] - .052), (XR, YF, WZ[0] - .026), lam2, .006)
box('denizlik', (WX[0] - .05, YF - .10, WZ[0] - .026), (WX[1] + .05, YF + T - .05, WZ[0]), pervaz, .006)
fy = (YF + .10, YF + .15)
for k, x in enumerate((WX[0], -.115, WX[1] - .05)): box(f'kasa{k}', (x, fy[0], WZ[0]), (x + .05, fy[1], WZ[1]), pervaz, .004)
for k, z in enumerate((WZ[0], .92, WZ[1] - .05)): box(f'kayit{k}', (WX[0], fy[0], z), (WX[1], fy[1], z + (.055 if k == 0 else .04)), pervaz, .004)
LY, LZ = (-1.05, .15), (.12, 1.5)
box('dl_alt', (XL - T, YB, ZB), (XL, YF + T, LZ[0]), lambri); box('dl_ust', (XL - T, YB, LZ[1]), (XL, YF + T, ZT), duvar)
box('dl_a', (XL - T, YB, LZ[0]), (XL, LY[0], LZ[1]), duvar); box('dl_b', (XL - T, LY[1], LZ[0]), (XL, YF + T, LZ[1]), duvar)
box('lkasa', (XL - .12, -.47, LZ[0]), (XL - .07, -.42, LZ[1]), pervaz); box('lkasa2', (XL - .12, LY[0], .9), (XL - .07, LY[1], .94), pervaz)
box('dr_alt', (XR, YB, ZB), (XR + T, YF + T, .3), lambri); box('dr', (XR, YB, .3), (XR + T, YF + T, ZT), duvar)
box('da_alt', (XL, YB - T, ZB), (XR, YB, .3), lambri); box('da', (XL, YB - T, .3), (XR, YB, ZT), duvar)
box('zemin', (XL - T, YB - T, ZB - .1), (XR + T, YF + T, ZB), zemin); box('tavan', (XL - T, YB - T, ZT), (XR + T, YF + T, ZT + .1), tavan)
# odada koyu kütleler (yansımalar için)
kumas = m_flat('kumas', (.028, .034, .05), .9); ten = m_flat('ten', (.45, .26, .17), .5); ahsap = m_flat('ahsap', (.13, .06, .03), .4, 20)
def blob(name, loc, s, m):
    ob = mesh_obj(name, EV_ * np.array(s), EF_.tolist(), (m,), loc=loc); return ob
EV_, EF_ = ell(40, 26)
blob('govde', (.05, -.86, -.12), (.23, .14, .36), kumas); blob('bas', (.04, -.78, .36), (.078, .095, .115), ten); blob('sac', (.04, -.80, .39), (.085, .098, .10), m_flat('sac', (.02, .014, .01), .6))
blob('kol1', (-.16, -.66, -.02), (.06, .20, .06), kumas); blob('kol2', (.22, -.66, -.02), (.06, .20, .06), kumas)
for k, (x, y) in enumerate(((1.1, -1.2), (-.6, -2.1), (1.2, -2.3))):
    box(f'mas{k}', (x - .35, y - .3, -.04), (x + .35, y + .3, 0), ahsap); box(f'may{k}', (x - .04, y - .04, ZB), (x + .04, y + .04, 0), ahsap)
    box(f'snd{k}', (x - .5, y - .2, -.3), (x - .46, y + .2, .2), ahsap)

# sardunya
def geranium(cx, cy, z0):
    tc, gt = mat('terra'); ot = gt.obj(); zt_ = gt.sep(ot)[2]; salt = gt.mul(gt.mr(gt.add(gt.noise(gt.map(ot, scale=(1, 1, .5)), 42, 5, .65), gt.mul(gt.sub(zt_, .035), 3.5)), .54, .72), .65)
    gt.out(principled(gt, Base_Color=gt.mix(salt, gt.mix(gt.noise(ot, 30, 5), (.30, .105, .05), (.46, .20, .11)), (.62, .52, .44)), Roughness=.85)); lf = m_flat('yaprak', (.055, .15, .030), .5, 40, (.10, .22, .05), .0008, Subsurface_Weight=.15, Subsurface_Scale=.003)
    fl = m_flat('cicek', (.62, .015, .02), .55, 60, (.75, .05, .06)); sp = m_flat('sap', (.09, .16, .04), .6)
    prof = [(0, 0), (40, 0), (44, 2), (56, 84), (63, 86), (66, 88), (67, 110), (64, 112), (60, 111), (57, 96), (0, 94)]
    prof = [(p_[0] * .72, p_[1] * .66) for p_ in prof]
    lathe('saksi', np.array(prof) * MM, 96, (tc,), loc=(cx, cy, z0))
    q = random.Random(4); V, F = [], []; stems = []
    def leaf(p, nrm, s):
        n_ = Vector(nrm).normalized(); x = n_.orthogonal().normalized(); x.rotate(Matrix.Rotation(q.uniform(0, 6.28), 3, n_)); y = n_.cross(x); b0 = len(V); V.append(tuple(p)); K = 40
        for ring in (.5, 1.0):
            for k in range(K):
                t = 2 * math.pi * k / K; rr = s * ring * (1 + .07 * math.cos(9 * t)) * (1 - .55 * math.exp(-((t - math.pi) / .28) ** 2)); hgt = s * .20 * ring ** 2 * (1 + .5 * math.cos(5 * t)) * (1 if ring < 1 else .75)
                V.append(tuple(Vector(p) + x * rr * math.cos(t) + y * rr * math.sin(t) + n_ * hgt))
        for k in range(K):
            k2 = (k + 1) % K; F.append((b0, b0 + 1 + k, b0 + 1 + k2)); F.append((b0 + 1 + k, b0 + 1 + K + k, b0 + 1 + K + k2, b0 + 1 + k2))
    for i in range(150):
        a = q.uniform(0, 6.28); rr = min(abs(q.gauss(0, .060)), .085); h = q.uniform(.052, .20) if rr > .055 else q.uniform(.075, .20); p = (cx + rr * math.cos(a), cy + rr * math.sin(a) * .7, z0 + h)
        stems.append(p); leaf(p, (math.cos(a) * .8 + q.gauss(0, .4), math.sin(a) * .8 + q.gauss(0, .4) - .25, .7), q.uniform(.016, .031))
    mesh_obj('yapraklar', V, F, (lf,))
    SV, SF = [], []
    for p_ in stems:
        a0 = Vector((cx + (p_[0] - cx) * .35, cy + (p_[1] - cy) * .35, z0 + .062)); b_ = Vector(p_); mid = (a0 + b_) / 2 + Vector((0, 0, .025))
        for k in range(9):
            t = k / 8; c_ = a0 * (1 - t) ** 2 + mid * 2 * t * (1 - t) + b_ * t * t
            for j in range(5): SV.append(tuple(c_ + Vector((math.cos(j * 1.2566), math.sin(j * 1.2566), 0)) * .0012))
        base_ = len(SV) - 45
        for k in range(8):
            for j in range(5): SF.append((base_ + k * 5 + j, base_ + k * 5 + (j + 1) % 5, base_ + (k + 1) * 5 + (j + 1) % 5, base_ + (k + 1) * 5 + j))
    mesh_obj('saplar', SV, SF, (sp,))
    for k in range(5):
        c = Vector((cx, cy, z0)) + Vector(((-.070, -.045, .132), (.034, -.070, .086), (-.02, -.05, .155), (.07, -.02, .17), (-.09, 0, .2))[k])
        for i in range(80):
            d = q.uniform(.35, 1) * Vector((q.gauss(0, 1), q.gauss(0, 1), q.gauss(.3, .8))).normalized(); blob(f'cic{k}_{i}', c + d * .023, (.0075, .0075, .0055), fl)
EV_, EF_ = ell(14, 9)
geranium(.168, YF + .005, WZ[0])

# =================================================================== IŞIK
w = bpy.data.worlds.new('dis') if not bpy.data.worlds else bpy.data.worlds[0]; sc.world = w
try: w.use_nodes = True
except Exception: pass
w.node_tree.nodes.clear(); g = G(w.node_tree)
d = g.n('TexCoord').outputs['Generated']; x, y, z = g.sep(d)
az = g.math('ARCTAN2', x, y); el = g.math('ARCSINE', z)
p = g.comb(g.mul(az, 1.0), g.mul(el, 1.0), 0)
sky = g.mix(g.mr(el, .0, 1.2), (1.0, .985, .95), (.62, .78, 1.0))
sky = g.mix(g.mr(g.noise(d, 1.6, 5, .6), .35, .7), sky, (1.0, 1.0, 1.0)); skyS = g.mr(el, .1, 1.3, 2.7, 1.5)
roof = g.add(.30, g.mul(g.sub(g.noise(g.comb(g.mul(az, 1.0), 0, 0), 2.6, 2, .5), .5), .35))
cell = g.voro(g.map(p, scale=(3.0, .0, 1)), 1.6, out='Color')
fac = g.mix(g.sep(cell)[0], (.50, .40, .29), (.40, .37, .34)); fac = g.mix(g.mr(g.sep(cell)[1], .6, .9), fac, (.52, .46, .40))
win = g.mul(g.math('GREATER_THAN', g.math('FRACT', g.add(g.mul(az, 7.4), .30)), .60), g.math('GREATER_THAN', g.math('FRACT', g.add(g.mul(el, 8.0), .55)), .42)); fac = g.mix(g.mul(win, .88), fac, g.mix(g.noise(p, 9, 2), (.05, .06, .07), (.34, .36, .38)))
tree = g.mr(g.add(g.noise(g.map(p, loc=(1, 4, 0)), 3.4, 5, .6), g.mul(g.sub(.12, el), .15)), .44, .50); tree = g.mul(tree, g.mr(g.math('ABSOLUTE', g.add(az, .20)), .10, .22, 1, 0))
fac = g.mix(tree, fac, g.ramp(g.noise(p, 26, 5, .7), [(.36, (.03, .065, .015)), (.52, (.13, .22, .05)), (.62, (.42, .52, .20)), (.70, (1.0, 1.0, .85))]))
bal = g.mul(g.math('LESS_THAN', g.math('ABSOLUTE', g.sub(el, .052)), .006), g.math('GREATER_THAN', g.noise(g.comb(g.mul(az, 1.0), 0, 3), 5, 1), .46)); fac = g.mix(g.mul(bal, .85), fac, (.06, .055, .05))
def eli(a0, e0, ra, re): return g.mr(g.math('SQRT', g.add(g.math('POWER', g.math('DIVIDE', g.sub(az, a0), ra), 2.0), g.math('POWER', g.math('DIVIDE', g.sub(el, e0), re), 2.0))), .95, 1.05, 1, 0)
street = g.mix(g.noise(g.map(p, scale=(1, 5, 1)), 4, 3), (.26, .26, .26), (.36, .35, .33)); fac = g.mix(g.mr(el, -.10, -.06), street, fac)
for (a0, e0, ra, re, cc_) in ((.045, -.050, .052, .016, (.05, .10, .26)), (.035, -.032, .030, .013, (.03, .035, .04)), (-.105, -.055, .045, .017, (.42, .05, .03)), (-.11, -.036, .028, .012, (.03, .03, .035)), (.128, .015, .020, .026, (.62, .12, .05)), (-.03, -.02, .006, .05, (.05, .05, .05))):
    fac = g.mix(g.mul(eli(a0, e0, ra, re), .92), fac, cc_)
isky = g.mr(el, g.sub(roof, .01), g.add(roof, .01)) if False else g.math('GREATER_THAN', el, roof)
sd_ = (math.sin(-.33) * math.cos(.41), math.cos(-.33) * math.cos(.41), math.sin(.41))
ca = g.vm('DOT_PRODUCT', d, sd_); glow = g.add(g.mul(g.math('EXPONENT', g.mul(g.sub(ca, 1.0), 1 / (.085 ** 2))), 34.0), g.mul(g.math('EXPONENT', g.mul(g.sub(ca, 1.0), 1 / (.38 ** 2))), 1.6))
sky = g.mix(1, sky, g.vm('SCALE', (1.0, .90, .74), scale=glow), 'ADD')
isky = g.math('MAXIMUM', isky, g.mr(ca, .955, .985))
col = g.mix(isky, g.mix(1, fac, (2.3, 2.28, 2.22), 'MULTIPLY'), g.mix(1, sky, g.comb(skyS, skyS, skyS), 'MULTIPLY'))
bg = g.n('Background', Color=col, Strength=6.0).outputs[0]
ow = g.N.new('ShaderNodeOutputWorld'); g.L.new(bg, ow.inputs[0])
try: w.cycles.sampling_method = 'MANUAL'; w.cycles.sample_map_resolution = 1024
except Exception as e: print(e)
def portal(name, loc, rot, sx, sy):
    l = bpy.data.lights.new(name, 'AREA'); l.shape = 'RECTANGLE'; l.size = sx; l.size_y = sy; l.cycles.is_portal = True
    ob = bpy.data.objects.new(name, l); sc.collection.objects.link(ob); ob.location = loc; ob.rotation_euler = rot
portal('p_arka', ((WX[0] + WX[1]) / 2, YF + T, (WZ[0] + WZ[1]) / 2), (-math.pi / 2, 0, 0), WX[1] - WX[0], WZ[1] - WZ[0])
portal('p_sol', (XL - T, (LY[0] + LY[1]) / 2, (LZ[0] + LZ[1]) / 2), (0, -math.pi / 2, 0), LZ[1] - LZ[0], LY[1] - LY[0])
# odanın derininde sıcak ampul (karışık renk sıcaklığı)
l = bpy.data.lights.new('ampul', 'POINT'); l.energy = 5; l.color = (1, .62, .30); l.shadow_soft_size = .04; ob = bpy.data.objects.new('ampul', l); sc.collection.objects.link(ob); ob.location = (.9, -1.6, 1.15)

tf, gtf = mat('floresan'); gtf.out(gtf.n('Emission', Color=(.93, 1.0, .97), Strength=9.0).outputs[0])
for k_, (fx_, fy_) in enumerate(((-.35, -1.3), (.75, -1.3))): box(f'flo{k_}', (fx_ - .04, fy_ - .6, ZT - .07), (fx_ + .04, fy_ + .6, ZT - .03), tf)
perde, gp = mat('perde'); tr_ = gp.n('BsdfTranslucent', Color=(.80, .78, .74)).outputs[0]; dfp = gp.n('BsdfDiffuse', Color=(.80, .78, .74)).outputs[0]
gp.out(gp.mixsh(.28, gp.mixsh(.5, tr_, dfp), gp.n('BsdfTransparent').outputs[0]))
def curtain(name, y0, y1, z0, z1, seed):
    V_, F_ = [], []; ny, nz_ = 140, 8
    for j in range(nz_ + 1):
        for i in range(ny + 1):
            u_ = i / ny; V_.append((XL + .035 + .022 * math.sin(u_ * 44 + seed + .4 * math.sin(u_ * 9)) * (.7 + .3 * j / nz_), y0 + (y1 - y0) * u_ + .01 * math.sin(j + u_ * 20), z0 + (z1 - z0) * j / nz_))
    for j in range(nz_):
        for i in range(ny): a__ = j * (ny + 1) + i; F_.append((a__, a__ + 1, a__ + ny + 2, a__ + ny + 1))
    mesh_obj(name, V_, F_, (perde,))
curtain('perde1', -1.15, -.78, .05, 1.6, 0); curtain('perde2', -.10, .25, .05, 1.6, 2)
kapi = m_flat('kapi', (.10, .055, .03), .4, 10); box('kapi', (-1.2, YB, ZB), (-.45, YB + .03, 1.2), kapi)
isik, gi = mat('koridor'); gi.out(gi.n('Emission', Color=(1, .93, .82), Strength=3.2).outputs[0]); box('koridor', (.35, YB, ZB), (1.15, YB + .02, 1.25), isik)
for k_ in range(3): box(f'cerceve{k_}', (XR - .03, -2.4 + .75 * k_, .55), (XR, -1.95 + .75 * k_, 1.15), kapi); box(f'resim{k_}', (XR - .034, -2.35 + .75 * k_, .60), (XR - .028, -2.0 + .75 * k_, 1.10), m_flat(f'resim{k_}', (.5, .42, .3), .5, 4, (.12, .18, .2)))
for k_ in range(2): box(f'raf{k_}', (-.35, YB, .5 + .4 * k_), (.28, YB + .22, .53 + .4 * k_), kapi)
for k_ in range(14): box(f'sise{k_}', (-.33 + .085 * (k_ % 7), YB + .05, .53 + .4 * (k_ // 7)), (-.28 + .085 * (k_ % 7), YB + .10, .70 + .4 * (k_ // 7) + .06 * math.sin(k_ * 3)), m_flat(f'sise{k_}', [(.35, .05, .03), (.04, .12, .05), (.5, .35, .1), (.06, .08, .2)][k_ % 4], .25))
bm_, gb_ = mat('buhar'); ob_ = gb_.obj(); bx, by, bz = gb_.sep(ob_)
wp = gb_.vm('SCALE', gb_.vm('SUBTRACT', gb_.noise(gb_.map(ob_, scale=(1, 1, .75)), 17, 3, .5, color=True), (.5, .5, .5)), scale=.062)
ns = gb_.noise(gb_.map(gb_.vm('ADD', ob_, wp), loc=(.31, .12, .4), scale=(1, 1, .42)), 34, 4, .55, .6)
rr_ = gb_.math('SQRT', gb_.add(gb_.mul(bx, bx), gb_.mul(by, by))); R_ = gb_.mr(bz, .0, .13, .016, .030)
dn_ = gb_.mul(gb_.mr(ns, .47, .70, 0, 1, True), gb_.mr(gb_.math('DIVIDE', rr_, R_), .45, 1.0, 1, 0, True)); dn_ = gb_.mul(dn_, gb_.mul(gb_.mr(bz, .0, .012), gb_.mr(bz, .035, .125, 1, 0, True)))
vs_ = gb_.n('VolumeScatter', Color=(1, 1, 1), Density=gb_.mul(dn_, 3.0), Anisotropy=.45).outputs[0]; gb_.out(None, vs_)
lathe('buhar', np.array([(0, 0), (12, 0), (18, 1), (19.5, 8), (21, 14), (26, 40), (31, 90), (32, 128), (0, 130)]) * MM, 48, (bm_,), loc=(0, 0, SZ + .0722))
# =================================================================== KAMERA
cam = bpy.data.cameras.new('kam'); co = bpy.data.objects.new('kam', cam); sc.collection.objects.link(co); sc.camera = co
cam.sensor_fit = 'VERTICAL'; cam.sensor_height = 36; cam.sensor_width = 27; cam.lens = 66
loc = Vector((.004, -.462, .168)); tgt = Vector((.0095, 0, .0555))
co.location = loc; q = (tgt - loc).to_track_quat('-Z', 'Y').to_euler(); q.rotate_axis('Z', math.radians(-1.1)); co.rotation_euler = q
cam.dof.use_dof = True; cam.dof.aperture_fstop = 5.6; cam.dof.aperture_blades = 9; cam.dof.aperture_rotation = .3
fwd = (tgt - loc).normalized(); cam.dof.focus_distance = (Vector((0, -.019, .06)) - loc).dot(fwd)
cam.clip_start = .01
nrg = 96; VV_, FF_ = [], []
for j in range(nrg):
    t_ = 2 * math.pi * j / nrg
    for r__ in (.0098, .09): VV_.append((r__ * math.cos(t_), r__ * math.sin(t_), -.030))
for j in range(nrg): j2_ = (j + 1) % nrg; FF_.append((2 * j, 2 * j + 1, 2 * j2_ + 1, 2 * j2_))
mk_, gk_ = mat('namlu'); gk_.out(gk_.n('Emission', Color=(0, 0, 0), Strength=0.0).outputs[0])
ng = mesh_obj('namlu', VV_, FF_, (mk_,)); ng.rotation_euler = co.rotation_euler; ng.location = co.location
for a__ in ('visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter', 'visible_shadow'): setattr(ng, a__, False)

# =================================================================== RENDER
sc.render.engine = 'CYCLES'; cy = sc.cycles
pf = bpy.context.preferences.addons['cycles'].preferences; pf.compute_device_type = 'OPTIX'; pf.get_devices()
for dv in pf.devices: dv.use = dv.type == 'OPTIX'
cy.device = 'GPU'; cy.samples = SPP; cy.use_adaptive_sampling = True; cy.adaptive_threshold = float(arg.get('thr', .012)); cy.adaptive_min_samples = 64
cy.max_bounces = 40; cy.diffuse_bounces = 24; cy.glossy_bounces = 12; cy.transmission_bounces = 32; cy.volume_bounces = 1; cy.transparent_max_bounces = 32
cy.caustics_reflective = True; cy.caustics_refractive = True; cy.blur_glossy = .05; cy.sample_clamp_indirect = float(arg.get('clamp', 30)); cy.use_light_tree = True
cy.use_denoising = False
vl = sc.view_layers[0]; vl.cycles.denoising_store_passes = True
sc.render.resolution_x = W; sc.render.resolution_y = int(W * 4 / 3); sc.render.resolution_percentage = 100
if CROP:
    a = list(map(float, CROP.split(','))); sc.render.use_border = True; sc.render.use_crop_to_border = True
    sc.render.border_min_x, sc.render.border_min_y, sc.render.border_max_x, sc.render.border_max_y = a
cy.use_denoising = bool(DEN)
if DEN: cy.denoiser = 'OPENIMAGEDENOISE'; cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'; cy.denoising_prefilter = 'ACCURATE'; cy.denoising_use_gpu = False
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Base Contrast' if False else 'None'
sc.view_settings.exposure = float(arg.get('ev', 0))
sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32' if False else '16'
sc.render.filepath = os.path.abspath(OUT) + '.exr'
sc.render.use_persistent_data = False
if arg.get('blend'): bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(arg['blend']))
if SPP > 0:
    bpy.ops.render.render(write_still=True)

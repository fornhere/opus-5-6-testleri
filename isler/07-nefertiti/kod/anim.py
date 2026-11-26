"""Sinematik film.  blender -b ../nefertiti_heykel.blend -P anim.py -- kur   -> ../film.blend
   (render: blender -b ../film.blend -P render_film.py -- ...)"""
import bpy, sys, os, math, mathutils
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
V = mathutils.Vector
# --- müze kurulumunu scene.py'den al (kamera/render öncesine kadar)
src = open(os.path.join(HERE, 'scene.py')).read().split('# --- kamera')[0].replace("inputs['Detail'].default_value = 8","inputs['Detail'].default_value = 8")
_av = sys.argv; sys.argv = ['x', '--', '/tmp/x.png', '10', '10', '1']
exec(compile(src, 'scene.py', 'exec'))
sys.argv = _av
sc = bpy.context.scene
FPS = 30; sc.render.fps = FPS
def fr(s): return int(round(s * FPS))
# ------------------------------------------------ zaman çizelgesi (sn)
T_GLIDE, T_WAVE0, T_PULL, T_D1, T_D2, T_D3, T_DARK, T_HERO, T_END = 0.0, 5.8, 14.4, 14.4, 15.7, 17.0, 18.6, 19.2, 28.0
NF = fr(T_END); sc.frame_start = 1; sc.frame_end = NF
t = np.arange(NF) / FPS
def smooth(x): x = np.clip(x, 0, 1); return x * x * x * (x * (x * 6 - 15) + 10)
def ease(a, b, tt): return smooth((tt - a) / (b - a))
def path(keys, tt):
    """keys: [(zaman, (değerler))] -> merkezcil olmayan yumuşak Hermite (hız sürekli)"""
    T = np.array([k[0] for k in keys], float); P = np.array([k[1] for k in keys], float)
    if P.ndim == 1: P = P[:, None]
    m = np.zeros_like(P)
    for i in range(1, len(T) - 1): m[i] = (P[i + 1] - P[i - 1]) / (T[i + 1] - T[i - 1])
    i = np.clip(np.searchsorted(T, tt, 'right') - 1, 0, len(T) - 2); h = (T[i + 1] - T[i])
    u = np.clip((tt - T[i]) / h, 0, 1)[:, None]; h = h[:, None]
    return (2*u**3 - 3*u**2 + 1) * P[i] + (u**3 - 2*u**2 + u) * h * m[i] + (-2*u**3 + 3*u**2) * P[i + 1] + (u**3 - u**2) * h * m[i + 1]
EYE = np.array([-.305, -1.315, 2.69])
def orb(az, dist, z, c=(0, 0)):
    a = math.radians(az); return (c[0] + dist * math.sin(a), c[1] - dist * math.cos(a), z)
pos = np.zeros((NF, 3)); tgt = np.zeros((NF, 3)); lens = np.zeros(NF); fst = np.zeros(NF); foc = np.zeros((NF, 3))
def put(a, b, kp, kt, kl, kf, kfoc=None):
    i0, i1 = fr(a), fr(b); s = t[i0:i1]
    pos[i0:i1] = path(kp, s); tgt[i0:i1] = path(kt, s); lens[i0:i1] = path(kl, s)[:, 0]; fst[i0:i1] = path(kf, s)[:, 0]
    foc[i0:i1] = path(kfoc or kt, s)
# 1+2: tek plan: dudak -> burun -> göz -> geri çekilip tam cepheye
kp = [(0, (-1.75, -2.75, 1.80)), (2.0, (-1.55, -2.95, 2.02)), (4.0, (-1.30, -3.02, 2.42)), (5.4, (-1.06, -2.92, 2.66)), (6.4, (-.99, -2.78, 2.70)), (7.4, (-1.06, -2.95, 2.71)),
      (9.0, orb(-30, 6.8, 2.70)), (10.8, orb(-24, 12.4, 2.52)), (13.0, orb(-9, 13.0, 2.40)), (14.4, orb(-1.5, 13.0, 2.36))]
kt = [(0, (-.16, -1.36, 1.92)), (2.0, (-.16, -1.40, 2.08)), (4.0, (-.20, -1.40, 2.44)), (5.4, (-.30, -1.33, 2.66)), (6.4, (-.31, -1.33, 2.70)), (7.4, (-.30, -1.31, 2.715)),
      (9.0, (-.04, -.70, 2.80)), (10.8, (0, -.1, 2.50)), (13.0, (0, 0, 2.40)), (14.4, (0, 0, 2.39))]
kl = [(0, 62), (2.0, 66), (4.0, 72), (6.4, 84), (7.4, 82), (9.0, 58), (10.8, 50), (14.4, 49)]
kf = [(0, .24), (2.0, .24), (4.0, .28), (6.4, .36), (7.4, .38), (9.0, .4), (11.0, .9), (14.4, 1.4)]
kfo = [(0, (-.20, -1.50, 2.02)), (2.0, (-.20, -1.50, 2.08)), (4.0, (-.26, -1.50, 2.44)), (5.4, (-.31, -1.36, 2.67)), (6.4, tuple(EYE)), (7.4, tuple(EYE)), (9.0, (-.2, -1.3, 2.7)), (11.0, (0, -1.2, 2.6)), (14.4, (0, -1.1, 2.6))]
put(0, T_PULL, kp, kt, kl, kf, kfo)
# 3: üç ayrıntı
put(T_D1, T_D2, [(T_D1, (1.15, -2.55, 1.15)), (T_D2, (.45, -2.75, 1.00))], [(T_D1, (.34, -.50, .60)), (T_D2, (.05, -.58, .54))], [(T_D1, 80), (T_D2, 80)], [(T_D1, .26), (T_D2, .26)], [(T_D1, (.34, -.52, .60)), (T_D2, (.05, -.62, .52))])
put(T_D2, T_D3, [(T_D2, (.80, -3.60, 3.45)), (T_D3, (1.25, -3.25, 4.00))], [(T_D2, (.06, -1.0, 3.66)), (T_D3, (.12, -.92, 3.95))], [(T_D2, 72), (T_D3, 72)], [(T_D2, .30), (T_D3, .30)], [(T_D2, (.02, -1.12, 3.70)), (T_D3, (.05, -1.02, 3.95))])
put(T_D3, T_DARK, [(T_D3, (4.2, -1.55, 2.30)), (T_DARK, (4.35, -2.0, 2.40))], [(T_D3, (.10, -1.00, 2.42)), (T_DARK, (.06, -1.02, 2.46))], [(T_D3, 70), (T_DARK, 70)], [(T_D3, .35), (T_DARK, .35)], [(T_D3, (.25, -1.25, 2.4)), (T_DARK, (.28, -1.25, 2.4))])
# 4: karanlık -> ışıklar -> kahraman
put(T_DARK, T_END, [(T_DARK, orb(97, 14.2, 2.55)), (20.2, orb(86, 14.2, 2.5)), (22.8, orb(52, 14.2, 2.38)), (25.4, orb(34, 13.8, 2.30)), (T_END, orb(29.5, 12.7, 2.28))],
    [(T_DARK, (-.10, -.05, 2.42)), (20.2, (-.05, -.05, 2.42)), (22.8, (.0, 0, 2.40)), (25.4, (.05, .05, 2.38)), (T_END, (.06, .06, 2.38))],
    [(T_DARK, 50), (25.4, 51), (T_END, 51)], [(T_DARK, .5), (22.8, .34), (T_END, .24)], [(T_DARK, (.6, -.9, 2.5)), (22.8, (.45, -1.2, 2.55)), (T_END, (.35, -1.35, 2.6))])
# el kamerası nefesi: çok küçük, sürekli
sh = np.stack([np.sin(t * 1.1) + .5 * np.sin(t * 2.3 + 1), np.sin(t * .9 + 2) + .5 * np.sin(t * 1.9), np.sin(t * 1.3 + 4) + .4 * np.sin(t * 2.7 + .5)], 1)
dist = np.linalg.norm(tgt - pos, axis=1)[:, None]
tgt = tgt + sh * .0012 * dist
c = bpy.data.cameras.new('FilmKamera'); co = bpy.data.objects.new('FilmKamera', c); mus.objects.link(co); sc.camera = co
c.sensor_width = 36; c.sensor_fit = 'HORIZONTAL'; c.dof.use_dof = True; c.clip_start = .02; c.clip_end = 400
co.rotation_mode = 'QUATERNION'
def fcurve(owner, path_, idx, vals):
    """kare başına doğrusal anahtar"""
    ad = owner.animation_data or owner.animation_data_create()
    if ad.action is None:
        ad.action = bpy.data.actions.new(owner.name + '_a')
    fc = ad.action.fcurve_ensure_for_datablock(owner, path_, index=idx) if hasattr(ad.action, 'fcurve_ensure_for_datablock') else ad.action.fcurves.new(path_, index=idx)
    fc.keyframe_points.add(len(vals))
    co_ = np.empty(2 * len(vals)); co_[0::2] = np.arange(len(vals)) + 1; co_[1::2] = vals
    fc.keyframe_points.foreach_set('co', co_); fc.keyframe_points.foreach_set('interpolation', np.full(len(vals), 1, dtype=np.int32)); fc.update()
Q = []
pq = None
for i in range(NF):
    q = (V(tgt[i]) - V(pos[i])).to_track_quat('-Z', 'Y')
    if pq and pq.dot(q) < 0: q.negate()
    pq = q; Q.append(tuple(q))
Q = np.array(Q)
for k in range(3): fcurve(co, 'location', k, pos[:, k])
for k in range(4): fcurve(co, 'rotation_quaternion', k, Q[:, k])
fcurve(c, 'lens', 0, lens); fcurve(c, 'dof.aperture_fstop', 0, fst); fcurve(c, 'dof.focus_distance', 0, np.linalg.norm(foc - pos, axis=1))

# ------------------------------------------------ hızlı malzeme + boya dalgası
R = np.where(t < T_WAVE0, -.2, .015 + .30 * smooth((t - T_WAVE0) / 1.9) + 2.80 * smooth((t - 7.2) / 6.9))
R[t >= T_PULL] = 9
GEN = .005 + .024 * smooth(np.clip(R, 0, 9) / 1.3)
HAFIF = 'hafif' in sys.argv
IMG = {im.name: im for im in bpy.data.images}
def fast(o, kind):
    # pişmemiş köşeleri ortalama ile doldur
    for ca in o.data.color_attributes:
        v = np.empty(len(o.data.vertices) * 4, np.float32); ca.data.foreach_get('color', v); v = v.reshape(-1, 4)
        if ca.name in ('bTen', 'bTas', 'bPuruz', 'bHam', 'bUzak', 'bTepe', 'bRenk'):
            bad = v[:, 0] <= 1e-5
            if bad.any() and ca.name != 'bUzak': v[bad, :3] = np.median(v[~bad, :3], axis=0)
            elif ca.name == 'bUzak':
                p = np.empty(len(o.data.vertices) * 3, np.float32); o.data.vertices.foreach_get('co', p); p = p.reshape(-1, 3)
                dd = np.linalg.norm(p - EYE, axis=1); bad = np.abs(v[:, 0] - dd) > .5; v[bad, :3] = dd[bad, None]
            print('dolgu', o.name, ca.name, int(bad.sum())); ca.data.foreach_set('color', v.ravel())
    mt = bpy.data.materials.new('Hızlı ' + o.name); mt.use_nodes = True; nt = mt.node_tree; N = nt.nodes; L = nt.links
    b = N['Principled BSDF']
    def n(k, **kw):
        x = N.new(k)
        for a, v in kw.items(): setattr(x, a, v)
        return x
    def lnk(v, inp):
        if hasattr(v, 'is_output'): L.new(v, inp)
        else: inp.default_value = v
    def A(name, col=False): return n('ShaderNodeAttribute', attribute_name=name).outputs['Color' if col else 'Fac']
    def tex(im, uvn, ext):
        u = n('ShaderNodeUVMap', uv_map=uvn); x = n('ShaderNodeTexImage', image=IMG[im], extension=ext, interpolation='Linear'); L.new(u.outputs[0], x.inputs[0]); return x
    def mix(f, a, c_):
        x = n('ShaderNodeMix', data_type='RGBA'); lnk(f, x.inputs[0]); lnk(a, x.inputs[6]); lnk(c_, x.inputs[7]); return x.outputs[2]
    def mixf(f, a, c_):
        x = n('ShaderNodeMix', data_type='FLOAT'); lnk(f, x.inputs[0]); lnk(a, x.inputs[2]); lnk(c_, x.inputs[3]); return x.outputs[0]
    def m(op, a, c_=0.0):
        x = n('ShaderNodeMath', operation=op); lnk(a, x.inputs[0]); lnk(c_, x.inputs[1]); return x.outputs[0]
    def mr(v, a, c_):
        x = n('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP'); lnk(v, x.inputs[0]); lnk(a, x.inputs[1]); lnk(c_, x.inputs[2]); return x.outputs[0]
    tc = n('ShaderNodeTexCoord')
    def noise(sc_, d):
        x = n('ShaderNodeTexNoise'); x.inputs['Scale'].default_value = sc_; x.inputs['Detail'].default_value = d; x.inputs['Roughness'].default_value = .58; L.new(tc.outputs['Object'], x.inputs['Vector']); return x.outputs[0]
    fz, fr_ = noise(9, 2 if HAFIF else 3), noise(95, 2)
    if kind == 'govde':
        tf = tex('yuz boyasi', 'yuz', 'CLIP'); fa = m('MULTIPLY', tf.outputs['Alpha'], A('on')); cm = mr(A('rho'), 0.0, .03); st_ = A('bTasM'); inv = m('SUBTRACT', 1.0, st_)
        c_ = mix(fa, A('bTen', True), tf.outputs['Color']); c_ = mix(cm, c_, tex('gerdanlik boyasi', 'gerdan', 'REPEAT').outputs['Color']); c_ = mix(st_, c_, A('bTas', True))
        r = mixf(m('MULTIPLY', fa, .6), A('bPuruz'), .5); r = mixf(A('goz'), r, mixf(A('solgoz'), .045, .55)); r = mixf(cm, r, .72); r = mixf(st_, r, .9)
        gh = m('MULTIPLY', m('MULTIPLY', m('ADD', m('MULTIPLY', tex('gerdanlik kabartma', 'gerdan', 'REPEAT').outputs['Color'], .011), .007), cm), inv)
        hp = m('ADD', gh, m('MULTIPLY', fz, mixf(st_, .0038, .011)))
        hraw = gh; b.inputs['Specular IOR Level'].default_value = .42
    elif kind == 'tac':
        cap = A('tepe'); c_ = mix(cap, tex('tac boyasi', 'tac', 'REPEAT').outputs['Color'], A('bTepe', True)); c_ = mix(A('bHi'), c_, srgb(190, 170, 134)); c_ = mix(A('bLo'), c_, srgb(44, 34, 26))
        r = mixf(cap, .60, .9); gh = m('MULTIPLY', tex('tac kabartma', 'tac', 'REPEAT').outputs['Color'], .0145); hp = m('ADD', gh, m('MULTIPLY', fz, .003)); hraw = gh
        b.inputs['Specular IOR Level'].default_value = .4
    else:
        c_ = A('bRenk', True); r = .68; hp = m('MULTIPLY', fz, .006); hraw = None
    if HAFIF:                       # dalga bitti: yalnız boyalı malzeme
        L.new(c_, b.inputs['Base Color']); lnk(r, b.inputs['Roughness'])
        bp = n('ShaderNodeBump'); bp.inputs['Distance'].default_value = 1.0; bp.inputs['Strength'].default_value = 1.0
        L.new(hp, bp.inputs['Height']); L.new(bp.outputs[0], b.inputs['Normal']); nt.nodes.remove(fr_.node)
        o.data.materials.clear(); o.data.materials.append(mt); return
    val = n('ShaderNodeValue'); val.name = 'DALGA'; gen = n('ShaderNodeValue'); gen.name = 'KALINLIK'
    act = m('LESS_THAN', val.outputs[0], 6.0)
    d = m('SUBTRACT', m('ADD', A('bUzak'), m('MULTIPLY', m('SUBTRACT', fr_, .5), m('MULTIPLY', gen.outputs[0], 1.1))), val.outputs[0])
    k = mr(d, .006, -.006)
    wetk = m('MULTIPLY', m('MULTIPLY', k, mr(d, -.40, -.01)), act)
    L.new(mix(k, A('bHam', True), c_), b.inputs['Base Color'])
    L.new(mixf(m('MULTIPLY', wetk, .72), mixf(k, .86, r), .12), b.inputs['Roughness'])
    rawh = m('ADD', m('MULTIPLY', fr_, .0030), m('MULTIPLY', fz, .0060))
    if hraw is not None: rawh = m('ADD', rawh, hraw)
    bp = n('ShaderNodeBump'); bp.inputs['Distance'].default_value = 1.0; bp.inputs['Strength'].default_value = 1.0
    L.new(mixf(k, rawh, hp), bp.inputs['Height']); L.new(bp.outputs[0], b.inputs['Normal'])
    ad = m('ABSOLUTE', d); edge = mr(ad, gen.outputs[0], 0.0)
    halo = m('MULTIPLY', mr(d, m('MULTIPLY', gen.outputs[0], 9.0), 0.0), m('SUBTRACT', 1.0, k))
    b.inputs['Emission Color'].default_value = (1.0, .31, .05, 1)
    L.new(m('MULTIPLY', m('ADD', m('MULTIPLY', m('MULTIPLY', edge, edge), 2.9), m('MULTIPLY', m('MULTIPLY', halo, halo), .16)), act), b.inputs['Emission Strength'])
    fcurve(nt, 'nodes["DALGA"].outputs[0].default_value', 0, R); fcurve(nt, 'nodes["KALINLIK"].outputs[0].default_value', 0, GEN)
    mt.cycles.emission_sampling = 'NONE'
    o.data.materials.clear(); o.data.materials.append(mt)
for o in bpy.data.collections['Heykel'].objects: fast(o, 'govde' if 'gövde' in o.name else 'tac' if 'taç' in o.name else 'uraeus')

# ------------------------------------------------ ışık koreografisi
LT = {o.name: o for o in mus.objects if o.type == 'LIGHT'}
base = {k: o.data.energy for k, o in LT.items()}
def en(name, vals): fcurve(LT[name].data, 'energy', 0, vals)
hero = t >= T_DARK
def clunk(a, up=.10):            # ani yanış + hafif titreme + oturma
    x = t - a
    f = np.where(x < 0, 0, np.where(x < up, (x / up)**2 * 1.15, 1 + .18 * np.exp(-(x - up) * 7) * np.cos((x - up) * 46)))
    return np.clip(f, 0, None) * hero
end = np.ones(NF)
on = {'Kenar sol': clunk(19.4) * 1.9, 'Kenar sağ': clunk(20.2), 'Ana': clunk(21.4) , 'Dolgu': ease(21.5, 22.8, t) * hero, 'Alttan yumuşak': ease(21.5, 22.8, t) * hero}
for k in LT:
    if k.startswith('Duvar'): on[k] = 1.35 * ease(21.5, 23.2, t) * hero
    elif k.startswith('Niş'): on[k] = 1.25 * ease(21.8, 23.6, t) * hero
    elif k.startswith('Vazo'): on[k] = ease(22.2, 24.0, t) * hero
for k, v in on.items(): en(k, base[k] * v * end)
# sıyırma ışığı (1. plan): arkadan öne dolanır
def moving(name, kpos, ktgt, kw, kelvin, ang, size):
    o = spot(name, (0, 0, 5), (0, 0, 2), 100, kelvin, ang, .8, size)
    P = path(kpos, t); G = path(ktgt, t)
    q = []; pq = None
    o.rotation_mode = 'QUATERNION'
    for i in range(NF):
        x = (V(G[i]) - V(P[i])).to_track_quat('-Z', 'Y')
        if pq and pq.dot(x) < 0: x.negate()
        pq = x; q.append(tuple(x))
    q = np.array(q)
    for k in range(3): fcurve(o, 'location', k, P[:, k])
    for k in range(4): fcurve(o, 'rotation_quaternion', k, q[:, k])
    fcurve(o.data, 'energy', 0, kw); return o
early = (t < T_PULL)
fade = ease(.2, 2.2, t)
moving('Sıyırma', [(0, orb(-118, 8, 3.2)), (2, orb(-108, 8, 3.6)), (4, orb(-98, 8, 4.4)), (6, orb(-84, 8, 5.0)), (9, orb(-72, 10, 6.5)), (14.4, orb(-58, 13, 8.5)), (28, orb(-58, 13, 8.5))],
       [(0, (0, -1.2, 2.0)), (4, (0, -1.1, 2.4)), (8, (0, -1.1, 2.6)), (11, (0, 0, 2.5)), (28, (0, 0, 2.5))], np.where(early, ease(.3, 1.8, t) * (1700 + 2200 * ease(8, 12.5, t)), 0), 5200, 40, .30)
moving('Karşı kenar', [(0, orb(96, 9, 3.6)), (6, orb(104, 9, 5)), (14.4, orb(125, 11, 8)), (28, orb(125, 11, 8))], [(0, (0, -1.0, 2.1)), (6, (0, -.8, 2.5)), (28, (0, 0, 2.6))], np.where(early, ease(0, 1.0, t) * (1500 + 2600 * ease(8, 12.5, t)), 0), 6200, 40, .5)
moving('Sıcak ön', [(0, orb(-20, 10, 6)), (6, orb(-22, 10, 6)), (14.4, orb(-30, 14, 9)), (28, orb(-30, 14, 9))], [(0, (0, -.8, 2.1)), (6, (0, -1, 2.5)), (28, (0, 0, 2.4))], np.where(early, 60 * fade + 260 * ease(5.8, 7.0, t) + 3900 * ease(7.8, 13.2, t), 0), 4500, 34, .8)
# ayrıntı planlarının ışıkları: her planda ışık süpürür
def win(a, b): return (t >= a) & (t < b)
d1, d2, d3 = win(T_D1, T_D2), win(T_D2, T_D3), win(T_D3, T_DARK)
kk = lambda a, b: np.clip((t - a) / (b - a), 0, 1)
moving('Ayrıntı1', [(0, orb(70, 6, 2.6)), (T_D1, orb(82, 6, 1.5)), (T_D2, orb(40, 6, 2.6)), (30, orb(28, 6, 3.2))], [(0, (.1, -.5, .6)), (30, (.1, -.5, .6))], np.where(d1, 900, 0), 4600, 30, .25)
moving('Ayrıntı2', [(0, orb(80, 7, 5.5)), (T_D2, orb(84, 7, 4.6)), (T_D3, orb(34, 7, 6.2)), (30, orb(34, 7, 6.2))], [(0, (0, -.8, 3.9)), (30, (0, -.8, 3.9))], np.where(d2, 1900, 0), 4600, 34, .25)
moving('Ayrıntı3', [(0, orb(-60, 7, 4.0)), (T_D3, orb(-74, 7, 2.6)), (T_DARK, orb(-14, 7, 4.4)), (30, orb(-18, 7, 4.2))], [(0, (0, -1.2, 2.4)), (30, (0, -1.2, 2.4))], np.where(d3, 2600, 0), 4600, 34, .25)
moving('Ayrıntı dolgu', [(0, orb(-30, 9, 5)), (30, orb(-30, 9, 5))], [(0, (0, -.6, 2)), (30, (0, -.6, 2.2))], np.where(d1 | d2, 170, 0) + np.where(d3, 0, 0), 6500, 50, 1.2)
moving('Ayrıntı kenar', [(0, orb(150, 9, 6)), (30, orb(150, 9, 6))], [(0, (0, -.2, 2.4)), (30, (0, -.2, 2.4))], np.where(d1 | d2 | d3, 1100, 0), 5600, 46, .4)
bgk = sc.world.node_tree.nodes['Background']
fcurve(sc.world.node_tree, 'nodes["Background"].inputs[1].default_value', 0, np.where(hero, .6 * ease(21.5, 23.4, t) * end, .10 * fade))

# ------------------------------------------------ toz zerreleri
rng = np.random.default_rng(7)
dm = bpy.data.materials.new('Toz'); dm.use_nodes = True; bb = dm.node_tree.nodes['Principled BSDF']; bb.inputs['Base Color'].default_value = (.42, .36, .28, 1); bb.inputs['Roughness'].default_value = 1
for g in range(3):
    bm = bmesh.new()
    for i in range(120):
        p = np.array([rng.uniform(-3.2, 3.2), rng.uniform(-4.2, 2.6), rng.uniform(.1, 5.6)])
        r = rng.choice([.0028, .004, .006], p=[.65, .28, .07])
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r, matrix=mathutils.Matrix.Translation(p))
    me = bpy.data.meshes.new(f'Toz{g}'); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(f'Toz{g}', me); mus.objects.link(o); me.materials.append(dm)
    ph = g * 2.1
    for k, (a, w_) in enumerate(((.22, .21), (.18, .17), (.16, .13))):
        fcurve(o, 'location', k, a * np.sin(t * w_ * (1 + .3 * g) + ph + k) + (0.015 * t if k == 2 else 0))
    fcurve(o, 'rotation_euler', 2, t * .012 * (1 if g % 2 else -1))
    fcurve(o, 'hide_render', 0, np.where(t > 7.8, 1.0, 0.0))
# arka plandaki sütunlar geri çekilsin
for o in list(mus.objects):
    if o.name.startswith('Pilaster'):
        o.data.materials.clear(); o.data.materials.append(bpy.data.materials.get('Pil') or mat('Pil', srgb(74, 66, 54), .85, 0, .2))
    if o.name.startswith('Profil'): o.hide_render = True
# salon ilk planlarda karanlıkta: hiç izlenmesin
for o in list(mus.objects):
    if o.type == 'MESH' and (o.name.startswith(('Duvar', 'Lambri', 'Silme', 'Zemin', 'Kemer', 'Niş', 'Pilaster', 'Arka', 'Vazo'))):
        fcurve(o, 'hide_render', 0, np.where(t < T_DARK, 1.0, 0.0))
# ------------------------------------------------ render ayarları
sc.render.engine = 'CYCLES'; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = .03
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.denoising_input_passes = 'RGB_ALBEDO_NORMAL'; sc.cycles.denoising_prefilter = 'ACCURATE'
sc.cycles.adaptive_min_samples = 5; sc.cycles.max_bounces = 3; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.sample_clamp_indirect = 4; sc.cycles.use_animated_seed = True
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .5; sc.render.use_persistent_data = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = .7
sc.render.resolution_x = 1920; sc.render.resolution_y = 1080; sc.render.image_settings.file_format = 'PNG'
for o in bpy.data.collections['Heykel'].objects: pass
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(HERE, '..', 'film_b.blend' if HAFIF else 'film.blend')))
print('FILM KURULDU', NF)

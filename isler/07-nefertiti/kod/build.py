"""Nefertiti büstünü kurar -> ../nefertiti_heykel.blend   (blender -b --factory-startup -P build.py -- <voksel>)"""
import sys, os; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, numpy as np, time
import geo, paint
from sdf import *
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
VOX = float(argv[0]) if argv else 0.06
TEX = float(argv[1]) if len(argv) > 1 else 1.0
OUT = os.path.join(HERE, '..', argv[2] if len(argv) > 2 else 'nefertiti_heykel.blend')
S = 0.1                        # 1 birim = 10 cm
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
col = bpy.data.collections.new('Heykel'); sc.collection.children.link(col)

def add(name, pts, quads):
    P = np.empty((len(pts), 3), F); P[:, 0] = pts[:, 0] * S; P[:, 1] = -pts[:, 1] * S; P[:, 2] = pts[:, 2] * S
    me = bpy.data.meshes.new(name)
    q = quads[:, ::-1].astype(np.int32)
    me.vertices.add(len(P)); me.vertices.foreach_set('co', P.ravel())
    me.loops.add(q.size); me.loops.foreach_set('vertex_index', q.ravel())
    me.polygons.add(len(q)); me.polygons.foreach_set('loop_start', np.arange(0, q.size, 4, dtype=np.int32))
    me.update(calc_edges=True)
    me.polygons.foreach_set('use_smooth', np.ones(len(q), bool))
    o = bpy.data.objects.new(name, me); col.objects.link(o); return o, q
def attr(o, name, v):
    a = o.data.attributes.new(name, 'FLOAT', 'POINT'); a.data.foreach_set('value', np.asarray(v, F))
def uv(o, q, name, U, V, wrap=False):
    lu = U[q.ravel()].reshape(q.shape).copy(); lv = V[q.ravel()].reshape(q.shape)
    if wrap:
        m = (lu.max(1) - lu.min(1)) > .5
        lu[m] = np.where(lu[m] < .5, lu[m] + 1, lu[m])
    l = o.data.uv_layers.new(name=name)
    l.uv.foreach_set('vector', np.stack([lu, lv], 2).astype(F).ravel())
def image(name, arr, color=True):
    H, W = arr.shape[:2]
    if arr.ndim == 2: arr = np.repeat(arr[..., None], 3, 2)
    if arr.shape[2] == 3: arr = np.concatenate([arr, np.ones((H, W, 1), F)], 2)
    im = bpy.data.images.new(name, W, H, alpha=True, float_buffer=False)
    im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    im.alpha_mode = 'CHANNEL_PACKED'
    im.pixels.foreach_set(np.clip(arr, 0, 1).astype(F).ravel()); im.update(); im.pack(); return im
def ev(fn, P, chunk=200000):
    return np.concatenate([fn(*(P[i:i + chunk].T.astype(F))) for i in range(0, len(P), chunk)])

t0 = time.time()
# ---------------------------------------------------------------- gövde
P, Q = mesh(geo.body, (-11.5, -10, -0.6), (11.5, 18, 37), VOX, verbose='govde')
YAMA = float(argv[3]) if len(argv) > 3 else 0
if YAMA:                         # yüze ince örgü yaması: kaba yüzler kutunun içinden çıkarılır, ince yüzler kutuya kırpılır
    lo, hi = np.array([-5.7, 10.0, 18.6]), np.array([5.7, 17.5, 31.2])
    Ph, Qh = mesh(geo.body, lo, hi, YAMA, verbose='yuz yamasi')
    ins = np.all((P > lo + .25) & (P < hi - .25), 1); Q = Q[~ins[Q].all(1)]
    inh = np.all((Ph > lo + .10) & (Ph < hi - .10), 1); Qh = Qh[inh[Qh].all(1)]
    Q = np.vstack([Q, Qh + len(P)]); P = np.vstack([P, Ph])
    use = np.zeros(len(P), bool); use[Q.ravel()] = True; mp = np.cumsum(use) - 1; P = P[use]; Q = mp[Q]
    print('yamali govde', len(P), len(Q))
ob, q = add('Baş ve gövde', P, Q)
x, f, z = P.T
soft = ev(geo.body_soft, P)
stone = np.where(z < 16, paint.ss(.10, .30, -soft), 0)
eps = VOX
for s in (1, -1):
    m = (x * s > 5.6) & (np.abs(z - 24.7) < 4.2) & (f > .5) & (f < 9)
    e = geo.ear(x[m], f[m], z[m], s, broken=False)
    hd = np.minimum(geo.loft(x[m], f[m], z[m]), 9)
    v = paint.ss(.012, .045, -e) * (hd > .22)
    ct = geo.ear(x[m], f[m], z[m], s, broken='kesik')
    v = np.maximum(v, paint.ss(.20, .05, ct) * (hd > .30) * .85)
    stone[m] = np.maximum(stone[m], v)
sN, rho, Lc = geo.collar_param(P); Atab, _ = geo.collar_arc()
rho = np.where((z < 15) & (f > -12), rho, -9)
ax = np.abs(x); al = geo.almond(ax, z)
eye = ((al < -.02) & (f > 10.5)).astype(F)
attr(ob, 'tas', stone); attr(ob, 'rho', rho); attr(ob, 'goz', eye); attr(ob, 'on', paint.ss(8.5, 9.5, f))
attr(ob, 'solgoz', (x > 0).astype(F))
uv(ob, q, 'yuz', (x + 6) / 12, (z - 19) / 11.5)
uv(ob, q, 'gerdan', sN, np.clip(rho / 8.4, 0.0005, .9995), wrap=True)
# ---------------------------------------------------------------- taç
P2, Q2 = mesh(geo.crown_solid, (-13, -20.5, 17.5), (13, 14.5, 50), VOX, verbose='tac')
oc, q2 = add('Mavi taç', P2, Q2)
def tp(a, b, c):
    t, u, v, hl, w = geo.crown_param(a, b, c); return np.stack([t, geo.crown_theta(u, v, t), geo.crown_r(t, u, v, hl, w)], 1)
A = ev(tp, P2); t_, th_, sh_ = A.T
T0, T1 = -.04, 1.02
attr(oc, 'tepe', paint.ss(.10, .30, -sh_) * (t_ > .9)); attr(oc, 'kirik', geo.chip(th_, t_))
uv(oc, q2, 'tac', (th_ / np.pi + 1) / 2, np.clip((t_ - T0) / (T1 - T0), 0, 1), wrap=True)
# ---------------------------------------------------------------- uraeus
P3, Q3 = mesh(geo.uraeus, (-5, 3, 33.5), (5.5, 13.5, 50), VOX * .7, verbose='uraeus')
ou, q3 = add('Uraeus', P3, Q3)
b0 = geo.crown_pos(*geo._upx(371, 306), 0)
attr(ou, 'kirik', paint.ss(1.1, .2, np.abs((P3[:, 2] - b0[2]))) * paint.ss(.25, .55, P3[:, 1] - b0[1]))
# ---------------------------------------------------------------- dokular
fi, fa = paint.face_all(int((300 if YAMA else 150) * TEX)); im_face = image('yuz boyasi', np.concatenate([fi, fa[..., None]], 2))
ci, ch, cr = paint.crown(int(6144 * TEX), int(2304 * TEX), T0, T1)
im_c = image('tac boyasi', ci); im_ch = image('tac kabartma', ch * .5 + .5, False); im_cr = image('tac puruz', cr, False)
gi, gh = paint.collar(Lc, int(8192 * TEX), 8.4, int(1536 * TEX), Atab)
im_g = image('gerdanlik boyasi', gi); im_gh = image('gerdanlik kabartma', gh * .5 + .4, False)
print('dokular', time.time() - t0, 'cevre', Lc, flush=True)

# ---------------------------------------------------------------- malzeme yardımcıları
def srgb(r, g, b):
    c = np.array([r, g, b]) / 255; c = np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055)**2.4); return (*c, 1)
class N:
    def __init__(s, name):
        s.m = bpy.data.materials.new(name); s.m.use_nodes = True; s.t = s.m.node_tree; s.t.nodes.clear()
        s.out = s.n('ShaderNodeOutputMaterial'); s.b = s.n('ShaderNodeBsdfPrincipled'); s.l(s.b.outputs[0], s.out.inputs[0])
    def n(s, k, **kw):
        n = s.t.nodes.new(k)
        for a, b in kw.items(): setattr(n, a, b)
        return n
    def l(s, a, b): s.t.links.new(a, b)
    def val(s, i, v):
        if hasattr(v, 'links') or isinstance(v, bpy.types.NodeSocket): s.l(v, i)
        else: i.default_value = v
    def mix(s, fac, a, b):
        n = s.n('ShaderNodeMix', data_type='RGBA'); s.val(n.inputs[0], fac); s.val(n.inputs[6], a); s.val(n.inputs[7], b); return n.outputs[2]
    def mixf(s, fac, a, b):
        n = s.n('ShaderNodeMix', data_type='FLOAT'); s.val(n.inputs[0], fac); s.val(n.inputs[2], a); s.val(n.inputs[3], b); return n.outputs[0]
    def math(s, op, a, b=0.0, clamp=False):
        n = s.n('ShaderNodeMath', operation=op, use_clamp=clamp); s.val(n.inputs[0], a); s.val(n.inputs[1], b); return n.outputs[0]
    def ss(s, x, a, b):
        n = s.n('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP'); s.val(n.inputs[0], x); n.inputs[1].default_value = a; n.inputs[2].default_value = b; return n.outputs[0]
    def attr(s, name): return s.n('ShaderNodeAttribute', attribute_name=name).outputs['Fac']
    def pos(s):
        return s.n('ShaderNodeTexCoord').outputs['Object']
    def noise(s, sc, det=4, rough=.55, vec=None, sx=(1, 1, 1)):
        v = vec or s.pos()
        if sx != (1, 1, 1):
            mp = s.n('ShaderNodeMapping'); mp.inputs['Scale'].default_value = sx; s.l(v, mp.inputs[0]); v = mp.outputs[0]
        n = s.n('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = sc; n.inputs['Detail'].default_value = det; n.inputs['Roughness'].default_value = rough; s.l(v, n.inputs['Vector']); return n.outputs[0]
    def tex(s, im, uvn, ext='EXTEND'):
        u = s.n('ShaderNodeUVMap', uv_map=uvn); t = s.n('ShaderNodeTexImage', image=im, extension=ext, interpolation='Cubic'); s.l(u.outputs[0], t.inputs[0]); return t
    def bump(s, h, dist, st=1.0, nrm=None):
        n = s.n('ShaderNodeBump'); s.val(n.inputs['Height'], h); n.inputs['Distance'].default_value = dist; n.inputs['Strength'].default_value = st
        if nrm: s.l(nrm, n.inputs['Normal'])
        return n.outputs[0]

# ---------------------------------------------------------------- gövde malzemesi
M = N('Boyali alci'); 
big, med, fin = M.noise(.9, 4), M.noise(5, 5), M.noise(34, 4)
skin = M.mix(M.ss(big, .35, .68), srgb(178, 125, 88), srgb(192, 140, 102))
skin = M.mix(M.math('MULTIPLY', M.ss(med, .50, .74), .55), skin, srgb(160, 108, 72))
skin = M.mix(M.math('MULTIPLY', M.ss(M.noise(2.2, 7, .65), .52, .70), .42), skin, srgb(206, 160, 126))
streak = M.noise(7, 5, .6, sx=(1, 1, .12))
skin = M.mix(M.math('MULTIPLY', M.ss(streak, .50, .80), .16), skin, srgb(146, 96, 70))
point = M.n('ShaderNodeNewGeometry').outputs['Pointiness']
skin = M.mix(M.math('MULTIPLY', M.ss(point, .500, .470), .45), skin, srgb(108, 68, 50))
skin = M.mix(M.math('MULTIPLY', M.ss(M.noise(52, 4, .6), .46, .70), .28), skin, srgb(206, 156, 116))
skin = M.mix(M.math('MULTIPLY', M.ss(M.noise(19, 6, .65), .50, .72), .34), skin, srgb(154, 100, 66))
spk = M.ss(M.noise(26, 2, .5), .75, .785)
spk2 = M.math('MULTIPLY', spk, M.math('MULTIPLY', M.ss(M.noise(1.4, 3), .54, .68), M.math('SUBTRACT', 1.0, M.attr('on'))))
skin = M.mix(M.math('MULTIPLY', spk2, .85), skin, srgb(226, 196, 156))
dark = M.math('MULTIPLY', M.ss(M.noise(40, 2, .5), .70, .78), .35)
skin = M.mix(dark, skin, srgb(96, 54, 36))
# yüz boyası
tf = M.tex(im_face, 'yuz', 'CLIP'); fa_ = M.math('MULTIPLY', tf.outputs['Alpha'], M.attr('on'))
skin = M.mix(fa_, skin, tf.outputs['Color'])
# gerdanlık
tg = M.tex(im_g, 'gerdan', 'REPEAT'); cm = M.ss(M.attr('rho'), .0, .03)
bodyc = M.mix(cm, skin, tg.outputs['Color'])
# taş / alçı
sn = M.noise(6, 8, .65)
stn = M.mix(M.ss(sn, .35, .70), srgb(186, 158, 118), srgb(222, 202, 166))
stn = M.mix(M.math('MULTIPLY', M.ss(M.noise(3, 5), .5, .75), .45), stn, srgb(160, 126, 88))
st_a = M.ss(M.math('ADD', M.attr('tas'), M.math('MULTIPLY', M.math('SUBTRACT', M.noise(14, 5), .5), .5)), .30, .62)
bodyc = M.mix(st_a, bodyc, stn)
M.l(bodyc, M.b.inputs['Base Color'])
r = M.mixf(M.ss(M.math('ADD', M.math('MULTIPLY', med, .6), M.math('MULTIPLY', M.noise(24, 4), .4)), .36, .64), .40, .62)
r = M.mixf(M.math('MULTIPLY', fa_, .6), r, .5)
r = M.mixf(M.math('MULTIPLY', M.attr('goz'), 1.0), r, M.mixf(M.attr('solgoz'), .10, .55))
r = M.mixf(cm, r, .72); r = M.mixf(st_a, r, .9)
M.l(r, M.b.inputs['Roughness'])
M.b.inputs['Specular IOR Level'].default_value = .42
nb = M.bump(M.mixf(st_a, M.math('ADD', M.math('MULTIPLY', fin, .45), M.math('MULTIPLY', M.noise(8, 4), 1.1)), M.math('ADD', M.math('MULTIPLY', sn, 4.0), M.noise(40, 4))), .006, .55)
nb = M.bump(M.math('MULTIPLY', tg.outputs['Color'] if False else M.tex(im_gh, 'gerdan', 'REPEAT').outputs['Color'], M.math('MULTIPLY', cm, M.math('SUBTRACT', 1.0, st_a))), .012, .9, nb)
nb = M.bump(M.math('MULTIPLY', cm, M.math('SUBTRACT', 1.0, st_a)), .012, .6, nb)
nb = M.bump(M.math('MULTIPLY', fa_, 1.0), .0012, .25, nb)
M.l(nb, M.b.inputs['Normal'])
ob.data.materials.append(M.m)
# ---------------------------------------------------------------- taç malzemesi
K = N('Boyali tac')
tc = K.tex(im_c, 'tac', 'REPEAT'); cap = K.attr('tepe')
capc = K.mix(K.ss(K.noise(4, 6), .35, .7), srgb(150, 128, 96), srgb(192, 168, 128))
c = K.mix(cap, tc.outputs['Color'], capc)
pt = K.n('ShaderNodeNewGeometry').outputs['Pointiness']
c = K.mix(K.math('MULTIPLY', K.ss(pt, .515, .56), .35), c, srgb(190, 170, 134))
c = K.mix(K.math('MULTIPLY', K.ss(pt, .495, .455), .5), c, srgb(44, 34, 26))
K.l(c, K.b.inputs['Base Color'])
K.l(K.mixf(cap, K.tex(im_cr, 'tac', 'REPEAT').outputs['Color'], .9), K.b.inputs['Roughness'])
K.b.inputs['Specular IOR Level'].default_value = .4
nb = K.bump(K.noise(30, 5), .005, .35)
nb = K.bump(K.tex(im_ch, 'tac', 'REPEAT').outputs['Color'], .016, .9, nb); K.l(nb, K.b.inputs['Normal'])
oc.data.materials.append(K.m)
# ---------------------------------------------------------------- uraeus malzemesi
U = N('Uraeus boya')
c = U.mix(U.ss(U.noise(7, 6), .35, .7), srgb(150, 118, 78), srgb(192, 158, 106))
c = U.mix(U.math('MULTIPLY', U.ss(U.noise(16, 4), .52, .7), .5), c, srgb(112, 84, 60))
c = U.mix(U.math('MULTIPLY', U.ss(U.n('ShaderNodeNewGeometry').outputs['Pointiness'], .50, .46), .6), c, srgb(70, 50, 36))
c = U.mix(U.math('MULTIPLY', U.attr('kirik'), .9), c, U.mix(U.ss(U.noise(12, 5), .4, .65), srgb(120, 84, 60), srgb(176, 140, 104)))
U.l(c, U.b.inputs['Base Color']); U.b.inputs['Roughness'].default_value = .68
U.l(U.bump(U.noise(22, 6, .6), .010, .6), U.b.inputs['Normal'])
ou.data.materials.append(U.m)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT))
print('KAYDEDILDI', OUT, time.time() - t0, flush=True)

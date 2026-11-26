"""Çay filmi: sahne_film.py üstüne kamera, güneş, buhar ve tarama dalgası. Kareleri EXR yazar."""
import sys, os, math
K = os.path.dirname(os.path.abspath(__file__)); RAWARG = sys.argv[sys.argv.index('--') + 1:]
A = dict(a.split('=', 1) for a in RAWARG)
sys.argv = ['blender', '--', 'spp=0']
__file__ = os.path.join(K, 'sahne_film.py')
exec(compile(open(__file__).read(), __file__, 'exec'))
import time
FPS = 24
SPP = int(A.get('spp', 96)); RW = int(A.get('w', 1600)); RH = int(RW * 9 / 16); DIRO = A.get('dir', 'film/taslak'); os.makedirs(os.path.join(K, DIRO), exist_ok=True)
STEP = int(A.get('step', 1)); SHOTS = A.get('shots', '1234'); F0 = int(A.get('f0', 0)); F1 = int(A.get('f1', 10 ** 6))
only = [int(x) for x in A['frames'].split(',')] if 'frames' in A else None

# ------------------------------------------------------------------ yumuşatmalar
def sm(x, a=0.0, b=1.0):
    t = min(1, max(0, (x - a) / (b - a))); return t * t * t * (t * (6 * t - 15) + 10)
def lerp(a, b, t): return a + (b - a) * t
def lv(a, b, t): return Vector([lerp(x, y, t) for x, y in zip(a, b)])
def drift(f, k): # el kamerası nefesi
    t = f / FPS; return Vector((math.sin(t * 1.7 + k) + .5 * math.sin(t * 3.1 + 2 * k), math.sin(t * 1.3 + 3 * k) * .6 + .4 * math.sin(t * 2.7 + k), math.sin(t * 1.9 + 5 * k) * .8)) * .00028

# ------------------------------------------------------------------ tarama dalgası: malzemelerin hepsine kil + tel kafes katmanı
SC = []          # (değer düğümü) listesi
POLAR = ('cam', 'cam_ic', 'cam_alt', 'cay', 'porselen', 'terra', 'hava', 'kabarcik'); GRID = {'mermer': .02, 'duvar': .10, 'lambri': .08, 'lambri2': .03, 'pervaz': .04, 'zemin': .2, 'tavan': .2, 'kumas': .05, 'perde': .05, 'seker_oz': .0016, 'simit': .0055, 'celik': .0042}
DUZ = ('seker', 'seker_tek', 'susam', 'kirinti', 'damla', 'lif', 'kumas', 'ten', 'sac')
DIRN = Vector((.34, .92, .20)).normalized()
for m_ in bpy.data.materials:
    if not m_.node_tree or m_.name.startswith(('buhar', 'namlu', 'floresan', 'koridor')): continue
    g = G(m_.node_tree); on = next((n for n in g.N if n.type == 'OUTPUT_MATERIAL'), None)
    if on is None or not on.inputs['Surface'].is_linked: continue
    src = on.inputs['Surface'].links[0].from_socket; base = m_.name.split('.')[0]
    val = g.n('Value'); val.outputs[0].default_value = 9.0; SC.append(val)
    pos = g.n('NewGeometry').outputs['Position']; o = g.obj()
    rip = g.mul(g.sub(g.noise(pos, 11, 2), .5), .012)
    dd = g.sub(g.add(g.vm('DOT_PRODUCT', pos, tuple(DIRN)), rip), val.outputs[0])            # >0: dalganın arkasında kalan = kil
    mask = g.mr(dd, 0, .0006)
    edge = g.mul(g.mr(dd, -.0009, 0), g.mr(dd, .0, .0026, 1, 0, True))
    x, y, z = g.sep(o)
    def ln(u, per, w): return g.mr(g.math('ABSOLUTE', g.sub(g.math('FRACT', g.add(g.math('DIVIDE', u, per), .5)), .5)), w / per * .5, w / per * .9, 1, 0)
    if base in POLAR:
        an = g.math('ARCTAN2', y, x); rr_ = g.math('SQRT', g.add(g.mul(x, x), g.mul(y, y)))
        l1 = g.mr(g.mul(g.math('ABSOLUTE', g.sub(g.math('FRACT', g.mul(an, 40 / (2 * math.pi))), .5)), g.mul(rr_, 2 * math.pi / 40)), .00010, .00018, 1, 0)
        nzv = g.math('ABSOLUTE', g.sep(g.n('NewGeometry').outputs['Normal'])[2]); l2 = g.mixf(g.math('GREATER_THAN', nzv, .72), ln(z, .0036, .00022), ln(rr_, .0046, .00026))
        wire = g.math('MAXIMUM', l1, l2)
    elif base in GRID:
        p_ = GRID[base]; w_ = p_ * (.022 if p_ > .015 else .075); nrm = g.sep(g.n('NewGeometry').outputs['Normal'])
        lx = g.mul(ln(x, p_, w_), g.math('LESS_THAN', g.math('ABSOLUTE', nrm[0]), .7)); ly = g.mul(ln(y, p_, w_), g.math('LESS_THAN', g.math('ABSOLUTE', nrm[1]), .7)); lz = g.mul(ln(z, p_, w_), g.math('LESS_THAN', g.math('ABSOLUTE', nrm[2]), .7))
        wire = g.math('MAXIMUM', g.math('MAXIMUM', lx, ly), lz)
    elif base in DUZ:
        wire = g.math('ADD', 0.0, 0.0)
    else:
        wf = g.N.new('ShaderNodeWireframe'); wf.use_pixel_size = True; wf.inputs[0].default_value = .55; wire = g.mul(wf.outputs[0], .75)
    clay = principled(g, Base_Color=g.mix(wire, (.44, .435, .425), (.045, .05, .055)), Roughness=.62, Specular_IOR_Level=.25)
    em = g.n('Emission', Color=(1.0, .42, .08), Strength=g.mul(edge, 26.0)).outputs[0]
    ad = g.N.new('ShaderNodeAddShader'); mx = g.mixsh(mask, src, clay); g.L.new(mx, ad.inputs[0]); g.L.new(em, ad.inputs[1])
    g.L.new(ad.outputs[0], on.inputs['Surface'])
for o_ in sc.objects:      # kristal kenarlarını yuvarlat (makro)
    if o_.type == 'MESH' and (o_.name.endswith('_kr') or o_.name.startswith('tane')):
        b_ = o_.modifiers.new('b', 'BEVEL'); b_.width = .000045; b_.segments = 2; b_.limit_method = 'NONE'; b_.use_clamp_overlap = True
buhar_mat = bpy.data.materials['buhar']
buhar_ob = bpy.data.objects['buhar']

# ------------------------------------------------------------------ çekimler: kare -> durum
def S1(f, n):      # şeker makro
    u = sm(f / (n - 1), -.15, 1.15)
    loc = lv((-.196, -.176, .0300), (-.128, -.212, .0340), u); tgt = lv((-.046, -.012, .0250), (-.040, -.012, .0265), u)
    foc = (lv((-.0735, -.0265, .006), (-.0640, -.0262, .007), u) - loc).dot((tgt - loc).normalized())
    return dict(loc=loc, tgt=tgt, lens=66, fs=10.0, foc=foc, gun=lerp(.14, .75, sm(f / n)), t=f / FPS + 4, roll=-.6)
def S2(f, n):      # buğu, netlik geçişi
    u = sm(f / (n - 1), -.15, 1.15)
    loc = lv((.062, -.182, .1200), (.018, -.190, .1130), u); tgt = lv((.004, -.004, .0835), (.003, -.004, .0865), u); d = (tgt - loc).normalized()
    a = (Vector((-.002, -.0262, .080)) - loc).dot(d); b = (Vector((.022, .010, .096)) - loc).dot(d)
    return dict(loc=loc, tgt=tgt, lens=86, fs=9.0, foc=lerp(a, b, sm(f / n, .45, .82)), gun=lerp(.40, .50, u), t=f / FPS + 9, roll=.5)
def S3(f, n):      # güneş çıkar, amber ışık yanar
    u = sm(f / (n - 1), -.1, 1.1)
    loc = lv((-.128, -.262, .056), (-.066, -.240, .070), u); tgt = lv((.004, -.004, .052), (.006, -.012, .046), u); d = (tgt - loc).normalized()
    a = (Vector((-.008, -.011, .050)) - loc).dot(d)
    return dict(loc=loc, tgt=tgt, lens=60, fs=9.0, foc=a, gun=lerp(.02, 1.08, sm(f / n, .16, .78)), t=f / FPS + 14, roll=.4)
def pw(x, xs, ys):
    for k in range(len(xs) - 1):
        if x <= xs[k + 1]: return lerp(ys[k], ys[k + 1], max(0, (x - xs[k]) / (xs[k + 1] - xs[k])))
    return ys[-1]
def wv(x, xs, ys):   # parçalı eğriyi yumuşat
    return sum(pw(x + o_, xs, ys) for o_ in (-.12, -.08, -.04, 0, .04, .08, .12)) / 7
def S4(f, n):      # geri çekilme + tarama
    s_ = f / FPS
    pull = sm(s_, -.4, 2.4)
    loc = lv((-.020, -.300, .108), (.004, -.440 + .022 * sm(s_, 5.9, 7.6), .150), pull); tgt = lv((.004, 0, .056), (.018, 0, .052), pull)
    orb = sm(s_, 2.2, 6.6) * math.radians(22)
    c = Vector((.01, 0, 0)); v = loc - c; loc = c + Vector((v.x * math.cos(orb) - v.y * math.sin(orb), v.x * math.sin(orb) + v.y * math.cos(orb), v.z + .020 * math.sin(math.pi * sm(s_, 2.2, 6.6))))
    d = (tgt - loc).normalized(); foc = (Vector((0, -.018, .06)) - loc).dot(d)
    wav = wv(s_, (0, 1.95, 2.35, 3.60, 3.90, 4.35, 4.65, 5.85, 6.25, 9), (1.1, 1.0, .33, -.17, -.50, -.50, -.17, .33, 1.0, 1.1))
    return dict(loc=loc, tgt=tgt, lens=lerp(58, 55, pull), fs=5.6, foc=foc, gun=lerp(.95, .80, pull), t=f / FPS + 20, roll=-.5, wav=wav)
CUT = {1: (S1, 56), 2: (S2, 56), 3: (S3, 60), 4: (S4, 176)}

cam.sensor_fit = 'HORIZONTAL'; cam.sensor_width = 36
ng.parent = co; ng.matrix_parent_inverse.identity(); ng.location = (0, 0, 0); ng.rotation_euler = (0, 0, 0)
sc.render.resolution_x = RW; sc.render.resolution_y = RH; sc.render.use_border = False
cy.samples = SPP; cy.adaptive_threshold = float(A.get('thr', .03)); cy.adaptive_min_samples = min(24, SPP); cy.max_bounces = 28; cy.transmission_bounces = 24; cy.diffuse_bounces = 12
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'; cy.denoising_use_gpu = True; cy.denoising_prefilter = 'ACCURATE'; cy.sample_clamp_indirect = 12
sc.render.use_persistent_data = True; sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '16'

def apply(shot, f):
    fn, n = CUT[shot]; S = fn(f, n)
    co.location = S['loc'] + drift(f, shot); q = (S['tgt'] + drift(f, shot + 7) * .6 - co.location).to_track_quat('-Z', 'Y').to_euler(); q.rotate_axis('Z', math.radians(S['roll'])); co.rotation_euler = q
    cam.lens = S['lens']; cam.dof.aperture_fstop = S['fs']; cam.dof.focus_distance = S['foc']
    ap = S['lens'] / S['fs'] / 2 / 1000; k_ = (ap + .030 * (36 / S['lens'] / 2 * 1.147) * .66) / .0098; ng.scale = (k_, k_, 1)
    gunes_v.outputs[0].default_value = S['gun']; bg_n.inputs['Strength'].default_value = 6.0 * (.62 + .38 * min(1, S['gun']))
    bz_v.outputs[0].default_value = S['t'] * .055
    w_ = S.get('wav', 9.0)
    for v_ in SC: v_.outputs[0].default_value = w_
    buhar_ob.hide_render = w_ < .04
    cy.seed = shot * 1000 + f
todo = [(s_, f) for s_ in sorted(CUT) if str(s_) in SHOTS for f in range(0, CUT[s_][1], STEP) if F0 <= f <= F1 and (only is None or f in only)]
print('kare sayisi', len(todo))
for (s_, f) in todo:
    out = os.path.join(K, DIRO, f's{s_}_{f:04d}.exr')
    if os.path.exists(out) and os.path.getsize(out) > 1000: continue
    apply(s_, f); sc.render.filepath = out + '.tmp.exr'; t0 = time.time(); bpy.ops.render.render(write_still=True); os.replace(out + '.tmp.exr', out); print('KARE', s_, f, round(time.time() - t0, 1), flush=True)
print('BITTI')

"""Node ve mesh yardımcıları. Hiçbir dış varlık yüklenmez."""
import bpy, math, random
import numpy as np
from mathutils import Vector, Matrix, noise

MM = 0.001
bpy.context.scene  # noqa

# ------------------------------------------------------------------ node DSL
class G:
    def __init__(self, tree):
        self.t = tree; self.N = tree.nodes; self.L = tree.links
    def put(self, sock, v):
        if v is None: return
        if hasattr(v, 'is_output'):
            self.L.new(v, sock)
        else:
            if sock.type in ('RGBA',) and not isinstance(v, (int, float)) and len(v) == 3: v = (*v, 1)
            if sock.type == 'RGBA' and isinstance(v, (int, float)): v = (v, v, v, 1)
            if sock.type == 'VECTOR' and isinstance(v, (int, float)): v = (v, v, v)
            sock.default_value = v
    def n(self, typ, props=None, **ins):
        nd = self.N.new('ShaderNode' + typ)
        for k, v in (props or {}).items(): setattr(nd, k, v)
        for k, v in ins.items():
            self.put(nd.inputs[k.replace('_', ' ')], v)
        return nd
    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self.N.new('ShaderNodeMath'); nd.operation = op; nd.use_clamp = clamp
        self.put(nd.inputs[0], a); self.put(nd.inputs[1], b); self.put(nd.inputs[2], c)
        return nd.outputs[0]
    def add(s, a, b): return s.math('ADD', a, b)
    def sub(s, a, b): return s.math('SUBTRACT', a, b)
    def mul(s, a, b): return s.math('MULTIPLY', a, b)
    def vm(self, op, a, b=None, scale=None):
        nd = self.N.new('ShaderNodeVectorMath'); nd.operation = op
        self.put(nd.inputs[0], a); self.put(nd.inputs[1], b)
        if scale is not None: self.put(nd.inputs['Scale'], scale)
        return nd.outputs['Value'] if op in ('LENGTH', 'DOT_PRODUCT', 'DISTANCE') else nd.outputs[0]
    def mix(self, f, a, b, blend='MIX'):
        nd = self.N.new('ShaderNodeMix'); nd.data_type = 'RGBA'; nd.blend_type = blend
        nd.clamp_factor = True
        self.put(nd.inputs[0], f); self.put(nd.inputs[6], a); self.put(nd.inputs[7], b)
        return nd.outputs[2]
    def mixf(self, f, a, b):
        nd = self.N.new('ShaderNodeMix'); nd.data_type = 'FLOAT'
        self.put(nd.inputs[0], f); self.put(nd.inputs[2], a); self.put(nd.inputs[3], b)
        return nd.outputs[0]
    def mr(self, v, a, b, c=0.0, d=1.0, smooth=False):
        nd = self.N.new('ShaderNodeMapRange'); nd.clamp = True
        nd.interpolation_type = 'SMOOTHSTEP' if smooth else 'LINEAR'
        for i, x in enumerate((v, a, b, c, d)): self.put(nd.inputs[i], x)
        return nd.outputs[0]
    def noise(self, vec, scale, detail=4, rough=.55, dist=0, lac=2.0, color=False, typ='FBM'):
        nd = self.N.new('ShaderNodeTexNoise'); nd.noise_type = typ
        self.put(nd.inputs['Vector'], vec)
        for k, v in dict(Scale=scale, Detail=detail, Roughness=rough, Distortion=dist, Lacunarity=lac).items():
            self.put(nd.inputs[k], v)
        return nd.outputs['Color' if color else 'Factor']
    def voro(self, vec, scale, feature='F1', rand=1, out='Distance', dim='3D'):
        nd = self.N.new('ShaderNodeTexVoronoi'); nd.feature = feature; nd.voronoi_dimensions = dim
        self.put(nd.inputs['Vector'], vec); self.put(nd.inputs['Scale'], scale); self.put(nd.inputs['Randomness'], rand)
        return nd.outputs[out]
    def obj(self): return self.n('TexCoord').outputs['Object']
    def map(self, vec, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
        nd = self.N.new('ShaderNodeMapping')
        self.put(nd.inputs[0], vec); nd.inputs[1].default_value = loc
        nd.inputs[2].default_value = rot; nd.inputs[3].default_value = scale
        return nd.outputs[0]
    def sep(self, vec):
        nd = self.N.new('ShaderNodeSeparateXYZ'); self.put(nd.inputs[0], vec); return nd.outputs
    def comb(self, x=0, y=0, z=0):
        nd = self.N.new('ShaderNodeCombineXYZ')
        for i, v in enumerate((x, y, z)): self.put(nd.inputs[i], v)
        return nd.outputs[0]
    def ramp(self, f, stops, interp='LINEAR'):
        nd = self.N.new('ShaderNodeValToRGB'); cr = nd.color_ramp; cr.interpolation = interp
        while len(cr.elements) < len(stops): cr.elements.new(.5)
        for e, (p, c) in zip(cr.elements, stops):
            e.position = p; e.color = (*c, 1) if not isinstance(c, (int, float)) else (c, c, c, 1)
        self.put(nd.inputs[0], f); return nd.outputs[0]
    def bump(self, h, dist, strength=1.0, normal=None):
        nd = self.N.new('ShaderNodeBump')
        self.put(nd.inputs['Height'], h); self.put(nd.inputs['Distance'], dist)
        self.put(nd.inputs['Strength'], strength); self.put(nd.inputs['Normal'], normal)
        return nd.outputs[0]
    def attr(self, name, out='Factor'):
        nd = self.N.new('ShaderNodeAttribute'); nd.attribute_name = name; return nd.outputs[out]
    def mixsh(self, f, a, b):
        nd = self.N.new('ShaderNodeMixShader')
        self.put(nd.inputs[0], f); self.L.new(a, nd.inputs[1]); self.L.new(b, nd.inputs[2]); return nd.outputs[0]
    def out(self, surf=None, vol=None):
        nd = self.N.new('ShaderNodeOutputMaterial')
        if surf is not None: self.L.new(surf, nd.inputs['Surface'])
        if vol is not None: self.L.new(vol, nd.inputs['Volume'])

def mat(name):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    m.node_tree.nodes.clear()
    return m, G(m.node_tree)

def principled(g, **k):
    return g.n('BsdfPrincipled', **{a: b for a, b in k.items()}).outputs[0]

# ------------------------------------------------------------------ mesh
def mesh_obj(name, verts, faces, mats=(), smooth=True, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(map(float, v)) for v in verts], [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    for m in mats: me.materials.append(m)
    if smooth: me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    return ob

def crspline(pts, per=10):
    """Merkezcil Catmull-Rom; noktalardan geçer."""
    P = np.array(pts, float)
    Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1:i + 3]
        t0 = 0; t1 = t0 + max(np.linalg.norm(p1 - p0), 1e-9) ** .5
        t2 = t1 + max(np.linalg.norm(p2 - p1), 1e-9) ** .5; t3 = t2 + max(np.linalg.norm(p3 - p2), 1e-9) ** .5
        for t in np.linspace(t1, t2, per, endpoint=False):
            A1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            A2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            A3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            B1 = (t2 - t) / (t2 - t0) * A1 + (t - t0) / (t2 - t0) * A2
            B2 = (t3 - t) / (t3 - t1) * A2 + (t - t1) / (t3 - t1) * A3
            out.append((t2 - t) / (t2 - t1) * B1 + (t - t1) / (t2 - t1) * B2)
    out.append(P[-1])
    return np.array(out)

def lathe(name, prof, seg=192, mats=(), perturb=None, matidx=None, loc=(0, 0, 0)):
    """prof: (r,z) listesi; r=0 uçlar kutup olur. Yön: normal, profil ilerleyişinin sağına bakar."""
    prof = np.asarray(prof, float)
    th = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    V, F, MI = [], [], []
    rows = []
    for k, (r, z) in enumerate(prof):
        if r < 1e-7:
            rows.append([len(V)]); V.append((0, 0, z)); continue
        rr = np.full(seg, r) if perturb is None else perturb(th, r, z, k)
        rows.append(list(range(len(V), len(V) + seg)))
        V += list(zip(rr * np.cos(th), rr * np.sin(th), np.full(seg, z)))
    for k in range(len(rows) - 1):
        a, b = rows[k], rows[k + 1]
        mi = 0 if matidx is None else matidx[k]
        for j in range(seg):
            j2 = (j + 1) % seg
            if len(a) == 1 and len(b) == 1: continue
            if len(a) == 1: F.append((a[0], b[j2], b[j]))
            elif len(b) == 1: F.append((a[j], a[j2], b[0]))
            else: F.append((a[j], a[j2], b[j2], b[j]))
            MI.append(mi)
    ob = mesh_obj(name, V, F, mats, loc=loc)
    ob.data.polygons.foreach_set('material_index', MI)
    return ob

def drop_dome(name, x, y, zfun, R, h, rng, mats, seg=64, rings=14, lumps=.18, elong=1.0, rot=0.0, contact=.62):
    """Yüzeye oturan düzensiz sıvı damlası; tabanı yüzeye hafif gömülü kapalı mesh."""
    ph = [rng.uniform(0, 6.28) for _ in range(5)]; am = [rng.uniform(.3, 1) * lumps / (i + 1) for i in range(5)]
    V, F = [], []
    def outline(t): return R * (1 + sum(a * math.sin((i + 2) * t + p) for i, (a, p) in enumerate(zip(am, ph))))
    top, bot = [], []
    for k in range(rings + 1):
        rho = k / rings
        rho_ = math.sin(rho * math.pi / 2)
        rt, rb = [], []
        for j in range(seg):
            t = 2 * math.pi * j / seg
            r = outline(t) * rho_
            lx, ly = r * math.cos(t) * elong, r * math.sin(t)
            px = x + lx * math.cos(rot) - ly * math.sin(rot); py = y + lx * math.sin(rot) + ly * math.cos(rot)
            z0 = zfun(px, py)
            rt.append(len(V)); V.append((px, py, z0 - 0.00004 + h * max(0, 1 - rho_ ** 2.2) ** contact))
        top.append(rt)
    for j in range(seg): pass
    for k in range(rings):
        for j in range(seg):
            j2 = (j + 1) % seg
            if k == 0 and False: pass
            F.append((top[k][j], top[k + 1][j], top[k + 1][j2], top[k][j2]))
    base = []
    for j in range(seg):
        vx = V[top[rings][j]]; base.append(len(V)); V.append((vx[0], vx[1], vx[2] - .0002))
    for j in range(seg):
        j2 = (j + 1) % seg; F.append((top[rings][j], base[j], base[j2], top[rings][j2]))
    F.append(tuple(reversed(base)))
    ob = mesh_obj(name, V, F, mats)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ob.data); bm.free()
    return ob

def rotm(pitch, roll, yaw):
    cp, sp, cr, sr, cy, sy = math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll), math.cos(yaw), math.sin(yaw)
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]]); Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

def settle(V, com, x, y, yaw, H, pr=(-.5, .5), rr=(-.35, .35), n=41, levels=4):
    """En düşük ağırlık merkezi = kararlı duruş. H(px,py): zemin yüksekliği (numpy)."""
    pc = (pr[0] + pr[1]) / 2; rc = (rr[0] + rr[1]) / 2; pw = (pr[1] - pr[0]) / 2; rw = (rr[1] - rr[0]) / 2
    best = None
    for lv in range(levels):
        for p in np.linspace(pc - pw, pc + pw, n):
            for r in np.linspace(rc - rw, rc + rw, n if rw > 0 else 1):
                W = V @ rotm(p, r, yaw).T
                cz = (rotm(p, r, yaw) @ com)[2]
                lift = np.max(H(W[:, 0] + x, W[:, 1] + y) - W[:, 2])
                e = cz + lift
                if best is None or e < best[0]: best = (e, p, r, lift)
        pc, rc = best[1], best[2]; pw *= 2.5 / n; rw *= 2.5 / n
    return best[1], best[2], best[3]

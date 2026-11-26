"""Hızlı kil önizlemesi: blender -b -P view.py -- <vox> <cikti on-eki>"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import bpy, numpy as np, math
import importlib, sdf, geo
from sdf import *
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
vox = float(argv[0]) if argv else 0.12
out = argv[1] if len(argv) > 1 else '../test/kil'
what = argv[2] if len(argv) > 2 else 'full'
bpy.ops.wm.read_factory_settings(use_empty=True)
def add(name, pts, quads, smooth=True):
    P = np.empty_like(pts); P[:, 0] = pts[:, 0]; P[:, 1] = -pts[:, 1]; P[:, 2] = pts[:, 2]   # f -> -Y
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(P)); me.vertices.foreach_set('co', P.ravel())
    q = quads[:, ::-1] if True else quads
    me.loops.add(q.size); me.loops.foreach_set('vertex_index', q.ravel().astype(np.int32))
    me.polygons.add(len(q)); me.polygons.foreach_set('loop_start', np.arange(0, q.size, 4, dtype=np.int32))
    me.update(calc_edges=True); me.validate()
    if smooth: me.polygons.foreach_set('use_smooth', np.ones(len(q), bool))
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); return o
if what == 'face':
    p, q = mesh(geo.body, (-9.5, 4, 14), (9.5, 18, 36), vox, verbose='yuz')
else:
    p, q = mesh(geo.body, (-11.5, -10, -0.6), (11.5, 18, 37), vox, verbose='govde')
ob = add('govde', p, q)
import math
def crown_simple():
    th = np.linspace(-np.pi, np.pi, 361)[:-1]; ts = np.linspace(0, 1, 60)
    V = []
    for t in ts:
        n = 2.32 - 0.27 * min(t * 1.3, 1)
        c = np.sign(np.cos(th)) * np.abs(np.cos(th))**(2 / n); s = np.sign(np.sin(th)) * np.abs(np.sin(th))**(2 / n)
        Fp = geo.F0 + (geo.F1 - geo.F0) * t; Bp = geo.B0 + (geo.B1 - geo.B0) * t
        C = (Fp + Bp) / 2; H = (Fp - Bp) / 2; w = geo.CW0 + (geo.CW1 - geo.CW0) * t
        gl = 0
        V.append(np.stack([s * w * 1.012, C[0] + c * H[0] * 1.012, C[1] + c * H[1] * 1.012], 1))
    V = np.concatenate(V); N = 360; Q = []
    for i in range(len(ts) - 1):
        for j in range(N):
            # altın bandın altını gizleme
            tt = ts[i + 1]; a = abs(math.degrees(th[j]))
            if tt < geo.gold_lo(np.array([a]))[0]: continue
            Q.append((i*N+j, i*N+(j+1)%N, (i+1)*N+(j+1)%N, (i+1)*N+j))
    return V.astype(np.float32), np.array(Q)
if what != 'face':
    cp, cq = mesh(geo.crown_solid, (-13, -20.5, 17.5), (13, 14.5, 50), vox, verbose='tac'); add('tac', cp, cq)
    up_, uq = mesh(geo.uraeus, (-5, 3, 33.5), (5.5, 13.5, 50), vox * .6, verbose='uraeus'); add('uraeus', up_, uq)
m = bpy.data.materials.new('kil'); m.use_nodes = True
b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (.55, .40, .30, 1); b.inputs['Roughness'].default_value = .45
for o in list(bpy.context.collection.objects): o.data.materials.append(m)
sc = bpy.context.scene
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.25, .27, .3, 1); w.node_tree.nodes['Background'].inputs[1].default_value = .6
def light(loc, e, size, tgt=(0, -5, 22)):
    l = bpy.data.lights.new('l', 'AREA'); l.energy = e; l.size = size
    o = bpy.data.objects.new('l', l); sc.collection.objects.link(o); o.location = loc
    import mathutils
    o.rotation_euler = (mathutils.Vector(tgt) - mathutils.Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
light((-45, -60, 75), 120000, 18); light((70, -40, 40), 25000, 40); light((20, 70, 60), 30000, 30)
# referans noktaları (profil)
if os.environ.get('REF'):
    prof = [(12.75,32.05),(13.33,30.67),(14.01,29.42),(14.43,27.87),(15.29,26.52),(16.33,25.08),(16.78,24.15),(16.84,23.84),(16.64,23.22),(16.33,22.91),(15.46,22.35),(15.61,21.87),(15.87,21.44),(15.75,20.98),(15.46,20.72),(15.73,20.16),(15.39,19.71),(15.13,19.39),(15.39,18.67),(15.54,18.05),(15.29,17.37),(14.47,16.98),(12.81,17.02),(10.96,16.92),(10.13,16.71),(9.3,15.57),(8.67,14.55),(6.67,13.06),(5.56,10.28),(5.28,8.06),(5.33,7.3),(5.83,5.83),(6.56,3.06),(6.4,1.1),(.56,20),(.28,18.06),(-.83,15.83),(-2.78,12.78),(-4.44,9.72),(-6.1,5.83),(-7.5,2.5)]
    frnt = [(6.65,26.5),(6.5,24),(6.2,22.4),(5.7,20.7),(4.95,19.2),(4.3,18.35),(3.6,17.7),(2.5,17.2),(1.62,26.4),(4.7,26.83),(3.0,27.5),(2.8,26.25),(.9,28.75),(3.25,29.7),(5.35,28.45),(1.68,23.3),(2.5,20.68),(.6,21.38),(0,19.43),(0,23.84),(0,20.7),(0,17.0)]
    mr = bpy.data.materials.new('r'); mr.use_nodes = True; nt = mr.node_tree; nt.nodes.clear()
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (1, .02, .02, 1); e.inputs[1].default_value = 2; ou = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0], ou.inputs[0])
    def dot(x, y, z):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=.07, location=(x, y, z), segments=8, ring_count=6); bpy.context.object.data.materials.append(mr)
        bpy.context.object['ref'] = 1
    for f_, z_ in prof: dot(-30, -f_, z_)
    for x_, z_ in frnt: dot(x_, -40, z_); dot(-x_, -40, z_)

import mathutils
def cam(name, loc, tgt, ortho=None, lens=85):
    c = bpy.data.cameras.new(name); o = bpy.data.objects.new(name, c); sc.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (mathutils.Vector(tgt) - mathutils.Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if ortho: c.type = 'ORTHO'; c.ortho_scale = ortho
    else: c.lens = lens
    c.clip_end = 1000
    return o
sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = False
pr = bpy.context.preferences.addons['cycles'].preferences
if os.environ.get('DEV', 'GPU') == 'GPU':
    pr.compute_device_type = 'OPTIX'; pr.get_devices()
    for d in pr.devices: d.use = d.type == 'OPTIX'
sc.cycles.device = os.environ.get('DEV', 'GPU')
try:
    sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.denoising_use_gpu = False
except Exception as e: print(e)
sc.view_settings.view_transform = 'AgX'
if what == 'face':
    cams = [cam('on', (0, -120, 24.5), (0, -10, 24.5), 18), cam('prof', (-120, -10, 24.5), (0, -10, 24.5), 18), cam('onp', (0, -96, 23), (0, -8, 23.5), None, 150), cam('uc2', (58, -88, 24), (0.5, -9, 24.3), None, 165)]
    sc.render.resolution_x = sc.render.resolution_y = 900
else:
    cams = [cam('on', (0, -83-13, 25), (0, 0, 24.5), None, 50), cam('prof', (-160, 1, 24.5), (0, 1, 24.5), 52), cam('uc', (70, -140, 30), (0, 0, 24.2), None, 85)]
    sc.render.resolution_x = 800; sc.render.resolution_y = 1000
for c in cams:
    sc.camera = c; sc.render.filepath = os.path.abspath(out + '_' + c.name.split('.')[0] + '.png'); bpy.ops.render.render(write_still=True)

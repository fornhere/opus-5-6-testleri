"""Müze sahnesi + render.  blender -b in.blend -P scene.py -- <cikti.png> <gx> <gy> <ornek> [kamera] [kaydet.blend]"""
import bpy, sys, os, math, mathutils
argv = sys.argv[sys.argv.index('--') + 1:]
out, RX, RY, SPP = argv[0], int(argv[1]), int(argv[2]), int(argv[3])
CAM = argv[4] if len(argv) > 4 else 'ana'
SAVE = argv[5] if len(argv) > 5 else None
V = mathutils.Vector
sc = bpy.context.scene
for o in list(sc.objects):
    if not any(o.name in c.objects for c in [bpy.data.collections['Heykel']]): bpy.data.objects.remove(o)
mus = bpy.data.collections.new('Müze'); sc.collection.children.link(mus)
def srgb(r, g, b):
    f = lambda c: c / 12.92 if c <= .04045 else ((c + .055) / 1.055)**2.4
    return (f(r / 255), f(g / 255), f(b / 255), 1)
def mat(name, color, rough, metal=0, spec=.5, noise=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; t = m.node_tree; b = t.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color; b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal; b.inputs['Specular IOR Level'].default_value = spec
    if noise:
        c2, scl, r2 = noise
        tc = t.nodes.new('ShaderNodeTexCoord'); n = t.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scl; n.inputs['Detail'].default_value = 8; n.inputs['Roughness'].default_value = .62
        t.links.new(tc.outputs['Object'], n.inputs['Vector'])
        mr = t.nodes.new('ShaderNodeMapRange'); mr.inputs[1].default_value = .33; mr.inputs[2].default_value = .70; t.links.new(n.outputs[0], mr.inputs[0])
        mx = t.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs[6].default_value = color; mx.inputs[7].default_value = c2
        t.links.new(mr.outputs[0], mx.inputs[0]); t.links.new(mx.outputs[2], b.inputs['Base Color'])
        m2 = t.nodes.new('ShaderNodeMapRange'); m2.inputs[3].default_value = rough; m2.inputs[4].default_value = r2; t.links.new(n.outputs[0], m2.inputs[0]); t.links.new(m2.outputs[0], b.inputs['Roughness'])
    return m
def box(name, c, s, m, bev=.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=c); o = bpy.context.object; o.name = name; o.scale = s; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bev: b = o.modifiers.new('b', 'BEVEL'); b.width = bev; b.segments = 4; b.limit_method = 'ANGLE'
    o.data.materials.append(m)
    for cl in o.users_collection: cl.objects.unlink(o)
    mus.objects.link(o); return o
# --- kaide: koyu patinalı bronz kutu, üstünde ince koyu plaka
br = mat('Kaide', srgb(34, 29, 26), .34, 0, .5, (srgb(52, 43, 36), 2.2, .46))
pl = mat('Plaka', srgb(30, 27, 25), .16, 0, .5, (srgb(40, 35, 31), 5, .24))
box('Kaide', (0, .05, -5.06), (4.1, 4.1, 10), br, .03)
box('Derz', (0, .05, -.085), (3.95, 3.95, .06), mat('Derz', srgb(8, 8, 8), .7), 0)
box('Kaide üst', (0, .05, -.035), (4.1, 4.1, .07), pl, .018)
# --- salon: yarım daire yeşil duvar, kırmızı süpürgelik, pilaster ve kemerli nişler
gw = mat('Yeşil duvar', srgb(62, 84, 62), .85, 0, .3, (srgb(38, 58, 44), 1.1, .9))
rd = mat('Kırmızı lambri', srgb(92, 30, 24), .7, 0, .3, (srgb(64, 20, 18), 1.6, .8))
gd = mat('Altın silme', srgb(150, 112, 60), .5, .3)
st = mat('Taş', srgb(128, 112, 92), .8, 0, .3, (srgb(96, 82, 66), 2, .85))
fl = mat('Zemin', srgb(44, 40, 38), .28, 0, .5, (srgb(70, 62, 56), 1.4, .4))
RAD, CY = 46, 0.0
import bmesh
def ring(name, r, z0, z1, m, a0=-20, a1=200, n=96, depth=0):
    bm = bmesh.new(); vs = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        vs.append((bm.verts.new((r * math.cos(a), CY + r * math.sin(a), z0)), bm.verts.new((r * math.cos(a), CY + r * math.sin(a), z1))))
    for i in range(n): bm.faces.new((vs[i][0], vs[i][1], vs[i + 1][1], vs[i + 1][0]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); mus.objects.link(o); me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    return o
FLOOR = -10.06
ring('Duvar', RAD, FLOOR + 11, 40, gw); ring('Lambri', RAD - .3, FLOOR, FLOOR + 10.6, rd); ring('Silme', RAD - .6, FLOOR + 10.6, FLOOR + 11.4, gd); ring('Silme2', RAD - .6, 24, 25, gd)
bpy.ops.mesh.primitive_plane_add(size=160, location=(0, 0, FLOOR)); o = bpy.context.object; o.data.materials.append(fl)
for cl in o.users_collection: cl.objects.unlink(o)
mus.objects.link(o); o.name = 'Zemin'
def arch(ang, w, h0, h1, r, m, d, name):
    """kemerli niş: düz panel + yarım daire"""
    bm = bmesh.new(); pts = [(-w, h0), (w, h0)]; n = 24
    for i in range(n + 1):
        a = math.pi * i / n; pts.append((w * math.cos(a), h1 + w * math.sin(a)))
    a = math.radians(ang); rx, ry = math.cos(a), math.sin(a)
    vs = [bm.verts.new((r * rx - p[0] * ry, CY + r * ry + p[0] * rx, p[1])) for p in pts]
    bm.faces.new(vs); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new(name, me); mus.objects.link(ob); me.materials.append(m)
dk = mat('Niş içi', srgb(26, 34, 28), .9, 0, .2)
nis = mat('Niş duvarı', srgb(104, 106, 88), .9, 0, .2, (srgb(80, 84, 70), 1.2, .95))
for k, ang in enumerate((31, 64, 97, 130, 163)):
    arch(ang, 5.2, FLOOR + .2, 5.2, RAD - .9, st, 0, f'Kemer{k}')
    arch(ang, 4.5, FLOOR + .3, 5.2, RAD - 1.1, nis, 0, f'Niş{k}')
    a = math.radians(ang - 16.5)
    for da in (-2.6, 2.6):
        a2 = a + math.radians(da)
        o = box(f'Pilaster{k}', ((RAD - .9) * math.cos(a2), (RAD - .9) * math.sin(a2), 7), (.8, 1.5, 34), st, .05); o.rotation_euler = (0, 0, a2)
# --- arkada bulanık iki kaide ve üstlerinde torna vazolar
import numpy as np
def lathe(name, prof, loc, m):
    bm = bmesh.new(); n = 48; R = []
    for r, z in prof: R.append([bm.verts.new((r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z)) for i in range(n)])
    for a, b in zip(R[:-1], R[1:]):
        for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); mus.objects.link(o); o.location = loc; me.materials.append(m); return o
ped = mat('Arka kaide', srgb(120, 114, 104), .7); al1 = mat('Kaymak taşı', srgb(200, 180, 146), .5); al2 = mat('Siyah bazalt', srgb(88, 84, 80), .35)
for (x, y), prof, mm in [((-16.3, 17.6), [(0, 0), (.7, 0), (.95, .5), (1.1, 1.4), (1.0, 2.2), (.62, 2.75), (.46, 3.1), (.44, 3.6), (.58, 3.95), (.72, 4.08), (.70, 4.14), (0, 4.14)], al1),
                     ((-5.3, 27.0), [(0, 0), (.6, 0), (.55, .3), (.9, 1.2), (1.05, 2.0), (.85, 2.8), (.45, 3.2), (.42, 3.6), (.62, 3.8), (.6, 3.86), (0, 3.86)], al2)]:
    box('Arka kaide', (x, y, FLOOR + 4.3), (2.6, 2.6, 8.6), ped, .04)
    lathe('Vazo', prof, (x, y, FLOOR + 8.62), mm)
VZ = [(-16.3, 17.6), (-5.3, 27.0)]
# --- vitrin: ince koyu profiller + arka cam
fr = mat('Vitrin profili', srgb(20, 19, 18), .35, .8)
H = 9.6; W = 3.3
for sx in (-1, 1):
    for sy in (1,):
        box('Profil', (sx * W, sy * W + .05, H / 2), (.07, .07, H), fr, .012)
box('Profil üst', (0, W + .05, H), (2 * W, .07, .07), fr, .012)
# --- ışıklar
def spot(name, loc, tgt, w, kelvin, ang, blend=.5, size=.25):
    l = bpy.data.lights.new(name, 'SPOT'); l.energy = w; l.spot_size = math.radians(ang); l.spot_blend = blend; l.shadow_soft_size = size
    l.use_temperature = True; l.temperature = kelvin
    o = bpy.data.objects.new(name, l); mus.objects.link(o); o.location = loc; o.rotation_euler = (V(tgt) - V(loc)).to_track_quat('-Z', 'Y').to_euler(); return o
def area(name, loc, tgt, w, kelvin, size, size_y=None):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = w; l.size = size; l.use_temperature = True; l.temperature = kelvin
    if size_y: l.shape = 'RECTANGLE'; l.size_y = size_y
    o = bpy.data.objects.new(name, l); mus.objects.link(o); o.location = loc; o.rotation_euler = (V(tgt) - V(loc)).to_track_quat('-Z', 'Y').to_euler(); return o
spot('Ana', (-5.5, -15, 13.5), (0, -.6, 2.5), 9400, 4700, 26, .6, .95)
spot('Dolgu', (14, -13, 8.5), (0, -.4, 2.4), 3300, 4700, 26, .7, .9)
spot('Kenar sol', (-11, 11, 13), (0, 0, 3.0), 3600, 5000, 24, .6, .5)
spot('Kenar sağ', (11, 9, 12), (0, 0, 3.0), 5600, 4800, 24, .6, .5)
area('Alttan yumuşak', (4, -12, 1.0), (0, 0, 2.2), 45, 4700, 5)
for k, ang in enumerate((31, 64, 97, 130, 163)):
    a = math.radians(ang); r = RAD - 6
    spot(f'Niş ışığı{k}', (r * math.cos(a), r * math.sin(a), 19), ((RAD - 1) * math.cos(a), (RAD - 1) * math.sin(a), 4), 2300, 4600, 60, 1, .5)
    a = math.radians(ang - 16.5); r = RAD - 8
    spot(f'Duvar ışığı{k}', (r * math.cos(a), r * math.sin(a), 24), ((RAD - 1) * math.cos(a), (RAD - 1) * math.sin(a), 6), 7000, 4600, 85, 1, .5)
for k, (x, y) in enumerate(VZ):
    spot(f'Vazo ışığı{k}', (x + 2.5, y - 4.5, 9), (x, y, FLOOR + 10), 190, 4300, 30, .8, .3)
w = bpy.data.worlds.new('Dünya'); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (.020, .022, .024, 1); bg.inputs[1].default_value = .5
# --- kamera
def cam(az, dist, hz, tgt, lens, fstop):
    c = bpy.data.cameras.new('Kamera'); o = bpy.data.objects.new('Kamera', c); mus.objects.link(o)
    a = math.radians(az); o.location = (dist * math.sin(a), -dist * math.cos(a), hz)
    o.rotation_euler = (V(tgt) - o.location).to_track_quat('-Z', 'Y').to_euler(); c.lens = lens; c.sensor_width = 36; c.sensor_fit = 'AUTO'
    c.dof.use_dof = fstop > 0; c.dof.aperture_fstop = max(fstop, .01); c.dof.focus_distance = (V((.35, -1.35, 2.6)) - o.location).length; c.clip_end = 500
    return o
cams = {'ana': (31, 16, 2.30, (.10, .12, 2.27), 91, .62), 'sag': (-35, 16, 2.4, (-.1, .12, 2.30), 85, .32), 'on': (0, 11, 2.4, (0, 0, 2.35), 60, 0),
        'yuz': (30, 12, 2.5, (.15, -.8, 2.55), 170, 0), 'prof': (-90, 16, 2.4, (0, 0, 2.4), 85, 0), 'gerdan': (22, 10, 2.2, (.05, -.3, .75), 130, 0), 'tac': (25, 12, 3.2, (.1, 0, 3.9), 130, 0), 'kulak': (70, 12, 2.6, (.4, -.4, 2.6), 200, 0)}
sc.camera = cam(*cams[CAM])
# --- render ayarları
sc.render.engine = 'CYCLES'; sc.cycles.samples = SPP; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = .012
dev = os.environ.get('DEV', 'CPU')
if dev == 'GPU':
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
    for d in pr.devices: d.use = d.type == 'OPTIX'
sc.cycles.device = dev
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'; sc.cycles.denoising_use_gpu = False
sc.cycles.max_bounces = 8; sc.cycles.sample_clamp_indirect = 6
sc.render.resolution_x = RX; sc.render.resolution_y = RY; sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = float(os.environ.get('EXP', '0'))
sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = os.path.abspath(out)
if SAVE: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(SAVE))
bpy.ops.render.render(write_still=True)

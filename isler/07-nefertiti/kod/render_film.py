"""blender -b ../film.blend -P render_film.py -- <klasör> <genişlik> <örnek> <CPU|GPU> <kare listesi: 1-90 ya da 1,30,60 ya da 1-840/30>"""
import bpy, sys, os, time
a = sys.argv[sys.argv.index('--') + 1:]
out, W, SPP, DEV, spec = a[0], int(a[1]), int(a[2]), a[3], a[4]
thr = float(a[5]) if len(a) > 5 else .03
sc = bpy.context.scene
sc.render.resolution_x = W; sc.render.resolution_y = W * 9 // 16; sc.cycles.samples = SPP; sc.cycles.adaptive_threshold = thr
if DEV == 'GPU':
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'OPTIX'; pr.get_devices()
    for d in pr.devices: d.use = d.type == 'OPTIX'
sc.cycles.device = DEV; sc.cycles.denoising_use_gpu = DEV == 'GPU'
if os.environ.get('THR'): sc.render.threads_mode = 'FIXED'; sc.render.threads = int(os.environ['THR'])
F = []
for p in spec.split(','):
    st = 1
    if '/' in p: p, s_ = p.split('/'); st = int(s_)
    if '-' in p:
        x, y = map(int, p.split('-')); F += list(range(x, y + 1, st)) if x <= y else list(range(x, y - 1, -st))
    else: F.append(int(p))
os.makedirs(out, exist_ok=True)
for f in F:
    fp = os.path.abspath(os.path.join(out, f'{f:04d}.png'))
    if os.path.exists(fp) and os.path.getsize(fp) > 1000: continue
    if os.path.exists(os.path.join(out, 'DUR')): break
    try: os.close(os.open(fp + '.kilit', os.O_CREAT | os.O_EXCL))      # iki işçi aynı kareyi almasın
    except FileExistsError: continue
    t0 = time.time()
    try:
        sc.frame_set(f); sc.render.filepath = fp + '.tmp.png'; bpy.ops.render.render(write_still=True)
        os.replace(fp + '.tmp.png', fp); print(f'KARE {f} {time.time()-t0:.1f}s', flush=True)
    finally:
        os.remove(fp + '.kilit')          # yalnız kendi kilidi

"""EXR kare dizisi -> PNG (tek süreç). banyo.py ile aynı matematik, kare başına farklı gren."""
import bpy, sys, os, glob, numpy as np
arg = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:])
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'banyo.py')).read()
files = sorted(glob.glob(os.path.join(arg['dir'], arg.get('pat', 's*.exr')))); files = [f for f in files if '.tmp.' not in f]
pi, pn = (int(v) for v in arg.get('part', '0/1').split('/'))
for i, f in enumerate(files):
    if i % pn != pi: continue
    d = f[:-4] + '.png'
    if os.path.exists(d) and os.path.getmtime(d) > os.path.getmtime(f): continue
    sys.argv = ['b', '--', f'in={f}', f'out={d}', f"ev={arg.get('ev', '-1.8')}", f"gren={arg.get('gren', '.45')}", f"wb={arg.get('wb', '1.03,.992,.965')}"]
    s = src.replace('default_rng(3)', f'default_rng({i * 7 + 3})').replace('default_rng(9)', f'default_rng({i * 7 + 9})').replace("S = w / 1500", "S = w / 2000")
    exec(compile(s, 'banyo.py', 'exec'), {'__name__': 'x'})
    for im in list(bpy.data.images): bpy.data.images.remove(im)
print('BANYO BITTI')

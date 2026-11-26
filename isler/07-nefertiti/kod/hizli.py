"""Pahalı gürültüleri köşe rengine pişirir, hafif malzemeler kurar -> ../nefertiti_hizli.blend"""
import bpy, os, time, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 1
sc.render.bake.target = 'VERTEX_COLORS'
EYE = (-.305, -1.315, 2.69)
def srgb(r, g, b):
    f = lambda c: c / 12.92 if c <= .04045 else ((c + .055) / 1.055)**2.4
    return (f(r / 255), f(g / 255), f(b / 255), 1)
col = bpy.data.collections['Heykel']
ob, oc, ou = [o for n in ('Baş ve gövde', 'Mavi taç', 'Uraeus') for o in col.objects if o.name == n]
def srcn(s): return s.links[0].from_node
def bake(o, sock, name):
    nt = o.data.materials[0].node_tree
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    old = out.inputs[0].links[0].from_socket
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(sock, em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
    ca = o.data.color_attributes.new(name, 'FLOAT_COLOR', 'POINT'); o.data.color_attributes.active_color = ca
    for x in bpy.data.objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    t0 = time.time(); bpy.ops.object.bake(type='EMIT')
    v = np.empty(len(o.data.vertices) * 4, np.float32); o.data.color_attributes[name].data.foreach_get('color', v); v = v.reshape(-1, 4)
    print('BAKE', o.name, name, f'{time.time()-t0:.1f}s', v[:, :3].min(0), v[:, :3].max(0), v[:, :3].mean(0), flush=True)
    nt.links.new(old, out.inputs[0]); nt.nodes.remove(em)
def extra(o):
    """ham taş rengi ve dalga uzaklığı"""
    nt = o.data.materials[0].node_tree; N = nt.nodes; L = nt.links
    def n(k, **kw):
        x = N.new(k)
        for a, v in kw.items(): setattr(x, a, v)
        return x
    tc = n('ShaderNodeTexCoord')
    def noise(s, d, r=.62):
        x = n('ShaderNodeTexNoise'); x.inputs['Scale'].default_value = s; x.inputs['Detail'].default_value = d; x.inputs['Roughness'].default_value = r; L.new(tc.outputs['Object'], x.inputs['Vector']); return x.outputs[0]
    def mr(v, a, c):
        x = n('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP'); L.new(v, x.inputs[0]); x.inputs[1].default_value = a; x.inputs[2].default_value = c; return x.outputs[0]
    def mix(f, a, c):
        x = n('ShaderNodeMix', data_type='RGBA'); L.new(f, x.inputs[0])
        for i, v in ((6, a), (7, c)):
            if hasattr(v, 'is_output'): L.new(v, x.inputs[i])
            else: x.inputs[i].default_value = v
        return x.outputs[2]
    def m(op, a, c):
        x = n('ShaderNodeMath', operation=op)
        for i, v in enumerate((a, c)):
            if isinstance(v, (int, float)): x.inputs[i].default_value = v
            else: L.new(v, x.inputs[i])
        return x.outputs[0]
    n2, n3 = noise(4, 8, .65), noise(60, 4, .55)
    pt = n('ShaderNodeNewGeometry').outputs['Pointiness']
    raw = mix(mr(n2, .34, .68), srgb(172, 156, 130), srgb(206, 192, 166)); raw = mix(mr(n3, .56, .72), raw, srgb(148, 132, 106)); raw = mix(mr(pt, .497, .46), raw, srgb(96, 80, 60))
    dv = n('ShaderNodeVectorMath', operation='DISTANCE'); L.new(tc.outputs['Object'], dv.inputs[0]); dv.inputs[1].default_value = EYE
    amp = m('MULTIPLY', m('SUBTRACT', noise(5.5, 6), .5), m('ADD', .05, m('MULTIPLY', m('MINIMUM', dv.outputs['Value'], 1.5), .42)))
    return raw, m('ADD', dv.outputs['Value'], amp)
def princ(o): return [n for n in o.data.materials[0].node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
# gövde soketleri
b = princ(ob); mS = srcn(b.inputs['Base Color']); mC = srcn(mS.inputs[6]); mF = srcn(mC.inputs[6])
skin0, stn, sta = mF.inputs[6].links[0].from_socket, mS.inputs[7].links[0].from_socket, mS.inputs[0].links[0].from_socket
r5 = srcn(b.inputs['Roughness']); r4 = srcn(r5.inputs[2]); r3 = srcn(r4.inputs[2]); r2 = srcn(r3.inputs[2]); r0 = r2.inputs[2].links[0].from_socket
raw, d0 = extra(ob)
for s, nm in ((skin0, 'bTen'), (stn, 'bTas'), (sta, 'bTasM'), (r0, 'bPuruz'), (raw, 'bHam'), (d0, 'bUzak')): bake(ob, s, nm)
# taç
b = princ(oc); c3 = srcn(b.inputs['Base Color']); c2 = srcn(c3.inputs[6]); c1 = srcn(c2.inputs[6])
lo, hi = c3.inputs[0].links[0].from_socket, c2.inputs[0].links[0].from_socket; capf, capc = c1.inputs[0].links[0].from_socket, c1.inputs[7].links[0].from_socket
raw, d0 = extra(oc)
for s, nm in ((lo, 'bLo'), (hi, 'bHi'), (capc, 'bTepe'), (raw, 'bHam'), (d0, 'bUzak')): bake(oc, s, nm)
b = princ(ou); raw, d0 = extra(ou)
for s, nm in ((b.inputs['Base Color'].links[0].from_socket, 'bRenk'), (raw, 'bHam'), (d0, 'bUzak')): bake(ou, s, nm)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, '..', 'nefertiti_hizli.blend'))
print('PISTI')

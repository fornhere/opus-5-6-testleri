import bpy, numpy as np, math, os, sys
from mathutils import Vector, Matrix, Quaternion
ROOT='esik-film'

def reset(w=1920,h=804,samples=96,scale=100):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene
    s.render.engine='CYCLES'
    p=bpy.context.preferences.addons['cycles'].preferences
    p.compute_device_type='OPTIX'; p.refresh_devices()
    for d in p.devices: d.use=(d.type=='OPTIX')
    c=s.cycles; c.device='GPU'; c.samples=samples; c.use_adaptive_sampling=True; c.adaptive_threshold=0.02
    c.use_denoising=True; c.denoiser='OPENIMAGEDENOISE'; c.denoising_use_gpu=True
    c.denoising_input_passes='RGB_ALBEDO_NORMAL'; c.denoising_prefilter='ACCURATE'
    c.max_bounces=8; c.glossy_bounces=4; c.transmission_bounces=8; c.diffuse_bounces=2; c.transparent_max_bounces=16
    c.caustics_reflective=False; c.caustics_refractive=False; c.sample_clamp_indirect=8; c.sample_clamp_direct=0
    c.blur_glossy=0.3
    r=s.render; r.resolution_x=w; r.resolution_y=h; r.resolution_percentage=scale; r.fps=24
    r.use_persistent_data=True
    r.image_settings.file_format='OPEN_EXR'; r.image_settings.color_depth='16'; r.image_settings.exr_codec='DWAA'
    r.film_transparent=False
    w=bpy.data.worlds.new('W'); s.world=w
    return s

class N:
    """tiny node-tree helper"""
    def __init__(s,nt,clear=True):
        s.nt=nt
        if clear: nt.nodes.clear()
    def n(s,t,**k):
        nd=s.nt.nodes.new(t); ins=k.pop('i',{})
        for a,v in k.items(): setattr(nd,a,v)
        for a,v in ins.items(): s.set(nd,a,v)
        return nd
    def set(s,nd,a,v):
        sock=nd.inputs[a]
        if isinstance(v,bpy.types.NodeSocket): s.nt.links.new(v,sock)
        elif isinstance(v,bpy.types.Node): s.nt.links.new(v.outputs[0],sock)
        else:
            if sock.type=='RGBA' and len(v)==3: v=(*v,1)
            sock.default_value=v
    def m(s,op,a,b=None,c=None,clamp=False):
        nd=s.n('ShaderNodeMath',operation=op,use_clamp=clamp)
        for i,v in enumerate((a,b,c)):
            if v is not None: s.set(nd,i,v)
        return nd.outputs[0]
    def v(s,op,a,b=None,scale=None):
        nd=s.n('ShaderNodeVectorMath',operation=op); s.set(nd,0,a)
        if b is not None: s.set(nd,1,b)
        if scale is not None: s.set(nd,'Scale',scale)
        return nd.outputs['Value'] if op in('DOT_PRODUCT','LENGTH','DISTANCE') else nd.outputs[0]
    def ramp(s,fac,stops,interp='LINEAR'):
        nd=s.n('ShaderNodeValToRGB'); s.set(nd,0,fac); cr=nd.color_ramp; cr.interpolation=interp
        while len(cr.elements)<len(stops): cr.elements.new(0.5)
        for e,(p,c) in zip(cr.elements,stops):
            e.position=p; e.color=(*c,1) if hasattr(c,'__len__') else (c,c,c,1)
        return nd.outputs[0]
    def mix(s,f,a,b,bt='MIX'):
        nd=s.n('ShaderNodeMix',data_type='RGBA',blend_type=bt)
        s.set(nd,0,f); s.set(nd,6,a); s.set(nd,7,b); return nd.outputs[2]
    def noise(s,vec,scale,detail=4,rough=.5,dim='3D',w=0,dist=0):
        nd=s.n('ShaderNodeTexNoise',noise_dimensions=dim); 
        if vec is not None: s.set(nd,'Vector',vec)
        for a,v in(('Scale',scale),('Detail',detail),('Roughness',rough),('Distortion',dist)): s.set(nd,a,v)
        if dim=='4D': s.set(nd,'W',w)
        return nd.outputs[0]
    def sep(s,v):
        nd=s.n('ShaderNodeSeparateXYZ'); s.set(nd,0,v); return nd.outputs
    def comb(s,x,y,z):
        nd=s.n('ShaderNodeCombineXYZ'); 
        for i,q in enumerate((x,y,z)): s.set(nd,i,q)
        return nd.outputs[0]
    def mr(s,v,a,b,c=0,d=1,t='LINEAR'):
        nd=s.n('ShaderNodeMapRange',interpolation_type=t); 
        for i,q in enumerate((v,a,b,c,d)): s.set(nd,i,q)
        return nd.outputs[0]
    def val(s,x,label=''):
        nd=s.n('ShaderNodeValue'); nd.outputs[0].default_value=x; nd.label=label; return nd.outputs[0]

FOG=dict(dens=1/2200.,h=260.,sun=Vector((0,1,.07)).normalized(),base=(.10,.15,.24),warm=(1.5,.62,.24),gain=1.0)
def fogcolor(N_,dirv):
    """colour of haze looking along dirv (unit, pointing away from eye)"""
    d=N_.v('DOT_PRODUCT',dirv,tuple(FOG['sun']))
    d=N_.m('MAXIMUM',d,0.0)
    a=N_.m('POWER',d,4.0); b=N_.m('POWER',d,40.0); c=N_.m('POWER',d,500.0)
    f=N_.m('ADD',N_.m('MULTIPLY',a,.28),N_.m('ADD',N_.m('MULTIPLY',b,.45),N_.m('MULTIPLY',c,1.3)))
    g=N_.v('ADD',tuple(x*FOG['gain'] for x in FOG['base']),N_.v('SCALE',tuple(x*FOG['gain'] for x in FOG['warm']),scale=f))
    return g
def fogged(mat_N,shader,out,dens=None):
    """mix a surface shader with analytic aerial perspective; works in reflections too"""
    n=mat_N; lp=n.n('ShaderNodeLightPath'); ge=n.n('ShaderNodeNewGeometry')
    z=n.sep(ge.outputs['Position'])[2]
    hz=n.m('EXPONENT',n.m('MULTIPLY',n.m('MAXIMUM',z,0.0),-1/FOG['h']))
    hz=n.m('ADD',n.m('MULTIPLY',hz,.75),.25)
    f=n.m('SUBTRACT',1.0,n.m('EXPONENT',n.m('MULTIPLY',n.m('MULTIPLY',lp.outputs['Ray Length'],-(dens or FOG['dens'])),hz)))
    f=n.m('MULTIPLY',f,n.m('MAXIMUM',lp.outputs['Is Camera Ray'],lp.outputs['Is Glossy Ray']))
    col=fogcolor(n,n.v('SCALE',ge.outputs['Incoming'],scale=-1.0))
    em=n.n('ShaderNodeEmission',i={'Color':col,'Strength':n.val(1.0,'fogg')})
    mx=n.n('ShaderNodeMixShader',i={0:f,1:shader,2:em})
    n.set(out,'Surface',mx)

def mat(name):
    m=bpy.data.materials.new(name); m.use_nodes=True; n=N(m.node_tree)
    o=n.n('ShaderNodeOutputMaterial'); return m,n,o
def pbsdf(n,**i):
    return n.n('ShaderNodeBsdfPrincipled',i={k.replace('_',' '):v for k,v in i.items()})

def meshobj(name,v,f,mats=(),smooth=False,col=None):
    me=bpy.data.meshes.new(name); me.from_pydata([tuple(map(float,x)) for x in v],[],[tuple(map(int,x)) for x in f]); me.update()
    if smooth: me.shade_smooth()
    o=bpy.data.objects.new(name,me)
    for m in mats: me.materials.append(m)
    (col or bpy.context.scene.collection).objects.link(o); return o
def grid_faces(nu,nv,cu=False,cv=False,off=0):
    f=[]
    for i in range(nu if cu else nu-1):
        for j in range(nv if cv else nv-1):
            a=i*nv+j;b=((i+1)%nu)*nv+j;c=((i+1)%nu)*nv+(j+1)%nv;d=i*nv+(j+1)%nv
            f.append((a+off,b+off,c+off,d+off))
    return f
def prim(kind,**k):
    getattr(bpy.ops.mesh,'primitive_%s_add'%kind)(**k); return bpy.context.object
def hidden(o):
    o.hide_render=True; o.hide_viewport=True; return o

class Swarm:
    """N instances of src driven by numpy arrays pos(N,3) quat(N,4 wxyz) scale(N,3) + optional float attr 'glow'"""
    def __init__(s,name,src,N_,realize=False):
        me=bpy.data.meshes.new(name); me.from_pydata(np.zeros((N_,3)).tolist(),[],[]); s.me=me; s.n=N_
        s.o=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(s.o)
        for a,t in(('rot','QUATERNION'),('scl','FLOAT_VECTOR'),('glow','FLOAT'),('rnd','FLOAT')): me.attributes.new(a,t,'POINT')
        me.attributes['rnd'].data.foreach_set('value',np.random.default_rng(1).random(N_).astype('f'))
        q=np.zeros((N_,4),'f');q[:,0]=1
        s.put(quat=q,scale=np.ones((N_,3),'f'),glow=np.zeros(N_,'f'))
        g=bpy.data.node_groups.new(name+'G','GeometryNodeTree')
        g.interface.new_socket('Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
        g.interface.new_socket('Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
        n=N(g); gi=n.n('NodeGroupInput'); go=n.n('NodeGroupOutput')
        oi=n.n('GeometryNodeObjectInfo',transform_space='ORIGINAL'); oi.inputs['Object'].default_value=src; oi.inputs['As Instance'].default_value=True
        ra=n.n('GeometryNodeInputNamedAttribute',data_type='QUATERNION'); ra.inputs[0].default_value='rot'
        sa=n.n('GeometryNodeInputNamedAttribute',data_type='FLOAT_VECTOR'); sa.inputs[0].default_value='scl'
        mp=n.n('GeometryNodeMeshToPoints'); g.links.new(gi.outputs[0],mp.inputs['Mesh'])
        ip=n.n('GeometryNodeInstanceOnPoints'); L=g.links.new
        L(mp.outputs[0],ip.inputs['Points']); L(oi.outputs['Geometry'],ip.inputs['Instance'])
        L([o for o in ra.outputs if o.name=='Attribute' and o.enabled][0],ip.inputs['Rotation']); L([o for o in sa.outputs if o.name=='Attribute' and o.enabled][0],ip.inputs['Scale'])
        L(ip.outputs[0],go.inputs[0])
        md=s.o.modifiers.new('gn','NODES'); md.node_group=g
    def put(s,pos=None,quat=None,scale=None,glow=None):
        if pos is not None: s.me.vertices.foreach_set('co',np.ascontiguousarray(pos,'f').ravel())
        for k,v,p in(('rot',quat,'value'),('scl',scale,'vector'),('glow',glow,'value')):
            if v is not None:s.me.attributes[k].data.foreach_set(p,np.ascontiguousarray(v,'f').ravel())
        s.me.update_tag(); s.me.update()

def qaxis(ax,ang):
    ax=np.asarray(ax,float); ang=np.asarray(ang,float)
    ax=ax/np.linalg.norm(ax,axis=-1,keepdims=True)
    return np.concatenate([np.cos(ang/2)[...,None],ax*np.sin(ang/2)[...,None]],-1)
def qmul(a,b):
    w,x,y,z=np.moveaxis(a,-1,0);W,X,Y,Z=np.moveaxis(b,-1,0)
    return np.stack([w*W-x*X-y*Y-z*Z,w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W],-1)
def ss(a,b,x):
    t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)
def sss(a,b,x):
    t=np.clip((x-a)/(b-a),0,1); return t**3*(t*(t*6-15)+10)

def camera(lens=35,fstop=None,focus=10):
    c=bpy.data.cameras.new('C'); o=bpy.data.objects.new('C',c); s=bpy.context.scene
    s.collection.objects.link(o); s.camera=o; c.lens=lens; c.sensor_width=36; c.clip_end=1e6; c.clip_start=.01
    if fstop: c.dof.use_dof=True; c.dof.aperture_fstop=fstop; c.dof.focus_distance=focus; c.dof.aperture_blades=0
    return o
def aim(o,pos,tgt,roll=0):
    pos=Vector(pos);q=(Vector(tgt)-pos).to_track_quat('-Z','Y')
    o.location=pos;o.rotation_mode='QUATERNION';o.rotation_quaternion=q@Quaternion((0,0,1),roll)

def sky(sun_el=3.2,strength=1.0,clouds=True,t=0.0,stars=0.0):
    s=bpy.context.scene; w=s.world; w.use_nodes=True; n=N(w.node_tree); o=n.n('ShaderNodeOutputWorld')
    tc=n.n('ShaderNodeTexCoord'); D=n.v('NORMALIZE',tc.outputs['Generated'])
    st=n.n('ShaderNodeTexSky',sky_type='MULTIPLE_SCATTERING',sun_disc=False,sun_elevation=math.radians(sun_el),sun_rotation=math.radians(0))
    for a,v in(('air_density',1.3),('aerosol_density',1.2),('dust_density',1.2),('ozone_density',3.0)):
        if hasattr(st,a): setattr(st,a,v)
    x,y,z=n.sep(D)[:3]
    skyc=n.v('SCALE',st.outputs[0],scale=strength*.22)
    # art-directed gradient on top
    up=n.m('MAXIMUM',z,0.0)
    grad=n.ramp(up,[(0,(.42,.26,.20)),(.08,(.28,.22,.26)),(.22,(.10,.14,.25)),(.6,(.02,.04,.10)),(1,(.008,.016,.045))])
    col=n.v('ADD',n.v('SCALE',skyc,scale=.35),n.v('SCALE',grad,scale=.75))
    fc=fogcolor(n,D)
    sunf=n.m('EXPONENT',n.m('MULTIPLY',up,-9.0))
    if clouds:
        zz=n.m('MAXIMUM',n.m('ADD',z,.045),.02)
        P=n.comb(n.m('DIVIDE',x,zz),n.m('DIVIDE',y,zz),n.val(t,'cloudt'))
        Pst=n.v('MULTIPLY',P,(.42,.16,1))
        w1=n.noise(Pst,.9,3,.5); 
        Pw=n.v('ADD',Pst,n.v('SCALE',n.comb(w1,w1,0.0),scale=.9))
        c1=n.noise(Pw,1.25,9,.6); 
        c2=n.noise(n.v('ADD',Pw,(0,.10,0)),1.25,9,.6)
        dens=n.mr(c1,.43,.70,0,1,'SMOOTHSTEP')
        edge=n.m('MAXIMUM',n.m('MULTIPLY',n.m('SUBTRACT',c1,c2),5.0),-.25)
        fade=n.mr(z,.0,.12,0,1,'SMOOTHSTEP')
        dot=n.m('MAXIMUM',n.v('DOT_PRODUCT',D,tuple(FOG['sun'])),0.0)
        lit=n.m('ADD',n.m('MULTIPLY',n.m('POWER',dot,4.0),2.2),.20)
        warm=n.ramp(up,[(0,(1.0,.36,.12)),(.25,(1.0,.40,.22)),(.55,(.55,.30,.36)),(1,(.18,.18,.32))])
        lc=n.v('SCALE',warm,scale=n.m('MULTIPLY',lit,n.m('ADD',.55,edge)))
        lc=n.v('ADD',lc,(.015,.02,.04))
        col=n.mix(n.m('MULTIPLY',n.m('MULTIPLY',dens,fade),.85),col,lc)
    hz=n.m('EXPONENT',n.m('MULTIPLY',up,-14.0))
    col=n.mix(hz,col,fc)
    glow=n.m('POWER',n.m('MAXIMUM',n.v('DOT_PRODUCT',D,tuple(FOG['sun'])),0.0),90.0)
    col=n.v('ADD',col,n.v('SCALE',(1.0,.45,.16),scale=n.m('MULTIPLY',glow,.9)))
    disc=n.mr(n.v('DOT_PRODUCT',D,tuple(FOG['sun'])),math.cos(.011),math.cos(.0095),0,1)
    lp=n.n('ShaderNodeLightPath')
    col=n.v('ADD',col,n.v('SCALE',(26.0,12.0,4.6),scale=n.m('MULTIPLY',disc,lp.outputs['Is Camera Ray'])))
    if stars>0:
        vo=n.n('ShaderNodeTexVoronoi',feature='F1'); n.set(vo,'Vector',D); n.set(vo,'Scale',160.0)
        sv=n.mr(vo.outputs['Distance'],.06,.0,0,1); col=n.v('ADD',col,n.v('SCALE',(1.,1.,1.2),scale=n.m('MULTIPLY',n.m('MULTIPLY',sv,n.m('POWER',up,.7)),stars)))
    if True:
        vo=n.n('ShaderNodeTexVoronoi',feature='F1'); n.set(vo,'Vector',D); n.set(vo,'Scale',130.0); hue=n.sep(vo.outputs['Color'])[0]
        sv=n.m('MULTIPLY',n.mr(vo.outputs['Distance'],.085,.0,0,1),n.m('POWER',hue,4.0)); sv=n.m('MULTIPLY',n.m('MULTIPLY',sv,n.mr(z,.02,.25,0,1)),n.val(0,'stars'))
    bg=n.n('ShaderNodeBackground',i={'Color':n.v('ADD',n.v('SCALE',col,scale=n.val(1.0,'skyg')),n.v('SCALE',(.9,1.,1.25),scale=sv)),'Strength':1.0}); n.set(o,'Surface',bg)
    w.cycles.sampling_method='MANUAL'; w.cycles.sample_map_resolution=1024
    sl=bpy.data.lights.new('sun','SUN'); sl.energy=3.2; sl.color=(1,.52,.24); sl.angle=.02
    so=bpy.data.objects.new('sun',sl); s.collection.objects.link(so)
    so.rotation_mode='QUATERNION'; so.rotation_quaternion=FOG['sun'].to_track_quat('Z','Y')
    return n,so

def water_mat(deep=(.004,.016,.022),rough=.04,bump=True):
    m,n,o=mat('water')
    ge=n.n('ShaderNodeNewGeometry'); P=ge.outputs['Position']
    z=n.sep(P)[2]; cam=n.n('ShaderNodeCameraData')
    crest=n.mr(z,.0,1.3,0,1,'SMOOTHSTEP')
    col=n.mix(crest,deep,(.015,.06,.065))
    dist=cam.outputs['View Distance']
    rg=n.mr(dist,20,2200,rough,.20)
    b=pbsdf(n,Base_Color=col,Roughness=rg,IOR=1.333,Specular_IOR_Level=.5)
    if bump:
        t=n.val(0,'wt')
        h1=n.noise(n.v('MULTIPLY',P,(1,1.5,1)),.35,5,.6,'4D',n.m('MULTIPLY',t,.5))
        h2=n.noise(P,2.6,4,.55,'4D',n.m('MULTIPLY',t,1.1))
        h3=n.noise(n.v('MULTIPLY',P,(1,2.5,1)),.028,4,.6,'4D',n.m('MULTIPLY',t,.15))
        nd=n.n('ShaderNodeBump',i={'Height':n.m('ADD',n.m('ADD',n.m('MULTIPLY',h1,.34),n.m('MULTIPLY',h2,.045)),n.m('MULTIPLY',h3,2.2)),'Strength':n.mr(dist,5,900,.55,.35),'Distance':1.0})
        n.set(b,'Normal',nd)
    fogged(n,b,o); return m

def ocean(m,size=160,rep=9,res=14,wind=6,scale=.6,chop=1.0,t=0,off=(0,0),align=.2):
    """ONE evaluated ocean tile, placed rep*rep times as collection instances (shared geometry) + far plane"""
    sc=bpy.context.scene; col=bpy.data.collections.new('octile')   # not linked: only instanced
    me=bpy.data.meshes.new('oc'); o=bpy.data.objects.new('oc',me); col.objects.link(o); me.materials.append(m)
    md=o.modifiers.new('o','OCEAN'); md.geometry_mode='GENERATE'; md.spatial_size=size; md.repeat_x=md.repeat_y=1
    md.resolution=res; md.viewport_resolution=res; md.wave_scale=scale; md.choppiness=chop; md.wind_velocity=wind; md.wave_alignment=align; md.random_seed=4
    md.wave_scale_min=.02; md.damping=.3; md.time=t
    for i in range(rep):
        for j in range(rep):
            e=bpy.data.objects.new('oci',None); e.instance_type='COLLECTION'; e.instance_collection=col; sc.collection.objects.link(e)
            e.location=(off[0]+(i-rep/2)*size,off[1]+(j-rep/2)*size,0)
    R=60000; hx=size*rep/2-2
    X=[-R,off[0]-hx,off[0]+hx,R];Y=[-R,off[1]-hx,off[1]+hx,R]
    v=[(x,y,-.05) for x in X for y in Y]; f=[g for k,g in enumerate(grid_faces(4,4)) if k!=4]
    meshobj('far',v,f,[m]); return o,md

def render(path):
    s=bpy.context.scene; s.render.filepath=path; bpy.ops.render.render(write_still=True)
def args():
    a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    return dict(x.split('=') for x in a)

def setval(label,v):
    for nt in [m.node_tree for m in bpy.data.materials if m.use_nodes]+[bpy.context.scene.world.node_tree]:
        for x in nt.nodes:
            if x.type=='VALUE' and x.label==label: x.outputs[0].default_value=float(v)

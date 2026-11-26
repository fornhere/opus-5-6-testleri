import sys; sys.path.insert(0,'esik-film/src')
from sea import *
import time
A=args(); SH=A['shot']; spp=int(A.get('spp',128)); scale=int(A.get('scale',100)); OUT=A.get('out',ROOT+'/frames/'+SH); os.makedirs(OUT,exist_ok=True)
n_=dict(s7=96,s8=230)[SH]; FR=[int(x) for x in A['f'].split(',')] if 'f' in A else range(int(A.get('a',0)),int(A.get('b',n_)))
s=reset(samples=spp,scale=scale); FOG['dens']=1/2600.; sk,sun=sky()
def galcol(n,P,tt,stars=1.0):
    x,y,z=n.sep(P)[:3]; r=n.v('LENGTH',n.comb(x,y,0.0)); ang=n.m('ARCTAN2',y,x)
    sw=n.m('ADD',ang,n.m('ADD',n.m('MULTIPLY',n.m('LOGARITHM',n.m('MAXIMUM',n.m('ADD',r,.04),.01),2.718),-2.5),n.m('MULTIPLY',tt,.06)))
    q=n.comb(n.m('MULTIPLY',n.m('COSINE',sw),r),n.m('MULTIPLY',n.m('SINE',sw),r),n.m('MULTIPLY',tt,.012))
    w=n.noise(q,3.,3,.5); q=n.v('ADD',q,n.v('SCALE',n.comb(w,n.noise(n.v('ADD',q,(5,2,1)),3.,3,.5),0.0),scale=.26))
    n1=n.noise(q,5.0,10,.62); n2=n.noise(n.v('ADD',q,(3,1,0)),13.,9,.64); n3=n.noise(q,3.0,3,.5)
    a=n.m('POWER',n.m('ADD',n.m('MULTIPLY',n.m('COSINE',n.m('MULTIPLY',n.m('ADD',sw,n.m('MULTIPLY',n.m('SUBTRACT',n3,.5),1.4)),2.0)),.5),.5),1.8)
    fal=n.m('MULTIPLY',n.m('EXPONENT',n.m('MULTIPLY',r,-2.2)),n.mr(r,1.15,.75,0,1,'SMOOTHSTEP'))
    d=n.m('MULTIPLY',n.m('MULTIPLY',n.m('ADD',n.m('MULTIPLY',a,1.1),.07),n.mr(n1,.38,.72,.02,1.5,'SMOOTHSTEP')),n.m('MULTIPLY',fal,n.mr(n2,.40,.66,1.25,.15,'SMOOTHSTEP')))
    col=n.ramp(r,[(0,(1.0,.62,.28)),(.07,(1.0,.38,.16)),(.17,(.95,.22,.40)),(.32,(.48,.22,1.0)),(.58,(.10,.34,1.0)),(1,(.05,.55,.85))])
    em=n.v('SCALE',col,scale=n.m('MULTIPLY',d,2.6))
    em=n.v('ADD',em,n.v('SCALE',(1,.14,.32),scale=n.m('MULTIPLY',n.m('MULTIPLY',n.mr(n2,.62,.75,0,1,'SMOOTHSTEP'),a),n.m('MULTIPLY',fal,n.m('MULTIPLY',n.mr(r,.12,.3,0,1),6.0)))))
    em=n.v('ADD',em,n.v('SCALE',(1.,.74,.45),scale=n.m('ADD',n.m('MULTIPLY',n.m('EXPONENT',n.m('MULTIPLY',r,-15.)),n.m('MULTIPLY',n1,.22)),n.m('MULTIPLY',n.m('EXPONENT',n.m('MULTIPLY',r,-60.)),2.5))))
    for sc_,br in((70.,10.),(170.,5.)):
        vo=n.n('ShaderNodeTexVoronoi',feature='F1'); n.set(vo,'Vector',n.comb(x,y,0.0)); n.set(vo,'Scale',sc_); hue=n.sep(vo.outputs['Color'])[0]
        em=n.v('ADD',em,n.v('SCALE',n.ramp(hue,[(0,(1,.6,.4)),(.5,(1,1,1)),(1,(.5,.7,1))]),scale=n.m('MULTIPLY',n.m('MULTIPLY',n.mr(vo.outputs['Distance'],.13,.0,0,1),n.m('POWER',hue,4.0)),br*stars)))
    return em,r
B,pl,fm=boat(70); cam=camera(50)
W=water_mat()
def bob(t): B.location=(0,0,.10+.03*math.sin(t*1.1)); B.rotation_euler=(.012*math.sin(t+1),.018*math.sin(t*.83),0)
if SH=='s7':
    oc,md=ocean(W,rep=41,off=(0,1600),scale=.34,t=90); R=Ring(); R.coreval.node.outputs[0].default_value=7; R.update(0,lambda th,rn:.3*rn)
    r0=.0135; C=np.array([.17,.30,2.02+.10-.155-r0*1.32])
    gm,n,o=mat('dropg'); n.set(o,'Surface',pbsdf(n,Base_Color=(1,1,1),Roughness=0.0,IOR=1.333,Transmission_Weight=1.0))
    nu,nv=160,120
    def drop(neck,st,free):
        v=[]
        for i in range(nu):
            a=2*math.pi*i/nu
            for j in range(nv):
                th=math.pi*j/(nv-1); zz=math.cos(th); rr=math.sin(th)
                if zz>0: rr*=1-(.22*neck)*zz**2; zz2=zz*(1+.32*neck+st*zz); rr+= neck*.34*max(0,zz-.80)/.2*(1-.75*st*2)
                else: zz2=zz*(1-.04*neck+free*.06); 
                v.append((rr*math.cos(a)*r0,rr*math.sin(a)*r0,zz2*r0))
        return v
    v=drop(1,0,0); D=meshobj('D',v,grid_faces(nu,nv,True),[gm],True); D.location=C
    pm,n,o=mat('gal'); tc=n.n('ShaderNodeTexCoord'); P=n.v('SCALE',tc.outputs['Object'],scale=1/(r0*.86)); tt=n.val(0,'gt'); em,r=galcol(n,P,tt,.6)
    lum=n.v('DOT_PRODUCT',em,(.5,.6,.5)); e=n.n('ShaderNodeEmission',i={'Color':n.v('SCALE',em,scale=n.mr(r,.97,.6,0,1,'SMOOTHSTEP')),'Strength':n.val(1.5,'gs')}); tr=n.n('ShaderNodeBsdfTransparent',i={'Color':(.55,.55,.6)})
    ad=n.n('ShaderNodeAddShader',i={0:e,1:tr}); n.set(o,'Surface',ad)
    prim('circle',vertices=96,radius=r0*.86,fill_type='NGON'); G=bpy.context.object; G.data.materials.append(pm); G.visible_shadow=False
    gl=bpy.data.lights.new('g','POINT'); gl.color=(.5,.5,1); gl.energy=0; gl.shadow_soft_size=.01; go=bpy.data.objects.new('g',gl); s.collection.objects.link(go)
    s.cycles.max_bounces=14; s.cycles.transmission_bounces=12; s.cycles.sample_clamp_indirect=20
def step7(f):
    u=f/(n_-1); t=f/24; bob(0); B.location=(0,0,.10); B.rotation_euler=(0,0,0); rel=76
    e=sss(-.12,.80,u); dist=.036+.27*e**1.35
    az=-.22*(1-e)+.10; cp=C+np.array([math.sin(az)*dist,-math.cos(az)*dist,-.004-.016*e])
    swl=.0006*math.sin(t*2.2); st=.35*ss(48,rel,f)**2; pos=C.copy(); pos[0]+=swl; free=0
    if f>=rel: tf=(f-rel)/24*.42; pos[2]-=.5*9.81*tf*tf; free=1
    neck=1 if f<rel else math.exp(-(f-rel)/5); wob=.10*math.sin((f-rel)*.9)*math.exp(-(f-rel)/12) if free else 0
    vv=np.array(drop(neck,st*(1-free),free)); 
    if free: vv=vv*np.array([1-wob,1-wob,1+2*wob])
    D.data.vertices.foreach_set('co',vv.astype('f').ravel()); D.data.update(); D.location=pos
    G.location=pos; q=(Vector(cp)-Vector(pos)).to_track_quat('Z','Y'); G.rotation_mode='QUATERNION'; G.rotation_quaternion=q@Quaternion((1,0,0),-.30)
    go.location=pos-np.array([0,.0,0]); 
    ty=C[2]-.008*e
    aim(cam,cp,(C[0],C[1],ty)); cam.data.lens=62; cam.data.dof.use_dof=True; cam.data.dof.aperture_fstop=4.0+10*(1-e); cam.data.dof.focus_distance=float(np.linalg.norm(cp-C))
    setval('gt',20+t); setval('wt',90+t); pl.energy=40*(1+.08*math.sin(t*13))
if SH=='s8':
    IM=np.array([2.1,1.0,0.]); RM=26.
    rr_=np.concatenate([[0.],np.geomspace(.006,.5,150),np.linspace(.515,RM,1150)]); nr=len(rr_); na=360
    ks=np.geomspace(.25,60,420); om=np.sqrt(9.81*ks+7.3e-5*ks**3); th=(np.arange(96)+.5)/96*math.pi
    J=np.stack([np.cos(np.outer(rr_,ks)*math.sin(tt_)).astype('f') for tt_ in th]).mean(0)
    sg=.10; spec=ks*np.exp(-(ks*sg)**2/4)*sg*sg/2*np.gradient(ks)
    ca,sa=np.cos(np.arange(na)/na*2*math.pi),np.sin(np.arange(na)/na*2*math.pi)
    X=np.outer(rr_,ca)+IM[0];Y=np.outer(rr_,sa)+IM[1]; V=np.stack([X,Y,0*X],-1).reshape(-1,3)
    Wm=water_mat(rough=.02); pat=meshobj('pat',V,grid_faces(nr,na,False,True),[Wm],True)
    a_=np.linspace(0,2*math.pi,na,endpoint=False); v=[(IM[0]+q*math.cos(x),IM[1]+q*math.sin(x),0) for q in(RM,200,4000,60000) for x in a_]; far=meshobj('farp',v,grid_faces(4,na,False,True),[Wm])
    # galaxy emission in water
    nt=Wm.node_tree; n=N(nt,False); out=[x for x in nt.nodes if x.type=='OUTPUT_MATERIAL'][0]; old=out.inputs[0].links[0].from_socket
    ge=n.n('ShaderNodeNewGeometry'); P=n.v('SUBTRACT',ge.outputs['Position'],(0.0,0.0,0)); nrm=ge.outputs['Normal']
    Pd=n.v('ADD',n.v('SCALE',P,scale=1/21.),n.v('MULTIPLY',nrm,(.16,.16,0)))
    tt=n.val(0,'gt'); em,r=galcol(n,Pd,tt,1.0); front=n.val(0,'front'); gs=n.val(0,'gs')
    d=n.v('LENGTH',n.v('SUBTRACT',ge.outputs['Position'],tuple(IM))); nzz=n.noise(ge.outputs['Position'],.5,4,.6)
    d2=n.m('ADD',d,n.m('MULTIPLY',n.m('SUBTRACT',nzz,.5),n.m('MINIMUM',n.m('MULTIPLY',d,.5),3.0)))
    mk=n.mr(d2,front,n.m('SUBTRACT',front,n.m('ADD',n.m('MULTIPLY',front,.35),.05)),0,1,'SMOOTHSTEP')
    edge=n.m('EXPONENT',n.m('MULTIPLY',n.m('ABSOLUTE',n.m('DIVIDE',n.m('SUBTRACT',d2,n.m('MULTIPLY',front,.92)),n.m('ADD',n.m('MULTIPLY',front,.07),.03))),-1.0))
    col=n.v('ADD',n.v('SCALE',em,scale=mk),n.v('SCALE',(.25,.5,1.0),scale=n.m('MULTIPLY',edge,n.val(.6,'edge'))))
    e=n.n('ShaderNodeEmission',i={'Color':col,'Strength':gs}); ad=n.n('ShaderNodeAddShader',i={0:old,1:e}); nt.links.new(ad.outputs[0],out.inputs[0])
    gm,n,o=mat('dropg'); n.set(o,'Surface',pbsdf(n,Base_Color=(1,1,1),Roughness=0.0,IOR=1.333,Transmission_Weight=1.0,Emission_Color=(.5,.55,1),Emission_Strength=.12))
    prim('uv_sphere',segments=48,ring_count=32,radius=.03); D=bpy.context.object; D.data.materials.append(gm); D.data.shade_smooth()
    # ejecta
    rg=np.random.default_rng(3); NE=60; ev=np.stack([rg.normal(0,1,NE),rg.normal(0,1,NE)],-1); ev/=np.linalg.norm(ev,axis=1)[:,None]; es=rg.uniform(.35,1.15,NE); ez=rg.uniform(.7,2.0,NE); er=np.exp(rg.normal(math.log(.0042),.45,NE)).clip(.0015,.010)
    prim('ico_sphere',subdivisions=3,radius=1); src=bpy.context.object; src.data.materials.append(gm); src.data.shade_smooth(); hidden(src); EJ=Swarm('ej',src,NE)
    gl=bpy.data.lights.new('g','POINT'); gl.color=(.5,.5,1); gl.shadow_soft_size=.5; go=bpy.data.objects.new('g',gl); s.collection.objects.link(go); go.location=(IM[0],IM[1],-.3); gl.energy=0
    fa=bpy.data.lights.new('fa','AREA'); fa.size=5; fa.color=(.62,.55,1.0); fao=bpy.data.objects.new('fa',fa); s.collection.objects.link(fao); fao.location=(1.5,-1.5,7); fao.rotation_euler=(-.2,.2,0); fao.visible_camera=False; fao.visible_glossy=False
    R=Ring(); R.coreval.node.outputs[0].default_value=6; R.update(0,lambda th,rn:.25*rn)
def step8(f):
    u=f/(n_-1); t=f/24; HIT=20; bob(t); tl=(f-HIT)/24; slow=.42; tm=max(0,tl)*(slow+.35*ss(1.5,5,tl)); pl.energy=60*(1+.08*math.sin(t*13))
    if tl>=0:
        amp=ss(0,.10,tm); h=J@(spec*np.cos(om*tm)*-.34*np.exp(-ks*ks*.00018*tm))
        h=np.where(h>0,.26*np.tanh(h/.26),.16*np.tanh(h/.16))*1.0
    else: h=0*rr_
    z=np.repeat((h*ss(RM,RM-5,rr_))[:,None],na,1); V[:,2]=z.ravel(); pat.data.vertices.foreach_set('co',V.astype('f').ravel()); pat.data.update()
    fz=.03+ (-tl)*1.9 if tl<0 else -1; D.location=(IM[0],IM[1],fz); D.hide_render=bool(tl>=0)
    te=max(0,tl)*slow*1.25; p=np.stack([IM[0]+ev[:,0]*es*te*.8,IM[1]+ev[:,1]*es*te*.8,.02+ez*te-4.9*te*te],-1); EJ.put(pos=p,scale=np.repeat((er*(tl>0)*(p[:,2]>0))[:,None],3,1))
    fr=0 if tl<0 else .05+2.2*tl+3.2*max(0,tl-1.0)**2; setval('front',fr+.0001); setval('edge',.9*math.exp(-tl*.35) if tl>=0 else 0); setval('gs',0 if tl<0 else 1.15*ss(0,.5,tl)); setval('gt',30+t*2.0)
    dk=ss(.3,4.2,tl); setval('skyg',1-.93*dk); setval('fogg',1-.95*dk); setval('stars',6*dk); sun.data.energy=3.2*(1-.97*dk); gl.energy=0 if tl<0 else 9*math.exp(-tl*1.6); setval('wt',t); pl.energy*=1+3.2*dk; fa.energy=260*dk
    e=sss(.20,1.02,u)
    az=-math.pi/2-.35+.75*e; 
    tg=Vector((IM[0]*(1-e),IM[1]*(1-e)+.2*e,.12*(1-e))); el=.20+1.28*e**.85; dist=2.1+24.*e**1.5
    cp=tg+Vector((math.cos(az)*math.cos(el)*dist,math.sin(az)*math.cos(el)*dist,math.sin(el)*dist)); aim(cam,cp,tg); cam.data.lens=30
    cam.data.dof.use_dof=u<.45; cam.data.dof.aperture_fstop=2.8; cam.data.dof.focus_distance=dist
for f in FR:
    p='%s/%04d.exr'%(OUT,f)
    if os.path.exists(p) and os.path.getsize(p)>20000 and 'force' not in A: continue
    (step7 if SH=='s7' else step8)(f); s.cycles.seed=f; t0=time.time(); render(p); print('FRAME',SH,f,'%.1fs'%(time.time()-t0),flush=True)

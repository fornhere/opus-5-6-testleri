import sys; sys.path.insert(0,'esik-film/src')
from sea import *
import lib, time
A=args(); SH=A['shot']; spp=int(A.get('spp',96)); scale=int(A.get('scale',100)); OUT=A.get('out',ROOT+'/frames/'+SH)
HIDE_RING='noring' in A
LEN=dict(s1=132,s2=144,s3=120,s4=132,s5=156); n_=LEN[SH]
if 'f' in A: FR=[int(x) for x in A['f'].split(',')]
else: FR=list(range(int(A.get('a',0)),int(A.get('b',n_))))
os.makedirs(OUT,exist_ok=True)
s=reset(samples=spp,scale=scale)
FOG['dens']=dict(s1=1/1500.,s2=1/2600.,s3=1/4500.,s4=1/2600.,s5=1/3200.)[SH]
if SH=='s5': FOG['gain']=.8
sk,sun=sky(clouds=True); W=water_mat(); oc,md=ocean(W,rep=41,off=(0,1600),scale=.34 if SH in('s1','s4') else .42)
R=Ring(); B,pl,fm=boat(); c=camera(30)
wt=[x for x in W.node_tree.nodes if x.type=='VALUE'][0]
ct=[x for x in sk.nt.nodes if x.type=='VALUE' and x.label=='cloudt'][0]
if HIDE_RING:
    for q in (R.sw.o,R.fin.o,R.core,*R.halo): q.hide_render=True
core=R.coreval.node.outputs[0]
rg=np.random.default_rng(11)
def glassdrop(name='drop'):
    m,n,o=mat(name); b=pbsdf(n,Base_Color=(.95,.98,1.0),Roughness=.0,IOR=1.333,Transmission_Weight=1.0); 
    lp=n.n('ShaderNodeLightPath'); fogged(n,b,o,FOG['dens']*.6); return m
def icos(m,sub,wob=0):
    prim('ico_sphere',subdivisions=sub,radius=1); o=bpy.context.object; o.data.materials.append(m); o.data.shade_smooth(); return hidden(o)
if SH=='s4':
    ND=5200; dm=glassdrop(); drops=Swarm('drops',icos(dm,4),ND)
    # distribute in front of / around camera-boat corridor
    dx=rg.uniform(-9,9,ND); dy=rg.uniform(-9,42,ND)**1.0; dst=rg.random(ND); 
    dr=np.exp(rg.normal(math.log(.026),.55,ND)).clip(.006,.085); dsp=rg.uniform(.16,.5,ND); t0=rg.uniform(.2,4.8,ND)-2.0*(np.hypot(dx,dy)>8); dph=rg.uniform(0,6.28,(ND,2))
    near=(np.abs(dx)<.8)&(np.abs(dy-.2)<2.6); 
if SH=='s5':
    ND=420000; dm=glassdrop('glob'); drops=Swarm('globs',icos(dm,2),ND)
    rg0=rg.random(ND); arm=rg.integers(0,5,ND); ss0=rg.random(ND); off=rg.normal(0,1,(ND,3)); dr=np.exp(rg.normal(math.log(.62),.5,ND)).clip(.2,2.6)
    pm,n,o=mat('portal'); tc=n.n('ShaderNodeTexCoord'); P=n.v('SCALE',tc.outputs['Object'],scale=1.0/(RR-45)); x,y,z=n.sep(P)[:3]
    tt=n.val(0,'pt'); op=n.val(0,'open')
    r=n.v('LENGTH',P); ang=n.m('ARCTAN2',y,x); sw=n.m('ADD',ang,n.m('ADD',n.m('MULTIPLY',n.m('LOGARITHM',n.m('MAXIMUM',r,.01),2.718),2.1),n.m('MULTIPLY',tt,-.35)))
    sp=n.comb(n.m('MULTIPLY',n.m('COSINE',sw),r),n.m('MULTIPLY',n.m('SINE',sw),r),n.m('MULTIPLY',tt,.08))
    n1=n.noise(sp,2.1,10,.62,dist=.35); n2=n.noise(n.v('SCALE',sp,scale=1.0),6.0,8,.65); 
    arms=n.m('POWER',n.m('ADD',n.m('MULTIPLY',n.m('COSINE',n.m('MULTIPLY',sw,2.0)),.5),.5),1.6)
    fil=n.mr(n1,.36,.72,0,1,'SMOOTHSTEP'); fal=n.m('POWER',n.m('SUBTRACT',1.0,n.m('MINIMUM',r,1.0)),.8)
    dust=n.mr(n2,.42,.66,1,.12,'SMOOTHSTEP')
    dens=n.m('MULTIPLY',n.m('MULTIPLY',n.m('ADD',n.m('MULTIPLY',fil,n.m('ADD',n.m('MULTIPLY',arms,1.1),.15)),.03),dust),fal)
    colr=n.ramp(r,[(0,(1.0,.86,.62)),(.14,(1.0,.62,.36)),(.34,(.72,.26,.62)),(.62,(.14,.26,1.0)),(1,(.04,.32,.75))])
    em=n.v('SCALE',colr,scale=n.m('MULTIPLY',dens,9.0)); corec=n.m('EXPONENT',n.m('MULTIPLY',n.m('MULTIPLY',r,r),-70.0))
    em=n.v('ADD',em,n.v('SCALE',(1.0,.86,.66),scale=n.m('MULTIPLY',corec,26.0)))
    rim=n.m('EXPONENT',n.m('MULTIPLY',n.m('ABSOLUTE',n.m('SUBTRACT',r,n.m('MULTIPLY',op,.985))),-38.0))
    em=n.v('ADD',em,n.v('SCALE',(.25,.6,1.0),scale=n.m('MULTIPLY',rim,n.m('ADD',.5,n.m('MULTIPLY',fil,5.0)))))
    for sc_,br in((95.,9.),(230.,4.)):
        vo=n.n('ShaderNodeTexVoronoi',feature='F1'); n.set(vo,'Vector',P); n.set(vo,'Scale',sc_); hue=n.sep(vo.outputs['Color'])[0]
        em=n.v('ADD',em,n.v('SCALE',n.ramp(hue,[(0,(1,.6,.4)),(.5,(1,1,1)),(1,(.5,.7,1))]),scale=n.m('MULTIPLY',n.m('MULTIPLY',n.mr(vo.outputs['Distance'],.16,.0,0,1),n.m('POWER',hue,3.0)),br)))
    e=n.n('ShaderNodeEmission',i={'Color':em,'Strength':1.0}); tr=n.n('ShaderNodeBsdfTransparent')
    wob=n.m('ADD',r,n.m('MULTIPLY',n.m('SUBTRACT',n1,.5),.10))
    mk=n.mr(wob,n.m('MULTIPLY',op,.99),n.m('SUBTRACT',n.m('MULTIPLY',op,1.0),.04),0,1,'SMOOTHSTEP')
    mx=n.n('ShaderNodeMixShader',i={0:mk,1:tr,2:e}); n.set(o,'Surface',mx)
    prim('circle',vertices=256,radius=RR-46,fill_type='NGON',location=tuple(RC),rotation=(math.pi/2,0,0)); po=bpy.context.object; po.data.materials.append(pm)
    al=bpy.data.lights.new('pl','AREA'); al.shape='DISK'; al.size=RR*1.1; al.color=(.42,.5,1.0); ao=bpy.data.objects.new('pl',al); s.collection.objects.link(ao); ao.location=(0,1440,RC[2]); ao.rotation_euler=(-math.pi/2,0,0); ao.visible_camera=False; ao.visible_glossy=False
def bob(t,amp=1.0):
    B.location=(0,0,.10+.05*math.sin(t*1.1)*amp); B.rotation_euler=(.018*math.sin(t*1.0+1)*amp,.030*math.sin(t*.83)*amp,.03*math.sin(t*.4))
def step(f):
    u=f/(n_-1); t=f/24.
    base=dict(s1=0,s2=8,s3=20,s4=30,s5=40)[SH]; T=base+t
    md.time=T*.8; wt.outputs[0].default_value=T; ct.outputs[0].default_value=T*.01; bob(T)
    fl=1+.10*math.sin(T*13)+.07*math.sin(T*21.7+2); pl.energy=70*fl
    if SH=='s1':
        e=sss(-.15,1.15,u)
        aim(c,(-3.6+2.2*e,-6.2-1.2*e,1.15+.75*e),(.25+.1*e,6,2.0+.55*e)); c.data.lens=34
        c.data.dof.use_dof=True; c.data.dof.aperture_fstop=1.6; c.data.dof.focus_distance=5.9+.6*e
    elif SH=='s2':
        e=sss(-.1,1.12,u)
        aim(c,(3.5+5.0*e,-13-57*e,2.0+6.0*e),(0,1500,165-38*e)); c.data.lens=24+1.5*e
        core.default_value=6*ss(.62,1,u)*(.75+.25*math.sin(t*5))
        R.update(t,lambda th,rn:.35*ss(.7,1,u)*np.exp(-((np.angle(np.exp(1j*(th-math.pi/2)))/(.15+1.3*max(0,u-.6)))**2)))
    elif SH=='s3':
        a=2.93-.16*u
        p=RC+np.array([math.cos(a)*(RR-118),-150+36*u,math.sin(a)*(RR-118)+10*u]); bb=2.40-.12*u; q=RC+np.array([math.cos(bb)*(RR+4),10,math.sin(bb)*(RR+4)])
        aim(c,p,q,roll=.06-.10*u); c.data.lens=24
        fr=3.0-1.75*ss(-.05,1.05,u)
        core.default_value=9; setval('cf0',fr-.09); setval('cf1',fr+.03)
        def wk(th,rn):
            d=np.angle(np.exp(1j*(th-fr))); lead=ss(-.10,.05,d+.05*(rn-.5)); return lead*(.42+.58*np.exp(-np.maximum(d,0)*5.5))
        R.update(t,wk)
        for k,h in enumerate(R.halo): h.rotation_euler=(math.pi/2+(.10+.05*k)*math.sin(t*.5+k),(.07*k)*math.sin(t*.6),0)
    elif SH=='s4':
        e=sss(-.1,1.1,u)
        aim(c,(2.75-.5*e,-4.3+.5*e,.42+.35*e),(-.35,6,1.75+.35*e)); c.data.lens=30
        c.data.dof.use_dof=True; c.data.dof.aperture_fstop=1.3; c.data.dof.focus_distance=4.5
        core.default_value=8; R.update(t,lambda th,rn:.2+.12*np.sin(th*9+t*2+rn*3))
        el=np.maximum(t-t0+1.0,0); z=-.3+dsp*el**1.35*.95; z0=z
        x=dx+.06*np.sin(el*1.3+dph[:,0]); y=dy+.06*np.cos(el*1.1+dph[:,1])
        w=np.stack([1+.10*np.sin(el*9+dph[:,0]),1+.10*np.sin(el*9+dph[:,0]+2.1),1+.10*np.sin(el*9+dph[:,0]+4.2)],-1)
        vis=(el>0)&~(near&(z<.75)); dc=np.linalg.norm(np.stack([x,y,z],-1)-np.array(c.location),axis=1); vis&=dc>.30
        drops.put(pos=np.stack([x,y,z],-1),scale=w*(dr*vis*ss(0,.5,el))[:,None])
    elif SH=='s5':
        e=sss(-.15,.95,u); k=max(0,(u-.70)/.30)
        aim(c,((8.5-3.5*e)*(1-k),-66+60*e+1335*k**3.2,8+4*e+98*k**1.8),(0,1500+400*k,128-18*k)); c.data.lens=25.5-3.5*k**2
        opn=sss(.10,.62,u); core.default_value=7+3*opn; setval('skyg',1-.86*opn); setval('fogg',1-.88*opn); setval('stars',7*opn)
        R.update(t,lambda th,rn:np.clip(.22+.45*opn*rn+.12*np.sin(th*7-t*3),0,1.2))
        nd=pm.node_tree.nodes
        for x_ in nd:
            if x_.type=='VALUE': x_.outputs[0].default_value={'pt':t,'open':opn}[x_.label]
        po.hide_render=bool(opn<.002); al.energy=1.1e8*opn
        for k,h in enumerate(R.halo): h.rotation_euler=(math.pi/2+(.55+.3*k)*opn*math.sin(t*.6+k*2)+.2*opn,(.35+.2*k)*opn*math.sin(t*.45+k),0)
        sun.data.energy=3.2*(1-.85*opn)
        sp_=(ss0+t*.045)%1.0; grow=ss(0,.30,u)
        rho=RR*(1.75*(1-sp_)**1.15+.06); phi=arm*2*math.pi/5+.6+sp_*5.6+t*.10
        wd=(10+44*(1-sp_))*(.35+.65*(off[:,2]**2).clip(0,2)/2)
        x=np.cos(phi)*rho+off[:,0]*wd; z=RC[2]+np.sin(phi)*rho+off[:,1]*wd; y=1500-120-(1-sp_)*620+off[:,2]*wd*1.3
        reach=(1-sp_)>(1-grow*1.25); vis=(z>.5)&reach
        rr=dr*(.6+.35*(1-sp_))*vis*ss(0,40,z)*(.12+.88*ss(.02,.45,1-sp_))*(rg0<.10+.9*ss(.15,.6,1-sp_))
        drops.put(pos=np.stack([x,y,z],-1),scale=np.repeat(rr[:,None],3,1))
for f in FR:
    p='%s/%04d.exr'%(OUT,f)
    if os.path.exists(p) and os.path.getsize(p)>20000 and 'force' not in A: continue
    step(f); s.cycles.seed=f; t0_=time.time(); render(p); print('FRAME',SH,f,'%.1fs'%(time.time()-t0_),flush=True)

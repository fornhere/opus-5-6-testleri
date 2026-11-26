import sys; sys.path.insert(0,'esik-film/src')
from lib import *
import OpenImageIO as oiio, time
from post import blur3,rs
import gal as G0
A=args(); spp=int(A.get('spp',48)); scale=int(A.get('scale',100)); NF=156; OUT=A.get('out',ROOT+'/frames/s6'); os.makedirs(OUT,exist_ok=True)
s=reset(samples=spp,scale=scale); c_=s.cycles; c_.volume_biased=True; c_.volume_step_rate=1.0; c_.volume_max_steps=400; c_.max_bounces=0; c_.transparent_max_bounces=4; c_.denoising_input_passes='RGB'; c_.adaptive_threshold=.01
s.world.use_nodes=True; wn=N(s.world.node_tree); wo=wn.n('ShaderNodeOutputWorld'); wn.set(wo,'Surface',wn.n('ShaderNodeBackground',i={'Color':(.0012,.0018,.005),'Strength':1.0}))
m,n,o=mat('vol'); tc=n.n('ShaderNodeTexCoord'); P=tc.outputs['Object']; x,y,z=n.sep(P)[:3]; rot=n.val(0,'rot'); T=n.val(0,'T')
r=n.v('LENGTH',n.comb(x,y,0.0)); ang=n.m('ARCTAN2',y,x)
PIT=2.7
sw=n.m('ADD',ang,n.m('ADD',n.m('MULTIPLY',n.m('LOGARITHM',n.m('ADD',r,.35),2.718281828),-PIT),rot))
# co-rotating noise domain (polar-warped) so filaments follow arms
q=n.comb(n.m('MULTIPLY',n.m('COSINE',sw),r),n.m('MULTIPLY',n.m('SINE',sw),r),n.m('MULTIPLY',z,1.6))
warp=n.noise(q,.55,3,.5); q2=n.v('ADD',q,n.v('SCALE',n.comb(warp,n.noise(n.v('ADD',q,(7,3,1)),.55,3,.5),warp),scale=1.5))
f1=n.noise(q2,.75,8,.62); f2=n.noise(n.v('ADD',q2,(11,5,2)),1.9,8,.64); f3=n.noise(q2,.42,3,.5)
ca=n.m('COSINE',n.m('MULTIPLY',n.m('ADD',sw,n.m('MULTIPLY',n.m('SUBTRACT',f3,.5),1.5)),2.0))
arm=n.m('POWER',n.m('ADD',n.m('MULTIPLY',ca,.5),.5),2.2)
ca2=n.m('COSINE',n.m('ADD',n.m('MULTIPLY',n.m('ADD',sw,n.m('MULTIPLY',n.m('SUBTRACT',f3,.5),1.5)),2.0),.75)); lane=n.m('POWER',n.m('ADD',n.m('MULTIPLY',ca2,.5),.5),5.0)
th=n.m('ADD',.20,n.m('MULTIPLY',n.m('EXPONENT',n.m('MULTIPLY',r,-.9)),.5))
zz=n.m('DIVIDE',n.m('SUBTRACT',z,n.m('MULTIPLY',n.m('SUBTRACT',f3,.5),.5)),th); vz=n.m('EXPONENT',n.m('MULTIPLY',n.m('MULTIPLY',zz,zz),-1.0))
fal=n.m('MULTIPLY',n.m('EXPONENT',n.m('MULTIPLY',r,-.26)),n.mr(r,10.5,7.0,0,1,'SMOOTHSTEP'))
gas=n.m('MULTIPLY',n.m('MULTIPLY',n.m('ADD',n.m('MULTIPLY',arm,1.0),.06),n.mr(f1,.40,.72,.02,1.5,'SMOOTHSTEP')),n.m('MULTIPLY',vz,fal))
colr=n.ramp(n.m('DIVIDE',r,10.0),[(0,(1.0,.80,.50)),(.12,(1.0,.55,.26)),(.26,(.95,.30,.36)),(.42,(.42,.26,.95)),(.65,(.12,.36,1.0)),(1,(.05,.50,.85))])
hii=n.m('MULTIPLY',n.mr(f2,.60,.74,0,1,'SMOOTHSTEP'),n.m('MULTIPLY',n.m('MULTIPLY',arm,vz),n.m('MULTIPLY',fal,n.mr(r,1.2,2.6,0,1))))
em=n.v('ADD',n.v('SCALE',colr,scale=n.m('MULTIPLY',gas,6.0)),n.v('SCALE',(1.0,.12,.30),scale=n.m('MULTIPLY',hii,13.0)))
rb=n.v('LENGTH',n.comb(x,y,n.m('MULTIPLY',z,1.7))); bul=n.m('ADD',n.m('MULTIPLY',n.m('EXPONENT',n.m('MULTIPLY',rb,-1.9)),2.2),n.m('MULTIPLY',n.m('EXPONENT',n.m('MULTIPLY',rb,-6.5)),26.0))
em=n.v('ADD',em,n.v('SCALE',(1.0,.70,.38),scale=n.m('MULTIPLY',bul,n.mr(n.m('ABSOLUTE',z),2.4,.6,0,1,'SMOOTHSTEP'))))
dust=n.m('MULTIPLY',n.m('MULTIPLY',n.m('ADD',lane,.10),n.mr(f2,.42,.62,0,1,'SMOOTHSTEP')),n.m('MULTIPLY',n.m('EXPONENT',n.m('MULTIPLY',n.m('MULTIPLY',zz,zz),-5.0)),n.m('MULTIPLY',n.mr(r,.5,1.5,0,1),n.mr(r,10,7,0,1))))
e=n.n('ShaderNodeEmission',i={'Color':em,'Strength':1.0}); ab=n.n('ShaderNodeVolumeAbsorption',i={'Color':(.45,.28,.16),'Density':n.m('MULTIPLY',dust,20.0)})
n.set(o,'Volume',n.n('ShaderNodeAddShader',i={0:e,1:ab})); 
prim('cube',size=1); box=bpy.context.object; box.data.transform(Matrix.Diagonal((21,21,5.0,1))); box.data.materials.append(m)
try: m.cycles.volume_sampling='DISTANCE'; m.cycles.volume_step_rate=float(A.get('step',.35)); m.volume_intersection_method='ACCURATE'
except Exception as ex: print('vol',ex)
cam=camera(24)
def campath(u):
    e=sss(-.25,1.08,u); 
    R=9.6+7.0*e**1.6-3.4*math.sin(min(1,u*1.5)*math.pi)*.9; az=-2.35+1.05*e+.25*u; el=.085+.80*ss(.18,1.05,u)
    p=Vector((R*math.cos(el)*math.cos(az),R*math.cos(el)*math.sin(az),R*math.sin(el)+.12)); return p,Vector((0,0,-.1)), .55*(1-e)*math.sin(u*2.2+1)
# stars
rg=np.random.default_rng(5); ns=1500000
r_=np.clip(rg.gamma(2.0,1.75,ns),.02,11); k=rg.integers(0,2,ns); on=rg.random(ns)<.6; w=rg.normal(0,1,ns)*np.where(on,.26,1.2)
ph=k*np.pi+w+PIT*np.log(r_+.35); zz_=rg.normal(0,1,ns)*(.13+.35*np.exp(-r_*.9)); SP=np.stack([r_*np.cos(ph),r_*np.sin(ph),zz_],-1)
t=np.clip(r_/7,0,1)[:,None]; blue=np.where(on,1,0)[:,None]*.8; col=np.array([1,.70,.42])*(1-t)+np.array([.62,.74,1.0])*t; col=col*(1-blue*t)+np.array([.42,.62,1.0])*blue*t
L=np.exp(rg.normal(-1.0,1.35,ns)).clip(0,50); SC=col*L[:,None]
nb=26000; d=rg.normal(0,1,(nb,3)); d/=np.linalg.norm(d,axis=1)[:,None]; BP=d*400; BC=(np.array([1,.8,.6])*(1-rg.random((nb,1)))+np.array([.6,.75,1])*rg.random((nb,1)))*np.exp(rg.normal(-1,1.6,nb)).clip(0,60)[:,None]
W=s.render.resolution_x*scale//100; H=s.render.resolution_y*scale//100; F=cam.data.lens/36*W
def stars(f):
    buf=np.zeros((H,W,3)); rt=f/24*.022
    SUB=4
    for j in range(SUB):
        ff=f+(j/SUB-.375)*.5; u=ff/(NF-1); p,tg,ro=campath(u); aim(cam,p,tg,ro); M=np.array(cam.rotation_quaternion.to_matrix()); pv=np.array(p)
        cr,srn=math.cos(-rt),math.sin(-rt)
        for X,C,b in((SP,SC,0),(BP,BC,1)):
            if not b: X=np.stack([X[:,0]*cr-X[:,1]*srn,X[:,0]*srn+X[:,1]*cr,X[:,2]],-1); D=(X-pv)@M
            else: D=X@M
            z=-D[:,2]; mk=z>.08; mk&=(np.abs(D[:,0])<z*.8)&(np.abs(D[:,1])<z*.36); D=D[mk]; z=z[mk]
            att=np.full(len(z),.55) if b else np.clip((z-.08)/.8,0,1)*30/(z*z+9)
            G0.splat(buf,D[:,0]/z*F+W/2,H/2-D[:,1]/z*F,C[mk]*att[:,None]/SUB)
    buf=buf.astype('f'); return buf*.16*(W/1920)**2*4/4+blur3(buf)*.11*(W/1920)**2
FR=[int(x) for x in A['f'].split(',')] if 'f' in A else range(int(A.get('a',0)),int(A.get('b',NF)))
for f in FR:
    p='%s/%04d.exr'%(OUT,f)
    if os.path.exists(p) and 'force' not in A: continue
    t0=time.time(); u=f/(NF-1); rot.node.outputs[0].default_value=f/24*.022
    q_,tg,ro=campath(u); aim(cam,q_,tg,ro); s.cycles.seed=f; render(p); t1=time.time()
    im=oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[:,:,:3]; st=stars(f)
    res=im+st; fl=2.4*np.exp(-f/1.6)*(f<14); res=res+np.array([1,.88,.74],'f')*fl*5
    b=oiio.ImageBuf(np.ascontiguousarray(res.astype('f'))); b.set_write_format(oiio.HALF); b.write(p); print('FRAME s6',f,'%.1fs +%.1fs'%(t1-t0,time.time()-t1),flush=True)

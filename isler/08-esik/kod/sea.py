from lib import *
import lib
# ---------- colossal ring ----------
RC=np.array([0,1500,110.]); RR=430.
def ring_frame(th): # radial dir in XZ plane, axis along Y
    return np.stack([np.cos(th),0*th,np.sin(th)],-1)
def metal_mats():
    m,n,o=mat('obsid'); ge=n.n('ShaderNodeNewGeometry'); oi=n.n('ShaderNodeObjectInfo')
    nz=n.noise(ge.outputs['Position'],.09,6,.6); r=n.m('ADD',n.mr(nz,.3,.7,.18,.5),n.m('MULTIPLY',oi.outputs['Random'],.12))
    c=n.mix(oi.outputs['Random'],(.018,.019,.022),(.05,.045,.042))
    b=pbsdf(n,Base_Color=c,Metallic=.85,Roughness=r); fogged(n,b,o)
    g,n,o=mat('gold'); ge=n.n('ShaderNodeNewGeometry'); nz=n.noise(ge.outputs['Position'],.2,5,.6)
    b=pbsdf(n,Base_Color=(1.0,.60,.22),Metallic=1.0,Roughness=n.mr(nz,.3,.7,.18,.42)); fogged(n,b,o)
    l,n,o=mat('core'); at=n.n('ShaderNodeAttribute',attribute_name='glow',attribute_type='INSTANCER')
    e=n.n('ShaderNodeEmission',i={'Color':(1.0,.62,.26),'Strength':n.m('ADD',n.m('MULTIPLY',at.outputs['Fac'],38.0),.02)}); fogged(n,e,o)
    return m,g,l
def plate(mats,bev=.06,name='plate'):
    """unit armour plate: x tangential, y axial, z outward; obsidian top, gold side, panel grooves"""
    prim('cube',size=1); o=bpy.context.object; o.name=name; o.scale=(.96,.94,.22); bpy.ops.object.transform_apply(scale=True)
    me=o.data
    for m in mats[:2]: me.materials.append(m)
    for p in me.polygons: p.material_index=0 if p.normal.z>.5 else 1
    bpy.context.view_layer.objects.active=o; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons: p.select=p.normal.z>.5
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.inset(thickness=.07,depth=0); bpy.ops.mesh.inset(thickness=.025,depth=-.035); bpy.ops.mesh.inset(thickness=.16,depth=.03); bpy.ops.mesh.inset(thickness=.05,depth=.05)
    bpy.ops.object.mode_set(mode='OBJECT')
    b=o.modifiers.new('b','BEVEL'); b.width=.012; b.segments=2; b.limit_method='ANGLE'
    bpy.ops.object.convert(target='MESH')
    return hidden(o)
class Ring:
    def __init__(s,detail=1.0,seed=3):
        rg=np.random.default_rng(seed); s.m=metal_mats(); src=plate(s.m); s.parts=[]
        # cross-section of tube: octagon-ish box, radial half rr, axial half ax
        P=[];Q=[];S=[];TH=[];NRM=[]
        faces=[]; rr,ax=26.,44.
        # profile faces: (center offset radial, axial, normal angle in (radial,axial) plane, width)
        prof=[(rr,0,0,ax*1.25),(-rr,0,math.pi,ax*1.25),(0,ax,math.pi/2,rr*1.2),(0,-ax,-math.pi/2,rr*1.2),
              (rr*.83,ax*.83,math.radians(50),26),(rr*.83,-ax*.83,-math.radians(50),26),(-rr*.83,ax*.83,math.radians(130),26),(-rr*.83,-ax*.83,-math.radians(130),26)]
        for fi,(dr,da,an,wid) in enumerate(prof):
            rows=max(1,int(wid//5)); 
            for row in range(rows):
                off=(row+.5)/rows-.5; w=wid/rows
                nt=int(2*math.pi*(RR+dr)/(w*rg.choice([.9,1.5,2.2]))); nt=(nt//24)*24
                for k in range(nt):
                    if rg.random()<.05: continue
                    th=(k+.5*(row%2))/nt*2*math.pi
                    sub=1
                    L=2*math.pi*(RR+dr)/nt
                    r0=RR+dr+math.sin(an)*(-off*wid)*-0+ (-math.sin(an))*off*wid
                    a0=da+math.cos(an)*off*wid
                    lift=rg.choice([0,.6,1.4,3.0,5.0],p=[.4,.25,.2,.1,.05])
                    P.append((th,r0+math.cos(an)*lift,a0+math.sin(an)*lift)); NRM.append(an); S.append((L*.975,w*.965,5+lift*1.2)); TH.append(th)
        P=np.array(P);s.N=len(P); s.th=P[:,0];s.r=P[:,1];s.a=P[:,2];s.an=np.array(NRM);s.S=np.array(S)
        s.rn=rg.random(s.N); s.rv=rg.normal(0,1,(s.N,3))
        s.sw=Swarm('ring',src,s.N)
        s.sw_pos0=None
        # glowing core torus ring inside the armour (seen through seams) + thin inner emitter
        u=np.linspace(0,2*math.pi,720,endpoint=False); v=[]
        for uu in u:
            for q in range(8):
                A=q*math.pi/4+.39; rr2=RR+math.cos(A)*21; v.append((rr2*math.cos(uu),math.sin(A)*38,rr2*math.sin(uu)))
        cm,n,o=mat('coreglow'); s.coreval=n.val(0.0,'core'); ge=n.n('ShaderNodeNewGeometry'); tc=n.n('ShaderNodeTexCoord')
        nz=n.noise(tc.outputs['Object'],.05,5,.7,'4D',n.val(0,'cw'))
        e=n.n('ShaderNodeEmission',i={'Color':n.ramp(nz,[(.25,(1.,.22,.04)),(.5,(1.,.40,.11)),(.7,(1.,.66,.34))]),'Strength':n.m('MULTIPLY',n.m('MULTIPLY',s.coreval,n.mr(nz,.3,.7,.3,1.8)),n.mr(n.m('ARCTAN2',n.sep(tc.outputs['Object'])[2],n.sep(tc.outputs['Object'])[0]),n.val(-9.1,'cf0'),n.val(-9.0,'cf1')))}); fogged(n,e,o)
        s.core=meshobj('core',v,grid_faces(720,8,True,True),[cm]); s.core.location=RC
        # 24 tapered buttresses + two thin gold halo rings
        tv=[(x*(.5 if z<0 else .16),y*(.5 if z<0 else .22),z) for x in(-1,1) for y in(-1,1) for z in(-.5,.5)]
        fin=meshobj('fin',tv,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],[s.m[0]]); hidden(fin)
        nf=24; th=np.linspace(0,2*math.pi,nf,endpoint=False); s.fin=Swarm('fins',fin,nf); big=np.arange(nf)%2==0
        s.fin.put(pos=RC+ring_frame(th)*(RR+26+np.where(big,26,14))[:,None],quat=qmul(qaxis(np.tile([0,-1.,0],(nf,1)),th),qaxis(np.tile([0,1.,0],(nf,1)),np.full(nf,math.pi/2))),
            scale=np.stack([np.where(big,16,9),np.where(big,46,30),np.where(big,60,32)],-1))
        s.halo=[]
        for R,w in((RR+92,1.6),(RR-62,1.3),(RR-74,.6)):
            prim('torus',major_radius=R,minor_radius=w,major_segments=512,minor_segments=10,location=tuple(RC),rotation=(math.pi/2,0,0)); h=bpy.context.object; h.data.materials.append(s.m[1]); h.data.shade_smooth(); s.halo.append(h)
        s.update(0)
    def update(s,t,wake=None):
        """wake(th)->0..1 per plate: plates lift, flip and expose glow"""
        w=np.zeros(s.N) if wake is None else wake(s.th,s.rn)
        rad=ring_frame(s.th); tan=np.stack([-np.sin(s.th),0*s.th,np.cos(s.th)],-1); axv=np.array([0,1.,0])
        # normal in world
        nrm=rad*np.cos(s.an)[:,None]+axv*np.sin(s.an)[:,None]
        lift=np.sin(np.clip(w,0,1)*math.pi/2)*(6+10*s.rn)
        pos=RC+rad*s.r[:,None]+axv*s.a[:,None]+nrm*lift[:,None]
        # basis: x=tan, z=nrm, y=z×x
        # quaternion: rotate about -Y by th (takes x->radial,z->tangent) then compose
        q0=qaxis(np.tile([0,-1.,0],(s.N,1)),s.th) # local X->rad, Z->tan
        # want local x->tan, z->rad cos+ y sin : first local rotation
        q1=qaxis(np.tile([0,1.,0],(s.N,1)),np.full(s.N,-math.pi/2)) # x->z(tan) , z->-x ... 
        q1=qaxis(np.tile([0,1.,0],(s.N,1)),np.full(s.N,math.pi/2)); # z->x(rad), x->-z(-tan)
        qn=qaxis(np.tile([0,0,1.],(s.N,1)),s.an) # rotates rad->y(axial)
        flip=qaxis(np.tile([1.,0,0],(s.N,1)),w*(.7+.9*s.rn)*np.where(s.rn>.5,1,-1))
        q=qmul(qmul(qmul(q0,qn),q1),flip)
        s.sw.put(pos=pos,quat=q,scale=s.S)
# ---------- boat ----------
def boat(lantern=60.):
    col=bpy.data.collections.new('boat'); bpy.context.scene.collection.children.link(col)
    root=bpy.data.objects.new('boat',None); col.objects.link(root)
    wm,n,o=mat('wood'); tc=n.n('ShaderNodeTexCoord'); P=tc.outputs['Object']
    g=n.noise(n.v('MULTIPLY',P,(14,.8,14)),1.6,8,.65,dist=.4); c=n.ramp(g,[(.3,(.018,.010,.006)),(.55,(.075,.042,.022)),(.75,(.15,.09,.05))])
    z=n.sep(P)[2]; seam=n.m('ABSOLUTE',n.m('SUBTRACT',n.m('FRACT',n.m('MULTIPLY',z,7.0)),.5)); 
    bp=n.n('ShaderNodeBump',i={'Height':n.m('ADD',n.m('MULTIPLY',g,.25),n.m('MULTIPLY',n.mr(seam,.42,.5,1,0),1.0)),'Strength':.5,'Distance':.02})
    b=pbsdf(n,Base_Color=c,Roughness=n.mr(g,.3,.7,.35,.6),Normal=bp.outputs[0]); fogged(n,b,o)
    L=2.6; nu,nv=49,17; v=[]
    def hull(u,w,inner):
        y=u*L; k=max(0,1-abs(u)**2.4); half=.72*k**.8+.015; sheer=.46+.42*abs(u)**2.6; keel=-.26+.36*abs(u)**3.2
        a=w*math.pi/2; e=.6
        x=half*math.copysign(abs(math.sin(a))**e,a); zz=keel+(sheer-keel)*(1-abs(math.cos(a))**1.15)
        if inner: x*=.93; zz=max(zz,keel+.07) if zz<sheer-.02 else zz
        return (x,y+(.12*u*abs(u)**4),zz)
    for inn in(0,1):
        v=[hull(u,w,inn) for u in np.linspace(-1,1,nu) for w in np.linspace(-1,1,nv)]
        h=meshobj('hull%d'%inn,v,grid_faces(nu,nv),[wm],True,col); h.parent=root
    # gunwale
    for sgn in(-1,1):
        cu=bpy.data.curves.new('gw','CURVE'); cu.dimensions='3D'; cu.bevel_depth=.035; sp=cu.splines.new('POLY'); us=np.linspace(-1,1,60); sp.points.add(59)
        for p,u in zip(sp.points,us): p.co=(*hull(u,sgn,0),1)
        ob=bpy.data.objects.new('gw',cu); cu.materials.append(wm); col.objects.link(ob); ob.parent=root
    us=np.linspace(-.93,.93,60); fv=[]
    for u in us: 
        hw=.70*max(0,1-abs(u)**2.4)**.8; fv+=[(-hw,u*L,.03),(hw,u*L,.03)]
    fl_=meshobj('floor',fv,grid_faces(60,2),[wm],False,col); fl_.parent=root
    for e in(-1,1):
        cu=bpy.data.curves.new('stem','CURVE'); cu.dimensions='3D'; cu.bevel_depth=.05; cu.bevel_resolution=3; sp=cu.splines.new('POLY'); ws=np.linspace(-1,0,20); sp.points.add(19)
        for p,w_ in zip(sp.points,ws): q=hull(e,w_,0); p.co=(0,q[1]-.01*e,q[2]+.03,1)
        ob=bpy.data.objects.new('stem',cu); cu.materials.append(wm); col.objects.link(ob); ob.parent=root
    for y in(-1.2,.1,1.35):
        prim('cube',size=1,location=(0,y,.28)); p=bpy.context.object; hw=.72*max(0,1-abs(y/L)**2.4)**.8; p.scale=(hw*1.82,.26,.05); p.data.materials.append(wm); p.parent=root
    # cloaked figure standing, facing +Y
    cm,n,o=mat('cloth'); ge=n.n('ShaderNodeTexCoord'); nz=n.noise(ge.outputs['Object'],180,2,.5)
    bp=n.n('ShaderNodeBump',i={'Height':nz,'Strength':.25,'Distance':.004}); b=pbsdf(n,Base_Color=(.09,.018,.014),Roughness=.85,Sheen_Weight=.4,Sheen_Roughness=.4,Normal=bp.outputs[0]); fogged(n,b,o)
    v=[]; nu,nv=90,96; rg=np.random.default_rng(5); ph=rg.uniform(0,6.28,6)
    prof=[(0,.36),(.25,.335),(.55,.285),(.85,.25),(1.1,.235),(1.28,.235),(1.36,.205),(1.43,.150),(1.48,.120),(1.54,.122),(1.61,.130),(1.68,.122),(1.74,.095),(1.79,.055),(1.82,.022),(1.83,.003)]
    zs=[p[0] for p in prof]; rs_=[p[1] for p in prof]
    for a in np.linspace(0,2*math.pi,nu,endpoint=False):
        for t in np.linspace(0,1,nv):
            zz=t*1.83; r=np.interp(zz,zs,rs_); low=max(0,1-zz/1.35)
            r+=(.048*math.sin(a*7+ph[0]+zz*1.6+.6*math.sin(a*3))+.026*math.sin(a*13+ph[1]-zz*2)+.012*math.sin(a*23+ph[2]))*low**.8+.006*math.sin(a*5+zz*22)*(1-low)
            hood=1.0 if zz<1.45 else 1+.28*max(0,math.sin(a))*math.sin(min(1,(zz-1.45)/.3)*math.pi)
            x=r*math.cos(a)*(1+.16*math.exp(-((zz-1.22)/.22)**2))*(1-.10*math.exp(-((zz-1.64)/.14)**2)); y=r*math.sin(a)*(.82 if zz<1.45 else 1.0)*hood-.10*low**2-.05*max(0,zz-1.62)/.2
            v.append((x,y,zz))
    f=meshobj('fig',v,grid_faces(nu,nv,True),[cm],True,col); sb=f.modifiers.new('s','SUBSURF'); sb.levels=sb.render_levels=1; f.parent=root; f.location=(0,-.55,.12)
    # arm sleeve reaching to the lantern pole
    def tube(pts,r,m,nm):
        cu=bpy.data.curves.new(nm,'CURVE'); cu.dimensions='3D'; cu.bevel_depth=r; cu.bevel_resolution=4; sp=cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts)-1)
        for p,q in zip(sp.bezier_points,pts): p.co=q; p.handle_left_type=p.handle_right_type='AUTO'
        ob=bpy.data.objects.new(nm,cu); cu.materials.append(m); col.objects.link(ob); ob.parent=root; return ob
    tube([(.2,-.52,1.42),(.27,-.40,1.22),(.18,-.16,1.12)],.065,cm,'arm')
    im,n,o=mat('iron'); fogged(n,pbsdf(n,Base_Color=(.03,.028,.026),Metallic=.9,Roughness=.45),o)
    tube([(.17,-.14,.05),(.175,-.13,1.0),(.17,-.12,2.05),(.17,.05,2.28),(.17,.30,2.26)],.016,im,'pole')
    # lantern
    LP=(.17,.30,2.02)
    for zz,r,h in((.12,.10,.03),(-.14,.095,.03),(.17,.05,.06)):
        prim('cylinder',vertices=24,radius=r,depth=h,location=(LP[0],LP[1],LP[2]+zz)); c_=bpy.context.object; c_.data.materials.append(im); c_.parent=root
    for k in range(6):
        a=k*math.pi/3; prim('cylinder',vertices=8,radius=.007,depth=.27,location=(LP[0]+.085*math.cos(a),LP[1]+.085*math.sin(a),LP[2])); c_=bpy.context.object; c_.data.materials.append(im); c_.parent=root
    fm,n,o=mat('flame'); s_=n.n('ShaderNodeEmission',i={'Color':(1,.50,.16),'Strength':lantern*1.2}); n.set(o,'Surface',s_)
    prim('uv_sphere',radius=.05,location=LP); fl=bpy.context.object; fl.scale=(.8,.8,1.6); fl.data.materials.append(fm); fl.data.shade_smooth(); fl.parent=root
    pl=bpy.data.lights.new('lan','POINT'); pl.energy=lantern; pl.color=(1,.52,.2); pl.shadow_soft_size=.06; po=bpy.data.objects.new('lan',pl); col.objects.link(po); po.location=LP; po.parent=root
    tube([(LP[0],LP[1],LP[2]+.2),(LP[0],LP[1],LP[2]+.25)],.006,im,'hook')
    return root,pl,fm

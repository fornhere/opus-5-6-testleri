import sys; sys.path.insert(0,'esik-film/src')
from post import *
A=dict(x.split('=') for x in sys.argv[sys.argv.index('--')+1:]); wk=int(A.get('w',0)); nw=int(A.get('n',1)); R='esik-film/'
D=14; TL=[]
for S,n in(('s1',132),('s2',144),('s3',120),('s4',132),('s5',156),('s6',156),('s7',96),('s8',230)): TL+=[(S,f,n) for f in range(n)] if S!='s7' else [(S,f,n) for f in range(D,n)]
def ss(a,b,x): q=min(1,max(0,(x-a)/(b-a))); return q*q*(3-2*q)
EXP=dict(s1=.12,s2=.10,s3=.35,s4=.15,s5=.10,s6=.15,s7=.15,s8=.30)
def zoomblur(a,amt,n=10):
    h,w=a.shape[:2]; out=a.copy()
    for k in range(1,n):
        s=1+amt*k/n; cw,ch=int(w/s),int(h/s); x0=(w-cw)//2; y0=int((h-ch)*.52); out+=rs(a[y0:y0+ch,x0:x0+cw].copy(),w,h)
    return out/n
def get(S,f): return load(R+'frames/%s/%04d.exr'%(S,f))
os.makedirs(R+'out/png',exist_ok=True); ONLY=A.get('only')
for i,(S,f,n) in enumerate(TL):
    if i%nw!=wk: continue
    if ONLY and S not in ONLY.split(','): continue
    p=R+'out/png/%05d.png'%i
    if os.path.exists(p) and 'force' not in A: continue
    try: a=get(S,f)
    except Exception: continue
    if a.shape[0]!=804: continue
    fade=1.0; kw={}
    if S=='s1': m=ss(18,112,f); b=get('s1b',f); a=b*(1-m)+a*m; fade=ss(-4,34,f)
    if S=='s5' and f>n-36:
        k=(f-(n-36))/36; a=zoomblur(a,.30*k**2); a=a+np.array([1,.9,.78],'f')*9*max(0,(k-.78)/.22)**2
    if S=='s6':
        if f>=n-D: m=ss(0,D,f-(n-D)+.5); a=a*(1-m)+get('s7',f-(n-D))*m
    if S=='s8': fade=1-ss(n-34,n-6,f)
    if S in('s5','s6'): kw['bl']=.10
    save(grade(a,exp=EXP[S],seed=i,fade=fade,**kw),p)
print('worker',wk,'done',len(TL))

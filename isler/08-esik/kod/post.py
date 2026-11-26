# linear EXR -> graded PNG. runs in Blender's python (numpy + OIIO)
import numpy as np, OpenImageIO as oiio, sys, os, glob
from OpenImageIO import ImageBuf, ImageBufAlgo as A, ImageSpec
def load(p):
    b=ImageBuf(p); a=b.get_pixels(oiio.FLOAT)[:,:,:3]; return np.nan_to_num(a,nan=0,posinf=200,neginf=0).clip(0,400)
def rs(a,w,h,f='triangle'):
    b=ImageBuf(np.ascontiguousarray(a,'f')); return A.resize(b,filtername=f,roi=oiio.ROI(0,w,0,h,0,1,0,3)).get_pixels(oiio.FLOAT)
def down(a):
    h,w=a.shape[:2]; h2,w2=h//2*2,w//2*2; a=a[:h2,:w2]
    return (a[::2,::2]+a[1::2,::2]+a[::2,1::2]+a[1::2,1::2])/4
def blur3(a):
    k=(1,4,6,4,1); p=np.pad(a,((2,2),(0,0),(0,0)),'edge'); a=sum(w*p[i:p.shape[0]-4+i] for i,w in enumerate(k))/16
    p=np.pad(a,((0,0),(2,2),(0,0)),'edge'); return sum(w*p[:,i:p.shape[1]-4+i] for i,w in enumerate(k))/16
def bloom(a,n=7,decay=.8):
    h,w=a.shape[:2]; lv=[]; x=a
    for i in range(n):
        x=blur3(down(x)); lv.append(x)
        if min(x.shape[:2])<6: break
    acc=lv[-1]
    for i in range(len(lv)-2,-1,-1):
        acc=lv[i]+decay*blur3(rs(acc,lv[i].shape[1],lv[i].shape[0]))
    s=sum(decay**i for i in range(len(lv))); return rs(acc,w,h)/s
def streak(a,thr=6.0):
    h,w=a.shape[:2]; x=np.clip(a-thr,0,24); x=down(down(x)); l=x.mean(2,keepdims=True)
    k=np.exp(-np.abs(np.arange(-160,161))/38.); k/=k.sum(); k=k.astype('f')
    n=l.shape[1]+320; out=np.fft.irfft(np.fft.rfft(l[:,:,0],n,axis=1)*np.fft.rfft(k,n)[None],n,axis=1)[:,160:160+l.shape[1]]
    out=out[:,:,None]; c=np.repeat(out,3,2)*np.array([.5,.65,1.0],'f')
    return rs(blur3(c),w,h)
# AgX-like (Minimal, Troy Sobotka / B. Wrensch fit)
M=np.array([[0.842479062253094,0.0423282422610123,0.0423756549057051],[0.0784335999999992,0.878468636469772,0.0784336],[0.0792237451477643,0.0791661274605434,0.879142973793104]]).T
Mi=np.linalg.inv(M)
def agx(a,sat=1.2,power=1.15):
    x=np.maximum(a@M.T,1e-10); x=(np.clip(np.log2(x),-12.47393,4.026069)+12.47393)/16.5
    y=15.5*x**6-40.14*x**5+31.96*x**4-6.868*x**3+.4298*x**2+.1191*x-.00232
    y=np.clip(y,0,1)**power; l=(y@np.array([.2126,.7152,.0722]))[...,None]; y=l+sat*(y-l)
    return np.clip(y@Mi.T,0,1)   # display-referred (2.2 encoded)
def grade(a,exp=0,bl=.07,stk=.06,sat=1.32,power=1.46,vig=.28,grain=.009,seed=0,tint=True,ca=.0011,fade=1.0):
    a=a*2**exp; b=bloom(a); a=a*(1-bl)+b*bl+streak(a)*stk
    h,w=a.shape[:2]
    if ca:
        for c,s in((0,1+ca),(2,1-ca)):
            W=int(round(w*s));H=int(round(h*s)); 
            if W!=w:
                t=rs(np.repeat(a[:,:,c:c+1],3,2),w+2*abs(W-w),h+2*abs(H-h)); 
                dy=(t.shape[0]-h)//2;dx=(t.shape[1]-w)//2
                if s>1:a[:,:,c]=t[dy:dy+h,dx:dx+w,0]
    Y,X=np.mgrid[0:h,0:w]; r=np.hypot((X-w/2)/(w/2),(Y-h/2)/(w/2)); a=a*(1-vig*np.clip(r,0,1.2)**2.2)[...,None]
    y=agx(a*fade,sat,power)
    if tint:
        l=y.mean(2,keepdims=True); y=y+(1-l)**3*np.array([-.010,.0,.016])+l**2*np.array([.012,.003,-.014])
    g=np.random.default_rng(seed).normal(0,1,(h,w,1)); g2=blur3(np.repeat(g,1,2)); y=y+(g*.6+g2*.5)*grain*(0.35+.65*(1-y.mean(2,keepdims=True)))
    return np.clip(y,0,1).astype('f')
def save(y,p):
    d=np.random.default_rng(1).uniform(-.5,.5,y.shape)/255
    o=ImageBuf(np.ascontiguousarray(np.clip(y+d,0,1),'f')); o.set_write_format(oiio.UINT8); o.write(p)
if __name__=='__main__':
    a=sys.argv[sys.argv.index('--')+1:]
    kw={k:float(v) for k,v in(x.split('=') for x in a[2:])}
    save(grade(load(a[0]),**kw),a[1])

import numpy as np, wave
SR=48000; T=48.6; N=int(SR*T); rg=np.random.default_rng(2); t=np.arange(N)/SR
L=np.zeros((N,2)); DRY=np.zeros((N,2))
def ss(a,b,x): q=np.clip((x-a)/(b-a),0,1); return q*q*(3-2*q)
def hz(m): return 440*2**((m-69)/12)
def env(a,b,fi,fo,x): return ss(a,a+fi,x)*(1-ss(b-fo,b,x))
def seg(a,b): return max(0,int(a*SR)),min(N,int(b*SR))
def pad(m,a,b,fi,fo,g,bright=1.2,vo=5,vib=.0025,formant=None,swell=None):
    i,j=seg(a,b); x=t[i:j]; e=env(a,b,fi,fo,x)*(swell(x) if swell else 1); f=hz(m); out=np.zeros((j-i,2))
    for v in range(vo):
        d=2**(rg.normal(0,6)/1200); ph=rg.uniform(0,6.28); pan=rg.uniform(.15,.85)
        vi=1+vib*np.sin(2*np.pi*rg.uniform(4.2,5.6)*x+rg.uniform(0,6))*ss(0,1.5,x-a); p=2*np.pi*np.cumsum(f*d*vi)/SR+ph
        s=0; 
        for h in range(1,26):
            fh=f*h
            if fh>9000: break
            w=h**-bright
            if formant is not None: w=h**-.7*sum(A*np.exp(-((fh-F)/B)**2) for F,B,A in formant)
            s=s+w*np.sin(h*p+rg.uniform(0,6.28))
        out+=np.stack([s*np.cos(pan*np.pi/2),s*np.sin(pan*np.pi/2)],-1)/vo**.6
    L[i:j]+=out*e[:,None]*g
AH=[(620,160,1.),(1080,200,.55),(2500,350,.22),(3300,400,.1)]; OO=[(360,130,1.),(760,160,.5),(2400,300,.08)]
def bell(m,a,g,dur=5,pan=.5,ratios=(1,2.0,2.76,5.4,8.93),wet=1):
    i,j=seg(a,a+dur); x=t[i:j]-a; f=hz(m); s=0
    for k,r in enumerate(ratios):
        if f*r>16000: continue
        s=s+np.sin(2*np.pi*f*r*x+k)*np.exp(-x*(1.1+k*1.5)*3/dur)/(k+1)**1.1
    s*=1-np.exp(-x*900); o=np.stack([s*np.cos(pan*np.pi/2),s*np.sin(pan*np.pi/2)],-1)*g; L[i:j]+=o*wet; DRY[i:j]+=o*.35
def boom(a,g,f0=95,f1=31,dur=4):
    i,j=seg(a,a+dur); x=t[i:j]-a; f=f1+(f0-f1)*np.exp(-x*7); s=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*1.3)*(1-np.exp(-x*400)); s=np.tanh(s*1.8)/1.2
    n=rg.normal(0,1,len(x))*np.exp(-x*9); n=np.convolve(n,np.ones(60)/60,'same')*3
    DRY[i:j]+=(s+n*.5)[:,None]*g; L[i:j]+=(s*.25+n*.8)[:,None]*g
def noise(a,b,fc,bw,g,e):
    i,j=seg(a,b); n=j-i; out=[]
    for c in range(2):
        S=np.fft.rfft(rg.normal(0,1,n)); f=np.fft.rfftfreq(n,1/SR); S*=np.exp(-((np.log2(np.maximum(f,1)/fc))/bw)**2); s=np.fft.irfft(S,n); out.append(s/np.std(s))
    o=np.stack(out,-1)*(e(t[i:j]))[:,None]*g; L[i:j]+=o*.4; DRY[i:j]+=o*.6
# cuts
C2,C3,C4,C5,C6,C7,C8=5.5,11.5,16.5,22.0,28.5,34.42,38.42; HIT=C8+20/24
# sea
swl=lambda x:.55+.45*np.sin(2*np.pi*x/5.3)*np.sin(2*np.pi*x/3.1+1)
noise(0,C6,420,1.3,.030,lambda x:env(0,C6,1.5,1.2,x)*swl(x)*(1-.5*env(C3,C4,.4,.4,x))); noise(0,C6,3000,1.0,.010,lambda x:env(0,C6,2,1.0,x)*swl(x-1)*(1-.8*env(C3,C4,.3,.3,x)))
noise(C7,T,420,1.3,.018,lambda x:env(C7,T,1,3,x)*swl(x)); 
for k in range(9): # wood creaks / lapping
    a=rg.uniform(.6,11); bell(rg.choice([38,41,45])+12,a,.010,.5,rg.random(),(1,1.31,1.77,2.4))
# s1-2 drone + slow theme
pad(26,0,C5+.5,4,1,.10,1.5,4); pad(38,.5,C5,4,2,.06,1.3); pad(45,2,C3+1,3,2,.045,1.4)
for m,a,b in((62,2.5,6.2),(65,4.6,8.4),(64,7.0,10.2),(69,8.6,12.2)): pad(m,a,b,1.4,1.6,.030,1.6,4)
pad(57,5.0,C3+.8,2.5,1.5,.04,1.4); pad(53,7.5,C3+.8,2.0,1.5,.04,1.4); pad(69,8.5,C3+.6,2,1,.02,formant=OO)
boom(C2+.1,.28,70,29,5); boom(10.3,.35,80,30); 
# s3 machine wake: pulses, metallic plates
for k in range(40):
    a=C3+k*.125
    if a<C4-.05:
        g=.05+.10*(k/40); i,j=seg(a,a+.5); x=t[i:j]-a; s=np.sin(2*np.pi*hz(38 if k%8<6 else 41)*x+.8*np.sin(2*np.pi*hz(38)*x))*np.exp(-x*13)*(1-np.exp(-x*500)); DRY[i:j]+=(s*g*1.7*(1.35 if k%4==0 else .8))[:,None]
for k in range(70): bell(rg.choice([50,53,57,62,65,69,74])+rg.uniform(-.3,.3),C3+.2+4.9*(k/70)**.85+rg.uniform(0,.05),.010+.016*k/70,1.1,rg.random(),(1,1.58,2.24,2.92,4.17,5.43))
for m in(50,57,62,65): pad(m,C3,C4+.5,3.5,.8,.030,1.05)
noise(C3,C4,1500,1.2,.03,lambda x:ss(C3,C4,x)**2*(1-ss(C4-.1,C4,x))); boom(C3,.55); boom(C4-.02,.40,70,29)
# s4 suspension: drops
for m in(50,57,60,64,69): pad(m,C4-.3,C5+.6,1.5,1.0,.030,1.5)
sc=[74,76,77,81,84,86,88,89,93]
for k in range(64):
    a=C4+.2+5.3*(k/64)**.9; bell(sc[int(min(8,(k/64)*6+rg.integers(0,4)))],a,.020,2.6,rg.random(),(1,2.01,3.02,4.2))
noise(C4,C5,5200,.8,.012,lambda x:ss(C4,C5,x)**1.5*(1-ss(C5-.05,C5,x)))
# s5 climax
boom(C5+.02,.5)
ch=[((46,53,58,62,65,70),C5,23.7),((41,53,57,60,65,69),23.6,25.2),((48,55,60,64,67,72),25.1,26.8),((50,57,62,66,69,74),26.7,28.55)]
for n_,(c,a,b) in enumerate(ch):
    for m in c: pad(m,a-.1,b+.1,.35,.4,.034+.007*n_,.95,5,swell=lambda x,a=a,b=b:.75+.4*ss(a,b,x)); 
    for m in c[2:]: pad(m+12,a-.1,b+.1,.4,.4,.020+.006*n_,formant=AH)
    pad(c[0]-12,a,b,.2,.3,.10,1.2,3); boom(a,.55 if n_ else .4,90,33,2.4)
for k in range(26):
    a=C5+k*.25; 
    if a>25: boom(a,.05+.10*(k/26),120,48,.5)
noise(25.2,C6,900,1.6,.10,lambda x:ss(25.2,C6-.06,x)**2.5*(1-ss(C6-.06,C6-.01,x)))
i,j=seg(25.5,C6-.02); x=(t[i:j]-25.5)/3; f=180*2**(x*3.2); s=np.sin(2*np.pi*np.cumsum(f)/SR)*ss(0,1,x)**2*.05; L[i:j]+=s[:,None]
# s6 cosmos
boom(C6+.03,.85,120,27,6); noise(C6,C6+5,700,1.7,.10,lambda x:np.exp(-(x-C6)*1.1)*ss(C6,C6+.03,x))
for m in(38,50,57,62,66,69,76): pad(m,C6,C7+1.6,.8,2.2,.034,1.25)
for m in(74,78,81): pad(m,C6+.8,C7+.8,2,1.8,.020,formant=AH)
for k in range(30): bell(rg.choice([86,88,90,93,95,98]),C6+.6+rg.uniform(0,5),.010,3.2,rg.random(),(1,2.0,3.01))
# s7 drop: hush
pad(50,C7-.3,HIT,1,.25,.035,1.7); pad(69,C7+.3,HIT-.1,1.6,.3,.018,formant=OO)
for a,m in((C7+1.0,81),(C7+1.9,86),(C7+2.6,85)): bell(m,a,.035,3.5,.5,(1,2.0,3.0))
REL=C7+76/24; i,j=seg(REL,HIT); x=t[i:j]-REL; s=np.sin(2*np.pi*np.cumsum(1500*np.exp(-x*1.3))/SR)*.018*env(REL,HIT,.05,.05,t[i:j]); L[i:j]+=s[:,None]
# impact + bloom
boom(HIT,.95,150,28,6); i,j=seg(HIT,HIT+.35); x=t[i:j]-HIT; s=np.sin(2*np.pi*np.cumsum(380+1900*(x/.35)**2)/SR)*np.exp(-x*11)*.22; DRY[i:j]+=s[:,None]; L[i:j]+=s[:,None]
bell(74,HIT,.09,7,.45,(1,2.0,3.0,4.1)); bell(86,HIT+.05,.05,6,.6); noise(HIT,HIT+3,2500,1.2,.05,lambda x:np.exp(-(x-HIT)*2.5))
for m,d in((38,.2),(45,.4),(50,.5),(57,.8),(62,1.1),(66,1.4),(69,1.8),(73,2.4),(76,3.0),(81,3.6)): pad(m,HIT+d*.8,T,2.0,4.0,.042,1.3)
for m in(74,78,81): pad(m,HIT+2.2,T,2,3.6,.022,formant=AH)
for a,m in((42.2,86),(43.0,85),(43.8,81),(44.6,78),(45.6,74)): bell(m,a,.040,4,.5,(1,2.0,3.0))
# reverb
R=int(4.8*SR); x=np.arange(R)/SR; ir=np.stack([rg.normal(0,1,R)*np.exp(-x*1.45)*(1-np.exp(-x*60)) for _ in(0,1)],-1)
for c in(0,1):
    S=np.fft.rfft(ir[:,c]); f=np.fft.rfftfreq(R,1/SR); S*=1/(1+(f/4200)**2)*(f/(f+140)); ir[:,c]=np.fft.irfft(S,R)
ir/=np.sqrt((ir**2).sum(0)); M=N+R; wet=np.stack([np.fft.irfft(np.fft.rfft(L[:,c],M)*np.fft.rfft(ir[:,c],M),M)[:N] for c in(0,1)],-1)
mix=L*.55+wet*.50+DRY; mix*=(1-ss(T-2.6,T-.1,t))[:,None]
S=np.fft.rfft(mix,axis=0); f=np.fft.rfftfreq(N,1/SR); mix=np.fft.irfft(S*(f/(f+24))[:,None],N,axis=0)
mix/=np.percentile(np.abs(mix),99.9); mix=np.tanh(mix*.95); mix*=.89/np.abs(mix).max()
w=wave.open('esik-film/audio/score.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype('<i2').tobytes()); w.close()
for a in range(0,48,3): s=mix[int(a*SR):int((a+3)*SR)]; print(a,'rms %.1f dB peak %.2f'%(20*np.log10(np.sqrt((s**2).mean())+1e-9),np.abs(s).max()))

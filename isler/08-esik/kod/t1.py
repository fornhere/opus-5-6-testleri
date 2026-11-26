import sys; sys.path.insert(0,'esik-film/src')
from sea import *
import time
A=args(); s=reset(samples=int(A.get('spp',48)),scale=int(A.get('scale',50)))
sky(); W=water_mat(); oc,md=ocean(W,t=3.0); R=Ring(); B,pl,fm=boat()
print('plates',R.N)
c=camera(28)
v=A.get('v','wide')
if v=='wide': aim(c,(3.5,-16,2.6),(0,400,62)); c.data.lens=24
if v=='boat': aim(c,(3.4,-5.2,1.5),(-.2,4,1.6)); c.data.lens=32
if v=='ring': aim(c,(-330,1250,180),(-300,1500,300)); c.data.lens=35; R.coreval.node.outputs[0].default_value=14; R.update(0,lambda th,rn: np.exp(-((np.angle(np.exp(1j*(th-2.35)))/.28)**2)))
t0=time.time(); render(ROOT+'/test/%s.exr'%v); print('TIME',time.time()-t0)

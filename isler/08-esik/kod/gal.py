import numpy as np
def splat(buf,x,y,col):
    h,w=buf.shape[:2]; x0=np.floor(x-.5).astype('i4'); y0=np.floor(y-.5).astype('i4'); fx=x-.5-x0; fy=y-.5-y0
    for dx,dy,ww in((0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),(0,1,(1-fx)*fy),(1,1,fx*fy)):
        X=x0+dx;Y=y0+dy; m=(X>=0)&(X<w)&(Y>=0)&(Y<h); id_=Y[m]*w+X[m]
        for c in range(3): buf[:,:,c]+=np.bincount(id_,weights=col[m,c]*ww[m],minlength=w*h).reshape(h,w)

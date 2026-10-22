import numpy as np, json
import voi2
def evpi(N,M=2.92,D=8,mu0=1.0,sd0=0.5,U=3,class_band=0.03):
    acts,outc,feas=voi2.make(N,M,D,class_band=class_band)
    bq=np.linspace(max(0,mu0-3.5*sd0),mu0+3.5*sd0,41); w=np.exp(-0.5*((bq-mu0)/sd0)**2); w/=w.sum()
    best=[];bestact=[]
    for b in bq:
        o=outc(b); f=feas(o); v=np.where(f,o[:,0],-np.inf); j=int(np.argmax(v)); best.append(v[j]); bestact.append(acts[j].tolist())
    return dict(N=N,class_band=class_band,EVPI_U=round(U*float(w@np.array(best))), act_at_mu=bestact[20], act_lo=bestact[8], act_hi=bestact[32])
for cb in [0.03,0.10,1.0]:
    for N in [600,4000]:
        print(json.dumps(evpi(N,class_band=cb)))

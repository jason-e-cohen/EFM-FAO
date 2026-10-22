import numpy as np, json, itertools
from math import sqrt
Z10=1.2816
def expit(x): return 1/(1+np.exp(-x))
def logit(p): return np.log(p/(1-p))
# Richmond-calibrated two-band pool (position above / below the school's enrolled median)
BANDS=dict(H=dict(share=.5,p=.15,NT=15700.), L=dict(share=.5,p=.27,NT=30700.))
P0=sum(b['share']*b['p'] for b in BANDS.values())
def se_slope(n_test,p,D,f=0.92,all_elig=True):
    return f*sqrt(p*(1-p))/(0.4472*D*sqrt(n_test))*100*(0.756 if all_elig else 1)
def make(N,M,D,cut=3,class_band=0.03):
    acts=np.array(list(itertools.product(range(-cut,D+1),repeat=2)),float)
    def outcomes(beta):
        out=[]
        for aH,aL in acts:
            enr={};rev=0
            for k,a in (('H',aH),('L',aL)):
                b=BANDS[k]; bl=beta/(100*b['p']*(1-b['p']))  # same AME per $1k at SQ in every band (one slope in pp terms)
                pa=expit(logit(b['p'])+bl*a); n=N*b['share']
                enr[k]=n*pa; rev+=M*n*(pa*(b['NT']-1000*a)-b['p']*b['NT'])
            out.append((rev,enr['H'],enr['H']+enr['L']))
        return np.array(out)
    sq_c=N*P0; sq_H=N*BANDS['H']['share']*BANDS['H']['p']
    def feasible(o): return (np.abs(o[:,2]/sq_c-1)<=class_band)&(o[:,1]>=sq_H-1e-9)&(o[:,0]>=-1e-6)
    return acts,outcomes,feasible
def voi(N,M=2.92,D=8,K=2,U=3,mu0=1.0,sd0=0.5,F=25000.,share=.4,class_band=0.03,pts=41):
    acts,outc,feas=make(N,M,D,class_band=class_band)
    bq=np.linspace(max(0.0,mu0-3.5*sd0),mu0+3.5*sd0,pts); w=np.exp(-0.5*((bq-mu0)/sd0)**2); w/=w.sum()
    cache={}
    def O(beta):
        k=round(float(beta),3)
        if k not in cache: cache[k]=outc(max(beta,0.0))
        return cache[k]
    Rm=np.array([O(b)[:,0] for b in bq])
    def choose(m,s):
        lo,hi=max(0,m-Z10*s),m+Z10*s
        ok=feas(O(lo))&feas(O(hi))&feas(O(m))
        wq=np.exp(-0.5*((bq-m)/s)**2); wq/=wq.sum(); ev=wq@Rm
        ev=np.where(ok,ev,-np.inf); j=int(np.argmax(ev)); return j
    j0=choose(mu0,sd0); V0=w@Rm[:,j0]
    se=se_slope(share*N*K,P0,D); ps=1/sqrt(1/sd0**2+1/se**2)
    zs=np.linspace(-3.5,3.5,pts); zw=np.exp(-0.5*zs**2); zw/=zw.sum(); V1=0; moved=0
    for i,b in enumerate(bq):
        for z,wz in zip(zs,zw):
            bh=b+z*se; m1=ps**2*(mu0/sd0**2+bh/se**2); m1=round(m1/0.025)*0.025
            j=choose(m1,ps); V1+=w[i]*wz*Rm[i,j]; moved+=w[i]*wz*(j!=j0)
    EVSI=U*(V1-V0)
    def tcost(beta):
        tot=0
        for k,b in BANDS.items():
            bl=beta/(100*b['p']*(1-b['p']))
            for dose,sd in [(0,.4),(D/2,.2),(D,.4)]:
                pa=expit(logit(b['p'])+bl*dose); tot+=b['share']*sd*(pa*(b['NT']-1000*dose)-b['p']*b['NT'])
        return -M*share*N*K*tot
    lo=max(0,mu0-Z10*sd0)
    C_lo=tcost(lo); C0=tcost(0)
    extra_enr=share*N*K*sum(b['share']*(sum(sd*expit(logit(b['p'])+(lo/(100*b['p']*(1-b['p'])))*dose) for dose,sd in [(0,.4),(D/2,.2),(D,.4)])-b['p']) for b in BANDS.values())
    return dict(N=N,D=D,K=K,se=round(se,2),mde=round(2.8*se,2),post_sd=round(ps,2),a0=acts[j0].tolist(),EVSI=round(EVSI),cost_at_p10=round(C_lo),cost_at_zero=round(C0),ops=F*K,
                net=round(EVSI-C_lo-F*K),ratio=round(EVSI/(C_lo+F*K),2),p_action_changes=round(moved,2),cohort_NTR=round(M*N*sum(b['share']*b['p']*b['NT'] for b in BANDS.values())),
                class_sq=round(N*P0,1))
if __name__=='__main__':
    import sys
    for N in [600,1000,2000,4000]:
        for D in [4,8]:
            for K in [1,2]:
                print(json.dumps(voi(N,D=D,K=K)),flush=True)

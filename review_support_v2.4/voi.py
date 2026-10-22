import numpy as np, json
from math import sqrt
Z10=1.2816
def expit(x): return 1/(1+np.exp(-x))
def logit(p): return np.log(p/(1-p))
def se_slope(n_test, p, D, f=0.92, all_elig=True):
    se=f*sqrt(p*(1-p))/(0.4472*D*sqrt(n_test))*100   # pp per $1k
    return se*(0.756 if all_elig else 1.0)
def voi(N, p=0.21, NT=26000., M=2.92, D=8., share=0.4, K=2, U=3, mu0=1.0, sd0=0.5, F=25000., cut=3, f=0.92, prior_pts=81, obs_pts=81, verbose=False):
    a=np.arange(-cut, int(D)+1, 1.0)                      # $k change, support-bounded
    bq=np.linspace(max(0,mu0-4*sd0), mu0+4*sd0, prior_pts)
    w=np.exp(-0.5*((bq-mu0)/sd0)**2); w/=w.sum()
    def R(av,beta):   # per-cohort multi-year revenue change vs status quo, for N admits
        b=beta/(100*p*(1-p))
        pa=expit(logit(p)+b*av)
        return M*N*(pa*(NT-1000*av)-p*NT)
    Rm=np.array([[R(x,bb) for x in a] for bb in bq])     # [beta, a]
    def choose(mean, sd):
        # max posterior expected gain subject to gain>=0 at posterior p10 and p90 (two-sided rule)
        wq=np.exp(-0.5*((bq-mean)/sd)**2); wq/=wq.sum()
        ev=wq@Rm
        lo,hi=max(0,mean-Z10*sd), mean+Z10*sd
        ok=np.array([(R(x,lo)>=-1e-6) and (R(x,hi)>=-1e-6) for x in a])
        ev=np.where(ok,ev,-np.inf); return int(np.argmax(ev))
    j0=choose(mu0,sd0); V0=w@Rm[:,j0]
    n_test=share*N*K
    se=se_slope(n_test,p,D,f)
    post_sd=1/sqrt(1/sd0**2+1/se**2)
    # preposterior: for each true beta, beta_hat ~ N(beta,se)
    zs=np.linspace(-4,4,obs_pts); zw=np.exp(-0.5*zs**2); zw/=zw.sum()
    V1=0.0; acts={}
    for i,bb in enumerate(bq):
        for z,wz in zip(zs,zw):
            bh=bb+z*se
            m1=post_sd**2*(mu0/sd0**2+bh/se**2)
            j=choose(m1,post_sd); V1+=w[i]*wz*Rm[i,j]; acts[a[j]]=acts.get(a[j],0)+w[i]*wz
    EVSI=U*(V1-V0)
    # test cost: bonuses to test students over K cycles, net of induced revenue, at prior mean
    def test_cost(beta):
        b=beta/(100*p*(1-p)); tot=0
        for dose,share_d in [(0,.4),(D/2,.2),(D,.4)]:
            pa=expit(logit(p)+b*dose); tot+=share_d*(pa*(NT-1000*dose)-p*NT)
        return -M*share*N*K*tot
    C=float(w@np.array([test_cost(bb) for bb in bq]))
    C0=test_cost(0.0)
    net=EVSI-C-F*K
    mde=2.8*se
    beta_star=100*1000*p/(NT-1000*D/2)
    return dict(N=N,n_test_total=round(n_test),se=round(se,2),mde=round(mde,2),post_sd=round(post_sd,2),a0=a[j0],EVSI=round(EVSI),test_cost_expected=round(C),test_cost_at_zero=round(C0),ops=F*K,net=round(net),ratio=round(EVSI/(C+F*K),2) if C+F*K>0 else None,
                beta_star=round(beta_star,2), annual_cohort_NTR=round(M*N*p*NT), act_dist={float(k):round(v,2) for k,v in sorted(acts.items()) if v>0.01})
if __name__=='__main__':
    out=[]
    for N in [600,1000,2000,4000]:
        for D in [4,8]:
            for K in [1,2]:
                r=voi(N,D=D,K=K); r.update(D=D,K=K); out.append(r); print(json.dumps(r))

import sys, json, numpy as np, pandas as pd, yaml
W='/tmp/work'
sys.path.insert(0,W+'/stub'); sys.path.insert(0,W+'/repo/src'); sys.path.insert(0,W)
from efa_fao.pipeline import prepare as prep, models as M, optimize as O
import lagr
from efa_fao.pipeline import validate as V
V.solve=lagr.solve
from efa_fao.run_pipeline import fit_models
cfg=yaml.safe_load(open(W+'/repo/config/institution.yaml'))
O.DEFAULT_MAX_CUT_K=cfg['aid_policy']['max_cut_per_student_k']; cap=cfg['aid_policy']['max_total_institutional_discount']
tabs=prep.load_tables(W+'/repo/data/synthetic'); tabs,qa=prep.validate_and_clean(tabs,cfg)
adm=prep.build_admit_frame(tabs,cfg)
train=adm[(adm.cohort<2026)&adm.enrolled.notna()].reset_index(drop=True); ho=adm[adm.cohort==2026].reset_index(drop=True)
fb=fit_models(train); A=fb['anchor']
ret=M.fit_retention(train[train.enrolled==1]); persist=O.persistence_factor(M.predict_retention(ret,ho),4)
truth=pd.read_csv(W+'/repo/data/synthetic/truth_admits.csv').set_index('student_key'); b0=json.load(open(W+'/repo/data/synthetic/world_meta.json'))['b0']
ma0=fit_models(train,fb,A,kappa=0.0)['ma']; hy0=M.HybridModel(fb['mo'],ma0)
fn_t=V.truth_fn_factory(truth,ho,b0)
sq=ho.disc_k.to_numpy(float)
class Scaled:
    def __init__(s,h,f): s.h=h; s.f=f
    def predict_p(s,df,disc_k=None):
        p0=np.clip(s.h.obs.predict_p(df),1e-6,1-1e-6)
        if disc_k is None: return p0
        delta=np.asarray(disc_k,float)-df.disc_k.to_numpy(float)
        return 1/(1+np.exp(-(np.log(p0/(1-p0))+s.f*s.h.anc._s_eff(df)*delta)))
import os
mid=float(os.environ.get('MID',A['ame']))/ (1.0 if 'MID' not in os.environ else 100.0)
def fn_at(beta): return Scaled(hy0,beta/A['ame']).predict_p
fn=fn_at(mid)
budget=float(os.environ.get('BF','1.0'))*O.evaluate(fn,ho,sq,persist)['discretionary_spend']   # production: budget = model-predicted status-quo spend at the middle slope
print('anchor pp',100*mid,'budget',budget)
# curves at a slope grid
def curves(beta): return O.build_curves(fn_at(beta),ho,persist,cap)
idx=np.arange(len(ho)); L=O.LEVELS_K
def ev(c,d):
    ch=np.clip(np.round(d).astype(int),0,12); return dict(ntr=c['ntr'][idx,ch].sum(), spend=c['spend'][idx,ch].sum(), enr=c['P'][idx,ch].sum())
SQ={}
def evsq(beta):
    k=round(beta,6)
    if k not in SQ: SQ[k]=O.evaluate(fn_at(beta),ho,sq,persist)
    return SQ[k]
def gain(beta,d):
    c=curves(beta); return ev(c,d)['ntr']-evsq(beta)['ntr_multi_year']
# one-sided / unconstrained mid-optimal allocation at the production budget
cM=curves(mid); dM,_=lagr.solve(cM,budget=budget)
print('mid-optimal: pred gain at mid',gain(mid,dM),'spend',ev(cM,dM)['spend'])
print('gain curve of mid-optimal allocation:')
for b in [0,0.2,0.4,0.6,0.8,1.0,1.138,1.4,1.7,2.0,2.5,3.0]:
    print(f'  beta={100*b/100:.3f}pp gain={gain(b*0.01,dM):,.0f}')
# two-sided solve: maximize ntr_M - lam*spend_H + muL*gain_L + muH*gain_H via multiplier search
def solve2(se, two_sided=True, budget_at='H'):
    lo=max(0.0,mid-1.2816*se); hi=mid+1.2816*se
    cL,cH=curves(lo),curves(hi)
    base={'L':evsq(lo)['ntr_multi_year'],'H':evsq(hi)['ntr_multi_year']}
    cB=cH if budget_at=='H' else cM
    def pick(lam,muL,muH):
        sc=np.where(cM['allowed'], cM['ntr']-lam*cB['spend']+muL*cL['ntr']+muH*cH['ntr'], -1e18)
        return L[sc.argmax(1)].astype(float)
    def feas(d):
        gL=ev(cL,d)['ntr']-base['L']; gH=ev(cH,d)['ntr']-base['H']; sp=ev(cB,d)['spend']
        return gL,gH,sp
    # outer search on mu's (subgradient), inner bisection on lam for budget
    muL=muH=0.0
    for it in range(60):
        lo_,hi_=0.0,1.0
        while ev(cB,pick(hi_,muL,muH))['spend']>budget: hi_*=2
        for _ in range(50):
            m=0.5*(lo_+hi_)
            if ev(cB,pick(m,muL,muH))['spend']>budget: lo_=m
            else: hi_=m
        d=pick(hi_,muL,muH); gL,gH,sp=feas(d)
        okL=gL>=-1; okH=(gH>=-1) or not two_sided
        if okL and okH: break
        step=0.05*(1+it/10)
        if gL<0: muL+=step
        if two_sided and gH<0: muH+=step
    return d, dict(se=se,lo=100*lo,hi=100*hi,muL=muL,muH=muH,gain_M=gain(mid,d),gain_L=gL,gain_H=gH,spend=sp,iters=it)
gM_full=gain(mid,dM)
for se in [float(x) for x in os.environ.get('SES','0.30,0.46,0.70').split(',')]:
    se_=se/100
    d1,r1=solve2(se_,two_sided=False); d2,r2=solve2(se_,two_sided=True)
    print(json.dumps(dict(se_pp=se, one_sided=r1, two_sided=r2, retained_two_vs_one=r2['gain_M']/max(r1['gain_M'],1e-9), retained_two_vs_uncon=r2['gain_M']/gM_full, share_changed_one=float((d1!=sq).mean()), share_changed_two=float((d2!=sq).mean()), realized_two=O.evaluate(fn_t,ho,d2,persist)['ntr_multi_year']-O.evaluate(fn_t,ho,sq,persist)['ntr_multi_year'], realized_one=O.evaluate(fn_t,ho,d1,persist)['ntr_multi_year']-O.evaluate(fn_t,ho,sq,persist)['ntr_multi_year']),default=float))

import sys, json, numpy as np, pandas as pd, yaml, time
sys.path.insert(0,'/tmp/work/stub'); sys.path.insert(0,'/tmp/work/repo/src'); sys.path.insert(0,'/tmp/work')
from efa_fao.pipeline import prepare as prep, models as M, optimize as O
import lagr
from efa_fao.pipeline import validate as V
V.solve=lagr.solve
from efa_fao.run_pipeline import fit_models
t0=time.time()
cfg=yaml.safe_load(open('/tmp/work/repo/config/institution.yaml'))
O.DEFAULT_MAX_CUT_K=cfg['aid_policy']['max_cut_per_student_k']; cap=cfg['aid_policy']['max_total_institutional_discount']
tabs=prep.load_tables('/tmp/work/repo/data/synthetic'); tabs,qa=prep.validate_and_clean(tabs,cfg)
adm=prep.build_admit_frame(tabs,cfg)
train=adm[(adm.cohort<2026)&adm.enrolled.notna()].reset_index(drop=True); ho=adm[adm.cohort==2026].reset_index(drop=True)
print('test n in train', int(train.in_price_test.sum()), sorted(train[train.in_price_test==1].cohort.unique()))
fb=fit_models(train); A=fb['anchor']
ret=M.fit_retention(train[train.enrolled==1]); persist=O.persistence_factor(M.predict_retention(ret,ho),4)
truth=pd.read_csv('/tmp/work/repo/data/synthetic/truth_admits.csv').set_index('student_key'); b0=json.load(open('/tmp/work/repo/data/synthetic/world_meta.json'))['b0']
ma0=fit_models(train,fb,A,kappa=0.0)['ma']; hy0=M.HybridModel(fb['mo'],ma0)
fn_t=V.truth_fn_factory(truth,ho,b0)
sq=ho.disc_k.to_numpy(float); target=O.evaluate(fn_t,ho,sq,persist)['discretionary_spend']
fn=lambda p_,dk: hy0.predict_p(p_,dk)
base_b=O.evaluate(fn,ho,sq,persist)['discretionary_spend']
d,bud=V.match_true_spend(fn,fn_t,ho,persist,cap,target,base_b)
print('anchor',A['ame'],A['se'],'lam',ma0.lam,'sbar',ma0.sbar)
class Scaled:
    def __init__(s,h,f): s.h=h; s.f=f
    def predict_p(s,df,disc_k=None):
        p0=np.clip(s.h.obs.predict_p(df),1e-6,1-1e-6)
        if disc_k is None: return p0
        delta=np.asarray(disc_k,float)-df.disc_k.to_numpy(float)
        return 1/(1+np.exp(-(np.log(p0/(1-p0))+s.f*s.h.anc._s_eff(df)*delta)))
mid=A['ame']; se=A['se']
res={}
for name,q in [('p10',mid-1.2816*se),('p50',mid),('p90',mid+1.2816*se),('truth_level',0.01488)]:
    f=q/mid; m=Scaled(hy0,f)
    g=O.evaluate(m.predict_p,ho,d,persist); s0=O.evaluate(m.predict_p,ho,sq,persist)
    res[name]=dict(beta_pp=100*q, pred_gain=g['ntr_multi_year']-s0['ntr_multi_year'], pred_spend=g['discretionary_spend'], sq_spend=s0['discretionary_spend'], pred_enr=g['expected_enrolled']-s0['expected_enrolled'])
tr=O.evaluate(fn_t,ho,d,persist); ts=O.evaluate(fn_t,ho,sq,persist)
res['realized']=dict(gain=tr['ntr_multi_year']-ts['ntr_multi_year'], spend=tr['discretionary_spend'], sq_spend=ts['discretionary_spend'], enr=tr['expected_enrolled']-ts['expected_enrolled'])
# calibration: model mean p at sq vs truth
res['calib']=dict(model_sq_enr=O.evaluate(fn,ho,sq,persist)['expected_enrolled'], true_sq_enr=ts['expected_enrolled'])
# budget: what if budget set on model-predicted spend = model sq spend (no oracle matching)
cur=O.build_curves(fn,ho,persist,cap); d2,_=O.solve(cur,budget=base_b,objective='ntr')
t2=O.evaluate(fn_t,ho,d2,persist); m2=O.evaluate(fn,ho,d2,persist)
res['model_budget']=dict(model_spend=m2['discretionary_spend'], true_spend=t2['discretionary_spend'], true_sq_spend=ts['discretionary_spend'], realized_gain=t2['ntr_multi_year']-ts['ntr_multi_year'], pred_gain=m2['ntr_multi_year']-O.evaluate(fn,ho,sq,persist)['ntr_multi_year'])
# allocation shape
res['alloc']=dict(mean_sq=float(sq.mean()), mean_new=float(d.mean()), share_up=float((d>sq).mean()), share_down=float((d<sq).mean()), n=len(d))
# where error comes: per-student predicted vs true change
pm=fn(ho,d)-fn(ho,sq); pt_=fn_t(ho,d)-fn_t(ho,sq)
res['dp']=dict(pred_dEnroll=float(pm.sum()), true_dEnroll=float(pt_.sum()))
print(json.dumps(res,indent=1,default=float)); print('sec',time.time()-t0)
pd.to_pickle(dict(d=d,sq=sq),'/tmp/work/bt_alloc.pkl')

import sys, json, numpy as np, pandas as pd
sys.path.insert(0,'/tmp/work/stub'); sys.path.insert(0,'/tmp/work/repo/src')
from efa_fao.synth import world
from efa_fao.pipeline.models import fit_logit
t=pd.read_csv('/tmp/work/repo/data/synthetic/truth_admits.csv')
pt=pd.read_csv('/tmp/work/repo/data/synthetic/price_test.csv')
b0=json.load(open('/tmp/work/repo/data/synthetic/world_meta.json'))['b0']
t=t.merge(pt[['student_key','offset_usd']],on='student_key',how='left'); t['offset_usd']=t.offset_usd.fillna(0)
e=t[(t.athlete==0)&(t.student_type=='First-time freshman')&t.cohort.between(2023,2025)].reset_index(drop=True)
base_gift=(e.nondisc_gift_known+e.inst_discretionary-e.offset_usd).to_numpy()
n=len(e); rng=np.random.default_rng(1)
# covariates (observable proxies): need via fafsa & first_gen, residency, gpa band, campus_visit, engagement
X0=np.column_stack([np.ones(n), e.first_gen, e.campus_visit, np.minimum(e.engagement_touches,8), e.fafsa_filed.fillna(0),
    (e.residency=='Out-of-state'), (e.residency=='International'), e.gpa_true, (e.app_lead_days>150)]).astype(float)
def ame_est(Xb, dose_k, y):
    X=np.column_stack([Xb,dose_k]); f=fit_logit(X,y); b=f['beta'][-1]; eta=X@f['beta']
    return float((1/(1+np.exp(-eta))-1/(1+np.exp(-(eta-b)))).mean())
def run(design, reps=300, analyse_all=False, D=4.0):
    out=[]; true=[]
    for r in range(reps):
        test=rng.random(n)<0.4
        if design=='uniform5': dose=rng.choice([0,1,2,3,4],size=n)*D/4
        elif design=='402040': dose=rng.choice([0,D/2,D],size=n,p=[.4,.2,.4])
        elif design=='two_arm': dose=rng.choice([0,D],size=n,p=[.5,.5])
        dose=np.where(test,dose,0.0)
        p=world.p_enroll(e,b0,base_gift+dose*1000); y=(rng.random(n)<p).astype(float)
        m=np.ones(n,bool) if analyse_all else test
        out.append(ame_est(X0[m],dose[m],y[m]))
    a=np.array(out)*100
    return dict(mean=a.mean(), sd=a.std(ddof=1))
tr=100*(world.p_enroll(e,b0,base_gift+1000)-world.p_enroll(e,b0,base_gift)).mean()
res={'truth_ame_pp':tr,'n_elig':n,'mean_p':float(world.p_enroll(e,b0,base_gift).mean())}
for k,(d,a) in {'uniform5_testonly':('uniform5',False),'402040_testonly':('402040',False),'402040_all_eligible':('402040',True),'two_arm_testonly':('two_arm',False)}.items():
    res[k]=run(d,analyse_all=a); print(k,res[k],flush=True)
print(json.dumps(res,indent=1,default=float))

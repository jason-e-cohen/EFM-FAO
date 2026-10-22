import sys, json, numpy as np, pandas as pd
W='/tmp/work'
sys.path.insert(0,W+'/stub'); sys.path.insert(0,W+'/repo/src')
from efa_fao.synth import world
from efa_fao.pipeline.models import fit_logit
t=pd.read_csv(W+'/repo/data/synthetic/truth_admits.csv'); pt=pd.read_csv(W+'/repo/data/synthetic/price_test.csv')
b0=json.load(open(W+'/repo/data/synthetic/world_meta.json'))['b0']
t=t.merge(pt[['student_key','offset_usd']],on='student_key',how='left'); t['offset_usd']=t.offset_usd.fillna(0)
e=t[(t.athlete==0)&(t.student_type=='First-time freshman')&t.cohort.between(2023,2025)].reset_index(drop=True)
base_gift=(e.nondisc_gift_known+e.inst_discretionary-e.offset_usd).to_numpy()
n=len(e); rng=np.random.default_rng(1)
X0=np.column_stack([np.ones(n), e.first_gen, e.campus_visit, np.minimum(e.engagement_touches,8), e.fafsa_filed.fillna(0),
    (e.residency=='Out-of-state'), (e.residency=='International'), e.gpa_true, (e.app_lead_days>150)]).astype(float)
def fit(Xb,dose,y):
    X=np.column_stack([Xb,dose]); f=fit_logit(X,y); b=f['beta'][-1]; eta=X@f['beta']; eta0=eta-b*dose
    ame_recv=float((1/(1+np.exp(-eta))-1/(1+np.exp(-(eta-b)))).mean())      # at received dose (review's desim)
    ame_sq=float((1/(1+np.exp(-(eta0+b)))-1/(1+np.exp(-eta0))).mean())      # at status-quo awards (dose 0)
    return ame_recv, ame_sq, float(b)
def run(design, reps=300, analyse_all=False, D=4.0, status_effect=0.0):
    rr=[]; rs=[]; bb=[]
    for r in range(reps):
        test=rng.random(n)<0.4
        if design=='402040': dose=rng.choice([0,D/2,D],size=n,p=[.4,.2,.4])
        elif design=='two_arm': dose=rng.choice([0,D],size=n,p=[.5,.5])
        else: dose=rng.choice([0,1,2,3,4],size=n)*D/4
        dose=np.where(test,dose,0.0)
        p=world.p_enroll(e,b0,base_gift+dose*1000)
        if status_effect: p=1/(1+np.exp(-(np.log(p/(1-p))+status_effect*test)))   # staff treat test-cohort admits differently
        y=(rng.random(n)<p).astype(float)
        m=np.ones(n,bool) if analyse_all else test
        a,s,b=fit(X0[m],dose[m],y[m]); rr.append(a); rs.append(s); bb.append(b)
    rr=100*np.array(rr); rs=100*np.array(rs)
    return dict(ame_received=dict(mean=rr.mean(),sd=rr.std(ddof=1)), ame_sq=dict(mean=rs.mean(),sd=rs.std(ddof=1)), logit_b=dict(mean=np.mean(bb),sd=np.std(bb,ddof=1)))
tr=100*(world.p_enroll(e,b0,base_gift+1000)-world.p_enroll(e,b0,base_gift)).mean()
print('truth AME at SQ', tr, 'n', n)
for k,(d,a,se) in {'402040_testonly':('402040',False,0),'402040_all':('402040',True,0),'two_arm_testonly':('two_arm',False,0),'uniform5_testonly':('uniform5',False,0),
                   '402040_all_status+0.10':('402040',True,0.10),'402040_testonly_status+0.10':('402040',False,0.10),'402040_all_status-0.10':('402040',True,-0.10)}.items():
    print(k, json.dumps(run(d,analyse_all=a,status_effect=se),default=float), flush=True)

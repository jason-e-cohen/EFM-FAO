import sys, json, numpy as np, pandas as pd
sys.path.insert(0,'/tmp/work/stub'); sys.path.insert(0,'/tmp/work/repo/src')
from efa_fao.synth import world
t=pd.read_csv('/tmp/work/repo/data/synthetic/truth_admits.csv')
pt=pd.read_csv('/tmp/work/repo/data/synthetic/price_test.csv')
b0=json.load(open('/tmp/work/repo/data/synthetic/world_meta.json'))['b0']
t=t.merge(pt[['student_key','offset_usd']],on='student_key',how='left'); t['offset_usd']=t.offset_usd.fillna(0)
e=t[(t.athlete==0)&(t.student_type=='First-time freshman')&t.cohort.between(2023,2025)]
te=e[e.in_price_test==1]
g=te.nondisc_gift_known+te.inst_discretionary
print('stored truth test', 100*te.true_ame_per_1k.mean(), 'recomputed at offset gifts', 100*(world.p_enroll(te,b0,g+1000)-world.p_enroll(te,b0,g)).mean())
g0=g-te.offset_usd
print('test at base gifts', 100*(world.p_enroll(te,b0,g0+1000)-world.p_enroll(te,b0,g0)).mean())
print('mean p test at offset', world.p_enroll(te,b0,g).mean(), 'enrolled col?' )

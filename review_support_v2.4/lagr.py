import numpy as np
from efa_fao.pipeline import optimize as O
def solve(curves, budget=None, objective="ntr", min_enroll=None, time_limit=60):
    P, spend, allowed = curves["P"], curves["spend"], curves["allowed"]
    val = curves["ntr"] if objective == "ntr" else P
    NEG=-1e18
    def pick(lam, mu=0.0):
        sc = np.where(allowed, val - lam*spend + mu*P, NEG)
        return sc.argmax(axis=1)
    idx=np.arange(P.shape[0])
    def sp(ch): return spend[idx,ch].sum()
    ch=pick(0.0)
    if budget is None or sp(ch)<=budget: return O.LEVELS_K[ch].astype(float), {"status":0}
    lo,hi=0.0,1.0
    while sp(pick(hi))>budget: hi*=2
    for _ in range(60):
        m=0.5*(lo+hi)
        if sp(pick(m))>budget: lo=m
        else: hi=m
    ch=pick(hi)
    return O.LEVELS_K[ch].astype(float), {"status":0}
O.solve=solve

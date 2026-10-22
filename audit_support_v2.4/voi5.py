"""Generalized value-of-information engine for the audit (Task 1).
Extends review_support_v2.4/voi2.py to: K position bands, one-logit-slope or one-pp-slope response,
class bands, median/position targets, priors, one-year bonus cost, capped vs uncapped cost models.
Synthetic/public inputs only."""
import numpy as np, itertools, json
from math import sqrt
Z10 = 1.2816

def expit(x): return 1/(1+np.exp(-x))
def logit(p): return np.log(p/(1-p))

# ---------- pools ----------
# share = share of eligible admits; p = status-quo yield; NT = net tuition per enrollee at status quo (year-1 $);
# up = max award increase ($k) before hitting tuition (stipends excluded); cut = max cut ($k) (guardrail 5% of $57,700 = 2.9k -> 2)
POOL2 = dict(name='2-band (review)', bands=[dict(share=.5, p=.15, NT=15700., up=99, cut=3), dict(share=.5, p=.27, NT=30700., up=99, cut=3)], above=[0])
# Richmond-calibrated 5 bands by enrolled position (<25, 25-50, 50-75, 75-85, >=85). Enrolled shares .25/.25/.25/.10/.15;
# yields fall with position; admit shares = enrolled share / yield (admits sit above matriculants); mean admit yield 0.207.
_p5 = np.array([.35, .28, .21, .15, .11]); _e5 = np.array([.25, .25, .25, .10, .15]); _a5 = _e5/_p5; _a5 /= _a5.sum()
_NT5 = np.array([54700., 36000., 15000., 1500., 0.])      # 2025-26 tuition 57,700 less comonotone grant from the 2024-25 509 distribution
_up5 = np.array([99, 99, 15, 1, 0]); _cut5 = np.array([2, 2, 2, 2, 2])
POOL5 = dict(name='5-band Richmond', bands=[dict(share=float(a), p=float(p), NT=float(n), up=int(u), cut=int(c)) for a, p, n, u, c in zip(_a5, _p5, _NT5, _up5, _cut5)], above=[2, 3, 4])
# variant: 5 bands with a flatter NT gradient (no zero-NT bands)
_NT5b = np.array([45000., 33000., 22000., 12000., 8000.])
POOL5B = dict(name='5-band flatter NT', bands=[dict(share=float(a), p=float(p), NT=float(n), up=99, cut=2) for a, p, n in zip(_a5, _p5, _NT5b)], above=[2, 3, 4])

def se_slope(n_test, p, D, f=0.92, all_elig=True):
    return f*sqrt(p*(1-p))/(0.4472*D*sqrt(n_test))*100*(0.756 if all_elig else 1)

def make(pool, N, M, levels, class_band=0.03, slope_mode='logit', median_target=None, margin_sd=0.0):
    """levels: list of candidate $k changes (e.g. [-2,-1,0,1,2,3,4,6,8]). Returns acts, outcomes(beta), feasible(out)."""
    B = pool['bands']; Kb = len(B)
    share = np.array([b['share'] for b in B]); p0 = np.array([b['p'] for b in B]); NT = np.array([b['NT'] for b in B])
    up = np.array([b['up'] for b in B]); cut = np.array([b['cut'] for b in B])
    per_band = [[l for l in levels if -cut[k] <= l <= up[k]] for k in range(Kb)]
    acts = np.array(list(itertools.product(*per_band)), float)            # [A, Kb]
    pbar = float((share*p0*(1-p0)).sum())                                  # mean p(1-p) over admits
    above = np.zeros(Kb, bool); above[pool['above']] = True
    def outcomes(beta):
        # beta = AME in pp per $1k at status-quo awards (pool mean). one logit slope b = beta/(100*pbar);
        # or (review's voi2 convention) the same pp effect in every band.
        if slope_mode == 'logit': bl = np.full(Kb, beta/(100*pbar))
        else: bl = beta/(100*p0*(1-p0))
        pa = expit(logit(p0)[None, :] + bl[None, :]*acts)                   # [A, Kb]
        n = N*share
        rev = (M*n[None, :]*(pa*(NT[None, :]-1000*acts) - p0[None, :]*NT[None, :])).sum(1)
        enr_above = (n[None, :]*pa)[:, above].sum(1); enr = (n[None, :]*pa).sum(1)
        return np.column_stack([rev, enr_above, enr])
    sq_c = N*(share*p0).sum(); sq_above = N*(share*p0)[above].sum()
    sig = sqrt(N*(share*p0*(1-p0)).sum())
    def feasible(o):
        ok = (np.abs(o[:, 2]/sq_c-1) <= class_band) & (o[:, 0] >= -1e-6)
        if median_target is None: ok &= o[:, 1] >= sq_above-1e-9           # floor: above-median enrollees not below status quo
        else: ok &= o[:, 1] >= median_target*o[:, 2] + margin_sd*sig        # target share of class above the cut position
        return ok
    return acts, outcomes, feasible, dict(sq_class=sq_c, sq_above=sq_above, pbar=pbar, cohort_NTR=M*N*(share*p0*NT).sum(), share=share, p0=p0, NT=NT)

def voi(pool, N, M=2.92, D=8, K=2, U=3, mu0=1.0, sd0=0.5, F=25000., test_share=.4, class_band=0.03, pts=41,
        levels=(-3, -2, -1, 0, 1, 2, 3, 4, 6, 8), slope_mode='logit', median_target=None, margin_sd=0.0, rule='two_sided',
        bonus_years=None, pv_response=False, choose_on='posterior_ev'):
    acts, outc, feas, info = make(pool, N, M, list(levels), class_band, slope_mode, median_target, margin_sd)
    bq = np.linspace(max(0.0, mu0-3.5*sd0), mu0+3.5*sd0, pts); w = np.exp(-0.5*((bq-mu0)/sd0)**2); w /= w.sum()
    cache = {}
    def O(beta):
        k = round(float(max(beta, 0.0)), 3)
        if k not in cache: cache[k] = outc(max(beta, 0.0))
        return cache[k]
    Rm = np.array([O(b)[:, 0] for b in bq])                                 # [pts, A]
    def cons(o):
        ok = np.abs(o[:, 2]/info['sq_class']-1) <= class_band
        if median_target is None: ok &= o[:, 1] >= info['sq_above']-1e-9
        else: ok &= o[:, 1] >= median_target*o[:, 2] + margin_sd*sqrt(N*(info['share']*info['p0']*(1-info['p0'])).sum())
        return ok
    def choose(m, s):
        lo, hi = max(0, m-Z10*s), m+Z10*s
        if rule == 'two_sided':
            ok = feas(O(lo)) & feas(O(hi)) & feas(O(m))
        elif rule == 'one_sided':   # v2.4: gain >= 0 at low only; constraints at all three
            ok = feas(O(lo)) & feas(O(m)) & cons(O(hi))
        elif rule == 'posterior_ev':  # constraints at the three quantiles; objective posterior EV; no gain tests
            ok = cons(O(lo)) & cons(O(hi)) & cons(O(m))
        if not ok.any():
            return None
        wq = np.exp(-0.5*((bq-m)/s)**2); wq /= wq.sum()
        if choose_on == 'posterior_ev': ev = wq@Rm
        else: ev = O(m)[:, 0]                                                # review Phase 3 S3: maximize NTR at b_M
        ev = np.where(ok, ev, -np.inf); return int(np.argmax(ev))
    j0 = choose(mu0, sd0)
    V0 = 0.0 if j0 is None else float(w@Rm[:, j0])
    # EVPI relative to the no-test choice
    best = np.array([np.where(feas(O(b)), O(b)[:, 0], -np.inf).max() for b in bq]); best = np.where(np.isfinite(best), best, 0.0)
    EVPI = U*float(w@best - V0)
    pbar_pool = float((info['share']*info['p0']).sum())
    n_test = test_share*N*K
    se = se_slope(n_test, pbar_pool, D)
    if pv_response: se *= M                                                  # one-year bonus read by students at present value
    ps = 1/sqrt(1/sd0**2+1/se**2)
    zs = np.linspace(-3.5, 3.5, pts); zw = np.exp(-0.5*zs**2); zw /= zw.sum(); V1 = 0.0; moved = 0.0
    for i, b in enumerate(bq):
        for z, wz in zip(zs, zw):
            bh = b+z*se; m1 = ps**2*(mu0/sd0**2+bh/se**2); m1 = round(m1/0.025)*0.025
            j = choose(m1, ps)
            v = 0.0 if j is None else Rm[i, j]
            V1 += w[i]*wz*v; moved += w[i]*wz*((j is None) != (j0 is None) or (j is not None and j != j0))
    EVSI = U*(V1-V0)
    # costs
    Mt = M if bonus_years is None else bonus_years
    share, p0, NT = info['share'], info['p0'], info['NT']
    doses = [(0, .4), (D/2, .2), (D, .4)]
    if slope_mode == 'logit': blf = lambda beta: np.full(len(p0), beta/(100*info['pbar']))
    else: blf = lambda beta: beta/(100*p0*(1-p0))
    def cost_capped(beta):   # bonus paid to every enrolled test student (induced included); no revenue offset
        bl = blf(beta); tot = 0
        for dose, sd in doses:
            pa = expit(logit(p0)+bl*dose); tot += (share*sd*pa*1000*dose).sum()
        return Mt*n_test*tot
    def cost_net(beta):      # uncapped: net of induced revenue
        bl = blf(beta); tot = 0
        for dose, sd in doses:
            pa = expit(logit(p0)+bl*dose); tot += (share*sd*(pa*(NT-1000*dose)-p0*NT)).sum()
        return -Mt*n_test*tot
    C0 = cost_capped(0.0); Cmu = float(w@np.array([cost_capped(b) for b in bq])); Cnet = float(w@np.array([cost_net(b) for b in bq]))
    net = EVSI-C0-F*K
    return dict(pool=pool['name'], N=N, D=D, K=K, band=class_band, mu0=mu0, sd0=sd0, slope_mode=slope_mode, median_target=median_target, rule=rule,
                se=round(se, 2), post_sd=round(ps, 2), a0=None if j0 is None else acts[j0].tolist(), EVPI=round(EVPI), EVSI=round(EVSI),
                cost0=round(C0), cost_mu_capped=round(Cmu), cost_net_uncapped=round(Cnet), ops=F*K, net=round(net),
                net_uncapped=round(EVSI-Cnet-F*K), ratio=round(EVSI/(C0+F*K), 2), p_move=round(moved, 2),
                cohort_NTR=round(info['cohort_NTR']), class_sq=round(info['sq_class'], 1), n_acts=len(acts))

def verdict(r, use='net'):
    n = r[use]; thr = max(50000, 0.005*r['cohort_NTR'])
    if n <= 0 or r['EVPI'] <= r['cost0']+r['ops']: return 'Not recommended'
    if n >= thr and r['EVSI']/(r['cost0']+r['ops']) >= 1.5 and r['cost0'] <= 0.05*r['cohort_NTR']: return 'Recommend'
    return 'Optional'

if __name__ == '__main__':
    # reproduction of the review's table with the 2-band pool, pp-slope convention, cut 3, D in {4,8} x K in {1,2}
    for N in [600, 1000, 2000, 4000]:
        best = None
        for D in [4, 8]:
            for K in [1, 2]:
                r = voi(POOL2, N, D=D, K=K, slope_mode='pp', levels=(-3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8))
                if best is None or r['net'] > best['net']: best = r
        print(json.dumps(best), verdict(best))

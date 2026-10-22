import json, sys, itertools
import voi5
from voi5 import voi, verdict, POOL2, POOL5, POOL5B
N = 650
rows = []
def best_design(**kw):
    best = None
    for D in [4, 8]:
        for K in [1, 2]:
            r = voi(N=N, D=D, K=K, **kw)
            if best is None or r['net'] > best['net']: best = r
    return best
def rec(label, r):
    rows.append(dict(label=label, pool=r['pool'], band=r['band'], prior=f"N({r['mu0']},{r['sd0']}^2)", target=r['median_target'], design=f"D={r['D']},K={r['K']}",
                     se=r['se'], a0=r['a0'], EVPI=r['EVPI'], EVSI=r['EVSI'], cost0=r['cost0'], cost_mu=r['cost_mu_capped'], cost_net=r['cost_net_uncapped'], ops=r['ops'],
                     net=r['net'], net_uncapped=r['net_uncapped'], p_move=r['p_move'], verdict=verdict(r), verdict_uncapped=verdict(r, 'net_uncapped'), n_acts=r['n_acts']))
    print(json.dumps(rows[-1]), flush=True)

# A. pools x bands, base prior
for pool, mode in [(POOL2, 'pp'), (POOL5, 'logit'), (POOL5, 'pp'), (POOL5B, 'logit')]:
    for cb in [0.03, 0.05, 0.10]:
        rec('pool x band', best_design(pool=pool, slope_mode=mode, class_band=cb))
# B. priors on the 5-band logit pool and 2-band pool, +/-3%
for pool, mode in [(POOL5, 'logit'), (POOL2, 'pp')]:
    for mu0, sd0 in [(0.6, 0.5), (1.0, 0.5), (1.4, 0.5), (1.0, 1.0)]:
        rec('prior', best_design(pool=pool, slope_mode=mode, mu0=mu0, sd0=sd0))
# C. median-position targets (share of the class above the current 50th position), 5-band logit pool
for cb in [0.03, 0.10]:
    for tgt in [0.50, 0.55, 0.60]:
        rec('median target', best_design(pool=POOL5, slope_mode='logit', class_band=cb, median_target=tgt))
# D. one-year bonus: cost at 1 year; (i) same response (review's assumption), (ii) PV-equivalent response (SE x M)
for pool, mode in [(POOL5, 'logit'), (POOL2, 'pp')]:
    rec('one-year bonus, sticker response', best_design(pool=pool, slope_mode=mode, bonus_years=1))
    rec('one-year bonus, PV response', best_design(pool=pool, slope_mode=mode, bonus_years=1, pv_response=True))
# E. rule variants under the base case (5-band logit): one-sided, posterior-EV without gain tests; objective at b_M vs posterior EV
for rule in ['two_sided', 'one_sided', 'posterior_ev']:
    rec(f'rule={rule}', best_design(pool=POOL5, slope_mode='logit', rule=rule))
rec('choose at b_M (review text)', best_design(pool=POOL5, slope_mode='logit', choose_on='bM'))
# F. larger pool sizes for context, 5-band logit
for n in [1000, 2000, 4000]:
    N = n; rec(f'N={n}', best_design(pool=POOL5, slope_mode='logit'))
N = 650
json.dump(rows, open('task1_rows.json', 'w'), indent=1)

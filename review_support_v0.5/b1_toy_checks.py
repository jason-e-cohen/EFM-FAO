"""Session B, Part B1: toy-grid checks of spec v0.5 formulas.
Synthetic numbers only (no fixture values). numpy + math; Python 3.10 on the device.
"""
import math, numpy as np
Phi = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))
rng = np.random.default_rng(20261116)

def pb_pmf(A, y):
    """Exact distribution of sum of independent Binomial(A_c, y_c)."""
    pmf = np.array([1.0])
    for a, p in zip(A, y):
        k = np.arange(a + 1)
        b = np.array([math.comb(int(a), int(i)) * p**i * (1 - p)**(a - i) for i in k])
        pmf = np.convolve(pmf, b)
    return pmf

def p_ge_exact(A, y, goal, s=0.0, n=20000):
    if s == 0:
        pmf = pb_pmf(A, y); return pmf[goal:].sum()
    e = rng.normal(1, s, n)
    Y = np.clip(np.outer(e, y), 0, 1)
    X = rng.binomial(np.array(A)[None, :], Y).sum(1)
    return (X >= goal).mean()

def p_ge_closed(A, y, goal, s=0.0):
    A, y = np.array(A, float), np.array(y, float)
    M = (A * y).sum(); V = (A * y * (1 - y)).sum() + s**2 * M**2
    return 1 - Phi((goal - 0.5 - M) / math.sqrt(V)), M, V

print("== Q1. Target-enrolled probability: closed form vs exact, small M_T")
cases = {"M_T~4 (3 thin target cells)": ([8, 6, 10], [0.15, 0.20, 0.18]),
         "M_T~8": ([20, 12, 15], [0.15, 0.20, 0.18]),
         "M_T~20": ([50, 30, 40], [0.15, 0.20, 0.18])}
for name, (A, y) in cases.items():
    for s in (0.0, 0.10):
        worst = (0, None)
        M = sum(a * p for a, p in zip(A, y))
        for g in range(1, int(M * 2.5) + 2):
            pc, _, _ = p_ge_closed(A, y, g, s)
            pe = p_ge_exact(A, y, g, s, 200000) if s else p_ge_exact(A, y, g)
            if abs(pc - pe) > worst[0]: worst = (abs(pc - pe), g, pc, pe)
        print(f"  {name:28s} s={s:.2f} M_T={M:5.2f}  max |closed-exact| = {worst[0]:.3f} at goal {worst[1]} (closed {worst[2]:.3f}, exact {worst[3]:.3f})")

print("\n== Q11/test 2. Six-cell toy grid (class), closed form vs exact, no shock")
A = [12, 20, 25, 18, 30, 10]; y = [0.30, 0.20, 0.15, 0.35, 0.25, 0.18]
pmf = pb_pmf(A, y); M = sum(a*p for a,p in zip(A,y)); V = sum(a*p*(1-p) for a,p in zip(A,y))
worst = max((abs((1-Phi((c+0.5-M)/math.sqrt(V))) - pmf[c+1:].sum()), c) for c in range(0, len(pmf)-1))
print(f"  M={M:.2f}, P(class > cap) worst error over all caps = {worst[0]:.4f} at cap {worst[1]}")

print("\n== Q1/Q11. Median closed form (no shock) vs simulation with multiplicative shock N(1,0.10)")
# 6 cells, 3 above threshold
A = np.array([60, 50, 40, 70, 60, 50]); y = np.array([0.18, 0.20, 0.22, 0.22, 0.25, 0.28]); g = np.array([1, 1, 1, -1, -1, -1])
for scale in (1.0, 1.15, 1.3):
    Ab = A.copy().astype(float); Ab[:3] *= scale; Ab = np.round(Ab).astype(int)
    m = (g * Ab * y).sum(); Vm = (Ab * y * (1 - y)).sum()
    pc = 1 - Phi((-0.5 - m) / math.sqrt(Vm))
    for s in (0.0, 0.10):
        e = rng.normal(1, s, 200000) if s else np.ones(200000)
        X = rng.binomial(Ab[None, :], np.clip(np.outer(e, y), 0, 1))
        ps = ((X * g).sum(1) >= 0).mean()
        print(f"  scale {scale:.2f}: margin {m:6.2f}  closed {pc:.3f}  sim(s={s:.2f}) {ps:.3f}  diff {pc-ps:+.3f}")

print("\n== Q3. Paid-anyway share with oos_min_lsat and the tuition cap")
T = 63000; b = 10000; slope = 1.0  # points per $1,000
cells = [  # lsat_lo, admits, y0, base award
    (170, 20, 0.12, 58000), (166, 25, 0.15, 40000), (161, 30, 0.18, 20000), (154, 30, 0.20, 5000)]
floor = 165
Ep = Es = Ep_el = Es_el = 0.0; cost = 0.0; paid_any_cell = 0.0
for lsat, Aa, y0, a0 in cells:
    elig = lsat >= floor
    a = min(a0 + b * elig, T); dy = slope / 100 * (a - a0) / 1000
    ep, es = Aa * y0, Aa * (y0 + dy)
    Ep += ep; Es += es
    if elig: Ep_el += ep; Es_el += es
    cost += es * (a - a0); paid_any_cell += min(ep, es) * (a - a0)
spec_share = min(1, Ep / Es); el_share = min(1, Ep_el / Es_el)
print(f"  spec (all target cells): share {spec_share:.3f} -> paid-anyway ${spec_share*cost:,.0f}")
print(f"  eligible cells only    : share {el_share:.3f} -> paid-anyway ${el_share*cost:,.0f}")
print(f"  cell-level (exact)     : share {paid_any_cell/cost:.3f} -> paid-anyway ${paid_any_cell:,.0f}  (incentive cost ${cost:,.0f})")

print("\n== Q7/test 16. Shrink path with protect_target: share at or above 166 as N falls")
# cells: (lsat_lo, gpa, tier, mu) expected enrolled at current rates; synthetic
cells = [(170,'hi','in',8),(170,'lo','out_other',6),(167,'hi','in',10),(166,'lo','out_other',12),
         (165,'lo','in',14),(161,'lo','out_other',16),(158,'lo','in',14),(154,'lo','out_target',10),
         (161,'hi','out_target',12),(167,'lo','out_target',8),(152,'blank','in',10)]
gord = {'blank':0,'lo':1,'hi':2}; tord = {'out_other':0,'in':1,'out_target':2}
order = sorted(range(len(cells)), key=lambda i: (cells[i][2]=='out_target', cells[i][0], gord[cells[i][1]], tord[cells[i][2]]))
mu = np.array([c[3] for c in cells], float); M = mu.sum(); above = np.array([c[0] >= 166 for c in cells])
prev = None
for N in range(int(M), 39, -5):
    rem = M - N; removed = np.zeros(len(cells)); E = 0.0
    for k in order:
        share = min(1, max(0, (rem - E) / mu[k])) if mu[k] > 0 else 0.0
        removed[k] = share; E += mu[k]
    keep = mu * (1 - removed); sh = keep[above].sum() / keep.sum()
    flag = "" if prev is None or sh >= prev - 1e-12 else "  <-- share falls (test 16 assertion fails)"
    print(f"  N={N:3d} (M={M:.0f}) share>=166 {sh:.3f}{flag}"); prev = sh

print("\n== Q11/test 13. Tier split vs the admits>=5 fallback")
# one out-of-state cell, 8 admits over 3 cohorts, own yield 0.25; residency pool yield 0.15
own, pool = 0.25, 0.15
print("  unsplit: admits 8 >= 5 -> y0 = own history", own)
print("  split 25/75 with equal parameters: target part admits 2 < 5 -> y0 = pool", pool, "; other part 6 -> own", own)
print("  expected enrolled unsplit", 8*own, " split", 2*pool + 6*own, " -> totals differ; invariance fails unless y0 is inherited")

print("\n== Q8. Pool tripwire monotonicity (bisection premise), synthetic split")
M_lo, M_hi, V_lo, V_hi, s, cap = 66, 74, 52, 60, 0.10, 140
G_lo, G_hi = -66, 50  # t=166, 165 band in hi part with g=-1
ms = np.linspace(0.3, 3, 200)
pc = [1 - Phi((cap + .5 - (M_lo + m*M_hi)) / math.sqrt(V_lo + m*V_hi + s**2*(M_lo + m*M_hi)**2)) for m in ms]
pm = [1 - Phi((-.5 - (G_lo + m*G_hi)) / math.sqrt(V_lo + m*V_hi)) for m in ms]
print("  P(class>cap) monotone increasing:", all(np.diff(pc) >= -1e-12), "; P(median) monotone increasing:", all(np.diff(pm) >= -1e-12))
print(f"  P(class>cap) at m=3: {pc[-1]:.3f} (bounded by Phi(1/s) as m grows: {Phi(1/s):.3f})")

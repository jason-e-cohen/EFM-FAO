"""Session B, Part B4: illustrative checks (synthetic numbers only)."""
import math, numpy as np
Phi = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))
rng = np.random.default_rng(4)

print("== 1. Median probability under segment-specific year shocks")
# expected enrolled at/above t (Gp) and below t (Gm); binomial variance ~ 0.79 * mean
for Gp, Gm in [(72, 68), (75, 65)]:
    m = Gp - Gm; Vb = 0.79 * (Gp + Gm)
    for s in (0.10,):
        for rho in (1.0, 0.8, 0.5, 0.0):
            Vs = s**2 * (Gp**2 + Gm**2 - 2 * rho * Gp * Gm)
            p = 1 - Phi((-0.5 - m) / math.sqrt(Vb + Vs))
            print(f"  margin {m:+d}  s={s} rho={rho:.1f}: sd {math.sqrt(Vb+Vs):5.2f}  P(median holds) {p:.3f}")

print("\n== 2. How well can s be estimated from 3 to 5 cycles? (true s = 0.10, class ~140)")
for n in (3, 4, 5):
    est = []
    for _ in range(20000):
        e = rng.normal(0, 0.10, n)               # year shocks
        bin_noise = rng.normal(0, math.sqrt(110) / 140, n)   # binomial part, relative
        r = e + bin_noise
        v = max(0.0, r.var(ddof=1) - 110 / 140**2)
        est.append(math.sqrt(v))
    q = np.percentile(est, [10, 50, 90]); z = np.mean(np.array(est) == 0)
    print(f"  {n} cycles: s-hat 10th/50th/90th = {q[0]:.3f} / {q[1]:.3f} / {q[2]:.3f}; estimated as zero in {z:.0%} of draws")

print("\n== 3. Calibration slope sampling SD at law size (650 admits, base yield ~0.21)")
sl = []
for _ in range(400):
    x = rng.normal(-1.45, 0.8, 650); p = 1 / (1 + np.exp(-x)); y = rng.random(650) < p
    # one-variable logistic regression by Newton
    X = np.c_[np.ones(650), x]; b = np.zeros(2)
    for _ in range(25):
        q_ = 1 / (1 + np.exp(-X @ b)); W = q_ * (1 - q_)
        b += np.linalg.solve(X.T @ (X * W[:, None]), X.T @ (y - q_))
    sl.append(b[1])
sl = np.array(sl)
print(f"  SD of slope {sl.std():.3f}; share outside [0.8, 1.2] {np.mean((sl<0.8)|(sl>1.2)):.2f}; outside [0.85, 1.15] {np.mean((sl<0.85)|(sl>1.15)):.2f}")

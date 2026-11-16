"""Session A, Part A1 checks. No fixture values stored here; reads the workbook via analysis.py's own loaders.
Usage: python3 a1_checks.py "<xlsx path>"   (run with Python 3.10 + numpy + openpyxl; scipy not needed)"""
import sys, io, contextlib, numpy as np
src = open("ya_workbook_support/analysis.py").read()
ns = {"__name__": "x"}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, "analysis.py", "exec"), ns)
cat, TUITION, NAMES = ns["cat"], ns["TUITION"], ns["NAMES"]
# 1. pure arithmetic
T0 = 59900
for pct in (0.055, 0.060):
    inc = T0 * pct
    for aw in (40000, 50000):
        net0 = T0 - aw
        print(f"incr {pct:.3f}: tuition +{inc:,.1f}; award {aw}: net {net0} -> +{inc/net0*100:.2f}%")
print("workbook tuition step 59,900 -> 63,500 =", round((63500/59900-1)*100, 2), "%")
f = 1.055 ** 5
print("1.055^5 =", round(f, 5), "| 140/f =", round(140 / f, 2), "| 138/f =", round(138 / f, 2))
f2 = 1.0551 ** 5
print("at 5.51% each year: 140/f =", round(140 / f2, 2))
# 2. break-even ratio of 1 pt per $1,000: (dy/da)*(T-a)/y ; 1 = aid exactly pays for itself at the margin
Y, A, N = cat("yield"), cat("aid_usd"), cat("n_admit")
for j in (2, 3):
    T = TUITION[NAMES[j]]
    m = (A[:, j] > 0) & (Y[:, j] > 0) & (N[:, j] > 0)
    r = 1e-5 * (T - A[:, j][m]) / Y[:, j][m]
    w = N[:, j][m]
    o = np.argsort(r); cw = np.cumsum(w[o]) / w.sum()
    wm = r[o][np.searchsorted(cw, 0.5)]
    print(f"{NAMES[j]}: cells {m.sum()}, ratio median {np.median(r):.2f}, admit-weighted median {wm:.2f}, IQR {np.percentile(r,25):.2f}-{np.percentile(r,75):.2f}, share within 0.8-1.25: {np.mean((r>=0.8)&(r<=1.25)):.2f}")

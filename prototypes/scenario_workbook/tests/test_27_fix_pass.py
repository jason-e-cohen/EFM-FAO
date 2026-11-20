"""Test 27: Phase 4 review fix pass (Review_Phase4_Build.md; DECISIONS Nov 19).

R4-06 hold: with hold_position_rows true every median and percentile figure on the Summary (main block, percentile
block and spread rows, selected-case and Low/High rows, yield, pool and class-size strip columns, the pool strip's m_q
break-evens, the narratives and the contract ranges) reads labels.HOLD_POSITION, the named ranges equal the Python dump,
every formula cell equals Python after a LibreOffice recalculation, and the figures that are not medians or percentiles
are unchanged from the unheld build. The held Summary is rendered to output/phase4/Summary_render_hold.pdf for review.

R4-03 one margin per event: the percentile block, the Low/High rows and the class-size table leave out q = 0.5 targets;
the percentile margin is labelled with labels.PCT_MARGIN_SWAPS. R4-08: the tie rule is stated on the Summary and the
README sheet. R4-12: the Summary shows ntr_target and the effective entering target, and the all_jd rows read "not used
(entering_y1)" under entering_y1.
"""
import re

from conftest import close, read_range
from sw import contract as K, labels, risk

POSITION = re.compile(r"median|percentile|Spread:|Share at or above|Enrolled at or above", re.I)


def _summary_rows(wb):
    ws = wb["Summary"]
    return ws, {r: str(ws.cell(r, 1).value or "") for r in range(1, ws.max_row + 1)}


def test_hold_workbook_equals_python(hold_wb):
    from test_03_excel_equals_python import _compare
    count, bad = _compare(hold_wb)
    assert sum(count.values()) > 10_000
    assert not bad, {k: v[:5] for k, v in bad.items()}


def test_hold_contract_ranges_equal_the_dump(hold_wb):
    wb, dump = hold_wb["values"], hold_wb["info"]["dump"]
    H = labels.HOLD_POSITION
    held = 0
    for rn, _, _, _ in K.contract_table():
        got, exp = read_range(wb, rn), dump[rn]
        assert all(close(g, e) for ga, ea in zip(got, exp) for g, e in zip(ga, ea)), rn
        held += sum(e == H for ea in exp for e in ea)
    for rn in ("SUM_MARGIN_T", "SUM_P_MEDIAN_T", "SUM_P_MEDIAN_T_RHO05", "SUM_MARGIN_Q_T", "SUM_P_PCT_Q_T",
               "SUM_P_PCT_Q_T_RHO05", "SUM_PCT_BAND_Q"):
        assert all(v == H for row in read_range(wb, rn) for v in row), rn
    assert held > 0


def test_hold_replaces_every_median_and_percentile_figure(hold_wb, main_wb):
    """No number in a median or percentile row or strip column; every other Summary figure equals the unheld build."""
    H = labels.HOLD_POSITION
    run = hold_wb["info"]["run"]
    nS = len(run.scenarios)
    ws, lab = _summary_rows(hold_wb["values"])
    wm, labm = _summary_rows(main_wb["values"])
    meas = run.cfg["score"]["measure"]
    held_ts = {f"{t:g}" for t in K.held_ts(run.cfg)}
    seen = 0
    for r, a in lab.items():
        if not a or a.startswith(("SUM_", "SEG_", "INC_", "Tie rule", "Percentile targets", "Pool growth",
                                  labels.RESPONSE_LABEL, "Pool multiplier at which")):
            continue
        is_pos = bool(re.search(r"median|percentile|Spread:", a, re.I))
        m = re.match(rf"(Share|Enrolled) at or above {meas} (\d+)", a)
        if m:
            is_pos = m.group(2) in held_ts
        if not is_pos:
            continue
        vals = [ws.cell(r, 3 + j).value for j in range(nS)]
        assert vals[0] == H and all(v in (H, None) for v in vals), (a, vals)
        seen += 1
    assert seen >= 15
    # strips: every held column holds the text in every row; contract cells too
    for which, prefix, _ in K.STRIPS:
        rn = K.range_name(which, prefix)
        cols = K.strip_columns(run.cfg)[which]
        rows = read_range(hold_wb["values"], rn)
        for j, c in enumerate(cols):
            if K.held_strip_col(c):
                assert all(row[j] == H for row in rows), (rn, c)
            else:
                assert not any(row[j] == H for row in rows), (rn, c)
    be = read_range(hold_wb["values"], "PS_POOL_BREAKEVEN_M")
    assert all(row[0] != H and all(v == H for v in row[1:]) for row in be)
    # narratives: no median margin or probability
    narr = [ws.cell(r, 3).value for r, a in lab.items() if a in [s.name for s in run.scenarios] or a == ""]
    outcome = [t for t in narr if isinstance(t, str) and t.startswith("Class ")]
    assert len(outcome) == nS
    for t in outcome:
        assert H in t and "margin" not in t
    # everything not held equals the unheld build: the layouts match row for row (a held figure is replaced, never
    # removed), so compare every number in the rows both builds label alike
    assert len(lab) == len(labm)
    same = 0
    for r, a in lab.items():
        if not a or labm.get(r) != a:
            continue
        for j in range(nS):
            v, vm = ws.cell(r, 3 + j).value, wm.cell(r, 3 + j).value
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                assert close(v, vm), (a, j)
                same += 1
    assert same > 300


def test_hold_render(hold_wb, lo_profile):
    """The held Summary renders legibly (test 10's layout checks) for review: output/phase4/Summary_render_hold.pdf."""
    from test_10_render import layout_problems, render
    import os
    dst, keep = render(hold_wb, lo_profile, "Summary_render_hold")
    assert os.path.getsize(dst) > 10_000
    bad = layout_problems(keep)
    assert not bad, bad[:10]


def test_one_margin_per_event(main_wb):
    """R4-03: the percentile block and the Low/High rows leave out q = 0.5 targets; the class-size table has no q = 0.5
    percentile columns; the percentile margin carries the swaps label; the median margin keeps its own."""
    run = main_wb["info"]["run"]
    targets = risk.pct_targets(run.cfg)
    assert any(q == 0.5 for q, _ in targets) and any(q != 0.5 for q, _ in targets)
    ws, lab = _summary_rows(main_wb["values"])
    texts = list(lab.values())
    assert not any("50th percentile" in a for a in texts if not a.startswith(("SUM_", "P(50th")))
    assert not any(re.match(r"P\(50th percentile", a) for a in texts)
    for q, t in targets:
        if q != 0.5:
            assert any(a.endswith(f"margin ({labels.PCT_MARGIN_SWAPS})") and f"(q {q:g})" in a for a in texts)
    assert any(a.startswith("Median margin") for a in texts)
    cols = K.strip_columns(run.cfg)["class_table"]
    assert not any(c.startswith(("margin_q0.5", "p_pct_q0.5")) for c in cols)
    assert sum(c.startswith("margin_q") for c in cols) == sum(q != 0.5 for q, _ in targets)


def test_tie_rule_stated(main_wb):
    """R4-08: the inclusive tie rule is on the Summary and the README sheet."""
    for sh in ("Summary", "README"):
        ws = main_wb["values"][sh]
        text = " ".join(str(c.value) for row in ws.iter_rows() for c in row if isinstance(c.value, str))
        assert labels.PCT_TIE_RULE in text, sh


def test_entering_rows_and_targets(main_wb, edge_wb):
    """R4-12: ntr_target and the effective entering target are shown; under entering_y1 the all_jd rows read 'not used
    (entering_y1)'; under all_jd (edge workbook) they carry figures and the effective target is ntr_target less
    continuing revenue."""
    for bundle, all_jd in ((main_wb, False), (edge_wb, True)):
        run = bundle["info"]["run"]
        cfg = run.cfg
        ws, lab = _summary_rows(bundle["values"])
        row = {a: r for r, a in lab.items() if a}
        assert ws.cell(row["ntr_target (Inputs; under all_jd the total JD goal)"], 3).value == cfg["ntr_target"]
        eff = ws.cell(row["Effective entering target (ntr_target, less continuing revenue under all_jd)"], 3).value
        assert close(eff, cfg["ntr_target"] - (cfg["continuing_ntr_usd"] if all_jd else 0))
        for a in ("Projected JD net tuition = continuing (client-supplied) + ntr_y1",
                  "P(continuing + ntr_y1 at or above ntr_target), all_jd"):
            v = ws.cell(row[a], 3).value
            assert (v == labels.NOT_USED_ENTERING) != all_jd, (a, v)


def test_hold_in_python(tmp_path):
    """R4-06 without LibreOffice: a hold build's dump replaces exactly the median and percentile figures (every cell of
    SKT, SKQ and the spread bands; the share at or above a median or percentile t; the median and percentile strip
    columns; m_q) and the projected-outcome narrative carries labels.HOLD_POSITION in place of every median's margin
    and probability. R4-03: the class-size table's columns leave out q = 0.5 targets."""
    import os
    import yaml
    from conftest import ROOT
    from sw import build, narrative as NAR
    with open(os.path.join(ROOT, "config", "synthetic.yaml")) as f:
        raw = yaml.safe_load(f)
    H = labels.HOLD_POSITION
    dumps = {}
    for hold in (False, True):
        raw["hold_position_rows"] = hold
        cp = str(tmp_path / f"cfg_{hold}.yaml")
        with open(cp, "w") as f:
            yaml.safe_dump(raw, f)
        _, info = build.build(cp, "synthetic", os.path.join(ROOT, "config", "scenarios_synthetic.yaml"),
                              str(tmp_path / f"out_{hold}"))
        dumps[hold] = (info["dump"], info["run"])
    (d0, run0), (d1, run) = dumps[False], dumps[True]
    cfg = run.cfg
    ts = K.held_ts(cfg)
    assert ts == set(cfg["score"]["median_thresholds"]) | {t for _, t in risk.pct_targets(cfg)}
    score_ts = sorted(set(cfg["score"]["median_thresholds"]) | {cfg["score"]["pool_threshold"], cfg["score"]["floor"]},
                      reverse=True)
    changed = 0
    for rn in d0:
        a, b = d0[rn], d1[rn]
        for i, (ra, rb) in enumerate(zip(a, b)):
            for j, (x, y) in enumerate(zip(ra, rb)):
                if rn in ("SUM_MARGIN_T", "SUM_P_MEDIAN_T", "SUM_P_MEDIAN_T_RHO05", "SUM_MARGIN_Q_T", "SUM_P_PCT_Q_T",
                          "SUM_P_PCT_Q_T_RHO05", "SUM_PCT_BAND_Q"):
                    held = True
                elif rn == "SUM_SHARE_AT_OR_ABOVE_T":
                    held = score_ts[i // 3] in ts
                elif rn == "PS_POOL_BREAKEVEN_M":
                    held = j > 0
                elif rn in [K.range_name(w, p) for w, p, _ in K.STRIPS]:
                    which = next(w for w, p, _ in K.STRIPS if K.range_name(w, p) == rn)
                    held = K.held_strip_col(K.strip_columns(cfg)[which][j])
                else:
                    held = False
                if held:
                    assert y == H, (rn, i, j)
                    changed += 1
                else:
                    assert y == x, (rn, i, j)
    assert changed > 100
    for col in ("margin_score_166", "p_median_score_166", "p_pct_q0.25_161"):
        assert K.held_strip_col(col)
    for col in ("class_mean", "ntr_y1", "growth", "marker", "status"):
        assert not K.held_strip_col(col)
    vals = K.compute(run)
    for s in run.scenarios:
        t = NAR.outcome(run, vals, s)
        assert t.count(H) == len(cfg["score"]["median_thresholds"]) + 1 and "margin" not in t
        assert "margin" in NAR.outcome(run0, K.compute(run0), s)
    cols = K.strip_columns(cfg)["class_table"]
    assert [c for c in cols if c.startswith("margin_q")] == [f"margin_q{q:g}_{t:g}" for q, t in
                                                             risk.pct_targets(cfg) if q != 0.5]

"""Test 9: reconciliation (spec section 11). Every output in the interface contract (section 15 item 11) agrees between
the Summary named range, the Ledger and a Python dump of the same run.

The Python dump (`sw.contract.dump`) is keyed by the range names; the Ledger side recomputes each figure from the
recalculated Ledger columns in the test, so the three sources are independent. `step_sizes` waits for the Distribution
sheet (Phase 4) and is not enumerated. Range names are canonical, with no aliases [v0.6.2, Q-1]; `p_segment_goal_exact`
is Python only and the Summary carries a static copy [v0.6.2, Q-2].
"""
import numpy as np

from conftest import close, read_range
from sw import CASES, contract as K


def _ledger(bundle, k, s, key):
    lay = bundle["info"]["layout"]
    ws = bundle["values"][lay["case_sheet"][k]]
    c = lay["lblock"][(k, s)][key] + 1
    r0 = lay["r0l"] + 1
    return np.array([ws.cell(r0 + i, c).value for i in range(lay["n"])], dtype=object)


def _head(bundle, k, s, key):
    lay = bundle["info"]["layout"]
    ws = bundle["values"][lay["case_sheet"][k]]
    return ws.cell(lay["ledger_head_rows"][key] + 1, lay["lblock"][(k, s)]["in_seg"] + 2).value


def _static(bundle, k, key):
    lay = bundle["info"]["layout"]
    ws = bundle["values"][lay["case_sheet"][k]]
    return np.array([ws.cell(lay["r0l"] + 1 + i, lay["lstat"][key] + 1).value for i in range(lay["n"])], dtype=object)


def test_every_contract_name_matches_the_python_dump(main_wb):
    wb, dump = main_wb["values"], main_wb["info"]["dump"]
    names = [rn for rn, _, _, _ in K.contract_table()]
    assert len(set(names)) == len(names)
    missing = [n for n in names if n not in wb.defined_names]
    assert not missing, missing
    bad = []
    for rn in names:
        got, exp = read_range(wb, rn), dump[rn]
        assert len(got) == len(exp) and all(len(a) == len(b) for a, b in zip(got, exp)), rn
        for i, (ga, ea) in enumerate(zip(got, exp)):
            for j, (g, e) in enumerate(zip(ga, ea)):
                if not close(g, e):
                    bad.append((rn, i, j, e, g))
    assert not bad, bad[:10]


def test_canonical_names_only(main_wb):
    """[v0.6.2, Q-1] One range per figure: every defined name is an Inputs name (in_*) or a contract range; the spec's
    short forms (SUM_PCAP, ...) are not defined."""
    wb = main_wb["formulas"]
    contract = {rn for rn, _, _, _ in K.contract_table()}
    extra = [n for n in wb.defined_names if not n.startswith("in_") and n not in contract]
    assert not extra, extra
    for short in ("SUM_PCAP", "SUM_PBAND", "SUM_FT", "SUM_NM", "SUM_BB", "SUM_PNTR", "SUM_EVID"):
        assert short not in wb.defined_names


def test_p_segment_goal_exact_python_only(main_wb):
    """[v0.6.2, Q-2] The dump carries p_segment_goal_exact from risk.segment_exact (every case); the Summary's static
    copy is the Middle case."""
    import math
    from sw import labels, ledger as L, risk
    run, wb, dump = main_wb["info"]["run"], main_wb["values"], main_wb["info"]["dump"]
    assert "p_segment_goal_exact" not in wb.defined_names
    got = dump["p_segment_goal_exact"]
    ws = wb["Summary"]
    row = next(r for r in range(1, ws.max_row + 1)
               if ws.cell(r, 1).value == "P(segment enrolled at or above goal), exact (static, from the build)")
    seen = 0
    for ki, k in enumerate(CASES):
        for j, s in enumerate(run.scenarios):
            lc = run.lcs[s.name][k]
            if s.segment_goal is None or not lc.in_segment.any():
                assert got[ki][j] in (None, labels.NO_SEGMENT_CELLS)
                continue
            assert got[ki][j] == risk.segment_exact(lc, math.ceil(s.segment_goal))
            assert got[ki][j] == L.segment(lc)["p_segment_goal"]
            if k == "middle":
                assert close(ws.cell(row, 3 + j).value, got[ki][j])
                seen += 1
    assert seen

def test_summary_agrees_with_ledger(main_wb):
    run = main_wb["info"]["run"]
    wb = main_wb["values"]
    S = [s.name for s in run.scenarios]
    rng = {n: read_range(wb, n) for n in ("SUM_CLASS_MEAN", "SUM_MERIT", "SUM_NTR_Y1", "SUM_NEED", "SUM_GROSS_Y1",
                                          "INC_INCENTIVE_COST", "SEG_SEGMENT_ENROLLED", "SUM_FULL_TUITION_N",
                                          "SUM_NO_MERIT_AWARD_N", "SUM_SPECIALTY", "SUM_UNSCORED_COUNT")}
    scored = _static(main_wb, "middle", "scored").astype(float)
    for ki, k in enumerate(CASES):
        for j, s in enumerate(S):
            mu = _ledger(main_wb, k, s, "mu").astype(float)
            e = _ledger(main_wb, k, s, "enrolled").astype(float)
            aw = _ledger(main_wb, k, s, "award").astype(float)
            inc = _ledger(main_wb, k, s, "incentive").astype(float)
            seg = _ledger(main_wb, k, s, "in_seg").astype(float)
            T, nr = _head(main_wb, k, s, "T"), _head(main_wb, k, s, "need_rate")
            spec = rng["SUM_SPECIALTY"][ki][j]
            assert close(rng["SUM_CLASS_MEAN"][ki][j], mu.sum())
            assert close(rng["SUM_MERIT"][ki][j], (e * aw).sum())
            assert close(rng["SUM_NEED"][ki][j], nr * e.sum())
            assert close(rng["SUM_GROSS_Y1"][ki][j], T * e.sum())
            assert close(rng["SUM_NTR_Y1"][ki][j], T * e.sum() - (e * aw).sum() - nr * e.sum() - spec)
            assert close(rng["INC_INCENTIVE_COST"][ki][j], (e * inc).sum())
            assert close(rng["SEG_SEGMENT_ENROLLED"][ki][j], (seg * e).sum())
            assert close(rng["SUM_FULL_TUITION_N"][ki][j], e[aw >= T - 1e-6].sum())
            assert close(rng["SUM_NO_MERIT_AWARD_N"][ki][j], e[aw <= 1e-9].sum())
            assert close(rng["SUM_UNSCORED_COUNT"][ki][j], e[scored == 0].sum())


def test_award_matrix_and_strips_agree_with_ledger(main_wb):
    run = main_wb["info"]["run"]
    wb = main_wb["values"]
    cfg = run.cfg
    S = [s.name for s in run.scenarios]
    am = np.array(read_range(wb, "AWARD_MATRIX"), dtype=float)
    for j, s in enumerate(S):
        assert np.allclose(am[:, j], _ledger(main_wb, "middle", s, "award").astype(float), rtol=1e-12)
    ntr = read_range(wb, "SUM_NTR_Y1")[1]
    cls = read_range(wb, "SUM_CLASS_MEAN")[1]
    tw = read_range(wb, "TW_TUITION_WHATIF")
    ps = read_range(wb, "PS_POOL_STRIP")
    ct = read_range(wb, "CT_CLASS_TABLE")
    tg, pg, ng = cfg["risk"]["tuition_grid"], cfg["risk"]["pool_grid"], cfg["class"]["what_if"]
    for j, sc in enumerate(run.scenarios):
        # tuition what-if at the scenario's own increase equals the Summary ntr_y1
        hit = [g for g, pct in enumerate(tg) if abs(pct - sc.tuition_increase_pct) < 1e-9]
        if hit:
            assert close(tw[j * len(tg) + hit[0]][1], ntr[j])
        # pool strip at the scenario's own multiplier equals the Summary class (no integer rounding in live mode)
        if sc.pool_multiplier in pg:
            assert close(ps[j * len(pg) + pg.index(sc.pool_multiplier)][1], cls[j])
        # class-size rows with N at or above the expected class keep the input rates: class equals Summary class
        for g, N in enumerate(ng):
            row = ct[j * len(ng) + g]
            if N <= sc.class_cap and N >= cls[j]:
                assert close(row[1], cls[j])


def test_contract_table_is_complete():
    """Every name of spec section 15 item 11 is enumerated (step_sizes waits for the Distribution sheet)."""
    names = {n for _, n, _, _ in K.contract_table()} | {n for n, _, _ in K.python_only_table()}
    spec = {"class_mean", "class_lo90", "class_hi90", "p_class_over_cap", "p_class_in_band", "margin_t",
            "p_median_t", "p_median_t_rho05", "share_at_or_above_t", "unscored_count", "gross_y1", "merit", "need",
            "specialty", "aid", "ntr_y1", "discount_entering_y1", "avg_aid", "p_ntr_y1_ge_target", "full_tuition_n",
            "no_merit_award_n", "barbell", "segment_enrolled", "segment_lo90", "segment_hi90", "p_segment_goal",
            "segment_share", "incentive_cost", "incentive_paid_anyway", "incentive_paid_anyway_share",
            "additional_enrollees", "aid_per_additional", "ntr_per_additional", "incentive_valid",
            "tuition_whatif[grid]", "net_tuition_line_fixed", "net_tuition_line_scaled", "yield_strip[grid]",
            "breakeven_shift_class", "breakeven_shift_ntr", "pool_strip[grid]", "class_table[grid]",
            "evidence_extrapolated_share", "award_matrix", "p_segment_goal_exact"}
    assert spec <= names, sorted(spec - names)


def test_aba509_reconciliation_counts_and_quartiles(worlds, syn_cfg):
    """R3-4 (report only): counts agree or differ exactly; a published quartile is consistent when it lies in the
    band range the shares allow (enrollees with a score or a GPA, the ABA 509 basis); no figures: not run."""
    import numpy as np
    from sw import labels
    from sw import ledger as L
    from sw.config import validate
    cells = worlds[syn_cfg["generator"]["seeds"][0]]
    assert L._band_range([0, 152, 154], [10, 10, 10], 0.5) == (1, 1)
    assert L._band_range([0, 152], [10, 10], 0.5) == (0, 1)        # on a band boundary: either band
    assert L._band_range([0, 152], [0, 0], 0.5) is None
    e = cells.enrolled[:, 0]
    y = cells.cohorts[0]
    rec0 = L.aba509_reconciliation(cells, syn_cfg)[0]
    assert rec0["summary"] == labels.ABA509_NOT_RUN.format(y=y)
    assert all(r["cells"] for r in rec0["rows"])
    sb = sorted(float(b) for b in syn_cfg["score"]["bands"])
    counts = [float(e[cells.scored & (cells.score_lo == b)].sum()) for b in sb]
    lo = sb[L._band_range(sb, counts, 0.5)[0]]                       # inside the median's band range
    k0, k1 = L._band_range(sb, counts, 0.75)
    far = sb[k1 + 1] + 0.5 if k1 + 1 < len(sb) else sb[k0] - 0.5     # outside the 75th percentile's range
    assert k1 + 1 < len(sb) or k0 > 0
    raw = {k: v for k, v in syn_cfg.items() if not k.startswith("_")}
    cfg = validate(raw | {"aba_509_by_cohort": {y: {"first_year_class": float(e.sum()),
                                                     "without_score": float(e[~cells.scored].sum()) + 1,
                                                     "score_p50": lo, "score_p75": far}}})
    rows = {r["key"]: r for r in L.aba509_reconciliation(cells, cfg)[0]["rows"]}
    assert rows["first_year_class"]["verdict"] == labels.ABA509_AGREES
    assert rows["without_score"]["verdict"] == labels.ABA509_DIFFERS
    assert rows["without_gpa"]["verdict"] == labels.ABA509_NOT_GIVEN
    assert rows["score_p50"]["verdict"] == labels.ABA509_CONSISTENT
    assert rows["score_p75"]["verdict"] == labels.ABA509_INCONSISTENT
    assert L.aba509_reconciliation(cells, cfg)[0]["summary"] == labels.ABA509_SOME_DIFFER.format(k=2, n=4)

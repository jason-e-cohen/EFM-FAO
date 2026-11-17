"""Test 9: reconciliation (spec section 11). Every output in the interface contract (section 15 item 11) agrees between
the Summary named range, the Ledger and a Python dump of the same run.

The Python dump (`sw.contract.dump`) is keyed by the range names; the Ledger side recomputes each figure from the
recalculated Ledger columns in the test, so the three sources are independent. `step_sizes` waits for the Distribution
sheet (Phase 4) and is not enumerated.
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
    names = [rn for rn, _, _, _ in K.contract_table()] + list(K.ALIASES)
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


def test_aliases_point_at_the_same_ranges(main_wb):
    wb = main_wb["formulas"]
    for alias, target in K.ALIASES.items():
        assert list(wb.defined_names[alias].destinations) == list(wb.defined_names[target].destinations)


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
    names = {n for _, n, _, _ in K.contract_table()}
    spec = {"class_mean", "class_lo90", "class_hi90", "p_class_over_cap", "p_class_in_band", "margin_t",
            "p_median_t", "p_median_t_rho05", "share_at_or_above_t", "unscored_count", "gross_y1", "merit", "need",
            "specialty", "aid", "ntr_y1", "discount_entering_y1", "avg_aid", "p_ntr_y1_ge_target", "full_tuition_n",
            "no_merit_award_n", "barbell", "segment_enrolled", "segment_lo90", "segment_hi90", "p_segment_goal",
            "segment_share", "incentive_cost", "incentive_paid_anyway", "incentive_paid_anyway_share",
            "additional_enrollees", "aid_per_additional", "ntr_per_additional", "incentive_valid",
            "tuition_whatif[grid]", "net_tuition_line_fixed", "net_tuition_line_scaled", "yield_strip[grid]",
            "breakeven_shift_class", "breakeven_shift_ntr", "pool_strip[grid]", "class_table[grid]",
            "evidence_extrapolated_share", "award_matrix"}
    assert spec <= names, sorted(spec - names)

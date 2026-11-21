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

Phase 4.2 (Review_Phase4_FixPass.md F-1 to F-4, section 7). F-1: a scan of the whole held Summary, inside and outside
the print area, by value: no cell holds a held figure or a part of one (G+, G-, their variances; the count at or above
a held t; the count below the floor when the floor is a held t; the GPA-hi count when it is the GPA median's G+). One
documented exception: when score.pool_threshold is a held t, the pool strip's working values M and V of the part at or
above the threshold equal that median's G+ and the binomial variance its sibling median uses; the strip's expected class
reads them, so they stay (and two rows of the printed expected class give M_hi anyway). F-2: a ceiling break-even reads
"at most m" in Excel (edited working values; the split by score cannot produce a ceiling from real cells). F-4: no q = 0.5
percentile entry in the strips, the break-evens or the contract. Section 7: the client legend in plain words; the
lowest band reads "below {next bound}".
"""
import math
import re

import pytest

from conftest import close, read_range
from sw import contract as K, dictionary as DD, labels, risk

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
    stop = next(r for r, a in lab.items() if a == DD.lab("definitions_title"))     # Phase 5: Definitions repeat labels
    for r, a in lab.items():
        if r >= stop or not a or ws.cell(r, 1).font.i or a.startswith(("From ", labels.RESPONSE_LABEL)) \
                or a in labels.LEGEND_NAMES.values():                        # notes, sub-headings, the legend
            continue
        is_pos = bool(re.search(r"median|percentile|band where", a, re.I))
        m = re.match(rf"(?:Share at|Students enrolled with) {meas} (\d+) or higher", a)
        if m:
            is_pos = m.group(1) in held_ts
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
    outcome = [t for t in narr if isinstance(t, str) and t.startswith("Expected class ")]
    assert len(outcome) == nS
    for t in outcome:
        assert H in t and "cushion" not in t
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


def test_held_strip_prints_no_wider(hold_wb, main_wb, lo_profile):
    """Section 7: in the held render the pool strip's held columns collapse into one column (labels.HELD_COLUMNS), so
    the held strip prints no wider, and on no more pages across, than the unheld one; the yield strip, the class-size
    table and the break-evens collapse the same way."""
    import os
    import openpyxl
    from openpyxl.utils import get_column_letter
    from test_10_render import PHASE4, render
    from sw import lo
    paths = {}
    for stem, bundle in (("Summary_render", main_wb), ("Summary_render_hold", hold_wb)):
        keep = os.path.join(PHASE4, f"{stem}_sections.xlsx")
        if not os.path.exists(keep):
            render(bundle, lo_profile, stem)
        paths[stem] = keep

    def strips(path):
        out = {}
        for ws in openpyxl.load_workbook(path).worksheets:
            t = ws.oddHeader.center.text
            maxc = max(c for c in range(1, ws.max_column + 1)
                       if any(ws.cell(r, c).value not in (None, "") for r in range(1, ws.max_row + 1)))
            width = sum(lo.col_pt(ws.column_dimensions[get_column_letter(c)].width or 8.43) for c in range(1, maxc + 1))
            heads = [ws.cell(r, c).value for r in range(1, ws.max_row + 1) for c in range(1, maxc + 1)
                     if lo._is_header(ws.cell(r, c))]
            out.setdefault(t, (width, heads, ws.sheet_properties.pageSetUpPr.fitToPage))
        return out
    u, h = strips(paths["Summary_render"]), strips(paths["Summary_render_hold"])
    for title in u:
        if title.startswith(("Pool strip", "Yield what-if", "Class-size table", "Break-even")):
            assert labels.HELD_COLUMNS in h[title][1] and labels.HELD_COLUMNS not in u[title][1], title
            if title.startswith("Pool strip"):
                assert h[title][0] <= u[title][0], (h[title][0], u[title][0])
                assert h[title][2] or not u[title][2]


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
    from sw.workbook import ordinal
    for q, t in targets:
        if q != 0.5:                       # Phase 5: the percentile cushion, counted in swaps (Notes on method)
            assert any(a.startswith(f"{ordinal(q)} percentile cushion at") and f" {t:g}:" in a for a in texts)
    notes = " ".join(str(ws.cell(r, 2).value) for r in range(1, ws.max_row + 1) if lab[r] == "Cushion")
    assert labels.PCT_MARGIN_SWAPS in notes
    assert any(a.startswith("Median cushion at") for a in texts)
    cols = K.strip_columns(run.cfg)["class_table"]
    assert not any(c.startswith(("margin_q0.5", "p_pct_q0.5")) for c in cols)
    assert sum(c.startswith("margin_q") for c in cols) == sum(q != 0.5 for q, _ in targets)
    # F-4: the pool strip, the break-evens and the contract carry no q = 0.5 percentile entry; the medians carry them
    meds = run.cfg["score"]["median_thresholds"]
    npq = sum(q != 0.5 for q, _ in targets)
    for which in ("pool_strip", "yield_strip", "class_table", "tuition_whatif"):
        assert not any("q0.5" in c for c in K.strip_columns(run.cfg)[which]), which
    ps_cols = K.strip_columns(run.cfg)["pool_strip"]
    assert [c for c in ps_cols if c.startswith("p_median")] == [f"p_median_score_{t:g}" for t in meds]
    assert sum(c.startswith("p_pct") for c in ps_cols) == npq
    wb, dump = main_wb["values"], main_wb["info"]["dump"]
    nS = len(run.scenarios)
    for rn in ("SUM_MARGIN_Q_T", "SUM_P_PCT_Q_T", "SUM_P_PCT_Q_T_RHO05"):
        assert len(read_range(wb, rn)) == 3 * npq == len(dump[rn]), rn
    be = read_range(wb, "PS_POOL_BREAKEVEN_M")
    assert len(be) == nS and all(len(r) == 1 + len(meds) + npq for r in be)
    assert not any("q 0.5" in a for a in texts)


def _held_values(run, vals):
    """Every held figure and every part of one, from an unheld build's Python values: value -> what (for messages)."""
    cfg = run.cfg
    out = {}

    def add(v, what):
        # a value within 1e-6 of an integer (a probability saturated at 1, a margin of 0) is no figure to look for: it
        # matches any count or grid value of the same size
        if isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v) > 1e-9 and abs(v - round(v)) > 1e-6:
            out.setdefault(float(v), what)
    hts = K.held_ts(cfg)
    for (s, k), d in vals["sk"].items():
        for key, md in d["median"].items():
            for x in ("margin_t", "margin_expected", "p_median_t", "p_median_t_rho05"):
                add(md.get(x), (s, k, "median", key, x))
        for key, pc in d["pct"].items():
            for x in ("margin_q_t", "margin_expected", "p_pct_q_t", "p_pct_q_t_rho05", "expected_below"):
                add(pc.get(x), (s, k, "pct", key, x))
        kp = d["kpis"]
        for t in kp["share_at_or_above_t"]:
            if t in hts:
                add(kp["share_at_or_above_t"][t], (s, k, "share at or above", t))
                add(kp["enrolled_at_or_above"][t], (s, k, "enrolled at or above", t))
        if K.is_held(dict(cfg, hold_position_rows=True), "enrolled_below_floor"):
            add(kp["enrolled_below_floor"], (s, k, "enrolled below floor"))
        if K.is_held(dict(cfg, hold_position_rows=True), "enrolled_gpa_hi"):
            add(kp["enrolled_gpa_hi"], (s, k, "enrolled gpa hi"))
    for sc in run.scenarios:
        s = sc.name
        ps = vals["strips"][s]["pool_strip"]
        for kind, parts in (("median", ps["med_parts"]), ("pct", ps["pct_parts"])):
            for key, pp in parts.items():
                for x in pp["lo"]:
                    add(pp["lo"][x], (s, "working values", kind, key, "lo", x))
                    add(pp["hi"][x], (s, "working values", kind, key, "hi", x))
                    add(pp["lo"][x] + pp["hi"][x], (s, "working values", kind, key, "lo + hi", x))
        for row in ps["pool_strip"]:
            for t, md in row["median"].items():
                add(md["margin"], (s, "pool strip", t, "margin")); add(md["p"], (s, "pool strip", t, "p"))
            for key, pc in row["pct"].items():
                add(pc["p"], (s, "pool strip", key, "p"))
        for row in vals["strips"][s]["yield_strip"]["yield_strip"]:
            for key, md in row["median"].items():
                add(md["margin"], (s, "yield strip", key)); add(md["p"], (s, "yield strip", key))
        for row in vals["strips"][s]["class_table"]["class_table"]:
            for key, md in row.get("median", {}).items():
                add(md["margin"], (s, "class table", key)); add(md["p"], (s, "class table", key))
            for key, pc in row.get("pct", {}).items():
                add(pc["margin"], (s, "class table", key)); add(pc["p"], (s, "class table", key))
        for x in vals["pool_be"][s][1:]:
            add(x, (s, "break-even"))
    return out


_NUM = re.compile(r"(?<![\d.])-?\d[\d,]*\.\d(?![\d])")


def _scan(ws, held, skip=()):
    """Cells of ws (every used cell) holding a held value: numbers to 1e-9; in text, a one-decimal number equal to a
    held value rounded to one decimal that no number cell on the sheet shows (rounded the same way)."""
    hits = []
    hk = sorted(held)
    shown = {round(c.value, 1) for row in ws.iter_rows() for c in row
             if isinstance(c.value, (int, float)) and not isinstance(c.value, bool)}
    h1 = {round(h, 1): w for h, w in held.items() if abs(h) >= 1}
    for row in ws.iter_rows():
        for c in row:
            v = c.value
            if (c.row - 1, c.column - 1) in skip:
                continue
            if isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v) > 1e-9:
                hit = [held[h] for h in hk if math.isclose(v, h, rel_tol=1e-9, abs_tol=1e-12)]
                if hit:
                    hits.append((c.coordinate, v, hit[0]))
            elif isinstance(v, str):
                for m in _NUM.findall(v):
                    x = float(m.replace(",", ""))
                    if x in h1 and x not in shown:
                        hits.append((c.coordinate, m, h1[x]))
    return hits


def _rc(a1_ref):
    """(row, col), 0-based, of an A1 reference such as $C$560."""
    from openpyxl.utils.cell import coordinate_from_string, column_index_from_string
    col, row = coordinate_from_string(a1_ref.replace("$", ""))
    return row - 1, column_index_from_string(col) - 1


def test_hold_scan_by_value(hold_wb, main_wb):
    """F-1: scan the whole held Summary (inside and outside the print area) by value for any held figure or part of
    one. The same scan on the unheld build finds them, inside and outside the print area (the scan works)."""
    run0, vals0 = main_wb["info"]["run"], main_wb["info"]["vals"]
    cfg = run0.cfg
    held = _held_values(run0, vals0)
    assert len(held) > 300
    lay = hold_wb["info"]["layout"]
    exempt = set()
    if cfg["score"]["pool_threshold"] in K.held_ts(cfg):
        # the documented exception (module docstring): M_hi is G+ at the pool threshold, V_hi a median's variance
        for s in run0.scenarios:
            for key in ("M", "V"):
                exempt.add(_rc(lay["pool_parts"][(s.name, "hi", key)]))
    ws = hold_wb["values"]["Summary"]
    hits = _scan(ws, held, exempt)
    assert not hits, hits[:10]
    # the exemption is exactly the documented coincidence
    for r, c in exempt:
        v = ws.cell(r + 1, c + 1).value
        assert any(math.isclose(v, h, rel_tol=1e-9) for h in held), (r, c, v)
    wm = main_wb["values"]["Summary"]
    on = _scan(wm, held, exempt)
    print_rows = main_wb["info"]["layout"].get("summary_print_rows")
    assert len(on) > 300
    below = [h for h in on if int(re.sub(r"[A-Z]+", "", h[0])) > (print_rows or 0)]
    assert print_rows and below, "the scan reaches past the print area"


def test_breakeven_ceiling_in_excel(main_wb, lo_profile):
    """F-2: with working values that make the expected margin fall as the top pool grows (e_lo > 0, e_hi < 0) and cross
    zero at m = 1.2, the break-even reads 'at most 1.200' in Excel, as strip.breakeven_m returns. The split by score
    cannot produce this from real cells (below the pool threshold G-_hi is 0, above it G+_lo is 0), so the copy edits
    the working values directly."""
    import os
    import openpyxl
    from conftest import PHASE2
    from sw import lo, strip
    run, lay = main_wb["info"]["run"], main_wb["info"]["layout"]
    cfg = run.cfg
    j, (q, t) = K.ct_ptargets(cfg)[0]
    s = run.scenarios[0].name
    x = q * 10.0 / ((1 - q) * 1.2)
    edits = {(s, "lo", f"Gp{j}"): 10.0, (s, "lo", f"Gm{j}"): 0.0, (s, "hi", f"Gp{j}"): 0.0, (s, "hi", f"Gm{j}"): x}
    wb = openpyxl.load_workbook(main_wb["path"])
    for key, v in edits.items():
        r, c = _rc(lay["pool_parts"][key])
        wb["Summary"].cell(r + 1, c + 1).value = v
    out = os.path.join(PHASE2, "ceiling")
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, "copy.xlsx")
    wb.save(p)
    got = openpyxl.load_workbook(lo.recalc(p, os.path.join(out, "recalculated"), profile=lo_profile), data_only=True)
    be = read_range(got, "PS_POOL_BREAKEVEN_M")
    col = 1 + len(cfg["score"]["median_thresholds"])
    want = strip.breakeven_m(q * 10.0, -(1 - q) * x, cfg["risk"]["pool_grid"])
    assert want == labels.POOL_BE_AT_MOST.format(m="1.200")
    assert be[0][col] == want
    assert read_range(main_wb["values"], "PS_POOL_BREAKEVEN_M")[0][col] != want


def test_legend_in_plain_words(main_wb, hold_wb):
    """Section 7: the client legend (Labels and range kinds) carries no review IDs (R4-n), config key names (snake_case,
    dotted keys) or label constant names (CAPS_WITH_UNDERSCORES); it states whether this workbook is held."""
    for bundle, state in ((main_wb, "not held"), (hold_wb, "held")):
        ws, lab = _summary_rows(bundle["values"])
        r0 = next(r for r, a in lab.items() if a == DD.lab("notes_title"))
        rows = []
        for r in range(r0 + 1, ws.max_row + 1):
            a = lab[r]
            if not a or str(ws.cell(r, 1).fill.fgColor.rgb).upper().endswith("E8E8E8"):
                break
            rows.append((a, str(ws.cell(r, 2).value or "")))
        assert len(rows) >= 12
        for a, b in rows:
            for txt in (a, b):
                assert not re.search(r"\bR\d-\d+", txt), txt
                assert not re.search(r"\b[a-z0-9]+_[a-z0-9_]+\b", txt), txt
                assert not re.search(r"\b[A-Z]+_[A-Z_]+\b", txt), txt
                assert not re.search(r"\b[a-z]+\.[a-z_]+\b", txt), txt
        assert rows[-1][0] == "Held figures" and rows[-1][1].endswith(f"This workbook: {state}")
        assert rows[0][0] == labels.LEGEND_NAMES["SHOCK_LABEL"]


def test_lowest_band_reads_below(main_wb):
    """Section 7: the lowest score band (lower bound 0) reads 'below {next bound}' in the class-size table's headers and
    'lowest band admitted' column and in the spread rows (a number format, so the contract value stays 0)."""
    import openpyxl
    run = main_wb["info"]["run"]
    lows = sorted(float(b) for b in run.cfg["score"]["bands"])
    assert lows[0] == 0
    txt = labels.LOWEST_BAND.format(b=f"{lows[1]:g}")
    ws = openpyxl.load_workbook(main_wb["path"])["Summary"]
    cut = DD.label("OUT-127", band="")
    heads = [c.value for row in ws.iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith(cut)]
    assert DD.label("OUT-127", band=txt) in heads and DD.label("OUT-127", band="0") not in heads
    fmt = f'[=0]"{txt}";General'
    ct = read_range(main_wb["values"], "CT_CLASS_TABLE")
    cols = K.strip_columns(run.cfg)["class_table"]
    k = cols.index("lowest_band_admitted")
    (sheet, coord), = list(main_wb["values"].defined_names["CT_CLASS_TABLE"].destinations)
    first = coord.replace("$", "").split(":")[0]
    from openpyxl.utils.cell import coordinate_from_string, column_index_from_string
    col, row0 = coordinate_from_string(first)
    c0 = column_index_from_string(col)
    zeros = 0
    for i, r in enumerate(ct):
        cell = ws.cell(row0 + i, c0 + k)
        if r[k] not in ("", None):
            assert cell.number_format == fmt
            zeros += r[k] == 0
    assert zeros > 0
    from sw import lo
    assert lo.display_text(0, fmt) == txt and lo.display_text(158.0, fmt) == "158"
    stop = next(r for r in range(1, ws.max_row + 1) if ws.cell(r, 1).value == DD.lab("definitions_title"))
    lb = DD.row("OUT-027")["client_label"].split("{")[0]
    spread = [r for r in range(1, stop)
              if str(ws.cell(r, 1).value or "").startswith(lb) and str(ws.cell(r, 1).value).endswith("lower bound")]
    assert spread and all(ws.cell(r, 3).number_format == fmt for r in spread)


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
        row = {}
        for r, a in lab.items():                         # first occurrence (Definitions repeat the labels below)
            if a:
                row.setdefault(a, r)
        assert ws.cell(row[DD.label("OUT-041")], 3).value == cfg["ntr_target"]
        eff = ws.cell(row[DD.label("OUT-042")], 3).value
        assert close(eff, cfg["ntr_target"] - (cfg["continuing_ntr_usd"] if all_jd else 0))
        for a in (DD.label("OUT-045"), DD.label("OUT-046")):
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
    dumps, paths = {}, {}
    for hold in (False, True):
        raw["hold_position_rows"] = hold
        cp = str(tmp_path / f"cfg_{hold}.yaml")
        with open(cp, "w") as f:
            yaml.safe_dump(raw, f)
        path, info = build.build(cp, "synthetic", os.path.join(ROOT, "config", "scenarios_synthetic.yaml"),
                                 str(tmp_path / f"out_{hold}"))
        dumps[hold] = (info["dump"], info["run"])
        paths[hold] = path
    (d0, run0), (d1, run) = dumps[False], dumps[True]
    # F-4: the unheld pool strip dump, read by column name, carries each strip figure in its own column
    vals0 = K.compute(run0)
    ps_cols = K.strip_columns(run0.cfg)["pool_strip"]
    ps_rows = d0[K.range_name("pool_strip", next(p for w, p, _ in K.STRIPS if w == "pool_strip"))]
    src = [r for s in run0.scenarios for r in vals0["strips"][s.name]["pool_strip"]["pool_strip"]]
    assert len(ps_rows) == len(src)
    for row, r in zip(ps_rows, src):
        got = dict(zip(ps_cols, row))
        for t in run0.cfg["score"]["median_thresholds"]:
            assert got[f"margin_score_{t:g}"] == pytest.approx(r["median"][t]["margin"], abs=1e-12)
            assert got[f"p_median_score_{t:g}"] == pytest.approx(r["median"][t]["p"], abs=1e-12)
        assert got["class_mean"] == pytest.approx(r["class_mean"], abs=1e-12)
        assert got["ntr_sd"] == pytest.approx(r["ntr_sd"], abs=1e-9)
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
        floor_held = cfg["score"]["floor"] in K.held_ts(cfg)                  # F-1: the count below the floor
        assert t.count(H) == len(cfg["score"]["median_thresholds"]) + 1 + floor_held and "cushion" not in t
        assert "cushion" in NAR.outcome(run0, K.compute(run0), s)
    cols = K.strip_columns(cfg)["class_table"]
    assert [c for c in cols if c.startswith("margin_q")] == [f"margin_q{q:g}_{t:g}" for q, t in
                                                             risk.pct_targets(cfg) if q != 0.5]
    # F-1: the counts a held figure can be read off directly are held (synthetic: floor 154 is the 10th percentile's t;
    # GPA hi starts at the GPA median threshold), and only under hold or when they coincide
    assert K.is_held(cfg, "enrolled_below_floor") and K.is_held(cfg, "enrolled_gpa_hi")
    assert not K.is_held(run0.cfg, "enrolled_below_floor") and not K.is_held(run0.cfg, "enrolled_gpa_hi")
    assert not K.is_held(dict(cfg, score=dict(cfg["score"], floor=152)), "enrolled_below_floor")
    assert not K.is_held(dict(cfg, gpa=dict(cfg["gpa"], hi_at_or_above=3.9)), "enrolled_gpa_hi")
    # F-4: no q = 0.5 percentile entry in the dump; the medians carry them, every one of them in the pool strip
    meds = cfg["score"]["median_thresholds"]
    npq = sum(q != 0.5 for q, _ in risk.pct_targets(cfg))
    for rn in ("SUM_MARGIN_Q_T", "SUM_P_PCT_Q_T", "SUM_P_PCT_Q_T_RHO05"):
        assert len(d0[rn]) == 3 * npq, rn
    assert all(len(r) == 1 + len(meds) + npq for r in d0["PS_POOL_BREAKEVEN_M"])
    assert K.strip_columns(cfg)["pool_strip"] == (
        ["growth", "class_mean", "p_class_over_cap", "ntr_mean", "ntr_sd"]
        + [x for t in meds for x in (f"margin_score_{t:g}", f"p_median_score_{t:g}")]
        + [f"p_pct_q{q:g}_{t:g}" for q, t in risk.pct_targets(cfg) if q != 0.5] + ["marker"])
    assert all(len(r) == len(K.strip_columns(cfg)["pool_strip"]) for r in d0["PS_POOL_STRIP"])
    # section 7: the hold text is padded (left-aligned, indent 1) wherever it stands
    import openpyxl
    ws = openpyxl.load_workbook(paths[True])["Summary"]
    hc = [c for row in ws.iter_rows() for c in row if c.value == H]
    assert len(hc) > 500 and all(c.alignment.indent == 1 and c.alignment.horizontal == "left" for c in hc)

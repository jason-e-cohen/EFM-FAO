import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sw import config  # noqa: E402


def pytest_collection_finish(session):
    """Mutation check (test 20) [v0.6.2, P2-02]: record how many tests were collected, so a mutant run can be compared
    with the baseline run."""
    p = os.environ.get("SW_COLLECT_COUNT_FILE")
    if p:
        with open(p, "w") as f:
            f.write(str(len(session.items)))


@pytest.fixture(scope="session")
def syn_cfg():
    return config.load(os.path.join(ROOT, "config", "synthetic.yaml"))


@pytest.fixture(scope="session")
def shape_targets():
    import yaml
    with open(os.path.join(ROOT, "config", "shape_targets.yaml")) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def worlds(syn_cfg):
    """The 20 synthetic worlds of config/synthetic.yaml (generator.seeds)."""
    from sw import synth_cells
    return {s: synth_cells.generate(syn_cfg, s) for s in syn_cfg["generator"]["seeds"]}


@pytest.fixture(scope="session")
def report_dir():
    d = os.path.join(ROOT, "output", "phase1")
    os.makedirs(d, exist_ok=True)
    return d


# ---------------------------------------------------------------------------------------------------------------
# Phase 2: workbook builds recalculated by LibreOffice (tests 3, 8, 9, 10, 18)

PHASE2 = os.path.join(ROOT, "output", "phase2")


@pytest.fixture(scope="session")
def soffice():
    """soffice from SOFFICE_PATH or config/tools.yaml. Skips (with the reason) when it is missing, or when
    SW_SKIP_EXCEL is set: the mutation check (test 20) runs the Python tests only."""
    if os.environ.get("SW_SKIP_EXCEL"):
        pytest.skip("SW_SKIP_EXCEL is set: workbook tests skipped (mutation check runs Python tests only)")
    from sw import lo
    p = lo.soffice_path()
    if not p:
        pytest.skip("soffice not found (set SOFFICE_PATH or soffice_path in config/tools.yaml); test reported, "
                    "not run")
    return p


@pytest.fixture(scope="session")
def lo_profile(soffice):
    import shutil
    from sw import lo
    os.makedirs(PHASE2, exist_ok=True)
    d = lo.make_profile()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _build_and_recalc(tag, scenarios_path, profile, sentinel=False, seed=101, cfg_path=None):
    import shutil
    import openpyxl
    from sw import build, lo
    out = os.path.join(PHASE2, tag)
    shutil.rmtree(out, ignore_errors=True)
    cfg_path = cfg_path or os.path.join(ROOT, "config", "synthetic.yaml")
    path, info = build.build(cfg_path, "synthetic", scenarios_path, out, seed=seed, sentinel=sentinel)
    rc = lo.recalc(path, os.path.join(out, "recalculated"), profile=profile)
    return {"path": path, "recalc_path": rc, "info": info,
            "values": openpyxl.load_workbook(rc, data_only=True),
            "formulas": openpyxl.load_workbook(rc, data_only=False)}


@pytest.fixture(scope="session")
def main_wb(lo_profile):
    """The synthetic workbook of config/scenarios_synthetic.yaml (world seed 101), recalculated."""
    return _build_and_recalc("main", os.path.join(ROOT, "config", "scenarios_synthetic.yaml"), lo_profile)


@pytest.fixture(scope="session")
def sentinel_wb(lo_profile):
    """The same workbook with every cached value set to -999, recalculated (test 3 guard)."""
    return _build_and_recalc("sentinel", os.path.join(ROOT, "config", "scenarios_synthetic.yaml"), lo_profile,
                             sentinel=True)


@pytest.fixture(scope="session")
def edge_wb(lo_profile):
    """The edge workbook of tests/edge.py [v0.6.2, P2-01], recalculated."""
    import edge
    cp, sp = edge.write(os.path.join(PHASE2, "edge_inputs"))
    return _build_and_recalc("edge", sp, lo_profile, seed=edge.SEED, cfg_path=cp)


@pytest.fixture(scope="session")
def edge_below_wb(lo_profile):
    """[R4-09] The edge workbook under unscored_in_median: below, recalculated."""
    import edge
    cp, sp = edge.write(os.path.join(PHASE2, "edge_below_inputs"), below=True)
    return _build_and_recalc("edge_below", sp, lo_profile, seed=edge.SEED, cfg_path=cp)


@pytest.fixture(scope="session")
def hold_wb(lo_profile):
    """[R4-06] The main synthetic workbook with hold_position_rows true, recalculated."""
    import yaml
    d = os.path.join(PHASE2, "hold_inputs")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(ROOT, "config", "synthetic.yaml")) as f:
        raw = yaml.safe_load(f)
    raw["hold_position_rows"] = True
    cp = os.path.join(d, "hold_config.yaml")
    with open(cp, "w") as f:
        f.write("# synthetic.yaml with hold_position_rows true (tests/conftest.py hold_wb). Every value is synthetic.\n")
        yaml.safe_dump(raw, f, sort_keys=False)
    return _build_and_recalc("hold", os.path.join(ROOT, "config", "scenarios_synthetic.yaml"), lo_profile, cfg_path=cp)


def read_range(wb, name):
    """Values of a workbook-level named range as a 2-D list (None read as '')."""
    dn = wb.defined_names[name]
    (sheet, coord), = list(dn.destinations)
    cells = wb[sheet][coord.replace("$", "")]
    if not isinstance(cells, tuple):
        cells = ((cells,),)
    elif not isinstance(cells[0], tuple):
        cells = (cells,)
    return [["" if c.value is None else c.value for c in row] for row in cells]


def close(a, b, rel=1e-6, abs_=1e-9):
    """Test 3 tolerance: strings and integers exact; floats within 1e-6 relative (1e-9 absolute near zero)."""
    import math
    a = "" if a is None else a
    b = "" if b is None else b
    if isinstance(a, str) or isinstance(b, str):
        return str(a) == str(b)
    if isinstance(b, int) and not isinstance(b, bool):
        return float(a) == float(b)
    return math.isclose(float(a), float(b), rel_tol=rel, abs_tol=abs_)


# ---------------------------------------------------------------------------------------------------------------
# Phase 3: reproduce mode (tests 3 and 6)

PHASE3 = os.path.join(ROOT, "output", "phase3")


def repro_synthetic(seed=101):
    """A synthetic reproduce-mode run's inputs (sw.reproduce.synthetic_inputs): the scenarios of
    config/scenarios_synthetic.yaml on world `seed`, with loaded yields (each scenario's Middle live yield rounded to 3
    decimals) and loaded tuition, integer admits and enrolled, applications rounded after the pool multiplier, and
    synthetic 509 figures. Returns (cfg_live, cfg, cells, scenarios, loaded)."""
    from sw import reproduce
    return reproduce.synthetic_inputs(seed)


@pytest.fixture(scope="session")
def repro_syn_wb(lo_profile):
    """Test 3 (integer branches): the synthetic reproduce-mode workbook, built as a sentinel copy (every cached value
    -999) and recalculated, so every formula cell must be recalculated to match Python."""
    import shutil
    import openpyxl
    from sw import lo, reproduce
    out = os.path.join(PHASE3, "repro_synthetic")
    shutil.rmtree(out, ignore_errors=True)
    cfg_live = repro_synthetic()[0]
    path, info = reproduce.build_synthetic(out, 101, sentinel=True)
    rc = lo.recalc(path, os.path.join(out, "recalculated"), profile=lo_profile)
    return {"path": path, "recalc_path": rc, "info": info, "cfg_live": cfg_live,
            "values": openpyxl.load_workbook(rc, data_only=True),
            "formulas": openpyxl.load_workbook(rc, data_only=False)}


@pytest.fixture(scope="session")
def ya_path():
    """Path of the validation fixture from YA_FIXTURE_PATH; tests that need it skip without it (spec rule 3)."""
    p = os.environ.get("YA_FIXTURE_PATH")
    if not p:
        pytest.skip("YA_FIXTURE_PATH not set: reproduce-mode fixture tests skipped")
    if not os.path.exists(p):
        pytest.skip(f"YA_FIXTURE_PATH does not point at a file: {p}")
    return p

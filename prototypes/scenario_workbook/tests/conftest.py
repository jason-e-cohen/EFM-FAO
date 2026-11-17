import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sw import config  # noqa: E402


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


def _build_and_recalc(tag, scenarios_path, profile, sentinel=False, seed=101):
    import shutil
    import openpyxl
    from sw import build, lo
    out = os.path.join(PHASE2, tag)
    shutil.rmtree(out, ignore_errors=True)
    path, info = build.build(os.path.join(ROOT, "config", "synthetic.yaml"), "synthetic", scenarios_path, out,
                             seed=seed, sentinel=sentinel)
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

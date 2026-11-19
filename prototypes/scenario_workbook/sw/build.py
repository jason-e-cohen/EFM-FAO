"""Build a scenario workbook (spec sections 1, 6 to 8).

    python -m sw.build --config config/synthetic.yaml --data synthetic --seed 101 \
        --scenarios config/scenarios_synthetic.yaml --out output/

Writes output/<client>/<plan_cycle>/<build_id>/workbook.xlsx (and, with --pdf, the Summary render; with --sentinel,
workbook_sentinel.xlsx, every cached value -999, for the desktop Excel check). The build id is a hash of the inputs
(config, cell data, scenarios, requirements.lock) and the generator code (sw/*.py) [v0.6.2, P21-03], so two builds
share it only if they are the same apart from RunLog's timestamp. Live mode; reproduce-mode workbooks are built by
sw/reproduce.py (spec section 9), which reuses make_run and the workbook generator.
"""
import argparse
import copy
import hashlib
import io
import os
import subprocess
from dataclasses import dataclass, field, fields

import yaml

from . import CASES
from . import ledger as L
from . import response
from .cells import read_csv
from .config import ConfigError, load as load_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCENARIO_FIELDS = {f.name for f in fields(L.Scenario)} - {"name", "parent", "admit_rate", "award_usd", "full_tuition",
                                                         "notices", "yield_loaded", "tuition_loaded_usd"}
BASELINE_FIELDS = {"name", "description", "segment"}


@dataclass
class Run:
    """Everything one workbook shows: config, cells, response base, scenarios (Baseline first) and ledger cases."""
    cfg: dict
    cells: object
    base: object
    scenarios: list
    parents: dict                      # name -> parent Scenario or None
    lcs: dict                          # name -> {case: LedgerCase}
    meta: dict = field(default_factory=dict)
    loaded: dict = field(default_factory=dict)   # reproduce builds: name -> loaded values (sw/reproduce.py)

    def scen(self, name):
        for s in self.scenarios:
            if s.name == name:
                return s
        raise KeyError(name)


def scenarios_from_specs(specs, cells, cfg):
    """Scenario list from spec dicts (scenarios.yaml). The first spec is Baseline (scenario 0, no parent); each
    later spec names its parent and sets fields and per-cell overrides relative to it."""
    if not specs:
        raise ConfigError("scenario file has no scenarios")
    b = specs[0]
    if b.get("parent"):
        raise ConfigError("the first scenario is Baseline and has no parent")
    extra = set(b) - BASELINE_FIELDS
    if extra:
        raise ConfigError(f"Baseline takes its levers from the data; fields not allowed: {sorted(extra)}")
    base = L.baseline(cells, cfg, name=b.get("name", "Baseline"), segment=b.get("segment"))
    base.description = b.get("description", "")
    out = [base]
    by_name = {base.name: base}
    for sp in specs[1:]:
        sp = copy.deepcopy(sp)
        name = sp.pop("name")
        if name in by_name:
            raise ConfigError(f"duplicate scenario name {name!r}")
        parent = sp.pop("parent", None)
        if parent not in by_name:
            raise ConfigError(f"scenario {name!r}: parent {parent!r} is not defined above it")
        ov = sp.pop("overrides", {}) or {}
        unknown = set(sp) - SCENARIO_FIELDS
        if unknown:
            raise ConfigError(f"scenario {name!r}: unknown fields {sorted(unknown)}")
        bad = set(ov) - {"admit_rate", "award_usd", "full_tuition"}
        if bad:
            raise ConfigError(f"scenario {name!r}: unknown override columns {sorted(bad)}")
        child = L.derive(by_name[parent], name, cfg, cells, admit_rate=ov.get("admit_rate"),
                         award=ov.get("award_usd"), full_tuition=ov.get("full_tuition"), **sp)
        out.append(child)
        by_name[name] = child
    return out


def make_run(cfg, cells, scenarios, meta=None, loaded=None):
    if cfg["mode"] == "live" and (cfg["integer_admits"] or cfg["integer_enrolled"]):
        raise ConfigError("live-mode workbook needs integer_admits and integer_enrolled false (spec section 2: integer "
                          "counts are reproduce mode only; the Trim sheet, built in live mode only, does not settle "
                          "integer admits)")
    base = response.base_yield(cells, cfg)
    by = {s.name: s for s in scenarios}
    parents = {s.name: (by[s.parent] if s.parent else None) for s in scenarios}
    lcs = {s.name: {k: L.evaluate(cells, cfg, s, base, k) for k in CASES} for s in scenarios}
    if cfg["mode"] == "reproduce":
        missing = [s.name for s in scenarios if s.name not in (loaded or {})]
        if missing:
            raise ConfigError(f"reproduce build: no loaded values for {missing}")
    return Run(cfg=cfg, cells=cells, base=base, scenarios=list(scenarios), parents=parents, lcs=lcs,
               meta=dict(meta or {}), loaded=dict(loaded or {}))


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def input_hashes(cfg_path, cells, scen_bytes):
    with open(cfg_path, "rb") as f:
        cfg_b = f.read()
    buf = io.StringIO()
    cells.to_long().to_csv(buf, index=False, float_format="%.10g")
    return hashes_from_bytes(cfg_b, buf.getvalue().encode(), scen_bytes)


def hashes_from_bytes(cfg_bytes, data_bytes, scen_bytes):
    """Hashes and build id from the bytes of the config, the cell table and the scenarios (reproduce builds pass the
    effective config and the loaded values)."""
    cfg_h = _sha(cfg_bytes)
    data_h = _sha(data_bytes)
    lock = os.path.join(ROOT, "requirements.lock")
    with open(lock, "rb") as f:
        lock_h = _sha(f.read())
    scen_h = _sha(scen_bytes)
    code_h = code_hash()
    build_id = _sha("|".join([cfg_h, data_h, scen_h, lock_h, code_h]).encode())[:12]
    return {"config_hash": cfg_h, "data_hash": data_h, "scenarios_hash": scen_h, "requirements_lock_hash": lock_h,
            "code_hash": code_h, "build_id": build_id}


def code_hash():
    """sha256 over sw/*.py (name and bytes, sorted by name) [v0.6.2, P21-03]: two workbooks share a build id only if
    the same generator built them from the same inputs."""
    h = hashlib.sha256()
    d = os.path.join(ROOT, "sw")
    for name in sorted(f for f in os.listdir(d) if f.endswith(".py")):
        with open(os.path.join(d, name), "rb") as f:
            h.update(name.encode() + b"\0" + f.read() + b"\0")
    return h.hexdigest()


def git_commit():
    try:
        h = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
        d = subprocess.run(["git", "status", "--porcelain", "--", "."], cwd=ROOT, capture_output=True, text=True)
        return h.stdout.strip() + (" (working tree has uncommitted changes)" if d.stdout.strip() else "")
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def uncommitted_files():
    """Files under the prototype with uncommitted changes (git status), for RunLog [v0.6.2, P21-03]. Output files are
    git-ignored and do not appear."""
    try:
        d = subprocess.run(["git", "status", "--porcelain", "--", "."], cwd=ROOT, capture_output=True, text=True,
                           check=True)
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"
    files = [ln[3:].strip() for ln in d.stdout.splitlines() if ln.strip()]
    return ", ".join(files) if files else "none"


def load_cells(cfg, data, seed):
    if data == "synthetic":
        from . import synth_cells
        return synth_cells.generate(cfg, seed), {"data_source": f"synthetic (sw/synth_cells.py, seed {seed})"}
    return read_csv(data, cfg), {"data_source": os.path.basename(data)}


def build(cfg_path, data, scenarios_path, out_root, seed=101, pdf=False, sentinel=False, name="workbook.xlsx",
          profile=None):
    """Build one workbook. Returns (path, info); info has the build id, the run, the expected value of every formula
    cell, the contract dump, the named ranges and the sheet layout (for the tests)."""
    from . import workbook
    cfg = load_config(cfg_path)
    cells, meta = load_cells(cfg, data, seed)
    with open(scenarios_path, "rb") as f:
        scen_bytes = f.read()
    specs = yaml.safe_load(scen_bytes)["scenarios"]
    scenarios = scenarios_from_specs(specs, cells, cfg)
    meta.update(input_hashes(cfg_path, cells, scen_bytes))
    # Levers shows a blank segment cell (the default: the only configured segment) unless Baseline names one
    # [v0.6.2, P2-07]
    meta["baseline_segment_named"] = bool(specs[0].get("segment"))
    meta["git_commit"] = git_commit()
    meta["uncommitted_files"] = uncommitted_files()
    meta["cached_values"] = "sentinel" if sentinel else "python"
    meta["config_path"] = os.path.relpath(cfg_path, ROOT)
    meta["scenarios_path"] = os.path.relpath(scenarios_path, ROOT)
    run = make_run(cfg, cells, scenarios, meta)
    out_dir = os.path.join(out_root, cfg["client"]["id"], str(cfg["cycle"]["plan_cycle"]), meta["build_id"])
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name)
    info = workbook.write(run, path, sentinel=sentinel)
    if pdf:
        from . import lo
        info["pdf"] = lo.render_summary_pdf(path, out_dir, profile=profile)
    return path, info


def main():
    ap = argparse.ArgumentParser(description="Build a scenario workbook (live mode).")
    ap.add_argument("--config", required=True)
    ap.add_argument("--data", required=True, help="cells.csv or 'synthetic'")
    ap.add_argument("--seed", type=int, default=101, help="synthetic world seed")
    ap.add_argument("--scenarios", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "output"))
    ap.add_argument("--pdf", action="store_true", help="render Summary to PDF with LibreOffice")
    ap.add_argument("--sentinel", action="store_true",
                    help="cache -999 in every formula cell (the copy for the desktop Excel check, spec test 3)")
    args = ap.parse_args()
    path, info = build(args.config, args.data, args.scenarios, args.out, seed=args.seed, pdf=args.pdf,
                       sentinel=args.sentinel, name="workbook_sentinel.xlsx" if args.sentinel else "workbook.xlsx")
    print(path)
    if info.get("pdf"):
        print(info["pdf"])


if __name__ == "__main__":
    main()

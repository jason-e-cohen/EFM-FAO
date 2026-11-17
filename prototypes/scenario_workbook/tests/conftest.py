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

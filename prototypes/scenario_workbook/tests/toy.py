"""Six-cell toy grid (one segment cell) with hand-computed answers (tests 1, 2, 12, 13, 17).

Tuition: base 50,000, plan +6.0% -> 53,000. Need 25,000 at a class of 25 -> 1,000 per enrollee.
Base yields and awards are fixed through base_override (y0 the same in every case; slopes 0.5, 1.0, 1.5).

cell  res  segment   score  GPA    apps  admit rate  award   y0
c1    in   -         170    hi     40    0.50        50,000  0.20   (award = base tuition: full-tuition rung)
c2    in   -         161    lo     60    0.50        10,000  0.40
c3    out  -         170    lo     50    0.40        30,000  0.15
c4    out  -         161    hi     50    0.60        20,000  0.25
c5    out  priority  170    hi     25    0.80        45,000  0.10
c6    in   -         unsc.  blank  20    0.25             0  0.30
"""
import copy
import os

import numpy as np
import pandas as pd

from sw import CASES, cells as C, config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TOY = [
    # id, res, seg, score, gpa, apps, rate, award, y0
    ("c1", "in", "", 170.0, "hi", 40, 0.50, 50000.0, 0.20),
    ("c2", "in", "", 161.0, "lo", 60, 0.50, 10000.0, 0.40),
    ("c3", "out", "", 170.0, "lo", 50, 0.40, 30000.0, 0.15),
    ("c4", "out", "", 161.0, "hi", 50, 0.60, 20000.0, 0.25),
    ("c5", "out", "priority", 170.0, "hi", 25, 0.80, 45000.0, 0.10),
    ("c6", "in", "", np.nan, "blank", 20, 0.25, 0.0, 0.30),
]


def toy_cfg(**over):
    cfg = config.load(os.path.join(ROOT, "config", "synthetic.yaml"))
    raw = {k: v for k, v in cfg.items() if not k.startswith("_")}
    raw = copy.deepcopy(raw)
    raw["tuition_by_cohort"] = {2024: 46000, 2025: 48000, 2026: 50000}
    raw["tuition_base"] = 50000
    raw["tuition_increase_by_year"] = {2027: 6.0}
    raw["need"] = {"total": 25000, "reference_class": 25}
    raw["class"] = {"cap": 40, "target": 40, "band": 3, "what_if": [25, 30, 35, 40],
                    "supported_range": [25, 40], "reject_range": [20, 44]}
    raw["integer_admits"] = False
    raw["integer_enrolled"] = False
    for k, v in over.items():
        raw[k] = v
    return config.validate(raw)


def toy_cells(cfg, segment_mode="one"):
    """segment_mode: 'one' (c5 in the segment), 'none' (no segment cells), 'all_out' (every out-of-state cell)."""
    rows = []
    for cid, res, seg, sc, gpa, apps, rate, award, _ in TOY:
        if segment_mode == "none":
            seg = ""
        elif segment_mode == "all_out":
            seg = "priority" if res == "out" else ""
        admits = apps * rate
        for coh in (2024, 2025, 2026):
            rows.append({"cell_id": cid, "residency": res, "segment": seg, "score_lo": sc, "gpa_class": gpa,
                         "cohort": coh, "apps": apps, "admits": admits, "award_usd": award,
                         "enrolled": round(admits * 0.2)})
    return C.from_long(pd.DataFrame(rows, columns=C.COLUMNS), cfg)


def idx(cells):
    """Positions of c1 to c6 in the standard cell order (hand answers are listed c1 to c6)."""
    return [cells.index(t[0]) for t in TOY]


def toy_override():
    return {cid: ({k: y0 for k in CASES}, award) for cid, _, _, _, _, _, _, award, y0 in TOY}


# Hand answers, Middle case (slope 1.0 point per $1,000)
# Scenario S: pool 1.2, segment lift 10%, bonus 10,000 to out-of-state, yield shift +1 with segment override -2,
# specialty 5,000.
S = dict(
    apps=[48, 60, 60, 50, 33, 20],
    admits=[24, 30, 24, 30, 26.4, 5],
    award_base=[53000, 10000, 30000, 20000, 45000, 0],
    award=[53000, 10000, 40000, 30000, 53000, 0],
    incentive=[0, 0, 10000, 10000, 8000, 0],
    yld=[0.24, 0.41, 0.26, 0.36, 0.16, 0.31],
    enrolled=[5.76, 12.3, 6.24, 10.8, 4.224, 1.55],
    class_n=40.874,
    merit=1225752.0,
    incentive_cost=204192.0,
    need=40874.0,
    gross_y1=2166322.0,
    aid=1271626.0,
    ntr_y1=894696.0,
    margin_166=-6.876,
    full_tuition_n=9.984,
    no_merit_award_n=1.55,
)
# Scenario P ("plain incentive"): pool 1.2, bonus 10,000 to out-of-state; no shift, no lift, no specialty.
P = dict(
    admits=[24, 30, 24, 30, 24, 5],
    award=[53000, 10000, 40000, 30000, 53000, 0],
    yld=[0.23, 0.40, 0.25, 0.35, 0.18, 0.30],
    enrolled=[5.52, 12.0, 6.0, 10.5, 4.32, 1.5],
    class_n=39.84,
    merit=1196520.0,
    incentive_cost=199560.0,
    ntr_y1=875160.0,
)

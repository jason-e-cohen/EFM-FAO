"""Cell data (spec section 2): one row per cell x cohort, long format, cell-level counts only.

Columns: cell_id, residency, segment, score_lo, gpa_class, cohort, apps, admits, award_usd, enrolled.
`score_lo` blank means unscored. `segment` blank means outside every segment. No other column is accepted, so no
protected attribute and no student-level field can enter.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .config import ConfigError

COLUMNS = ["cell_id", "residency", "segment", "score_lo", "gpa_class", "cohort",
           "apps", "admits", "award_usd", "enrolled"]
RES_ORDER = {"in": 0, "out": 1}
GPA_ORDER = {"hi": 0, "lo": 1, "blank": 2}


@dataclass
class Cells:
    cell_id: np.ndarray
    residency: np.ndarray
    segment: np.ndarray          # "" when blank
    score_lo: np.ndarray         # float; nan when unscored
    gpa_class: np.ndarray
    cohorts: tuple
    apps: np.ndarray             # [cell, cohort]
    admits: np.ndarray
    award: np.ndarray
    enrolled: np.ndarray
    meta: dict = field(default_factory=dict)

    @property
    def n(self):
        return len(self.cell_id)

    def col(self, cohort):
        return self.cohorts.index(cohort)

    @property
    def scored(self):
        return ~np.isnan(self.score_lo)

    def index(self, cell_id):
        hits = np.flatnonzero(self.cell_id == cell_id)
        if len(hits) != 1:
            raise KeyError(cell_id)
        return int(hits[0])

    def to_long(self):
        rows = []
        for i in range(self.n):
            for j, coh in enumerate(self.cohorts):
                rows.append({
                    "cell_id": self.cell_id[i], "residency": self.residency[i], "segment": self.segment[i],
                    "score_lo": self.score_lo[i], "gpa_class": self.gpa_class[i], "cohort": coh,
                    "apps": self.apps[i, j], "admits": self.admits[i, j],
                    "award_usd": self.award[i, j], "enrolled": self.enrolled[i, j],
                })
        return pd.DataFrame(rows, columns=COLUMNS)


def order_key(residency, segment, score_lo, gpa_class):
    """Cell order: residency (in, out), segment (blank first), score_lo descending (unscored last), GPA (hi, lo, blank)."""
    s = -1e9 if np.isnan(score_lo) else score_lo
    return (RES_ORDER[residency], 0 if segment == "" else 1, -s, GPA_ORDER[gpa_class])


def from_long(df, cfg):
    """Validate a long-format cell table and return Cells in the standard order."""
    extra = set(df.columns) - set(COLUMNS)
    if extra:
        raise ConfigError(f"cell data has columns outside the schema: {sorted(extra)}")
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ConfigError(f"cell data is missing columns: {sorted(missing)}")
    df = df.copy()
    df["segment"] = df["segment"].fillna("").astype(str)
    df["score_lo"] = pd.to_numeric(df["score_lo"], errors="coerce")
    history = tuple(cfg["cycle"]["history"])
    cohorts_present = tuple(sorted(df["cohort"].unique()))
    if cohorts_present != tuple(sorted(history)):
        raise ConfigError(f"cell data cohorts {cohorts_present} do not match cycle.history {history}")

    seg_within = {s["name"]: s["within"]["residency"] for s in cfg["segments"]}
    bands = set(cfg["score"]["bands"])
    static = df.groupby("cell_id")[["residency", "segment", "score_lo", "gpa_class"]].nunique(dropna=False)
    if (static > 1).any().any():
        raise ConfigError("a cell's residency, segment, score_lo or gpa_class varies across cohorts")
    first = df.drop_duplicates("cell_id").set_index("cell_id")
    for cid, r in first.iterrows():
        if r["residency"] not in RES_ORDER:
            raise ConfigError(f"cell {cid}: residency must be 'in' or 'out'")
        if r["gpa_class"] not in GPA_ORDER:
            raise ConfigError(f"cell {cid}: gpa_class must be hi, lo or blank")
        if not np.isnan(r["score_lo"]) and r["score_lo"] not in bands:
            raise ConfigError(f"cell {cid}: score_lo {r['score_lo']} is not a configured band")
        if r["segment"] != "":
            if r["segment"] not in seg_within:
                raise ConfigError(f"cell {cid}: segment {r['segment']!r} is not configured")
            if seg_within[r["segment"]] != r["residency"]:
                raise ConfigError(f"cell {cid}: segment {r['segment']!r} lies outside its residency")
    ids = sorted(first.index, key=lambda c: order_key(*first.loc[c, ["residency", "segment", "score_lo", "gpa_class"]]))
    n, t = len(ids), len(history)
    arr = {k: np.zeros((n, t)) for k in ("apps", "admits", "award_usd", "enrolled")}
    pos = {c: i for i, c in enumerate(ids)}
    seen = np.zeros((n, t), dtype=bool)
    hist = list(sorted(history))
    for r in df.itertuples(index=False):
        i, j = pos[r.cell_id], hist.index(r.cohort)
        if seen[i, j]:
            raise ConfigError(f"cell {r.cell_id} cohort {r.cohort} appears twice")
        seen[i, j] = True
        for k in arr:
            arr[k][i, j] = getattr(r, k)
    if not seen.all():
        raise ConfigError("every cell needs one row per history cohort")
    for k in arr:
        if (arr[k] < 0).any():
            raise ConfigError(f"{k} has negative values")
    if (arr["admits"] > arr["apps"] + 1e-9).any():
        raise ConfigError("admits exceed applications in some cell")
    if (arr["enrolled"] > arr["admits"] + 1e-9).any():
        raise ConfigError("enrolled exceeds admits in some cell")
    return Cells(
        cell_id=np.array(ids, dtype=object),
        residency=np.array([first.loc[c, "residency"] for c in ids], dtype=object),
        segment=np.array([first.loc[c, "segment"] for c in ids], dtype=object),
        score_lo=np.array([first.loc[c, "score_lo"] for c in ids], dtype=float),
        gpa_class=np.array([first.loc[c, "gpa_class"] for c in ids], dtype=object),
        cohorts=tuple(hist),
        apps=arr["apps"], admits=arr["admits"], award=arr["award_usd"], enrolled=arr["enrolled"],
    )


def read_csv(path, cfg):
    return from_long(pd.read_csv(path, keep_default_na=True), cfg)


def split_cells(cells, splits, cfg):
    """Split cells into a segment part and a non-segment part.

    `splits` maps cell_id to (share, segment_name). Counts are multiplied by share and 1 - share (fractional counts
    allowed); awards are copied. New ids are '<id>|seg' and '<id>|non'. Used by test 11 and available to the generator.
    """
    df = cells.to_long()
    out = []
    for r in df.to_dict("records"):
        if r["cell_id"] in splits:
            share, seg = splits[r["cell_id"]]
            a = dict(r, cell_id=f"{r['cell_id']}|seg", segment=seg)
            b = dict(r, cell_id=f"{r['cell_id']}|non", segment="")
            for k in ("apps", "admits", "enrolled"):
                a[k] = r[k] * share
                b[k] = r[k] * (1.0 - share)
            out += [a, b]
        else:
            out.append(r)
    return from_long(pd.DataFrame(out, columns=COLUMNS), cfg)

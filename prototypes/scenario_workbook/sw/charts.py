"""Chart specifications (spec v0.6.4 section 0B, CP-5).

The workbook's charts are written through a recorder with XlsxWriter's own call names (add_chart, add_series,
combine, set_*), then drawn into the workbook by `draw`. The specification is also saved beside the workbook
(`<workbook>_charts.json`; ranges, labels and formats, no figures), so the PDF render (sw/lo.py) draws the same charts
on the recalculated values: one chart definition, two places.
"""
import json
import os


class _Chart:
    def __init__(self, opts):
        self.spec = {"opts": dict(opts), "series": [], "calls": [], "combine": None}

    def add_series(self, d):
        self.spec["series"].append(d)

    def combine(self, other):
        self.spec["combine"] = other.spec

    def __getattr__(self, name):
        if name.startswith("set_"):
            return lambda d: self.spec["calls"].append([name, d])
        raise AttributeError(name)


class Recorder:
    """Stands in for an XlsxWriter workbook while the charts are specified."""

    def __init__(self):
        self.inserts = []

    def add_chart(self, opts):
        return _Chart(opts)

    def insert(self, row, col, chart, options):
        self.inserts.append({"row": row, "col": col, "chart": chart.spec, "options": dict(options)})


def _make(wb, spec):
    ch = wb.add_chart(spec["opts"])
    for s in spec["series"]:
        ch.add_series(s)
    for name, d in spec["calls"]:
        getattr(ch, name)(d)
    if spec.get("combine"):
        ch.combine(_make(wb, spec["combine"]))
    return ch


def draw(wb, ws, inserts):
    """Draw recorded charts into XlsxWriter workbook wb, sheet ws."""
    for it in inserts:
        ws.insert_chart(it["row"], it["col"], _make(wb, it["chart"]), it["options"])


def sidecar_path(xlsx):
    return os.path.splitext(xlsx)[0] + "_charts.json"


def save(xlsx, inserts, meta):
    with open(sidecar_path(xlsx), "w") as fh:
        json.dump({"inserts": inserts, **meta}, fh, indent=1)


def load(xlsx):
    p = sidecar_path(xlsx)
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return json.load(fh)

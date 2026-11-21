"""Supporting checks (not a numbered spec test): config rule 7 and the exact label text of spec section 4."""
import os

import pytest

from sw import config, labels
from sw.config import ConfigError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_richmond_config_names_pending_values():
    """Richmond tuition is pending (not copied from the fixture); a missing required value is an error."""
    with pytest.raises(ConfigError) as e:
        config.load(os.path.join(ROOT, "config", "richmond.yaml"))
    msg = str(e.value)
    assert "tuition_by_cohort" in msg and "tuition_base" in msg
    other = msg.split(":", 1)[1].replace("tuition_by_cohort", "").replace("tuition_base", "").strip(" ,")
    assert other == ""


def test_synthetic_config_loads():
    cfg = config.load(os.path.join(ROOT, "config", "synthetic.yaml"))
    assert config.scenario_tuition(cfg, 6.0) == 57150.0          # 53,900 x 1.06 = 57,134 -> 57,150


def test_label_text():
    assert labels.RESPONSE_LABEL == "Response based on client-input"
    assert labels.ASSUMPTION_LABEL == "Includes client-input assumptions (yield shift, application lift)"
    assert labels.shock_label(0.1) == "Year-to-year variation assumed (s = 0.1), not yet calibrated"
    assert labels.SEGMENT_SHARE_LABEL == "Segment share assumed, not from client data"
    assert labels.RANGE_OUTCOME == "Likely range (90%)"                      # spec v0.6.4 CP-2
    assert labels.RANGE_CASES == "Low and High price-response cases"
    assert labels.fmt_prob(0.03, "illustrative") == "under 5%"
    assert labels.fmt_prob(0.97, "illustrative") == "over 95%"
    assert labels.fmt_prob(0.03, "public") == "3%"


def test_no_guardrail_language():
    """No label characterizes an award (D2)."""
    text = " ".join(str(v) for k, v in vars(labels).items() if k.isupper()).lower()
    for word in ("exceptional", "anomalous", "out of bounds", "beyond a limit"):
        assert word not in text


def test_xl_rounding_matches_excel_text():
    """labels.xl rounds as Excel's TEXT shows numbers (half away from zero after 15 significant digits); Python's own
    formatting rounds an exact tie half to even (Phase 3 finding: a $x.50 net-tuition example)."""
    from sw import labels
    assert f"{1424.5:,.0f}" == "1,424" and f"{labels.xl(1424.5):,.0f}" == "1,425"
    assert labels.xl(-2.5) == -3 and labels.xl(0.125, 2) == 0.13 and labels.xl(130.25, 1) == 130.3
    assert labels.xl(2.4999999999999996) == 3          # 15 significant digits first, as Excel shows it
    assert labels.xl(1.44) == 1 and labels.xl(0.0) == 0


def test_ledger_rounding_matches_excel_round():
    """ledger.xround and config.round_to round as Excel and LibreOffice ROUND do: 15 significant digits, then half up
    (LibreOffice ROUND(2.4999999999999996, 0) = 3, checked in Phase 3)."""
    import numpy as np
    from sw import ledger as L
    from sw.config import round_to
    assert L.xround(2.4999999999999996) == 3 and L.xround(2.5) == 3 and L.xround(1.44) == 1
    assert np.array_equal(L.xround(np.array([0.5, 1.4999999999999998, 2.0, 0.0])), [1, 2, 2, 0])
    assert round_to(1024.0, 50) == 1000 and round_to(1025.0, 50) == 1050 and round_to(1074.99, 50) == 1050

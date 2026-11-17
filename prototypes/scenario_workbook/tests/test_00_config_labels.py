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
    assert labels.RANGE_OUTCOME == "90% outcome range"
    assert labels.RANGE_CASES == "Low and High price-response cases"
    assert labels.fmt_prob(0.03, "illustrative") == "under 5%"
    assert labels.fmt_prob(0.97, "illustrative") == "over 95%"
    assert labels.fmt_prob(0.03, "public") == "3%"


def test_no_guardrail_language():
    """No label characterizes an award (D2)."""
    text = " ".join(str(v) for k, v in vars(labels).items() if k.isupper()).lower()
    for word in ("exceptional", "anomalous", "out of bounds", "beyond a limit"):
        assert word not in text

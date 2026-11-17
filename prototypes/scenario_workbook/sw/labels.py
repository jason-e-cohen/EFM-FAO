"""Fixed text (spec section 4 and the blocks of section 3). Each label is one constant with exact text."""

# Spec section 4 labels [v0.6, B4-6]
RESPONSE_LABEL = "Response based on client-input"
ASSUMPTION_LABEL = "Includes client-input assumptions (yield shift, application lift)"
SHOCK_LABEL = "Year-to-year variation assumed (s = {s}), not yet calibrated"
SEGMENT_SHARE_LABEL = "Segment share assumed, not from client data"

# Range kinds [v0.6, B4-9]; never combined
RANGE_OUTCOME = "90% outcome range"
RANGE_CASES = "Low and High price-response cases"
RANGE_OUTCOME_NOTE = "enrollment noise and year-level variation, Middle case"
RANGE_CASES_NOTE = "placeholder slopes now"

# Probability display while the shock is illustrative [v0.6, B4-7]
PROB_UNDER = "under 5%"
PROB_OVER = "over 95%"

# Section 3 blocks
DISCOUNT_LABEL = "Discount rate (entering class, first year)"
NEED_LABEL = "Need aid: {total} at a class of {ref} ({rate} per enrollee; scales with class)"
STICKER_LABEL = "Sticker-price demand effect not modeled."
NET_TUITION_FIXED = "Awards fixed in dollars: every student below full tuition pays {diff} more than at base-cycle tuition."
NET_TUITION_SCALED = (
    "Awards scaled with tuition: a student pays {p} x (base-cycle tuition minus award) more, "
    "for example {x} at an award of {award}."
)
POOL_STRIP_LABEL = "yield held constant as the pool changes"
POOL_YTD_LABEL = "growth to date; final growth may differ if applicants file earlier or later than last year"
LINEAR_APPROX = "linear approximation"
RHO_SENSITIVITY = "if high-score and other admits' yields move differently year to year"

# Segment block [v0.6, B1-8, B1-14]
NO_SEGMENT_CELLS = "no segment cells in the data"
SEGMENT_APPROX = "approximate (fewer than 20 expected)"

# Incentive block [v0.6, B1-4, B1-11]
INCENTIVE_VALID = "valid"
INCENTIVE_NOT_VALID = "not valid: parent differs in more than the incentive"
AID_PER_ADDITIONAL = "aid per additional enrollee"
SAVINGS_PER_LOST = "savings per enrollee lost"
UNDER_HALF = "change under half a student"

# Class-size table [v0.6, B1-19]
CT_OK = "OK"
CT_NOT_APPLICABLE = "not applicable (N at or above expected class)"
CT_ABOVE_CAP = "above cap"
CT_SHORTFALL = "N not reachable: shortfall {shortfall}"

# Evidence label (information only; never a judgment of the award)
EVIDENCE_OBSERVED = "observed"
EVIDENCE_EXTRAPOLATED = "extrapolated"

# Notices
CLASS_TARGET_NOTICE = (
    "Class target {target} is outside the supported range ({lo} to {hi}); "
    "figures are computed, but this class size is outside the tested range."
)
MARGINAL_ADMIT_NOTE = (
    "marginal_admit_yield_slope is {x}; marginal-admit yield is not modeled, so the value is read and ignored."
)

# Policy choices stated in the README [v0.6, B1-24, B3-3]
POLICY_UNSCORED_TRIMMED_FIRST = (
    "The shrink path trims unscored applicants first. This is a policy choice with access implications."
)
POLICY_UNSCORED_EXCLUDED = (
    "Unscored enrollees are excluded from both sides of the median margins and reported as a count."
)


def shock_label(s):
    return SHOCK_LABEL.format(s=f"{s:g}")


def fmt_prob(p, shock_source):
    """Probability as display text. While the shock is illustrative, values beyond 5% and 95% are clamped in text."""
    if shock_source == "illustrative":
        if p < 0.05:
            return PROB_UNDER
        if p > 0.95:
            return PROB_OVER
    return f"{100 * p:.0f}%"

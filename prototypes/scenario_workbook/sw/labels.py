"""Fixed text (spec section 4 and the blocks of section 3). Each label is one constant with exact text."""

# Spec section 4 labels [v0.6, B4-6]
RESPONSE_LABEL = "Response based on client-input"
ASSUMPTION_LABEL = "Includes client-input assumptions (yield shift, application lift)"
SHOCK_LABEL = "Year-to-year variation assumed (s = {s}), not yet calibrated"
SEGMENT_SHARE_LABEL = "Segment share assumed, not from client data"

# Range kinds [v0.6, B4-9]; never combined
RANGE_OUTCOME = "Likely range (90%)"                       # CP-2: was "90% outcome range"
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

# Percentile targets, revenue goal and pool growth [v0.6.3, BM-1, BM-4, BM-6]
PCT_APPROX_LABEL = "approximate (fewer than 20 students expected below the target score)"
BAND_NOT_SCORE_LABEL = "band, not a score"
CONTINUING_LABEL = "continuing-student revenue as supplied by the client; attrition and renewals not modeled"
CONTINUING_HELD = "continuing revenue held at the supplied figure"
POOL_BREAKEVEN_LABEL = ("pool multiplier at which the expected class meets the target / the expected margin is zero; "
                        "not a probability")
POOL_YTD_MARKER = "growth to date ({as_of}) is about here"
POOL_YTD_NO_DATE = "date not given"
PCT_MARGIN_UNIT = ("cushion counted in swaps: replacing a student at or above the target score with one below it "
                   "uses one; adding a student below it, without removing one, uses less than one")
GPA_PCT_NOTE = "GPA percentiles are not supported (the cell schema has one GPA boundary)."

# Phase 4 review fix pass (Review_Phase4_Build.md; DECISIONS Nov 19)
PCT_MARGIN_SWAPS = "swaps: students below the target score who could replace students at or above it"            # R4-03
PCT_TIE_RULE = ("counts as met when exactly the target share is below the score; the ABA averages the two middle "
                "scores, so near a tie this can read a few points high")                                                     # R4-08
HOLD_POSITION = "held until the LSAT basis is confirmed"                                       # CP-2                             # R4-06
POOL_BE_ANY = "holds at any pool size"                                                            # R4-04
POOL_BE_NOT_REACHED = "not reached by growth"
POOL_BE_ABOVE_GRID = "above the pool grid"
POOL_BE_BELOW_GRID = "below the pool grid"
POOL_YTD_TIE = "a tie between two grid rows goes to the upper row"                                # R4-13
NOT_USED_ENTERING = "not used (the goal covers the entering class only)"                       # CP-2                                                       # R4-12
ALL_JD_NEEDS_CONTINUING = "ntr_goal_basis all_jd needs continuing_ntr_usd"                         # R4-11
NEED_DEPARTURE_NOTE = ("a scenario's need_total departure from need.total is a fixed dollar amount (it does not scale "
                       "with class); need.total itself scales with class")                       # R4-07

# Phase 4.2 (Review_Phase4_FixPass.md F-1 to F-6, section 7)
POOL_BE_AT_MOST = "at most {m}"                     # F-2: a break-even that is a ceiling (the target fails beyond m)
LOWEST_BAND = "below {b}"                           # section 7: the lowest score band (lower bound 0 or less)
HELD_COLUMNS = "median and percentile figures"      # section 7: held strip columns collapsed into one in the PDF
# The client legend (Summary "Labels and range kinds"): plain names and wording, no review IDs or config keys
LEGEND_NAMES = {"SHOCK_LABEL": "Year-to-year variation", "RESPONSE_LABEL": "Response",
                "ASSUMPTION_LABEL": "Client-input assumptions", "SEGMENT_SHARE_LABEL": "Segment share",
                "PCT_APPROX_LABEL": "Approximate percentile", "BAND_NOT_SCORE_LABEL": "Score bands",
                "CONTINUING_LABEL": "Continuing students", "POOL_BREAKEVEN_LABEL": "Break-even pool multiplier"}
LEGEND_PROB = ("while the year-to-year variation is illustrative (not yet calibrated), probabilities below 5% read "
               "'{under}' and above 95% read '{over}'")
LEGEND_NEED = ("need aid scales with the class at a fixed amount per enrollee; a scenario's change to total need aid "
               "is a fixed dollar amount and does not scale with the class")
LEGEND_TIE = "a median or percentile target {rule}"
LEGEND_HELD = "until the LSAT basis is confirmed, every median and percentile figure reads '{hold}'. This workbook: {state}"

# Segment block [v0.6, B1-8, B1-14]
NO_SEGMENT_CELLS = "no segment cells in the data"
SEGMENT_APPROX = "approximate (fewer than 30 expected)"          # [v0.6.1, OP-3]

# Incentive block [v0.6, B1-4, B1-11]
INCENTIVE_VALID = "valid"
INCENTIVE_NOT_VALID = "not valid: parent differs in more than the incentive"
AID_PER_ADDITIONAL = "aid per additional enrollee"
SAVINGS_PER_LOST = "savings per enrollee lost"
UNDER_HALF = "change under half a student"

# Class-size table [v0.6, B1-19]
CT_OK = "OK"
CT_NOT_APPLICABLE = "not applicable (class size at or above the expected class)"
CT_ABOVE_CAP = "above cap"
CT_SHORTFALL = "class size not reachable: shortfall {shortfall}"

# Award entries ignored under a full-tuition flag [v0.6.2, P2-03]
AWARD_IGNORED = "award entry ignored: full-tuition flag set"
AWARDS_IGNORED_ONE = "1 award entry ignored: full-tuition flag set."
AWARDS_IGNORED_MANY = "{k} award entries ignored: full-tuition flag set."
FT_CONFLICT_CHECK = "award entered on a full-tuition cell is ignored; clear the flag to use it"

# Build-time inputs and static figures [v0.6.2, P2-06, P2-07]
REBUILD_NEEDED = "rebuild needed: differs from its value at build ({build})"
EXACT_CURRENT = "current"
EXACT_STALE = ("stale: segment expected enrollment, goal or cells changed since the build; rebuild for the exact "
               "value")
SCOPE_ERROR = ("error: bonus scope 'segment' with no segment cells and a bonus, lift or goal (Python refuses this "
               "scenario)")
SEGMENT_UNNAMED = "error: several segments are configured and none is named; name the active segment on Levers"

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


def xl(v, nd=0):
    """v rounded to nd decimals the way Excel's TEXT and ROUND show it: 15 significant digits, then half away from
    zero. Python's own formatting rounds an exact binary tie (for example 1424.5) half to even, so every Python text
    that a TEXT() formula also renders goes through this first."""
    from decimal import ROUND_HALF_UP, Decimal
    v = float(v)
    if v != v or v in (float("inf"), float("-inf")):
        return v
    d = Decimal(format(v, ".15g")).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return float(d)


def fmt_prob(p, shock_source):
    """Probability as display text. While the shock is illustrative, values beyond 5% and 95% are clamped in text."""
    if shock_source == "illustrative":
        if p < 0.05:
            return PROB_UNDER
        if p > 0.95:
            return PROB_OVER
    return f"{xl(100 * p):.0f}%"

# Reproduce mode (spec section 9)
MODE_REPRO_OK = "OK (Reproduce: the Ledgers take the loaded yields and tuition)"
MODE_REPRO_LIVE = "Live: the Ledgers take the response yields and the tuition formula; the loaded values are not read"
MODE_UNKNOWN = "mode must be Live or Reproduce"
MODE_LIVE_BUILD = "this is a live build with no loaded values; the Ledgers ignore the switch (set it back to Live)"
REPRO_LEVERS_DIFFER = "{rates} admit rates and {awards} awards differ from the loaded values; pool multiplier {pool}"
REPRO_TUITION_DIFFERS = "tuition formula gives {formula}; loaded tuition {loaded}"

# ABA 509 reconciliation on History (R3-4; report only, never asserted)
ABA509_NOT_GIVEN = "not given"
ABA509_AGREES = "agrees"
ABA509_DIFFERS = "differs"
ABA509_CONSISTENT = "consistent"
ABA509_INCONSISTENT = "inconsistent"
ABA509_NOT_RUN = "not run: no ABA 509 figures for {y} (aba_509_by_cohort)"
ABA509_ALL_AGREE = "report only: the cell data agree with every given 509 figure"
ABA509_SOME_DIFFER = "report only: {k} of {n} given 509 figures disagree with the cell data (see History)"

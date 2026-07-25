"""
Unit tests for backend/algorithm/rules.py — the individual HARD/SOFT rule
functions (hand size, connectivity, budget, value, left-hand, user type,
game genre, weight, RGB, portability, extra buttons, long hours) and the
GENERAL_RULES / GAMER_RULES / STUDENT_RULES / OFFICE_RULES wiring.

Unlike test_recommend.py (which exercises rules together through
recommend()), these tests call the private rule-helper functions directly
so a boundary bug in one rule can't hide behind another rule's scoring.

Edge cases covered on top of the "happy path" numbers:
  - Boundary values at the exact config thresholds (e.g. hand length at
    exactly 115mm/130mm, weight at exactly 80g/100g, buttons at exactly 6/10).
  - Mice with missing specs the DB schema allows to be NULL: weight,
    max_DPI, min_battery_life, number_of_buttons, connectivity, and
    gaming_specs.tracking_speed. These used to raise TypeError deep inside
    scoring (comparing None to a number); the rule functions now treat an
    unknown spec as "doesn't meet the requirement" instead of crashing.
  - Every Preferability/Usage/Game_Type/Connectivity enum bucket.

Run from the backend/ directory:
    python test_rules.py           # runs every test_* below, exits non-zero on failure
    pytest test_rules.py           # same tests, discovered by name
"""

import sys, os
from types import SimpleNamespace

BACKEND = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND)
for _p in (PROJECT_ROOT, BACKEND, os.path.join(BACKEND, "algorithm")):
    sys.path.insert(0, _p)

from database.models import Ergonomy
from algorithm import rules, config
from algorithm.classes import (
    Hand_Size, Preferability, Connectivity, Game_Type, Usage, User_Type, RuleType,
)


# ── Mock builders ─────────────────────────────────────────────────────────────
# Every field defaults to a "well-formed" value; tests override only what they
# need, including setting fields to None to exercise missing-data paths that
# the real (nullable) DB columns allow.

def _conn(bluetooth=False, dongle=False, wired=False):
    return SimpleNamespace(bluetooth=bluetooth, dongle=dongle, wired=wired)


def _gaming(rgb=False, tracking_speed=400, max_polling_rate=1000):
    return SimpleNamespace(rgb=rgb, tracking_speed=tracking_speed, max_polling_rate=max_polling_rate)


def _mouse(*, id=1, length=120, weight=90, left_fit=False,
           ergonomy=Ergonomy.SYMMETRICAL, max_DPI=8000, number_of_buttons=6,
           min_battery_life=50, connectivity=None, gaming_specs=None):
    return SimpleNamespace(
        id=id, length=length, weight=weight, left_fit=left_fit, ergonomy=ergonomy,
        max_DPI=max_DPI, number_of_buttons=number_of_buttons,
        min_battery_life=min_battery_life, connectivity=connectivity,
        gaming_specs=gaming_specs,
    )


# ── Hand size ──────────────────────────────────────────────────────────────

def test_hand_size_small_boundary():
    """Small requires length strictly under SMALL_HAND_SIZE (115mm)."""
    just_under = _mouse(length=config.SMALL_HAND_SIZE - 0.1)
    exactly_at = _mouse(length=config.SMALL_HAND_SIZE)
    assert rules._hand_size_compatible({"hand_size": Hand_Size.SMALL}, just_under)
    assert not rules._hand_size_compatible({"hand_size": Hand_Size.SMALL}, exactly_at)


def test_hand_size_medium_boundaries_are_inclusive():
    """Medium is [SMALL_HAND_SIZE, MEDIUM_HAND_SIZE] inclusive on both ends."""
    low_edge = _mouse(length=config.SMALL_HAND_SIZE)
    high_edge = _mouse(length=config.MEDIUM_HAND_SIZE)
    just_below = _mouse(length=config.SMALL_HAND_SIZE - 0.1)
    just_above = _mouse(length=config.MEDIUM_HAND_SIZE + 0.1)
    facts = {"hand_size": Hand_Size.MEDIUM}
    assert rules._hand_size_compatible(facts, low_edge)
    assert rules._hand_size_compatible(facts, high_edge)
    assert not rules._hand_size_compatible(facts, just_below)
    assert not rules._hand_size_compatible(facts, just_above)


def test_hand_size_large_boundary():
    """Large requires length strictly over MEDIUM_HAND_SIZE (130mm)."""
    exactly_at = _mouse(length=config.MEDIUM_HAND_SIZE)
    just_over = _mouse(length=config.MEDIUM_HAND_SIZE + 0.1)
    facts = {"hand_size": Hand_Size.LARGE}
    assert not rules._hand_size_compatible(facts, exactly_at)
    assert rules._hand_size_compatible(facts, just_over)


def test_hand_size_missing_length_never_passes():
    """A mouse with no recorded length can't satisfy any hand-size preference."""
    no_length = _mouse(length=None)
    for hand in (Hand_Size.SMALL, Hand_Size.MEDIUM, Hand_Size.LARGE):
        assert not rules._hand_size_compatible({"hand_size": hand}, no_length)
    assert "No size data" in rules._hand_size_explanation({"hand_size": Hand_Size.MEDIUM}, no_length)


# ── Connectivity ──────────────────────────────────────────────────────────────

def test_mouse_conn_type_matrix():
    """Every bluetooth/dongle/wired combination maps to the right product type."""
    cases = [
        (dict(bluetooth=False, dongle=False, wired=False), None),
        (dict(bluetooth=True,  dongle=False, wired=False), Connectivity.STRICTLY_WIRELESS),
        (dict(bluetooth=False, dongle=True,  wired=False), Connectivity.STRICTLY_WIRELESS),
        (dict(bluetooth=True,  dongle=True,  wired=False), Connectivity.STRICTLY_WIRELESS),
        (dict(bluetooth=False, dongle=False, wired=True),  Connectivity.STRICTLY_WIRED),
        (dict(bluetooth=True,  dongle=False, wired=True),  Connectivity.BOTH),
        (dict(bluetooth=False, dongle=True,  wired=True),  Connectivity.BOTH),
        (dict(bluetooth=True,  dongle=True,  wired=True),  Connectivity.BOTH),
    ]
    for flags, expected in cases:
        mouse = _mouse(connectivity=_conn(**flags))
        assert rules._mouse_conn_type(mouse) == expected, f"{flags} -> expected {expected}"


def test_mouse_conn_type_no_connectivity_row():
    """A mouse with no Mouse_Connectivity row at all (connectivity is None)."""
    assert rules._mouse_conn_type(_mouse(connectivity=None)) is None


def test_conn_acceptable_matrix():
    """desired x actual acceptability, including the 'actual unknown' column."""
    both, wireless, wired = Connectivity.BOTH, Connectivity.STRICTLY_WIRELESS, Connectivity.STRICTLY_WIRED
    # (desired, actual) -> expected
    cases = {
        (both, both): True, (both, wireless): False, (both, wired): False, (both, None): False,
        (wireless, wireless): True, (wireless, both): True, (wireless, wired): False, (wireless, None): False,
        (wired, wired): True, (wired, both): True, (wired, wireless): False, (wired, None): False,
    }
    for (desired, actual), expected in cases.items():
        assert rules._conn_acceptable(desired, actual) == expected, f"{desired}, {actual}"


def test_connectivity_weight_exact_acceptable_wrong_unknown():
    """Four distinct outcomes: exact match, acceptable-but-not-ideal, wrong type,
    and no connectivity data at all — each with its own weight tier."""
    facts_wireless = {"connectivity": Connectivity.STRICTLY_WIRELESS}
    exact = _mouse(connectivity=_conn(dongle=True))
    acceptable = _mouse(connectivity=_conn(dongle=True, wired=True))  # BOTH satisfies a wireless wish
    wrong = _mouse(connectivity=_conn(wired=True))  # strictly wired when wireless wanted
    unknown = _mouse(connectivity=None)

    assert rules._connectivity_weight(facts_wireless, exact) == config.MAJOR_FACTOR
    assert rules._connectivity_weight(facts_wireless, acceptable) == config.MINOR_FACTOR
    assert rules._connectivity_weight(facts_wireless, wrong) == config.NEGATIVE_MAJOR_FACTOR
    assert rules._connectivity_weight(facts_wireless, unknown) == config.NEGATIVE_NORMAL_FACTOR


def test_connectivity_weight_no_preference_is_neutral():
    assert rules._connectivity_weight({"connectivity": None}, _mouse()) == 0.0


def test_connectivity_rule_type_strict_vs_preferably():
    """A definitive yes/no makes connectivity HARD; 'preferably' keeps it SOFT."""
    assert rules._connectivity_rule_type({"connectivity_strict": True}) == RuleType.HARD
    assert rules._connectivity_rule_type({"connectivity_strict": False}) == RuleType.SOFT
    assert rules._connectivity_rule_type({}) == RuleType.SOFT


# ── Budget ─────────────────────────────────────────────────────────────────
# The buffer formula is intentionally left as-is (see PR discussion): it uses
# 95% of the budget's *midpoint* as slack on each side rather than 5% of each
# bound, so the effective band is far wider than "budget ± 5%" — these tests
# pin that actual behaviour precisely so a future change to the formula shows
# up as a deliberate, visible diff instead of a silent shift in results.

def test_budget_buffer_matches_documented_formula():
    facts = {"budget": (100.0, 100.0), "prices": {}}
    budget = facts["budget"]
    midpoint = (budget[0] + budget[1]) / 2
    slack = midpoint * (1 - config.BUDGET_BUFFER)
    lower, upper = budget[0] - slack, budget[1] + slack  # 5, 195 for a (100, 100) budget

    at_lower = _mouse(id=1)
    just_under_lower = _mouse(id=2)
    at_upper = _mouse(id=3)
    just_over_upper = _mouse(id=4)
    facts["prices"] = {1: lower, 2: lower - 0.01, 3: upper, 4: upper + 0.01}

    assert rules._budget_compatible(facts, at_lower)
    assert not rules._budget_compatible(facts, just_under_lower)
    assert rules._budget_compatible(facts, at_upper)
    assert not rules._budget_compatible(facts, just_over_upper)


def test_budget_no_price_data_fails_closed():
    """A mouse with no price on record can't be confirmed to fit the budget."""
    facts = {"budget": (50.0, 150.0), "prices": {}}
    assert not rules._budget_compatible(facts, _mouse(id=99))


def test_budget_explanation_above_within_below():
    facts = {"budget": (50.0, 150.0), "prices": {1: 200.0, 2: 100.0, 3: 10.0}}
    above = rules._budget_explanation(facts, _mouse(id=1))
    within = rules._budget_explanation(facts, _mouse(id=2))
    below = rules._budget_explanation(facts, _mouse(id=3))
    assert "exceeds" in above
    assert "fits within" in within
    assert "falls below" in below


# ── Value for money ────────────────────────────────────────────────────────

def test_value_weight_no_budget_or_price():
    assert rules._value_weight({"budget": None}, _mouse()) == 0.0
    assert rules._value_weight({"budget": (50.0, 150.0), "prices": {}}, _mouse(id=42)) == 0.0


def test_value_weight_zero_width_budget_uses_high_as_span():
    """low == high (a single-figure budget): span falls back to `high`, not
    a divide-by-zero."""
    facts = {"budget": (100.0, 100.0), "prices": {1: 100.0}}
    # relative = (high - price) / span = (100 - 100) / 100 = 0
    assert rules._value_weight(facts, _mouse(id=1)) == 0.0


def test_value_weight_degenerate_zero_budget_falls_back_to_one():
    """low == high == 0: span falls back to the literal 1.0, still no crash."""
    facts = {"budget": (0.0, 0.0), "prices": {1: 0.0}}
    assert rules._value_weight(facts, _mouse(id=1)) == 0.0


def test_value_weight_clips_at_plus_minus_1_5():
    facts = {"budget": (100.0, 200.0), "prices": {1: -1000.0, 2: 5000.0}}
    very_cheap = rules._value_weight(facts, _mouse(id=1))
    very_expensive = rules._value_weight(facts, _mouse(id=2))
    assert very_cheap == 1.5 * config.VALUE_FACTOR * rules._price_emphasis(facts)
    assert very_expensive == -1.5 * config.VALUE_FACTOR * rules._price_emphasis(facts)


def test_value_priority_emphasis_scaling():
    cheap_facts_price = {"value_priority": "price"}
    cheap_facts_perf = {"value_priority": "performance"}
    cheap_facts_neutral = {"value_priority": "balance"}
    assert rules._price_emphasis(cheap_facts_price) == config.PRICE_EMPHASIS
    assert rules._price_emphasis(cheap_facts_perf) == config.PRICE_DEEMPHASIS
    assert rules._price_emphasis(cheap_facts_neutral) == 1.0
    assert rules._performance_emphasis(cheap_facts_perf) == config.PERF_EMPHASIS
    assert rules._performance_emphasis(cheap_facts_price) == config.PERF_DEEMPHASIS
    assert rules._performance_emphasis(cheap_facts_neutral) == 1.0


# ── Left-handed ────────────────────────────────────────────────────────────

def test_left_hand_symmetrical_always_compatible():
    """A symmetrical shape works for left hands even without a left_fit flag."""
    mouse = _mouse(ergonomy=Ergonomy.SYMMETRICAL, left_fit=False)
    assert rules._left_hand_compatible({}, mouse)


def test_left_hand_ergonomic_requires_left_fit_flag():
    ergonomic_right_only = _mouse(ergonomy=Ergonomy.ERGONOMIC, left_fit=False)
    ergonomic_left_fit = _mouse(ergonomy=Ergonomy.ERGONOMIC, left_fit=True)
    assert not rules._left_hand_compatible({}, ergonomic_right_only)
    assert rules._left_hand_compatible({}, ergonomic_left_fit)


def test_left_hand_ambidextrous_is_not_treated_as_symmetrical():
    """AMBIDEXTROUS is a distinct enum value from SYMMETRICAL, so it still
    needs left_fit=True to pass — pinned since this reads easy to conflate."""
    mouse = _mouse(ergonomy=Ergonomy.AMBIDEXTROUS, left_fit=False)
    assert not rules._left_hand_compatible({}, mouse)


def test_left_hand_unknown_ergonomy_falls_back_to_left_fit_flag():
    mouse_no_fit = _mouse(ergonomy=None, left_fit=False)
    mouse_with_fit = _mouse(ergonomy=None, left_fit=True)
    assert not rules._left_hand_compatible({}, mouse_no_fit)
    assert rules._left_hand_compatible({}, mouse_with_fit)


# ── User type ──────────────────────────────────────────────────────────────

def test_user_type_gamer_needs_gaming_specs():
    gamer_facts = {"user_type": User_Type.GAMER}
    assert rules._type_of_user_weight(gamer_facts, _mouse(gaming_specs=_gaming())) == config.MODERATE_FACTOR
    assert rules._type_of_user_weight(gamer_facts, _mouse(gaming_specs=None)) == 0.0


def test_user_type_office_battery_boundary_is_exclusive():
    """Battery life must be strictly over 60h to count as 'good'."""
    office_facts = {"user_type": User_Type.OFFICE_WORKER}
    at_60 = _mouse(gaming_specs=None, min_battery_life=60)
    at_61 = _mouse(gaming_specs=None, min_battery_life=61)
    assert rules._type_of_user_weight(office_facts, at_60) == 0.0
    assert rules._type_of_user_weight(office_facts, at_61) == config.NORMAL_FACTOR


def test_user_type_office_missing_battery_life_no_crash():
    """A mouse with no min_battery_life recorded must score, not crash."""
    office_facts = {"user_type": User_Type.OFFICE_WORKER}
    mouse = _mouse(gaming_specs=None, min_battery_life=None)
    assert rules._type_of_user_weight(office_facts, mouse) == 0.0
    assert "isn't listed" in rules._type_of_user_explanation(office_facts, mouse)


def test_user_type_office_gaming_mouse_rgb_penalty_plus_battery():
    office_facts = {"user_type": User_Type.OFFICE_WORKER}
    mouse = _mouse(gaming_specs=_gaming(rgb=True), min_battery_life=100)
    expected = config.NEGATIVE_MINOR_FACTOR + config.NORMAL_FACTOR  # rgb penalty + good battery
    assert rules._type_of_user_weight(office_facts, mouse) == expected


def test_user_type_student_else_branch_missing_battery_no_crash():
    """STUDENT (and anything else not GAMER/OFFICE_WORKER) hits the 'else'
    branch, which used to crash on a None battery life too."""
    student_facts = {"user_type": User_Type.STUDENT}
    mouse = _mouse(min_battery_life=None)
    assert rules._type_of_user_weight(student_facts, mouse) == 0.0
    mouse_good_battery = _mouse(min_battery_life=61)
    assert rules._type_of_user_weight(student_facts, mouse_good_battery) == config.MODERATE_FACTOR


# ── Type of game (gamer) ──────────────────────────────────────────────────────

def test_mmorpg_button_boundary_and_missing_data():
    facts = {"type_of_game": Game_Type.MMORPG}
    at_minimum = _mouse(number_of_buttons=config.MINIMUM_BUTTONS_MMORPG)
    one_short = _mouse(number_of_buttons=config.MINIMUM_BUTTONS_MMORPG - 1)
    unknown = _mouse(number_of_buttons=None)
    assert rules._type_of_game_compatibility(facts, at_minimum)
    assert not rules._type_of_game_compatibility(facts, one_short)
    assert not rules._type_of_game_compatibility(facts, unknown)  # no crash


def test_mmorpg_and_not_mentioned_score_zero():
    """MMORPG is a HARD filter (buttons only); NOT_MENTIONED has nothing to
    score against. Neither contributes soft points."""
    mouse = _mouse(number_of_buttons=20, max_DPI=32000, weight=50, gaming_specs=_gaming())
    assert rules._type_of_game_points({"type_of_game": Game_Type.MMORPG}, mouse) == 0.0
    assert rules._type_of_game_points({"type_of_game": Game_Type.NOT_MENTIONED}, mouse) == 0.0
    assert rules._type_of_game_points({"type_of_game": None}, mouse) == 0.0


def test_fps_points_with_and_without_gaming_specs():
    facts = {"type_of_game": Game_Type.FPS}
    ideal_with_specs = _mouse(max_DPI=config.REQUIRED_DPI_FPS, weight=config.REQUIRED_MOUSE_WEIGHT_FPS,
                               gaming_specs=_gaming(tracking_speed=config.REQUIRED_TRACKING_SPEED_FPS))
    ideal_without_specs = _mouse(max_DPI=config.REQUIRED_DPI_FPS, weight=config.REQUIRED_MOUSE_WEIGHT_FPS,
                                  gaming_specs=None)
    # with gaming_specs: 3 criteria met * MODERATE_FACTOR
    assert rules._type_of_game_points(facts, ideal_with_specs) == 3 * config.MODERATE_FACTOR
    # without gaming_specs: only 2 criteria exist, weighted MAJOR_FACTOR instead
    assert rules._type_of_game_points(facts, ideal_without_specs) == 2 * config.MAJOR_FACTOR


def test_fps_missing_dpi_weight_tracking_no_crash():
    """A mouse missing every FPS-relevant spec must score 0, not raise."""
    facts = {"type_of_game": Game_Type.FPS}
    blank = _mouse(max_DPI=None, weight=None, gaming_specs=_gaming(tracking_speed=None))
    assert rules._type_of_game_points(facts, blank) == 0.0
    assert "isn't listed" in rules._type_of_game_explanation(facts, blank)


def test_rts_and_moba_dpi_and_polling_boundaries():
    rts_facts = {"type_of_game": Game_Type.RTS}
    moba_facts = {"type_of_game": Game_Type.MOBA}

    rts_ideal = _mouse(max_DPI=config.REQUIRED_DPI_RTS,
                        gaming_specs=_gaming(max_polling_rate=config.REQUIRED_POLLING_RATE_RTS))
    assert rules._type_of_game_points(rts_facts, rts_ideal) == 2 * config.MODERATE_FACTOR

    moba_ideal = _mouse(max_DPI=config.REQUIRED_DPI_MOBA,
                         gaming_specs=_gaming(max_polling_rate=config.REQUIRED_POLLING_RATE_MOBA))
    assert rules._type_of_game_points(moba_facts, moba_ideal) == 2 * config.NORMAL_FACTOR


def test_rts_missing_dpi_and_polling_no_crash():
    facts = {"type_of_game": Game_Type.RTS}
    blank = _mouse(max_DPI=None, gaming_specs=None)  # no gaming_specs -> polling_rate None too
    assert rules._type_of_game_points(facts, blank) == 0.0
    assert "isn't listed" in rules._type_of_game_explanation(facts, blank)


# ── Lightweight (gamer) ────────────────────────────────────────────────────

def test_mouse_weight_weightage_boundaries():
    at_light = _mouse(weight=config.LIGHT_WEIGHT)
    just_over_light = _mouse(weight=config.LIGHT_WEIGHT + 0.1)
    at_moderate = _mouse(weight=config.MODERATE_WEIGHT)
    just_over_moderate = _mouse(weight=config.MODERATE_WEIGHT + 0.1)
    assert rules._mouse_weight_weightage({}, at_light) == config.MAJOR_FACTOR
    assert rules._mouse_weight_weightage({}, just_over_light) == config.NORMAL_FACTOR
    assert rules._mouse_weight_weightage({}, at_moderate) == config.NORMAL_FACTOR
    assert rules._mouse_weight_weightage({}, just_over_moderate) == 0.0


def test_mouse_weight_weightage_missing_weight_no_crash():
    mouse = _mouse(weight=None)
    assert rules._mouse_weight_weightage({}, mouse) == 0.0
    assert "isn't listed" in rules._mouse_weight_explanation({}, mouse)


def test_mouse_weight_performance_emphasis_scales_result():
    light = _mouse(weight=config.LIGHT_WEIGHT)
    base = rules._mouse_weight_weightage({}, light)
    perf_priority = rules._mouse_weight_weightage({"value_priority": "performance"}, light)
    price_priority = rules._mouse_weight_weightage({"value_priority": "price"}, light)
    assert perf_priority == base * config.PERF_EMPHASIS
    assert price_priority == base * config.PERF_DEEMPHASIS


# ── RGB (gamer) ────────────────────────────────────────────────────────────

def test_rgb_weightage():
    assert rules._mouse_rgb_weightage({}, _mouse(gaming_specs=_gaming(rgb=True))) == config.MINOR_FACTOR
    assert rules._mouse_rgb_weightage({}, _mouse(gaming_specs=_gaming(rgb=False))) == 0.0
    assert rules._mouse_rgb_weightage({}, _mouse(gaming_specs=None)) == 0.0


# ── Travel portability (student) ──────────────────────────────────────────

def test_travel_portability_usage_bucket_factors():
    ideal = _mouse(weight=config.REQUIRED_WEIGHT_PORT, connectivity=_conn(dongle=True))
    expected_factor = {
        Usage.MOST_OF_THE_TIME: config.DOMINANT_FACTOR,
        Usage.OFTEN: config.MAJOR_FACTOR,
        Usage.OCCASIONALLY: config.MODERATE_FACTOR,
        Usage.RARELY: config.NORMAL_FACTOR,
        Usage.NEVER: config.MINOR_FACTOR,
    }
    for usage, factor in expected_factor.items():
        got = rules._travel_portability_weight({"travel_portability": usage}, ideal)
        assert got == 2 * factor, f"{usage}: expected {2 * factor}, got {got}"


def test_travel_portability_missing_connectivity_no_crash():
    """A mouse with no Mouse_Connectivity row must be treated as wired
    (not portable-wireless), not crash on `.bluetooth`."""
    facts = {"travel_portability": Usage.OFTEN}
    mouse = _mouse(connectivity=None, weight=config.REQUIRED_WEIGHT_PORT)
    # only the weight criterion can be met; wireless can't
    assert rules._travel_portability_weight(facts, mouse) == 1 * config.MAJOR_FACTOR
    assert "isn't listed" not in rules._travel_portability_explanation(facts, mouse)
    assert "wired connection limits portability" in rules._travel_portability_explanation(facts, mouse)


def test_travel_portability_missing_weight_no_crash():
    facts = {"travel_portability": Usage.OFTEN}
    mouse = _mouse(connectivity=_conn(dongle=True), weight=None)
    assert rules._travel_portability_weight(facts, mouse) == 1 * config.MAJOR_FACTOR
    assert "isn't listed" in rules._travel_portability_explanation(facts, mouse)


def test_travel_portability_unrecognised_usage_scores_zero():
    assert rules._travel_portability_weight({"travel_portability": None}, _mouse()) == 0.0


# ── Extra buttons (student & office) ──────────────────────────────────────

def test_extra_buttons_button_boundary_student():
    facts_yes = {"extra_buttons": Preferability.YES}
    facts_pref = {"extra_buttons": Preferability.PREFERABLY}
    at_min = _mouse(number_of_buttons=config.NUMBER_OF_BUTTONS)
    one_short = _mouse(number_of_buttons=config.NUMBER_OF_BUTTONS - 1)
    assert rules._extra_buttons_weight_student(facts_yes, at_min) == config.MODERATE_FACTOR
    assert rules._extra_buttons_weight_student(facts_yes, one_short) == 0.0
    assert rules._extra_buttons_weight_student(facts_pref, at_min) == config.NORMAL_FACTOR


def test_extra_buttons_no_preference_scores_zero_student():
    assert rules._extra_buttons_weight_student({"extra_buttons": Preferability.NO}, _mouse(number_of_buttons=20)) == 0.0
    assert rules._extra_buttons_weight_student({"extra_buttons": None}, _mouse(number_of_buttons=20)) == 0.0


def test_extra_buttons_missing_count_no_crash_student_and_office():
    mouse = _mouse(number_of_buttons=None)
    facts_yes = {"extra_buttons": Preferability.YES}
    assert rules._extra_buttons_weight_student(facts_yes, mouse) == 0.0
    assert rules._extra_buttons_weight_office(facts_yes, mouse) == 0.0
    assert "isn't listed" in rules._extra_buttons_explanation_student(facts_yes, mouse)
    assert "isn't listed" in rules._extra_buttons_explanation_office(facts_yes, mouse)


def test_extra_buttons_button_boundary_office():
    facts_yes = {"extra_buttons": Preferability.YES}
    at_min = _mouse(number_of_buttons=config.NUMBER_OF_BUTTONS)
    one_short = _mouse(number_of_buttons=config.NUMBER_OF_BUTTONS - 1)
    assert rules._extra_buttons_weight_office(facts_yes, at_min) == config.MODERATE_FACTOR
    assert rules._extra_buttons_weight_office(facts_yes, one_short) == 0.0


# ── Long hours (office) ────────────────────────────────────────────────────

def test_work_long_hours_usage_bucket_factors_when_ergonomic():
    ergonomic = _mouse(ergonomy=Ergonomy.ERGONOMIC)
    expected_factor = {
        Usage.MOST_OF_THE_TIME: config.ERGONOMY_FACTOR,
        Usage.OFTEN: config.DOMINANT_FACTOR,
        Usage.OCCASIONALLY: config.MAJOR_FACTOR,
        Usage.RARELY: config.MODERATE_FACTOR,
        Usage.NEVER: config.MINOR_FACTOR,
    }
    for usage, factor in expected_factor.items():
        got = rules._work_long_hours({"hours_worked": usage}, ergonomic)
        assert got == factor, f"{usage}: expected {factor}, got {got}"


def test_work_long_hours_non_ergonomic_always_zero():
    symmetrical = _mouse(ergonomy=Ergonomy.SYMMETRICAL)
    for usage in Usage:
        assert rules._work_long_hours({"hours_worked": usage}, symmetrical) == 0.0


def test_work_long_hours_unknown_ergonomy_no_crash():
    mouse = _mouse(ergonomy=None)
    assert rules._work_long_hours({"hours_worked": Usage.OFTEN}, mouse) == 0.0


# ── Rule dict wiring ───────────────────────────────────────────────────────

_ALL_RULE_DICTS = [rules.GENERAL_RULES, rules.GAMER_RULES, rules.STUDENT_RULES, rules.OFFICE_RULES]


def test_every_rule_key_matches_its_own_id():
    """recommend.py looks rules up by id in several places; a mismatched key
    would silently orphan a rule."""
    for rule_dict in _ALL_RULE_DICTS:
        for key, rule in rule_dict.items():
            assert key == rule.id, f"dict key {key!r} != rule.id {rule.id!r}"


def test_fixed_hard_rules_are_hard():
    for rule_id in (config.HAND_SIZE, config.BUDGET, config.LEFT_HANDED):
        assert rules.GENERAL_RULES[rule_id].rule_type == RuleType.HARD


def test_conditional_rule_types_are_callables():
    """CONNECTIVITY and TYPE_OF_GAME decide HARD vs SOFT from facts, so their
    rule_type must be a function, not a fixed RuleType."""
    assert callable(rules.GENERAL_RULES[config.CONNECTIVITY].rule_type)
    assert callable(rules.GAMER_RULES[config.TYPE_OF_GAME].rule_type)


def test_applicable_to_users_gates_on_missing_facts():
    """Spot-check a representative rule from each group: no answer for its
    fact -> not applicable; an answer -> applicable."""
    hand_rule = rules.GENERAL_RULES[config.HAND_SIZE]
    assert not hand_rule.applicable_to_users({})
    assert hand_rule.applicable_to_users({"hand_size": Hand_Size.SMALL})

    game_rule = rules.GAMER_RULES[config.TYPE_OF_GAME]
    assert not game_rule.applicable_to_users({})
    assert game_rule.applicable_to_users({"type_of_game": Game_Type.FPS})

    travel_rule = rules.STUDENT_RULES[config.TRAVEL_PORTABILITY]
    assert not travel_rule.applicable_to_users({})
    assert travel_rule.applicable_to_users({"travel_portability": Usage.OFTEN})

    hours_rule = rules.OFFICE_RULES[config.LONG_HOURS]
    assert not hours_rule.applicable_to_users({})
    assert hours_rule.applicable_to_users({"hours_worked": Usage.OFTEN})


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for _t in _tests:
        _t()
        print("OK", _t.__name__)
    print("ALL PASSED")

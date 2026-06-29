"""
Expected answers
---------------------
General Questions (all users):
  hand_size        : "small" | "medium" | "large"
  wireless         : "yes" | "preferably" | "no"
  budget_min       : number
  budget_max       : number
  left_hand        : bool
  user_type        : "gamer" | "office_worker" | "student"

Gamer Questions:
  type_of_game     : "fps" | "rts" | "moba" | "mmorpg" | "none_of_the_above"
  light_weight     : bool
  rgb              : bool

Student Questions:
  travel_portability : "most_of_the_time" | "often" | "occasionally" | "rarely" | "never"
  extra_buttons      : "yes" | "preferably" | "no"

Office worker Questions:
  hours_worked    : "most_of_the_stime" | "often" | "occasionally" | "rarely" | "never"
  extra_buttons   : "yes" | "preferably" | "no"
"""

from .classes import Hand_Size, Game_Type, Preferability, Connectivity, RuleType, Usage, User_Type
from .rules import GENERAL_RULES, GAMER_RULES, STUDENT_RULES, OFFICE_RULES
from . import engine
from . import config
from database.models import Ergonomy


# Short, tag-friendly labels for each rule, surfaced as criterion chips on the
# recommendations page. Falls back to the raw rule id if a label is missing.
CRITERION_LABELS = {
    config.HAND_SIZE: "Hand size",
    config.CONNECTIVITY: "Connectivity",
    config.BUDGET: "Price",
    config.LEFT_HANDED: "Left-handed",
    config.USER_TYPE: "Usage fit",
    config.TYPE_OF_GAME: "Game genre",
    config.LIGHT_WEIGHT_MOUSE: "Lightweight",
    config.RGB_LIGHTING: "RGB",
    config.TRAVEL_PORTABILITY: "Portability",
    config.EXTRA_BUTTONS_REQUIRED: "Extra buttons",
    config.LONG_HOURS: "Ergonomics",
    config.SHORTCUT_BUTTONS_REQUIRED: "Shortcut buttons",
}

# A price outside the budget but within this fraction of the nearer bound is a
# "neutral" near-miss rather than a hard "doesn't fit".
BUDGET_NEUTRAL_BAND = 0.25


def _connectivity(wireless_value, wired_too):
    """Combine the wireless preference (Q15) and the wired-too follow-up (Q16)
    into a desired connectivity product type."""
    if wireless_value is None:
        return None
    if wireless_value == "no":
        return Connectivity.STRICTLY_WIRED
    # "yes" / "preferably": want wireless; "wired too" means they also want a cable
    return Connectivity.BOTH if wired_too else Connectivity.STRICTLY_WIRELESS


def recommend(payload: dict, candidates: list) -> dict:
    """
    payload — data from frontend
    candidates — Mouse ORM objects

    Returns:
      {
        "passed_rules": [...rule ids...],
        "failed_rules": [...rule ids...],
        "results":      [ { id, product_name, brand_name, score, explanations }, ... ]
      }
    """
    facts = _build_facts(payload)
    rules = _select_rules(facts)
    bundles = engine.run(facts, candidates, rules)

    if not bundles:
        return {"passed_rules": [], "failed_rules": [], "results": []}

    applicable_rules = [r for r in rules if r.applicable_to_users(facts)]
    soft_rules = [r for r in applicable_rules if _is_soft(r, facts)]

    # Hard rules don't exclude anything — every candidate is returned. Bundles
    # that passed more hard rules come first, so mice that don't fit are pushed
    # below the ones that do; within a bundle they're ordered by soft score.
    results = []
    for bundle in reversed(bundles):  # bundles are sorted ascending by priority
        results.extend(_format_mice(facts, bundle, applicable_rules, soft_rules))

    best = bundles[-1]
    return {
        "passed_rules": best.passed_hard_rules,
        "failed_rules": best.failed_hard_rules,
        "results": results,
    }


def _is_soft(rule, facts) -> bool:
    rule_type = rule.rule_type(facts) if callable(rule.rule_type) else rule.rule_type
    return rule_type != RuleType.HARD


def _build_facts(payload: dict) -> dict:
    def _enum(cls, value):
        if value is None:
            return None
        try:
            return cls(value)
        except ValueError:
            return None

    budget_min = payload.get("budget_min")
    budget_max = payload.get("budget_max")

    wireless_value = payload.get("wireless")

    return {
        "hand_size":_enum(Hand_Size, payload.get("hand_size")),
        "wireless":_enum(Preferability, payload.get("wireless")),
        "budget":(float(budget_min), float(budget_max))
                if budget_min is not None and budget_max is not None
                else None,
        "left_hand":payload.get("left_hand"),
        "user_type":_enum(User_Type, payload.get("user_type")),
        "type_of_game":_enum(Game_Type, payload.get("type_of_game")),
        "light_weight":payload.get("light_weight"),
        "rgb":payload.get("rgb"),
        "travel_portability":_enum(Usage, payload.get("travel_portability")),
        "extra_buttons":_enum(Preferability, payload.get("extra_buttons")),
        "hours_worked":_enum(Usage, payload.get("hours_worked")),
    }


def _select_rules(facts: dict) -> list:
    rules = list(GENERAL_RULES.values())

    user_type = facts.get("user_type")
    if user_type == User_Type.GAMER:
        rules += list(GAMER_RULES.values())
    elif user_type == User_Type.STUDENT:
        rules += list(STUDENT_RULES.values())
    elif user_type == User_Type.OFFICE_WORKER:
        rules += list(OFFICE_RULES.values())

    return rules


def _budget_status(facts: dict, mouse):
    """Three-way price fit: inside budget -> fit; outside but within the neutral
    band -> neutral; further out -> unfit. None when price/budget is unknown."""
    budget = facts.get("budget")
    prices = facts.get("prices") or {}
    price = prices.get(getattr(mouse, "id", None))
    if budget is None or price is None:
        return None
    low, high = budget
    if low <= price <= high:
        return "fit"
    if low * (1 - BUDGET_NEUTRAL_BAND) <= price < low or high < price <= high * (1 + BUDGET_NEUTRAL_BAND):
        return "neutral"
    return "unfit"


def _criterion_status(facts: dict, mouse, rule, bundle) -> str:
    """fit | unfit | neutral for one rule against one mouse.

    Hard rules: passed -> fit, failed -> unfit (price gets a neutral near-miss
    band). Soft rules: positive score -> fit, negative -> unfit, no effect ->
    neutral.
    """
    if rule.id == config.BUDGET:
        budget_status = _budget_status(facts, mouse)
        if budget_status is not None:
            return budget_status

    rule_type = rule.rule_type(facts) if callable(rule.rule_type) else rule.rule_type
    if rule_type == RuleType.HARD:
        return "fit" if rule.id in bundle.passed_hard_rules else "unfit"

    points = rule.points(facts, mouse)
    if points > 0:
        return "fit"
    if points < 0:
        return "unfit"
    return "neutral"


# ── Specific, mouse-aware tag labels ──────────────────────────────────────────
# Each returns a short, concrete descriptor of THIS mouse for the criterion
# (e.g. "Wired + wireless", "Expensive", "8 buttons") rather than the generic
# category name. Signature: (facts, mouse, status) -> str.

def _label_connectivity(facts, mouse, status):
    conn = getattr(mouse, "connectivity", None)
    if conn is None:
        return "Connectivity"
    wireless = bool(conn.bluetooth or conn.dongle)
    wired = bool(conn.wired)
    if wireless and wired:
        return "Wired + wireless"
    if wireless:
        return "Wireless"
    if wired:
        return "Wired"
    return "Connectivity"


def _label_price(facts, mouse, status):
    budget = facts.get("budget")
    prices = facts.get("prices") or {}
    price = prices.get(getattr(mouse, "id", None))
    if budget is None or price is None:
        return "Price"
    low, high = budget
    if low <= price <= high:
        return "In budget"
    if price > high:
        return "A bit pricey" if status == "neutral" else "Expensive"
    return "A bit cheap" if status == "neutral" else "Below budget"


def _label_hand_size(facts, mouse, status):
    if status == "fit":
        return "Right size"
    hand = facts.get("hand_size")
    length = getattr(mouse, "length", None)
    if length is None:
        return "Size unknown"
    if hand == Hand_Size.SMALL:
        return "Too large"
    if hand == Hand_Size.LARGE:
        return "Too small"
    if length > config.MEDIUM_HAND_SIZE:
        return "Too large"
    if length < config.SMALL_HAND_SIZE:
        return "Too small"
    return "Right size"


def _label_left_hand(facts, mouse, status):
    return "Left-friendly" if getattr(mouse, "left_fit", False) else "Right-hand shape"


def _label_usage(facts, mouse, status):
    if facts.get("user_type") == User_Type.GAMER:
        return "Gaming-grade" if getattr(mouse, "gaming_specs", None) is not None else "Not gaming-focused"
    battery = getattr(mouse, "min_battery_life", None)
    return "Long battery" if (battery is not None and battery > 60) else "Short battery"


_GENRE_NAME = {
    Game_Type.FPS: "FPS",
    Game_Type.MMORPG: "MMORPG",
    Game_Type.RTS: "RTS",
    Game_Type.MOBA: "MOBA",
}


def _label_game(facts, mouse, status):
    name = _GENRE_NAME.get(facts.get("type_of_game"))
    if name is None:
        return "Game specs"
    if name == "MMORPG":
        return "Enough buttons" if status == "fit" else "Too few buttons"
    return f"{name}-ready" if status == "fit" else f"Weak for {name}"


def _label_weight(facts, mouse, status):
    weight = getattr(mouse, "weight", None)
    if not weight:
        return "Weight"
    if weight <= config.LIGHT_WEIGHT:
        return "Lightweight"
    if weight <= config.MODERATE_WEIGHT:
        return "Mid-weight"
    return "Heavy"


def _label_rgb(facts, mouse, status):
    gaming = getattr(mouse, "gaming_specs", None)
    return "Has RGB" if (gaming is not None and gaming.rgb) else "No RGB"


def _label_portability(facts, mouse, status):
    return "Portable" if status == "fit" else "Less portable"


def _label_buttons(facts, mouse, status):
    count = getattr(mouse, "number_of_buttons", None)
    return f"{count} buttons" if count else "Buttons"


def _label_ergonomics(facts, mouse, status):
    return "Ergonomic" if getattr(mouse, "ergonomy", None) == Ergonomy.ERGONOMIC else "Not ergonomic"


CRITERION_LABEL_FUNCS = {
    config.CONNECTIVITY: _label_connectivity,
    config.BUDGET: _label_price,
    config.HAND_SIZE: _label_hand_size,
    config.LEFT_HANDED: _label_left_hand,
    config.USER_TYPE: _label_usage,
    config.TYPE_OF_GAME: _label_game,
    config.LIGHT_WEIGHT_MOUSE: _label_weight,
    config.RGB_LIGHTING: _label_rgb,
    config.TRAVEL_PORTABILITY: _label_portability,
    config.EXTRA_BUTTONS_REQUIRED: _label_buttons,
    config.SHORTCUT_BUTTONS_REQUIRED: _label_buttons,
    config.LONG_HOURS: _label_ergonomics,
}


def _criterion_label(facts, mouse, rule, status) -> str:
    func = CRITERION_LABEL_FUNCS.get(rule.id)
    if func is not None:
        return func(facts, mouse, status)
    return CRITERION_LABELS.get(rule.id, rule.id)


def _criteria(facts: dict, mouse, bundle, applicable_rules: list) -> list:
    """Per-criterion tags for a mouse: a specific mouse-aware label, a fit status,
    and the full explanation (used as the tag's tooltip on the frontend)."""
    out = []
    for rule in applicable_rules:
        status = _criterion_status(facts, mouse, rule, bundle)
        out.append({
            "label": _criterion_label(facts, mouse, rule, status),
            "status": status,
            "detail": rule.explain(facts, mouse),
        })
    return out


def _format_mice(facts: dict, bundle, applicable_rules: list, soft_rules: list) -> list:
    results = []

    for mouse in bundle.candidates:
        score = sum(r.points(facts, mouse) for r in soft_rules)
        explanations = {r.id: r.explain(facts, mouse) for r in applicable_rules}

        results.append({
            "id":           mouse.id,
            "product_name": mouse.product_name,
            "brand_name":   mouse.brand_name,
            "score":        score,
            "passed_rules": list(bundle.passed_hard_rules),
            "failed_rules": list(bundle.failed_hard_rules),
            "explanations": explanations,
            "criteria":     _criteria(facts, mouse, bundle, applicable_rules),
        })

    results.sort(key=lambda m: m["score"], reverse=True)
    return results
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
    payload    — raw key/value data from the frontend form submission.
    candidates — Mouse ORM objects provided by the API route.

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
        "hand_size":          _enum(Hand_Size, payload.get("hand_size")),
        "wireless":           _enum(Preferability, wireless_value),
        "connectivity":       _connectivity(wireless_value, payload.get("wired_too")),
        # a definitive yes/no filters; "preferably" only scores
        "connectivity_strict": wireless_value in ("yes", "no"),
        "budget":             (float(budget_min), float(budget_max))
                              if budget_min is not None and budget_max is not None
                              else None,
        "left_hand":          payload.get("left_hand"),
        "user_type":          _enum(User_Type, payload.get("user_type")),
        "type_of_game":       _enum(Game_Type, payload.get("type_of_game")),
        "light_weight":       payload.get("light_weight"),
        "rgb":                payload.get("rgb"),
        "travel_portability": _enum(Usage, payload.get("travel_portability")),
        "extra_buttons":      _enum(Preferability, payload.get("extra_buttons")),
        "hours_worked":       _enum(Usage, payload.get("hours_worked")),
        # preloaded {mouse_id: price} so budget scoring needs no per-mouse query
        "prices":             payload.get("prices"),
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
        })

    results.sort(key=lambda m: m["score"], reverse=True)
    return results
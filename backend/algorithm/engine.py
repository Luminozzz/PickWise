from .classes import Bundle, RuleType


def run(facts: dict, candidates: list, rules: list) -> list[Bundle]:
    """
    Returns bundles sorted ascending by relevance — index -1 is the best match.
    """
    applicable = [r for r in rules if r.applicable_to_users(facts)]

    bundles = [Bundle(candidates=candidates, passed_hard_rules=[], failed_hard_rules=[])]

    for rule in applicable:
        # rule_type may be a callable that decides HARD/SOFT from the facts
        # (e.g. connectivity is HARD on a definitive yes/no, SOFT on "preferably").
        rule_type = rule.rule_type(facts) if callable(rule.rule_type) else rule.rule_type
        if rule_type == RuleType.HARD:
            next_bundles = []
            for bundle in bundles:
                passed = [m for m in bundle.candidates if rule.mouse_compatibility(facts, m)]
                failed = [m for m in bundle.candidates if not rule.mouse_compatibility(facts, m)]
                if passed:
                    next_bundles.append(Bundle(
                        candidates=passed,
                        passed_hard_rules=bundle.passed_hard_rules + [rule.id],
                        failed_hard_rules=bundle.failed_hard_rules,
                        score=bundle.score,
                    ))
                if failed:
                    next_bundles.append(Bundle(
                        candidates=failed,
                        passed_hard_rules=bundle.passed_hard_rules,
                        failed_hard_rules=bundle.failed_hard_rules + [rule.id],
                        score=bundle.score,
                    ))
            bundles = next_bundles
        else:  # SOFT rule
            for bundle in bundles:
                bundle.score += sum(rule.points(facts, m) for m in bundle.candidates)

    bundles.sort(key=lambda b: b.priority)
    return bundles

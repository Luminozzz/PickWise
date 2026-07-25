"""
Unit tests for backend/algorithm/engine.py — the core bundle-splitting/scoring
loop, in isolation from the real rules (rules.py) and the database.

engine.run() only ever touches the Rule interface (applicable_to_users,
rule_type, mouse_compatibility, points) and plain candidate objects, so every
rule here is a hand-built algorithm.classes.Rule with no DB-backed mouse
fields required — candidates are bare strings/objects. This pins the
engine's own contract (bundle splitting, priority ordering, callable
rule_type/applicable_to_users) separately from test_recommend.py, which
exercises engine.run() together with the real rules and mock ORM mice.

Run from the backend/ directory:
    python test_engine.py           # runs every test_* below, exits non-zero on failure
    pytest test_engine.py           # same tests, discovered by name
"""

import sys, os

BACKEND = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND)
for _p in (PROJECT_ROOT, BACKEND, os.path.join(BACKEND, "algorithm")):
    sys.path.insert(0, _p)

from algorithm import engine
from algorithm.classes import Rule, RuleType


def _hard_rule(id, ok_ids):
    """A HARD rule that passes only candidates whose id is in ok_ids."""
    return Rule(
        id=id,
        rule_type=RuleType.HARD,
        description=id,
        applicable_to_users=lambda facts: True,
        mouse_compatibility=lambda facts, m: m in ok_ids,
    )


def _soft_rule(id, points_by_id):
    """A SOFT rule awarding points_by_id.get(candidate, 0) per candidate."""
    return Rule(
        id=id,
        rule_type=RuleType.SOFT,
        description=id,
        applicable_to_users=lambda facts: True,
        mouse_compatibility=True,
        weight=lambda facts, m: points_by_id.get(m, 0),
    )


CANDIDATES = ["A", "B", "C", "D"]


def test_no_applicable_rules_returns_single_bundle():
    """No rules apply -> one bundle holding every candidate, untouched."""
    bundles = engine.run({}, CANDIDATES, [])
    assert len(bundles) == 1
    assert bundles[0].candidates == CANDIDATES
    assert bundles[0].passed_hard_rules == []
    assert bundles[0].failed_hard_rules == []
    assert bundles[0].score == 0.0


def test_inapplicable_rule_is_skipped():
    """A rule whose applicable_to_users(facts) is False must not run at all."""
    rule = _hard_rule("R", ok_ids={"A"})
    rule.applicable_to_users = lambda facts: False
    bundles = engine.run({}, CANDIDATES, [rule])
    assert len(bundles) == 1
    assert bundles[0].candidates == CANDIDATES
    assert bundles[0].passed_hard_rules == []


def test_hard_rule_splits_into_pass_and_fail_bundles():
    """A HARD rule must produce exactly two bundles: passers and failers,
    each tagged with the rule id on the correct side."""
    rule = _hard_rule("HAND_SIZE", ok_ids={"A", "B"})
    bundles = engine.run({}, CANDIDATES, [rule])
    assert len(bundles) == 2

    by_tag = {tuple(sorted(b.candidates)): b for b in bundles}
    passed = by_tag[("A", "B")]
    failed = by_tag[("C", "D")]
    assert passed.passed_hard_rules == ["HAND_SIZE"]
    assert passed.failed_hard_rules == []
    assert failed.passed_hard_rules == []
    assert failed.failed_hard_rules == ["HAND_SIZE"]


def test_hard_rule_all_pass_yields_single_bundle():
    """If every candidate passes, no empty 'failed' bundle should appear."""
    rule = _hard_rule("R", ok_ids=set(CANDIDATES))
    bundles = engine.run({}, CANDIDATES, [rule])
    assert len(bundles) == 1
    assert sorted(bundles[0].candidates) == sorted(CANDIDATES)
    assert bundles[0].passed_hard_rules == ["R"]


def test_hard_rule_all_fail_yields_single_bundle():
    """If nothing passes, no empty 'passed' bundle should appear."""
    rule = _hard_rule("R", ok_ids=set())
    bundles = engine.run({}, CANDIDATES, [rule])
    assert len(bundles) == 1
    assert sorted(bundles[0].candidates) == sorted(CANDIDATES)
    assert bundles[0].failed_hard_rules == ["R"]


def test_two_hard_rules_cascade_into_four_bundles():
    """Each HARD rule bisects every existing bundle, so two independent HARD
    rules over 4 candidates can split into up to 2*2 = 4 bundles."""
    r1 = _hard_rule("R1", ok_ids={"A", "B"})   # A,B pass / C,D fail
    r2 = _hard_rule("R2", ok_ids={"A", "C"})   # A,C pass / B,D fail
    bundles = engine.run({}, CANDIDATES, [r1, r2])

    by_tag = {tuple(sorted(b.candidates)): b for b in bundles}
    assert set(by_tag.keys()) == {("A",), ("B",), ("C",), ("D",)}
    assert by_tag[("A",)].passed_hard_rules == ["R1", "R2"]
    assert by_tag[("B",)].passed_hard_rules == ["R1"]
    assert by_tag[("B",)].failed_hard_rules == ["R2"]
    assert by_tag[("C",)].passed_hard_rules == ["R2"]
    assert by_tag[("C",)].failed_hard_rules == ["R1"]
    assert by_tag[("D",)].failed_hard_rules == ["R1", "R2"]


def test_soft_rule_scores_without_filtering():
    """A SOFT rule never drops or splits candidates — it only adds to the
    bundle's aggregate score."""
    rule = _soft_rule("VALUE", {"A": 5, "B": -2})
    bundles = engine.run({}, CANDIDATES, [rule])
    assert len(bundles) == 1
    assert bundles[0].candidates == CANDIDATES
    # score is summed over every candidate in the bundle: 5 + (-2) + 0 + 0
    assert bundles[0].score == 3


def test_soft_rule_applies_independently_per_bundle():
    """After a HARD split, a later SOFT rule must score each resulting bundle
    using only its own candidates, not the original full list."""
    hard = _hard_rule("R", ok_ids={"A", "B"})
    soft = _soft_rule("S", {"A": 1, "B": 1, "C": 10, "D": 10})
    bundles = engine.run({}, CANDIDATES, [hard, soft])

    by_tag = {tuple(sorted(b.candidates)): b for b in bundles}
    assert by_tag[("A", "B")].score == 2
    assert by_tag[("C", "D")].score == 20


def test_callable_rule_type_switches_hard_or_soft_per_facts():
    """rule_type may be a callable deciding HARD/SOFT from facts (e.g.
    connectivity: HARD on a strict yes/no, SOFT on 'preferably')."""
    rule = Rule(
        id="CONN",
        rule_type=lambda facts: RuleType.HARD if facts.get("strict") else RuleType.SOFT,
        description="conn",
        applicable_to_users=lambda facts: True,
        mouse_compatibility=lambda facts, m: m == "A",
        weight=lambda facts, m: 7 if m == "A" else 0,
    )

    strict_bundles = engine.run({"strict": True}, CANDIDATES, [rule])
    assert len(strict_bundles) == 2  # HARD path: split into pass/fail

    loose_bundles = engine.run({"strict": False}, CANDIDATES, [rule])
    assert len(loose_bundles) == 1  # SOFT path: no split, just scored
    assert loose_bundles[0].score == 7


def test_bundles_sorted_ascending_by_priority_best_last():
    """Bundle.priority is (hard rules passed, score); more passes ranks
    higher, and within equal passes, the higher score ranks higher. The
    engine returns bundles ascending, so index -1 is the best match."""
    rule = _hard_rule("R", ok_ids={"A", "B"})  # A,B pass; C,D fail
    bundles = engine.run({}, CANDIDATES, [rule])
    priorities = [b.priority for b in bundles]
    assert priorities == sorted(priorities), "bundles must be ascending by priority"
    assert bundles[-1].passed_hard_rules == ["R"], "the best bundle should be the one that passed"


def test_empty_candidates_no_crash():
    """No candidates in -> the single starting bundle carries an empty list,
    and any HARD rule that finds nothing to split just vanishes cleanly."""
    rule = _hard_rule("R", ok_ids={"A"})
    bundles = engine.run({}, [], [rule])
    assert bundles == []


def test_rule_order_preserved_in_passed_and_failed_lists():
    """passed_hard_rules / failed_hard_rules must record rules in the order
    they were applied, matching the order they were passed in."""
    r1 = _hard_rule("FIRST", ok_ids=set(CANDIDATES))
    r2 = _hard_rule("SECOND", ok_ids=set(CANDIDATES))
    bundles = engine.run({}, CANDIDATES, [r1, r2])
    assert len(bundles) == 1
    assert bundles[0].passed_hard_rules == ["FIRST", "SECOND"]


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for _t in _tests:
        _t()
        print("OK", _t.__name__)
    print("ALL PASSED")

# PickWise recommendation algorithm

Turns a filled-in questionnaire and a list of candidate mice into a ranked,
explained recommendation list. This document covers how the pieces fit
together and what the test suite in `backend/` checks. For the full
question-by-question wiring (which quiz answer maps to which DB column and
rule), see [`QUESTION_MAP.md`](QUESTION_MAP.md).

## Files

| File | Responsibility |
|---|---|
| `classes.py` | Enums (`Hand_Size`, `Game_Type`, `Connectivity`, ...) and the two core dataclasses: `Rule` and `Bundle`. |
| `config.py` | Every tunable constant — thresholds (DPI, weight, hand-size cutoffs) and scoring weights (`MAJOR_FACTOR`, `NEGATIVE_MINOR_FACTOR`, ...). Change numbers here, not in the logic files. |
| `rules.py` | The actual `Rule` objects, grouped into `GENERAL_RULES` (everyone), `GAMER_RULES`, `STUDENT_RULES`, `OFFICE_RULES`. Each rule is a compatibility check (hard) or a weight function (soft) plus a human-readable explanation. |
| `engine.py` | `run(facts, candidates, rules)` — the generic bundle-splitting/scoring loop. Knows nothing about mice or questionnaires, only the `Rule` interface. |
| `recommend.py` | The public API: builds `facts` from the raw questionnaire payload, picks the right rule set for the user type, calls `engine.run`, then formats the ranked results (scores, pass/fail tags, per-criterion explanations) for the frontend. Also powers the product-detail and compare pages. |

## How a recommendation is built

```
payload (raw questionnaire answers)
        │  _build_facts()
        ▼
facts (typed dict: Hand_Size, Connectivity, budget tuple, ...)
        │  _select_rules() — GENERAL + rules for the user's type
        ▼
rules (list[Rule])
        │  engine.run(facts, candidates, rules)
        ▼
bundles (list[Bundle], ascending priority — best is last)
        │  _format_mice() per bundle, reversed
        ▼
results (ranked list of {id, score, passed_rules, failed_rules, explanations, criteria})
```

### The engine's bundle model

`engine.run` starts with **one bundle holding every candidate** and folds in
each applicable rule in order:

- **HARD rule** — splits every current bundle in two: candidates that pass
  keep the bundle's `passed_hard_rules` with this rule's id appended;
  candidates that fail keep `failed_hard_rules` with this rule's id appended.
  A bundle that would end up empty on one side is simply not created — hard
  rules **reorder, never delete**: every candidate that went in comes back
  out in some bundle.
- **SOFT rule** — never splits anything. It just adds `rule.points(facts, m)`
  for every candidate `m` in the bundle to that bundle's aggregate `score`.

A `Rule.rule_type` can also be a callable that decides HARD vs SOFT from the
facts themselves — e.g. connectivity is HARD when the user gave a strict
yes/no answer, but only SOFT (a scoring nudge) when they said "preferably".

Bundles are finally sorted by `Bundle.priority = (len(passed_hard_rules),
score)`, ascending, so `bundles[-1]` — the last one — is the best match.
`recommend()` walks the bundles in reverse (best bundle first) and, within
each bundle, re-scores and sorts the individual mice by their own per-mouse
soft-rule total (the bundle-level `score` is only used to rank *bundles*
against each other, not to rank mice within one).

### Rule types at a glance

- **Hard** rules exclude nothing from the final result — they only push
  non-conforming mice further down (see `test_every_candidate_survives`).
  Example: hand size, budget, left-hand fit.
- **Soft** rules add or subtract points. Example: value-for-money, RGB
  preference, ergonomics for long work hours.

### Missing mouse specs never crash a rule

Several `Mouse` columns are nullable (`weight`, `max_DPI`, `min_battery_life`,
`number_of_buttons`, the whole `connectivity` row, `gaming_specs.tracking_speed`)
— a scraped mouse can legitimately be missing any of them. Every rule in
`rules.py` treats an unknown spec as **"doesn't meet the requirement"** (0
score / hard-filter fail) rather than crashing, the same way `_hand_size_compatible`
has always treated a missing `length`. `test_rules.py` pins this for every
rule that reads a nullable column.

### A known quirk: the budget "±5% buffer" is much wider in practice

`_budget_compatible`'s buffer formula uses 95% of the budget's *midpoint* as
slack on each side, not 5% of each bound — for a $50–150 budget the real
accepted band is roughly **-$45 to $245**, not $47.50–$157.50. This makes the
BUDGET hard rule far more permissive than the "±5%" name and `QUESTION_MAP.md`
suggest. It's left as-is intentionally (a formula change would shift ranking
for every user), so `test_budget_buffer_matches_documented_formula` pins the
*actual* wide band precisely — if the formula is ever tightened, that test
will need updating deliberately, not accidentally pass or fail.

## Tests

All tests live in `backend/` (not inside the `algorithm/` package) and use
plain `assert` + a `test_*` naming convention, runnable with either `python
file.py` or `pytest`. None of them touch a real database — mice are
`SimpleNamespace` stand-ins or bare values, and rules are either the real
ones or hand-built mocks.

```bash
cd backend
python -m pytest test_engine.py test_rules.py test_recommend.py test_product.py test_compare.py -v
```

| File | Scope | What it pins down |
|---|---|---|
| `test_engine.py` | `engine.run()` in isolation, with mock `Rule` objects (no DB, no real rules) | Bundle splitting on HARD rules, that empty pass/fail sides don't create phantom bundles, SOFT rules only scoring (never filtering), callable `rule_type` switching HARD/SOFT per-facts, bundle priority ordering, rule-id ordering in `passed_hard_rules`/`failed_hard_rules`, and the empty-candidates edge case. |
| `test_rules.py` | Every individual rule function in `rules.py`, called directly (not through `recommend()`) | Boundary values at exact config thresholds (hand length at 115/130mm, weight at 80/100g, buttons at 6/10, battery at 60h), every enum bucket (`Preferability`, `Usage`, `Game_Type`, `Connectivity`), the budget buffer's actual (wide) band, and — the main edge-case focus — mice missing a nullable spec (`weight`, `max_DPI`, `min_battery_life`, `number_of_buttons`, `connectivity`, `tracking_speed`) scoring gracefully instead of raising. Also sanity-checks the rule dicts themselves: dict key == `rule.id`, HARD rules are actually `RuleType.HARD`, conditional rules expose a callable `rule_type`. |
| `test_recommend.py` | `recommend()` end-to-end with the real rules and mock ORM-like mice | Behavioural regressions, not exact scores: a lightweight mouse must rank first for a weight-conscious FPS gamer, a heavy one must rank last for a travelling student, results always come back sorted, every candidate always survives, and the result shape (`passed_rules`/`failed_rules`/`results` keys) is stable. |
| `test_product.py` | `product_detail()` — the single-mouse spec page | Spec rows are ordered by what matters to the user's type, a mouse missing a spec (e.g. no `gaming_specs`) just drops that row, hidden rules (`VALUE_FOR_MONEY`) never surface as a criterion tag, and an unanswered quiz falls back to a sane default order. |
| `test_compare.py` | `compare_detail()` — the side-by-side comparison table | Rows stay aligned (one cell per mouse) even when one mouse lacks a spec the other has (null cell, not a dropped row), and a row is dropped only when *nobody* in the group has that spec. |

`test_engine.py` exercises the engine's own contract in isolation;
`test_rules.py` exercises each rule's own contract in isolation; the other
three exercise engine + rules together through the public API, so between
them a change to the generic splitting/scoring logic, an individual rule's
behaviour, or the result formatting should all show up as a failing test.

Everything above passed as of this writing (88 tests total: 12 + 52 + 7 + 7
+ 7 across the five algorithm test files, plus 3 in `test_profile.py`, which
covers the unrelated preference-profile persistence layer).

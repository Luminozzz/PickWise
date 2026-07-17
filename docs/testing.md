# Tests

All of this runs on GitHub Actions on every push and every pull request. Red means don't merge. You can run the same tests locally; commands are at the bottom.

There are 24 tests in five files, three on the backend and two on the frontend. They're all unit tests. Nothing here starts a browser or connects to a real database, so the whole suite finishes in well under a minute and needs no Postgres running.

## Read this before you touch `test_recommend.py`

This file used to print scores and assert nothing. It passed no matter what `recommend()` returned, which made it worse than useless: a green check that couldn't catch a regression. It now asserts.

The recommend tests check behaviour, not exact numbers. They say "the light mouse ranks above the heavy one for a gamer," not "the score is 8.5." That's on purpose. The scoring weights get tuned, and pinning the exact numbers would turn every tuning into a fake failure that trains people to ignore CI. So: nudge a weight and these should still pass. Change what the ranking is *supposed* to do and they'll fail, which is the point. Update them when the intent changes, not when a number moves.

## Backend

Three files, 17 tests. They use mock mice or a throwaway SQLite file, never the real `mouse.db`.

### `test_recommend.py` — the scoring and ranking algorithm

`recommend()` in `algorithm/recommend.py`.

| Test | Targets | Why it's here |
|---|---|---|
| `test_gamer_ranks_lightweight_first` | Ranking for a gamer who wants a light mouse | This is the whole promise of the product. The 60g mouse has to come first and the 141g one last. |
| `test_student_ranks_heavy_last` | Ranking for a student who travels | Someone carrying it around shouldn't be handed the heavy brick. |
| `test_results_sorted_by_score_desc` | Order of the returned list, all three personas | Results come back best-first. If the sort ever breaks, the UI shows the wrong winner. |
| `test_every_candidate_survives` | Which mice make it into the output | Hard rules reorder the list, they don't cut mice from it. Every mouse that went in comes back out. |
| `test_result_shape_is_stable` | The keys on each result | The frontend reads `id`, `score`, `explanations` and the rest by name. A rename breaks the page silently, so this catches it. |
| `test_empty_mice_no_crash` | Passing no mice | Empty in, empty out, no exception. |
| `test_empty_payload_returns_all` | Passing no answers | Someone who skipped the quiz still sees every mouse. |

### `test_compare.py` — the side-by-side spec rows

`compare_detail()` in `algorithm/recommend.py`, which feeds the `/compare` page.

| Test | Targets | Why it's here |
|---|---|---|
| `test_rows_are_aligned_one_cell_per_mouse` | Shape of each row | Every row has exactly one cell per mouse. This is what lets the frontend line the columns up without them drifting. |
| `test_missing_spec_keeps_row_with_null_cell` | A mouse that lacks a spec | When one mouse has no tracking speed, its cell goes empty and the row stays. Drop the row instead and every column below it shifts up and misaligns. This was a real bug risk, so it gets its own test. |
| `test_row_dropped_only_when_nobody_has_it` | When a row disappears | A row only vanishes if none of the mice have that spec, e.g. Price when nothing is priced. |
| `test_gamer_order_follows_importance` | Row order for a gamer | A gamer sees Max DPI at the top, not Price. |
| `test_no_quiz_falls_back_to_default_order` | Row order with no answers | No quiz means the default importance order, same as the product page. |
| `test_single_mouse` | Comparing one mouse | One cell per row, doesn't fall over. |
| `test_empty_mice` | Comparing nothing | Returns an empty list. |

### `test_profile.py` — saved preference profiles

The `Preference_Profile` model and the profile routes in `app/routers/profile.py`.

| Test | Targets | Why it's here |
|---|---|---|
| `test_model_round_trip` | Saving and loading the model | A profile, including its nested JSON answers, comes back out of the database exactly as it went in. |
| `test_route_round_trip` | create / get / update routes | Create a profile, fetch it, update it, fetch again, and the changes stuck. |
| `test_unknown_id_404` | Asking for an id that isn't there | You get a 404, not a 500. |

## Frontend

Two files, 7 tests, using Node's built-in test runner. No React rendering, just the pure logic.

### `format.test.js` — the review-count formatter

`formatCount()` in `src/format.js`.

| Test | Targets | Why it's here |
|---|---|---|
| `counts under 1000 stay a plain number` | Small counts | 0, 950, 999 show as-is. |
| `1000+ abbreviates to "k"` | Large counts | 1500 becomes "1.5k", 1999 rounds to "2k", and a trailing ".0" is dropped. |
| `nullish / non-finite returns null` | Junk input | null, undefined and NaN return null so the caller can just hide the count. |

### `sections.test.js` — the quiz's branching logic

`profileSections()` in `src/questionnaire/sections.js`, which decides what questions to show based on answers so far.

| Test | Targets | Why it's here |
|---|---|---|
| `gamer persona then about` | A gamer's question set | Picking gamer opens the gaming questions, in the right order. |
| `student who games reveals the gamer block` | A conditional reveal | A student who says they game also gets the gaming questions. |
| `wired-too (16) only when wireless is yes/preferably` | One gated question | Question 16 only shows for people leaning wireless, and it lands right after question 15. |
| `no persona section when user type is unset` | The empty state | No user type picked yet means only the base section shows. |

## Running them

Backend, from `backend/`:

```
python test_recommend.py
python test_compare.py
python test_profile.py
```

Run each file separately. It's not just tidiness: `test_profile.py` repoints the database at a temporary SQLite file, and it has to do that before the models get imported. Run everything in one process and the files step on each other's database setup.

Frontend, from `frontend/`:

```
npm test
```

## Where CI runs it

`.github/workflows/ci.yml`, two jobs in parallel:

- **Backend tests** — Ubuntu, Python 3.11, runs each `test_*.py` as its own process.
- **Frontend tests + build** — Ubuntu, Node 22, runs `npm test` and then a build so a change that stops compiling also fails.

## What these don't cover

Everything here is unit-level. It checks the scoring function, the compare rows, the profile model, and two frontend helpers, each in isolation. It won't catch the wiring coming loose between components: a wrong prop, a route that stopped matching, a fetch whose shape changed. Catching that needs a browser or end-to-end test, and there isn't one yet. So a green run means the pieces work, not that the pages do.

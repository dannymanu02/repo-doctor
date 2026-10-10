# Repo Doctor evaluation

Suite: holdout

Completed: 4/4

Outcomes: {'tests_failed': 2, 'repaired': 2}

Repair rate among valid attempts: 0.5

| Case | Outcome | Model seconds |
|---|---|---:|
| clamp_bounds | tests_failed | 25.08 |
| batch_count | repaired | 48.26 |
| explicit_zero | tests_failed | 24.6 |
| filter_boundary | repaired | 25.45 |

## Explanation review

Review each case JSON: compare the diagnosis to the stored context. Record incorrect statements,
unsupported citations, and false missing-evidence claims. No automated accuracy score is assigned.

These are small synthetic cases, not a production benchmark. Reference repairs and test
assertions are excluded from model context. Subsequent prompt tuning makes reused cases development data.

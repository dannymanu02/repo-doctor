# Repo Doctor evaluation

Suite: holdout

Completed: 4/4

Outcomes: {'output_truncated': 1, 'repaired': 2, 'tests_failed': 1}

Repair rate among valid attempts: 0.5

| Case | Outcome | Model seconds |
|---|---|---:|
| clamp_bounds | output_truncated | 28.73 |
| batch_count | repaired | 43.11 |
| explicit_zero | tests_failed | 39.45 |
| filter_boundary | repaired | 29.75 |

## Explanation review

Review each case JSON: compare the diagnosis to the stored context. Record incorrect statements,
unsupported citations, and false missing-evidence claims. No automated accuracy score is assigned.

These are small synthetic cases, not a production benchmark. Reference repairs and test
assertions are excluded from model context. Subsequent prompt tuning makes reused cases development data.

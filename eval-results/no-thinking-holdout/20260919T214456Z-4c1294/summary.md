# Repo Doctor evaluation

Suite: holdout

Completed: 4/4

Outcomes: {'validation_rejected': 1, 'repaired': 2, 'tests_failed': 1}

Repair rate among valid attempts: 0.5

Cases retried: 0; repairs after retry: 0

Test-feedback retries: 1; repairs after test feedback: 0

| Case | Outcome | Model seconds |
|---|---|---:|
| clamp_bounds | validation_rejected | 9.05 |
| batch_count | repaired | 4.68 |
| explicit_zero | tests_failed | 4.09 |
| filter_boundary | repaired | 3.99 |

## Explanation review

Review each case JSON: compare the diagnosis to the stored context. Record incorrect statements,
unsupported citations, and false missing-evidence claims. No automated accuracy score is assigned.

These are small synthetic cases, not a production benchmark. Reference repairs and test
final scoring assertions stay out of model context. Public reproduction checks may be used for one retry. Reused cases are development data.

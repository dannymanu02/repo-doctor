# Repo Doctor evaluation

Suite: holdout

Completed: 4/4

Outcomes: {'repaired': 4}

Repair rate among valid attempts: 1.0

Cases retried: 0; repairs after retry: 0

Test-feedback retries: 0; repairs after test feedback: 0

| Case | Outcome | Model seconds |
|---|---|---:|
| clamp_bounds | repaired | 9.01 |
| batch_count | repaired | 4.58 |
| explicit_zero | repaired | 4.07 |
| filter_boundary | repaired | 3.94 |

## Explanation review

Review each case JSON: compare the diagnosis to the stored context. Record incorrect statements,
unsupported citations, and false missing-evidence claims. No automated accuracy score is assigned.

These are small synthetic cases, not a production benchmark. Reference repairs and test
final scoring assertions stay out of model context. Public reproduction checks may be used for one retry. Reused cases are development data.

# Repo Doctor evaluation

Suite: development

Completed: 6/6

Outcomes: {'repaired': 3, 'execution_rejected': 1, 'tests_failed': 2}

Repair rate among valid attempts: 0.5

Cases retried: 0; repairs after retry: 0

Test-feedback retries: 1; repairs after test feedback: 0

| Case | Outcome | Model seconds |
|---|---|---:|
| inclusive_range | repaired | 9.19 |
| numeric_strings | execution_rejected | 4.1 |
| numeric_sort | repaired | 3.95 |
| stable_dedup | tests_failed | 4.37 |
| timeout_units | repaired | 4.98 |
| normalize_lookup | tests_failed | 4.08 |

## Explanation review

Review each case JSON: compare the diagnosis to the stored context. Record incorrect statements,
unsupported citations, and false missing-evidence claims. No automated accuracy score is assigned.

These are small synthetic cases, not a production benchmark. Reference repairs and test
final scoring assertions stay out of model context. Public reproduction checks may be used for one retry. Reused cases are development data.

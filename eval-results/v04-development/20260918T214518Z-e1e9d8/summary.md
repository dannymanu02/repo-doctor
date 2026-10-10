# Repo Doctor evaluation

Suite: development

Completed: 6/6

Outcomes: {'repaired': 3, 'output_truncated': 1, 'execution_rejected': 1, 'tests_failed': 1}

Repair rate among valid attempts: 0.5

| Case | Outcome | Model seconds |
|---|---|---:|
| inclusive_range | repaired | 21.36 |
| numeric_strings | output_truncated | 28.97 |
| numeric_sort | repaired | 20.07 |
| stable_dedup | execution_rejected | 19.99 |
| timeout_units | repaired | 19.35 |
| normalize_lookup | tests_failed | 42.25 |

## Explanation review

Review each case JSON: compare the diagnosis to the stored context. Record incorrect statements,
unsupported citations, and false missing-evidence claims. No automated accuracy score is assigned.

These are small synthetic cases, not a production benchmark. Reference repairs and test
assertions are excluded from model context. Subsequent prompt tuning makes reused cases development data.

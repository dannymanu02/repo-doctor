# Repo Doctor evaluation

Suite: development

Completed: 6/6

Outcomes: {'repaired': 4, 'validation_rejected': 1, 'tests_failed': 1}

Repair rate among valid attempts: 0.6666666666666666

| Case | Outcome | Model seconds |
|---|---|---:|
| inclusive_range | repaired | 22.43 |
| numeric_strings | repaired | 20.23 |
| numeric_sort | repaired | 17.7 |
| stable_dedup | validation_rejected | 21.53 |
| timeout_units | repaired | 26.8 |
| normalize_lookup | tests_failed | 33.94 |

## Explanation review

Review each case JSON: compare the diagnosis to the stored context. Record incorrect statements,
unsupported citations, and false missing-evidence claims. No automated accuracy score is assigned.

These are small synthetic cases, not a production benchmark. Reference repairs and test
assertions are excluded from model context. Subsequent prompt tuning makes reused cases development data.

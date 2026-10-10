# Repo Doctor evaluation

Completed: 6/6

Outcomes: {'repaired': 4, 'tests_failed': 2}

Repair rate among valid attempts: 0.6666666666666666

| Case | Outcome | Model seconds |
|---|---|---:|
| inclusive_range | repaired | 19.89 |
| numeric_strings | repaired | 17.84 |
| numeric_sort | repaired | 19.94 |
| stable_dedup | tests_failed | 14.99 |
| timeout_units | repaired | 25.02 |
| normalize_lookup | tests_failed | 15.47 |

## Explanation review

Review each case JSON: compare the diagnosis to the stored context. Record incorrect statements,
unsupported citations, and false missing-evidence claims. No automated accuracy score is assigned.

These are small synthetic cases, not a production benchmark. Reference repairs and test
assertions are excluded from model context. Subsequent prompt tuning makes reused cases development data.

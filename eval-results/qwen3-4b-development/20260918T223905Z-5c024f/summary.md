# Repo Doctor evaluation

Suite: development

Completed: 6/6

Outcomes: {'output_truncated': 6}

Repair rate among valid attempts: 0.0

| Case | Outcome | Model seconds |
|---|---|---:|
| inclusive_range | output_truncated | 120.12 |
| numeric_strings | output_truncated | 236.53 |
| numeric_sort | output_truncated | 184.97 |
| stable_dedup | output_truncated | 177.08 |
| timeout_units | output_truncated | 166.94 |
| normalize_lookup | output_truncated | 111.22 |

## Explanation review

Review each case JSON: compare the diagnosis to the stored context. Record incorrect statements,
unsupported citations, and false missing-evidence claims. No automated accuracy score is assigned.

These are small synthetic cases, not a production benchmark. Reference repairs and test
assertions are excluded from model context. Subsequent prompt tuning makes reused cases development data.

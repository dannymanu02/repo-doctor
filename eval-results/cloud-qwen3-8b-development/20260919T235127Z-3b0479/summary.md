# Repo Doctor evaluation

Suite: development

Completed: 6/6

Outcomes: {'validation_rejected': 5, 'repaired': 1}

Repair rate among valid attempts: 0.16666666666666666

Cases retried: 5; repairs after retry: 0

Test-feedback retries: 0; repairs after test feedback: 0

| Case | Outcome | Model seconds |
|---|---|---:|
| inclusive_range | validation_rejected | 10.35 |
| numeric_strings | validation_rejected | 4.84 |
| numeric_sort | validation_rejected | 5.24 |
| stable_dedup | validation_rejected | 5.14 |
| timeout_units | repaired | 4.04 |
| normalize_lookup | validation_rejected | 4.69 |

## Explanation review

Review each case JSON: compare the diagnosis to the stored context. Record incorrect statements,
unsupported citations, and false missing-evidence claims. No automated accuracy score is assigned.

These are small synthetic cases, not a production benchmark. Reference repairs and test
final scoring assertions stay out of model context. Public reproduction checks may be used for one retry. Reused cases are development data.

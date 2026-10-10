# Repo Doctor evaluation

Suite: holdout

Completed: 4/4

Outcomes: {'output_truncated': 4}

Repair rate among valid attempts: 0.0

| Case | Outcome | Model seconds |
|---|---|---:|
| clamp_bounds | output_truncated | 76.24 |
| batch_count | output_truncated | 109.6 |
| explicit_zero | output_truncated | 111.18 |
| filter_boundary | output_truncated | 163.27 |

## Explanation review

Review each case JSON: compare the diagnosis to the stored context. Record incorrect statements,
unsupported citations, and false missing-evidence claims. No automated accuracy score is assigned.

These are small synthetic cases, not a production benchmark. Reference repairs and test
assertions are excluded from model context. Subsequent prompt tuning makes reused cases development data.

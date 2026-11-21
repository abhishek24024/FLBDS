# V10 analysis

## Per-condition pass rates (runs; Wilson 95% CI)

| condition | runs | eval pass | rate | Wilson CI | screen pass | S&!E | !S&E | tmpl err | tokens/run |
|---|---|---|---|---|---|---|---|---|---|
| A24x1 | 144 | 59 | 0.410 | [0.333, 0.491] | 69 | 10 | 0 | 0 | 3258 |
| A3x8 | 144 | 102 | 0.708 | [0.629, 0.776] | 118 | 16 | 0 | 0 | 1820 |
| A8x3 | 144 | 96 | 0.667 | [0.586, 0.738] | 104 | 8 | 0 | 0 | 2538 |
| V10 | 144 | 102 | 0.708 | [0.629, 0.776] | 113 | 11 | 0 | 0 | 3096 |

## Paired instance-level comparisons (per-instance pass fraction across seeds)

Confirmatory (Holm across these only): L3:B0, OPT:L3, L3_BIOMATCH:L3_BIOMISMATCH

| A | B | N | mean A | mean B | diff | 95% CI | p (sign-flip) | p (Holm) |
|---|---|---|---|---|---|---|---|---|

Per-family breakdown:
| A vs B | family | n | mean A | mean B | diff | 95% CI | p |
|---|---|---|---|---|---|---|---|

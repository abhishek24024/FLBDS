# V10 analysis

## Per-condition pass rates (runs; Wilson 95% CI)

| condition | runs | eval pass | rate | Wilson CI | screen pass | S&!E | !S&E | tmpl err | tokens/run |
|---|---|---|---|---|---|---|---|---|---|
| B0 | 60 | 18 | 0.300 | [0.199, 0.425] | 18 | 1 | 1 | 0 | 134 |
| L3 | 60 | 39 | 0.650 | [0.524, 0.758] | 42 | 3 | 0 | 0 | 357 |
| OPT | 60 | 41 | 0.683 | [0.558, 0.787] | 60 | 19 | 0 | 0 | 134 |
| OPTONLY | 60 | 39 | 0.650 | [0.524, 0.758] | 60 | 21 | 0 | 0 | 0 |

## Paired instance-level comparisons (per-instance pass fraction across seeds)

Confirmatory (Holm across these only): L3:B0, OPT:L3, L3_BIOMATCH:L3_BIOMISMATCH

| A | B | N | mean A | mean B | diff | 95% CI | p (sign-flip) | p (Holm) |
|---|---|---|---|---|---|---|---|---|
| L3 | B0 | 12 | 0.650 | 0.300 | +0.350 | [+0.183, +0.533] | 0.007812 | 0.01562 |
| OPT | L3 | 12 | 0.683 | 0.650 | +0.033 | [-0.250, +0.350] | 0.9375 | 0.9375 |
| OPTONLY | OPT | 12 | 0.650 | 0.683 | -0.033 | [-0.100, +0.000] | 1 | nan |

Per-family breakdown:
| A vs B | family | n | mean A | mean B | diff | 95% CI | p |
|---|---|---|---|---|---|---|---|
| L3 vs B0 | F_HX | 3 | 0.133 | 0.000 | +0.133 | [+0.000, +0.200] | 0.5 |
| L3 vs B0 | F_MEM | 3 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] | 1 |
| L3 vs B0 | F_PCM | 3 | 0.600 | 0.000 | +0.600 | [+0.400, +0.800] | 0.25 |
| L3 vs B0 | F_RAD | 3 | 0.867 | 0.200 | +0.667 | [+0.400, +0.800] | 0.25 |
| OPT vs L3 | F_HX | 3 | 1.000 | 0.133 | +0.867 | [+0.800, +1.000] | 0.25 |
| OPT vs L3 | F_MEM | 3 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] | 1 |
| OPT vs L3 | F_PCM | 3 | 0.000 | 0.600 | -0.600 | [-0.800, -0.400] | 0.25 |
| OPT vs L3 | F_RAD | 3 | 0.733 | 0.867 | -0.133 | [-0.400, +0.000] | 1 |
| OPTONLY vs OPT | F_HX | 3 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] | 1 |
| OPTONLY vs OPT | F_MEM | 3 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] | 1 |
| OPTONLY vs OPT | F_PCM | 3 | 0.000 | 0.000 | +0.000 | [+0.000, +0.000] | 1 |
| OPTONLY vs OPT | F_RAD | 3 | 0.600 | 0.733 | -0.133 | [-0.400, +0.000] | 1 |

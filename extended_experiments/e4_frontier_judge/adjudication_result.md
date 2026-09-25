# Grader-blind adjudication of judge/cascade disagreements (P1-2)

Sample: 40 of the 127 judge-ACCEPT/strict-NOT_ACCEPT pairs, stratified by the cascade's failure
mechanism; adjudicated 34 (sheet: `adjudication_sheet.{jsonl,txt}`, released). The adjudicator saw only
the response tail + canonical + grading note — never which grader said what. Author-run, not external.

Question asked per item: is the response's final answer mathematically equivalent to the canonical?

## Result (n=34)

| Verdict | n | % |
|---|---:|---:|
| **Cascade false-negative** (response correct; cascade could not parse/match) | 18 | 53% |
| **Malformed canonical** (reference answer itself defective: `\1`, `x_1=x_2=`, `15to25`) | 6 | 18% |
| **Judge over-acceptance** (cascade right to reject) | 10 | 29% |

## The mechanism split is near-deterministic

| Cascade failure mode | n in sample | Verdict |
|---|---:|---|
| PARSE_ERROR | 22 | 21/22 (95%) cascade-FN or malformed canonical |
| no \boxed found | 9 | 8/9 (89%) judge over-acceptance |
| NOT_EQUIVALENT | 3 | 2 cascade-FN, 1 judge-over |

Projected over the full 127 disagreements (75 parse_error / 35 no_boxed / 17 not_equivalent):
**~82 (65%) are cascade-too-strict or defective canonicals; ~40 (30%) are genuine judge over-acceptance.**

## What the judge actually gets wrong

Every one of the 8 no_boxed judge-over cases is the same failure: the response is **truncated mid-reasoning
and never produces a final answer**, and the judge credits the reasoning anyway. The protocol requires a
boxed final answer, so the cascade is correct to reject. Two further judge-over cases are substantively
wrong answers (one picks the wrong root of a quadratic; one answers only the first of a two-part question).

## Examples of cascade false-negatives (all confirmed by hand)

| Canonical | Response's boxed answer | Why the cascade rejected |
|---|---|---|
| `\sqrt{2}(\frac{8+\ln5}{5})` | `\frac{\sqrt{2}(8+\ln 5)}{5}` | identical value, different nesting |
| `-\frac{1}{2^{70}}\cdot C_{70}^{28}` | `-\binom{70}{42}\cdot 2^{-70}` | identical (C(70,28)=C(70,42)) |
| `(C) 3.15 \mathrm{~m}` | `3.15 \mathrm{~m}` | canonical carries an MCQ letter prefix |
| `174,13` | two separate `\boxed{174}`, `\boxed{13}` | extractor keeps only the last box |
| `n\neq2^{k}(k\in{N})` | `n \neq 2^k \text{ for any } k \geq 0` | relational + text schema |

## Reading

The headline 12.7% over-acceptance is not one phenomenon. About two thirds of it is the deterministic
cascade being conservative on brittle canonicals — which independently corroborates the 22–28% artifact
layer estimated by the residual audit, via a completely different method. The remaining third is a
specific, real judge pathology: crediting unfinished work. Both halves argue for the same design
conclusion as the paper's — a deterministic grader for condition contrasts, with its conservatism
quantified rather than hidden.

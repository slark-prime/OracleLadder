# E9: the worked example used in the talk, poster, and video

The NeurIPS talk, poster, and explainer video walk through one family, `ff548f26` (lines p: y = 2x − 1 and q ⟂ p through (2, 3); area of the convex quadrilateral they bound with the axes; answer 19/4). The six-model panel stores only correct counts per family, so this folder re-samples one model on this family and keeps every response.

**Setup.** Qwen/Qwen3-8B with thinking disabled (Tinker, `qwen3_disable_thinking` renderer), the panel's student system prompt, temperature 1.0, `max_tokens=16384`, K = 8 per condition. Conditions: the two tested milestones alone (M1, M2) and the parent probes C1 (no help), C2 (roadmap), C3 (roadmap + gold milestone answers), built with the same prompt templates as the panel. Each response is graded by the released verifier (default cascade and `extended=True`) and was also read by hand.

**Result.**

| Condition | Correct (default / extended) | Final boxed answers |
|---|---|---|
| M1 | 8/8 / 8/8 | y = -\frac{1}{2}x + 4, y = -\frac{1}{2}x + 4, y = -\frac{1}{2}x + 4, y = -\frac{1}{2}x + 4, y = -\frac{1}{2}x + 4, y = -\frac{1}{2}x + 4, y = -\frac{1}{2}x + 4, y = -\frac{1}{2}x + 4 |
| M2 | 8/8 / 8/8 | 2x - 1 = 0, 2x - 1 = 0, 2x - 1 = 0, 2x - 1 = 0, 2x - 1 = 0, 0 = 2x - 1, 2x - 1 = 0, 2x - 1 = 0 |
| C1 | 0/8 / 0/8 | \frac{65}{4}, 16.25, \frac{65}{4}, \frac{65}{4}, 17, \frac{65}{4}, \frac{25}{4}, \frac{65}{4} |
| C2 | 0/8 / 0/8 | 16, \frac{65}{4}, 16, \frac{75}{4}, \frac{65}{4}, 6, 8.5, 20 |
| C3 | 0/8 / 0/8 | \frac{65}{4}, \frac{85}{4}, \frac{23}{8}, \frac{75}{4}, \frac{65}{4}, \frac{65}{4}, \frac{17}{2}, 18.75 |

The model solves both milestones alone 8/8 and fails the parent 0/8 at every rung, so the family is a composition gap for this model. No response states 19/4. With the roadmap and both milestone answers (C3), every response finds the four axis intercepts and none uses the corner (2, 3) as a vertex; one response computes (2, 3) and then excludes it because it is not on an axis. This agrees with the hand-graded retest in `e1_composition_probe` (temperature 0.7, no system prompt), where the same model also scores 0/8 under C3.

In the six-model panel (counts only), this family is a composition gap for Llama-3.3-70B-Instruct, OutcomeRL-2K, and MilestoneRL-2K. Llama-3.3-70B-Instruct can no longer be re-sampled on Tinker, so its responses for this family cannot be recovered.

Files: `run_example.py` (rerun script, needs `TINKER_API_KEY`), `ff548f26_qwen3_8b.jsonl` (every response with its grades), `summary.json`.

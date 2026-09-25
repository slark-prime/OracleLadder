# Dataset card: OracleLadder

OracleLadder is a diagnostic set for locating where LLM math reasoning fails. Each of the 354 **milestone families** pairs a NuminaMath parent problem with a teacher-written roadmap of intermediate sub-goals (milestones), each with a gold answer that a symbolic verifier can check. A model is tested with no help (C1), with the roadmap (C2), and with the roadmap plus the milestone answers (C3), and separately on each milestone alone (Stage 0). The paper is *Solving Every Step Is Not Enough: Milestone Oracles Reveal a Composition Gap in LLM Math Reasoning* (NeurIPS 2026, Evaluations and Datasets Track).

## Scope and conditioning (read this first)

**1. This is a screened stress set.** A family enters the set only if the screening model (Qwen3-8B-Base, called Qwen-base) fails the parent in all 8 direct attempts at a 4K-token budget and solves every tested milestone at least once. Category shares therefore describe this set, the source data, and the student together. The screen alone changes a lot: a direct-failure screen with Qwen3-8B keeps 7% of MATH500 but 63% of AIME 2024/25, gpt-oss-20b keeps 1% and 17%, and Llama-3.2-1B-Instruct keeps 69% and 97%. Use the set to compare conditions and models on the same problems.

**2. Roadmaps are written by a teacher model.** GPT-5.4 Thinking wrote each roadmap from the problem and its reference solution. It never sees an evaluated model's output. A roadmap is one valid decomposition of a problem. With gpt-oss-20b as the student and K=8, per-family recovery changes little when the roadmap changes:

| Change to the roadmaps | C2 agreement | C3 agreement | Joint agreement |
|---|---|---|---|
| Independent second teacher (Inkling), 53 families | 44/53 (83%) | 46/53 (87%) | 41/53 (77%) |
| Same teacher, 4.1× finer roadmaps, 33 families | 28/33 (85%) | 28/33 (85%) | 25/33 (76%) |

The five-way labels are more sensitive, because the milestone test requires every milestone. Compare five-way labels only between roadmaps of matched granularity, and report the milestone count and the student's milestone-test pass rate with them.

**3. Composition-gap counts need a passable milestone test.** On MATH500 and AIME, the teacher writes 4.7 to 6.1 tested milestones per family and Qwen3-8B passes the milestone test on 0 to 2 families. Unsolved families there fall into the capability gap. Check the milestone-test pass rate before reading composition-gap counts.

**4. Grading is deterministic and strict.** A symbolic cascade grades every answer (boxed extraction, schema-aware parsing, SymPy, math-verify), with no LLM fallback. It had 0 false positives in a 400-response paired audit (95% upper bound 0.75%). It rejects some correct answers written in unusual forms. A grader-blind adjudication of disagreements with a frontier judge puts this at about 8.7% of graded responses. An LLM rubric review flags 22–29% of each model's composition-gap families as verifier or format errors.

**5. Known defects in reference answers.** Ten parent reference answers are wrong or malformed, and one family (`a0759695`) has three wrong milestone gold answers. The files keep the original values, because every count in the paper was graded against them. Each affected record carries a `parent_answer_corrected` field or a `milestone_gold_invalid` list, and `data/corrections.jsonl` gives the evidence for each change.

## Contents

| Path | What it is |
|---|---|
| `data/diagnostic_354_families.jsonl` | Main set: parent, reference answer, milestones with gold answers |
| `data/diagnostic_held_out_32.jsonl` | 32-family held-out slice from a separate NuminaMath sample |
| `data/stage0_panel_16k/` | Milestone test for six models, K=8, 16K tokens |
| `data/oracle_panel_16k/` | Per-family success counts under the six probe conditions, six models, K=8, 16K tokens |
| `data/audit_*.jsonl`, `data/human_validation.jsonl` | Two-rater author audit of 100 unrecovered families and a human validation pass on 50 |
| `data/format_audit_c1/` | Unaided solutions (C1) of four models on 50 families, used for the trace analysis |
| `data/corrections.jsonl` | Corrected reference answers with evidence |
| `prompts/` | Teacher, student, and control prompts |
| `code/` | Verifier cascade, probe builders, family compiler, analysis scripts |
| `extended_experiments/` | Second datasets (MATH500, AIME 2024/25), code pilot (LiveCodeBench), second teacher, granularity ablation, trace analysis, frontier judge, six-model rubric review, raw-output retest |

## Intended use

Comparing probe conditions on a fixed set of problems, locating where a model's failures sit, tracking how training moves families between states, and re-screening with your own anchor model using the released screen.

**Out of scope:** leaderboard ranking, estimating a model's general math ability, and reading category shares as constants that hold on other data.

## Provenance and license

Problems come from NuminaMath-1.5-RL-Verifiable (Apache 2.0). The extended experiments also use MATH500 (MIT), the AIME 2024 and 2025 competitions of the Mathematical Association of America, and LiveCodeBench (Creative Commons). Roadmaps were written by GPT-5.4 Thinking, with second-teacher subsets by Claude Sonnet 4.6 and Inkling. Our data and annotations are released under CC BY 4.0 and our code under MIT. The data contain no personal information.

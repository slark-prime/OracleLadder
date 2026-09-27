"""Compare the default cascade with extended mode on released raw responses.

Reads data/format_audit/*.jsonl (unaided and C3-gold responses of four models on 50 families)
and the reference answers in data/diagnostic_354_families.jsonl. Prints every verdict that
changes and, where available, the gpt-5.5 judge label from extended_experiments/e4_frontier_judge.
Run from the repository root:  python code/scripts/verifier_extended_regression.py
"""
import glob, json, os, sys, collections
sys.path.insert(0, "code")
from decomposer.verifier.verifier import VerifierModule

gold = {json.loads(l)["pid"]: json.loads(l)["parent_answer"] for l in open("data/diagnostic_354_families.jsonl")}
judge = {}
for l in open("extended_experiments/e4_frontier_judge/paired_gpt_5_5_v2.jsonl"):
    r = json.loads(l); judge[r["case_id"]] = r["judge_label"]
legacy, ext = VerifierModule(), VerifierModule(extended=True)
counts, flips = collections.Counter(), []
for f in sorted(glob.glob("data/format_audit/*.jsonl")):
    model = os.path.basename(f)[:-6]
    for l in open(f):
        r = json.loads(l)
        if r.get("pid") not in gold or not r.get("response"):
            continue
        g = gold[r["pid"]]
        a = legacy.verify(response=r["response"], answer=g)["label"] == "ACCEPT"
        e_v = ext.verify(response=r["response"], answer=g)
        e = e_v["label"] == "ACCEPT"
        counts[(a, e)] += 1
        if a != e:
            cid = f"numina_parent:{r['pid']}:{model}:{r.get('condition')}:{r.get('rollout')}"
            flips.append({"case_id": cid, "gold": g, "legacy": a, "extended": e, "reason": e_v["reason"],
                          "judge": judge.get(cid, "-"), "boxed_tail": r["response"][-300:]})
print("legacy/extended verdict counts:", {f"{'A' if k[0] else 'N'}->{'A' if k[1] else 'N'}": v for k, v in sorted(counts.items())})
for x in flips:
    print(json.dumps({k: x[k] for k in ("case_id", "gold", "legacy", "extended", "reason", "judge")}, ensure_ascii=False))
json.dump(flips, open("verifier_extended_flips.json", "w"), indent=1, ensure_ascii=False)

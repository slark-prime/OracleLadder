"""Re-sample Qwen3-8B (thinking disabled) on family ff548f26 with the panel's exact setup (Tinker, llama3 renderer,
student system prompt, temperature 1.0, max_tokens 16384, K=8): Stage 0 milestones M1, M2 and parent probes C1, C2, C3.
Saves every raw response and grades it with the released verifier (default cascade and extended mode)."""
import json, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
import tinker
from tinker import types as T
from tinker_cookbook import renderers
from tinker_cookbook.tokenizer_utils import get_tokenizer
from decomposer.common.prompts import STUDENT_SYSTEM_PROMPT
from decomposer.verifier.verifier import VerifierModule

OUT = Path(__file__).resolve().parent
MODEL = "Qwen/Qwen3-8B"  # thinking disabled, as in the paper retest
K, MAXTOK = 8, 16384

fam = next(json.loads(l) for l in open(ROOT / "data/diagnostic_354_families.jsonl")
           if json.loads(l)["pid"].startswith("ff548f26"))

def desc(ms_prompt):  # same as oracle_panel.extract_ms_description
    m = re.search(r"\nMilestone:\n(.+?)(?:\n\nOutput instruction:|\Z)", ms_prompt, re.DOTALL)
    return m.group(1).strip() if m else ms_prompt[:200]

def build_c2(p, ms):
    return p.rstrip() + "\n\nHint — the following sub-goals structure the solution:\n" + "\n\n".join(
        f"Sub-goal {i+1}: {desc(m['prompt'])}" for i, m in enumerate(ms))

def build_c3(p, ms):
    return p.rstrip() + "\n\nThe following sub-goals have been solved:\n" + "\n\n".join(
        f"Sub-goal {i+1}: {desc(m['prompt'])}\n  Answer: {m['answer']}" for i, m in enumerate(ms)) + "\n\nUse these results to solve the original problem."

tested = [m for m in fam["milestones"] if m.get("type") != "INTEGRATE"]
jobs = [(f"M{i+1}", m["prompt"], m["answer"], m.get("note", "")) for i, m in enumerate(tested)]
jobs += [("C1", fam["parent_prompt"], fam["parent_answer"], fam.get("parent_note", "")),
         ("C2", build_c2(fam["parent_prompt"], fam["milestones"]), fam["parent_answer"], fam.get("parent_note", "")),
         ("C3", build_c3(fam["parent_prompt"], fam["milestones"]), fam["parent_answer"], fam.get("parent_note", ""))]

sc = tinker.ServiceClient()
client = sc.create_sampling_client(base_model=MODEL)
tok = get_tokenizer(MODEL)
rend = renderers.get_renderer("qwen3_disable_thinking", tokenizer=tok)
params = T.SamplingParams(max_tokens=MAXTOK, temperature=1.0, stop=rend.get_stop_sequences())

GP = {j[0]: rend.build_generation_prompt([{"role": "system", "content": STUDENT_SYSTEM_PROMPT}, {"role": "user", "content": j[1]}]) for j in jobs}
FUT = {j[0]: client.sample(prompt=GP[j[0]], num_samples=K, sampling_params=params) for j in jobs}

def run(job):
    name, prompt, ans, note = job
    r = FUT[name].result(timeout=3600)
    outs = []
    for s in r.sequences:
        msg, _ = rend.parse_response(s.tokens)
        outs.append({"content": msg["content"], "n_tokens": len(s.tokens)})
    return name, prompt, ans, note, outs

t0 = time.time()
results = [run(j) for j in jobs]
vd, ve = VerifierModule(), VerifierModule(extended=True)
rows, summary = [], {}
for name, prompt, ans, note, outs in results:
    for k, o in enumerate(outs):
        d = vd.verify(response=o["content"], answer=ans, note=note)["label"] == "ACCEPT"
        e = ve.verify(response=o["content"], answer=ans, note=note)["label"] == "ACCEPT"
        boxes = re.findall(r"\\boxed\{((?:[^{}]|\{[^{}]*\})*)\}", o["content"])
        rows.append({"condition": name, "rollout": k, "gold": ans, "default_accept": d, "extended_accept": e,
                     "last_box": boxes[-1] if boxes else None, "n_tokens": o["n_tokens"], "prompt": prompt if k == 0 else None,
                     "response": o["content"]})
    summary[name] = {"default": sum(r["default_accept"] for r in rows if r["condition"] == name),
                     "extended": sum(r["extended_accept"] for r in rows if r["condition"] == name), "k": len(outs)}
(OUT / "ff548f26_qwen3_8b.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
(OUT / "summary_qwen3_8b.json").write_text(json.dumps({"model": MODEL, "K": K, "max_tokens": MAXTOK, "temperature": 1.0,
                                              "seconds": round(time.time() - t0), "summary": summary}, indent=1))
print(json.dumps(summary, indent=1), round(time.time() - t0), "s")
for r in rows:
    print(r["condition"], r["rollout"], "D" if r["default_accept"] else "-", "E" if r["extended_accept"] else "-", "|", (r["last_box"] or "NO BOX")[:80])

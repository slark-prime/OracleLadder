# All-pairs cross-problem control for the trace analysis (Appendix: Milestone Answers in the Models' Own Solutions).
import json, collections, random, sys
sys.path.insert(0,'.')
sys.path.insert(0, 'code')
from decomposer.verifier.math_reward import strip_string
def present(t,g):
    g=(g or '').strip()
    if not g or len(g)>60: return False
    t=t or ''
    if g in t: return True
    try:
        gn=strip_string(g); tn=strip_string(t)
        if gn and gn in tn: return True
    except Exception: pass
    try:
        val=float(g.replace(',',''))
        for tok in t.replace('$',' ').replace('\\',' ').replace('{',' ').replace('}',' ').split():
            try:
                if abs(float(tok.strip('.,;:()[]'))-val)<1e-9: return True
            except ValueError: continue
    except ValueError: pass
    return False
FA='data/format_audit/'  # run from the repository root
D='data/'
fams={json.loads(l)['pid']:json.loads(l) for l in open(D+'diagnostic_354_families.jsonl')}
all_pids=sorted(fams)
out={}
for slug in ['deepseek_v3_1','llama_3_3_70b_instruct','mile_2k_step_180','qwen3_8b_pre_rl']:
    traces=collections.defaultdict(list)
    for l in open(FA+slug+'.jsonl'):
        r=json.loads(l)
        if r['condition']=='C1_direct': traces[r['pid']].append(r['response'] or '')
    s0={}
    for l in open(D+'stage0_panel_16k/%s.jsonl'%slug):
        d=json.loads(l); s0[(d['pid'],d['ms_idx'])]=d['n_correct']
    rng=random.Random(42)
    own=[0,0]; cA=[0,0]; nov=[0,0]; instmt=[0,0]; s0p=[0,0]; s0f=[0,0]
    for pid,rl in traces.items():
        fam=fams.get(pid)
        if not fam: continue
        ms=fam['milestones']
        other=fams[rng.choice([p for p in all_pids if p!=pid])]
        stmt=fam['parent_prompt']
        for resp in rl:
            for i,m in enumerate(ms):
                g=str(m.get('answer','')); h=present(resp,g)
                own[0]+=h; own[1]+=1
                ins=present(stmt,g)
                if not ins: nov[0]+=h; nov[1]+=1
                n=s0.get((pid,i))
                if n is not None:
                    if n>=1: s0p[0]+=h; s0p[1]+=1
                    else: s0f[0]+=h; s0f[1]+=1
            for m in other['milestones']:
                cA[0]+=present(resp,str(m.get('answer',''))); cA[1]+=1
    # statement share (per milestone, not per rollout)
    ms_all=[(pid,m) for pid in traces for m in fams[pid]['milestones']]
    st=sum(present(fams[p]['parent_prompt'],str(m.get('answer',''))) for p,m in ms_all)
    # Control B: this family's golds vs other problems' traces (all other traced pids, averaged)
    tp=sorted(traces)
    cB=[0,0]
    for pid in tp:
        for q in tp:
            if q==pid: continue
            for resp in traces[q]:
                for m in fams[pid]['milestones']:
                    cB[0]+=present(resp,str(m.get('answer',''))); cB[1]+=1
    # Control B single random other trace-pid (seeded)
    rng2=random.Random(42); cB1=[0,0]
    for pid in tp:
        q=rng2.choice([x for x in tp if x!=pid])
        for resp in traces[q]:
            for m in fams[pid]['milestones']:
                cB1[0]+=present(resp,str(m.get('answer',''))); cB1[1]+=1
    r=lambda x: x[0]/x[1]
    out[slug]=dict(fams=len(traces),own=own,ctrlA=cA,ctrlB_all=cB,ctrlB_one=cB1,novel=nov,stmt_share=(st,len(ms_all)),s0p=s0p,s0f=s0f)
    print(f"{slug:24s} fams={len(traces)} own={r(own):.4f} ({own[0]}/{own[1]}) ctrlA={r(cA):.4f} ctrlB_all={r(cB):.4f} ctrlB_one={r(cB1):.4f} ratioB_all={r(own)/r(cB):.2f} ratioB_one={r(own)/r(cB1):.2f} novel={r(nov):.4f} ({nov[0]}/{nov[1]}) stmt={st}/{len(ms_all)}={st/len(ms_all):.3f} s0pass={r(s0p):.4f} s0fail={r(s0f) if s0f[1] else None} ({s0f[0]}/{s0f[1]})")
json.dump(out,open('trace_recompute.json','w'),indent=1)

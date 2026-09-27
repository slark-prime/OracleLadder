"""Extended equivalence checks for relational and compound answers (release v1.1).

These checks are OFF by default. ``VerifierModule()`` keeps the exact cascade that
produced every number in the paper. ``VerifierModule(extended=True)`` adds the
checks below, and we recommend it for new evaluations.

What the extended mode adds:
  * equations that are equal up to rearrangement or a nonzero constant factor
    (``2a-c=0`` and ``c=2a``);
  * inequalities, intervals, and unions compared as solution sets over the reals
    in the single-variable case (``a \\le -2`` and ``(-\\infty,-2]``);
  * a labeled answer against a bare value (``S_{ABC} = \\frac{3}{2}`` and ``\\frac{3}{2}``);
  * compound answers split at top-level commas, semicolons, or "and", matched
    by variable name when every part is an assignment, otherwise by position
    and then as an unordered list; answers split over several ``\\boxed{}`` are
    joined before this comparison;
  * a fix for thousands separators: commas are removed only when the whole
    answer is one number, so ``(1,234)`` is no longer read as ``1234``.

``is_leak`` applies the same equivalence to decide whether a milestone's gold
answer gives away the parent answer.
"""

from __future__ import annotations

import re
from typing import Callable, Optional

_THOUSANDS_ONLY = re.compile(r"^[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?$")
_ASSIGN = re.compile(r"^\s*([A-Za-z](?:_\{?[A-Za-z0-9]+\}?)?)\s*=\s*(.+?)\s*$")
MAX_LEN = 300  # extended checks skip very long answers
_AND_SEPS = (r"\text{ and }", r"\text{and}", r"\quad", r"\qquad", " and ")


def normalize_for_math_verify(text: str) -> str:
    """Normalization used before math-verify in extended mode."""
    s = (text or "").strip()
    if _THOUSANDS_ONLY.match(s):
        s = s.replace(",", "")
    s = s.replace(";", ",")
    s = re.sub(r"^[a-zA-Z_]\w*\s*=\s*", "", s)
    return s


def _mv_parse(tex: str):
    try:
        from math_verify import parse
    except ImportError:
        return None
    try:
        out = parse(r"\boxed{" + tex + "}")
        return out[0] if out else None
    except Exception:
        return None


def _split_top_level(tex: str) -> list[str]:
    """Split at commas, semicolons, and 'and' that are not inside brackets."""
    s = tex
    for sep in _AND_SEPS:
        s = s.replace(sep, ";")
    parts, depth, cur, i = [], 0, [], 0
    while i < len(s):
        ch = s[i]
        if s.startswith(r"\left", i) or s.startswith(r"\right", i):
            step = 5 if s.startswith(r"\left", i) else 6
            cur.append(s[i:i + step]); i += step
            continue
        if s.startswith(r"\{", i):
            depth += 1; cur.append(r"\{"); i += 2; continue
        if s.startswith(r"\}", i):
            depth -= 1; cur.append(r"\}"); i += 2; continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch in ",;" and depth == 0:
            parts.append("".join(cur).strip()); cur = []
        else:
            cur.append(ch)
        i += 1
    parts.append("".join(cur).strip())
    return [p for p in parts if p]


def _assignment(part: str) -> Optional[tuple[str, str]]:
    m = _ASSIGN.match(part)
    if not m or "=" in m.group(2):
        return None
    key = re.sub(r"[{}\s]", "", m.group(1))
    return key, m.group(2)


def equations_equivalent(pred: str, gold: str) -> bool:
    """True if both answers are single equations equal up to a nonzero constant factor."""
    from sympy import Eq, simplify
    gp, pp = _mv_parse(gold), _mv_parse(pred)
    if not isinstance(gp, Eq) or not isinstance(pp, Eq):
        return False
    try:
        dg, dp = gp.lhs - gp.rhs, pp.lhs - pp.rhs
        if dg == 0 or dp == 0:
            return False
        ratio = simplify(dg / dp)
    except Exception:
        return False
    return (not ratio.free_symbols) and ratio != 0 and bool(ratio.is_finite)


def _real_solution_set(obj):
    from sympy import S, solveset
    from sympy.core.relational import Relational, Eq
    from sympy.logic.boolalg import And, Or
    from sympy.sets.sets import Set
    from sympy import FiniteSet, Union
    if isinstance(obj, FiniteSet) and len(obj) > 0 and all(
            isinstance(e, Relational) and not isinstance(e, Eq) for e in obj):
        syms = set().union(*(e.free_symbols for e in obj))
        if len(syms) != 1:
            return None
        v = next(iter(syms))
        try:
            return Union(*(solveset(e, v, S.Reals) for e in obj))
        except Exception:
            return None
    if isinstance(obj, Set):
        return obj
    if isinstance(obj, (Relational, And, Or)) and not isinstance(obj, Eq):
        syms = obj.free_symbols
        if len(syms) != 1:
            return None
        try:
            return solveset(obj, next(iter(syms)), S.Reals)
        except Exception:
            return None
    return None


def relations_equivalent(pred: str, gold: str) -> bool:
    """True if both answers describe the same set of reals (inequalities, intervals, unions)."""
    from sympy import S
    fix = lambda t: t.replace(r"\lor", r"\text{ or }").replace(r"\vee", r"\text{ or }")
    gset, pset = _real_solution_set(_mv_parse(fix(gold))), _real_solution_set(_mv_parse(fix(pred)))
    if gset is None or pset is None:
        return False
    if gset.free_symbols or pset.free_symbols:
        return False
    try:
        return gset.symmetric_difference(pset) == S.EmptySet
    except Exception:
        return False


def labeled_value_equivalent(pred: str, gold: str, base: Callable[[str, str], bool]) -> bool:
    """Compare a labeled answer ('LHS = value') with a bare value, in either direction."""
    def last_side(t: str) -> Optional[str]:
        if t.count("=") < 1 or any(op in t for op in ("\\le", "\\ge", "<", ">", "\\neq")):
            return None
        if len(_split_top_level(t)) > 1:  # compound answers are handled by compound_equivalent
            return None
        return t.rsplit("=", 1)[1].strip() or None
    if "=" in pred and "=" not in gold:
        v = last_side(pred)
        return bool(v) and base(v, gold)
    if "=" in gold and "=" not in pred:
        v = last_side(gold)
        return bool(v) and base(pred, v)
    return False


def compound_equivalent(pred: str, gold: str, base: Callable[[str, str], bool]) -> bool:
    """Compare multi-part answers part by part."""
    gparts, pparts = _split_top_level(gold), _split_top_level(pred)
    # a bare tuple '(v1, v2)' against 'x=v1, y=v2': compare values by position
    if len(pparts) == 1 and len(gparts) >= 2 and all(_assignment(g) for g in gparts):
        inner = re.sub(r"^\\left\(|\\right\)$", "", pparts[0].strip())
        inner = inner[1:-1] if inner.startswith("(") and inner.endswith(")") else None
        if inner is not None:
            tparts = _split_top_level(inner)
            if len(tparts) == len(gparts):
                return all(base(t, _assignment(g)[1]) for t, g in zip(tparts, gparts))
        return False
    if len(gparts) < 2 or len(gparts) != len(pparts):
        return False
    ga, pa = [_assignment(x) for x in gparts], [_assignment(x) for x in pparts]
    if all(ga) and all(pa):
        gd, pd = dict(ga), dict(pa)
        if len(gd) != len(ga) or set(gd) != set(pd):
            return False
        return all(base(pd[k], gd[k]) for k in gd)
    if all(base(p, g) for p, g in zip(pparts, gparts)):
        return True
    used: set[int] = set()
    for g in gparts:
        for j, p in enumerate(pparts):
            if j not in used and base(p, g):
                used.add(j)
                break
        else:
            return False
    return True


def all_boxed(response: str) -> list[str]:
    """Contents of every \\boxed{...} in order."""
    out, i = [], 0
    while True:
        j = response.find(r"\boxed{", i)
        if j < 0:
            return out
        k, depth = j + len(r"\boxed{"), 1
        while k < len(response) and depth:
            depth += {"{": 1, "}": -1}.get(response[k], 0)
            k += 1
        out.append(response[j + len(r"\boxed{"):k - 1])
        i = k


def is_leak(milestone_answer: str, parent_answer: str) -> bool:
    """True if a milestone's gold answer is equivalent to the parent answer (extended mode)."""
    from decomposer.verifier.verifier import VerifierModule
    v = VerifierModule(extended=True)
    return v.answers_equivalent(milestone_answer, parent_answer) or v.answers_equivalent(parent_answer, milestone_answer)

"""Tests for the extended verifier mode (relational and compound answers).

Run from the code/ directory:  python -m pytest tests/test_verifier_extended.py -q
or:                            python tests/test_verifier_extended.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from decomposer.verifier.verifier import VerifierModule
from decomposer.verifier.extended import is_leak

LEGACY, EXT = VerifierModule(), VerifierModule(extended=True)
B = lambda s: r"\boxed{" + s + "}"

# (gold, response, expected legacy, expected extended)
CASES = [
    # equations
    ("2a-c=0", B("c=2a"), False, True),
    ("x^2-4=0", B("x^2=4"), None, True),
    ("2a-c=0", B("c=3a"), False, False),
    ("x^2=4", B("x=2"), False, False),
    ("x=5", B("y=5"), True, True),  # stage 3 (math_reward) already treats short variable prefixes as labels
    ("x=5", B("x=6"), False, False),
    # inequalities, intervals, unions
    (r"a\le -2", B(r"(-\infty,-2]"), None, True),
    (r"0\le x\le 2", B("[0,2]"), None, True),
    (r"x<1 \text{ or } x>3", B(r"(-\infty,1)\cup(3,\infty)"), None, True),
    (r"a\le -2", B("a<-2"), False, False),
    (r"a\ge -2", B(r"(-\infty,-2]"), False, False),
    (r"x<1 \lor x>3", B(r"(-\infty,1)\cup[3,\infty)"), False, False),
    # labeled values
    (r"\frac{3}{2}", B(r"S_{\triangle ABC}=\frac{3}{2}"), None, True),
    (r"\frac{3}{2}", B(r"S=\frac{2}{3}"), False, False),
    # compound answers
    (r"a=2, b=\frac{1}{4}", B("b=0.25, a=2"), None, True),
    (r"a=2, b=\frac{1}{4}", B(r"a=2, b=\frac13"), False, False),
    ("3, 5", B("5, 3"), None, True),
    (r"x_{1}=\frac{15}{2},y_{1}=\frac{25}{2}", B(r"\left(\frac{15}{2},\frac{25}{2}\right)"), None, True),
    # Known limitation inherited from math-verify (stage 5, both modes): an assignment list and a
    # tuple are compared as sets, so the swapped tuple is accepted.
    (r"x_{1}=\frac{15}{2},y_{1}=\frac{25}{2}", B(r"\left(\frac{25}{2},\frac{15}{2}\right)"), True, True),
    (r"x_{1}=\frac{15}{2},y_{1}=\frac{25}{2}", B(r"\frac{25}{2}"), False, False),
    ("3, 5", B("3, 5, 7"), False, False),
    ("174,13", r"so \boxed{174} and \boxed{13}", False, True),
    ("174,13", r"so \boxed{174} and \boxed{12}", False, False),
    ("7", r"\boxed{7} or \boxed{8}", False, False),
    # thousands separator
    ("(1,234)", B("1234"), True, False),
    ("1,234", B("1234"), True, True),
]


def test_cases():
    failures = []
    for gold, resp, want_legacy, want_ext in CASES:
        got_l = LEGACY.verify(response=resp, answer=gold)["label"] == "ACCEPT"
        got_e = EXT.verify(response=resp, answer=gold)["label"] == "ACCEPT"
        if want_legacy is not None and got_l != want_legacy:
            failures.append(("legacy", gold, resp, got_l))
        if got_e != want_ext:
            failures.append(("extended", gold, resp, got_e))
    assert not failures, failures


def test_leak():
    assert is_leak(r"a\le -2", r"a \leq -2")
    assert is_leak(r"\frac{98}{100}", r"\frac{49}{50}")
    assert not is_leak("(6,8)", r"\frac{49}{50}")
    assert not is_leak("14", "15")


if __name__ == "__main__":
    for gold, resp, wl, we in CASES:
        l = LEGACY.verify(response=resp, answer=gold); e = EXT.verify(response=resp, answer=gold)
        flag = "" if (e["label"] == "ACCEPT") == we and (wl is None or (l["label"] == "ACCEPT") == wl) else "   <-- MISMATCH"
        print(f"{gold[:24]:26} {resp[:34]:36} legacy={l['label']:10} ext={e['label']:10} ({e['reason'][:38]}){flag}")
    test_leak(); print("leak tests ok")

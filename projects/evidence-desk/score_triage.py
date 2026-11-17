"""Score triage.py and baseline.py against the triage test cases."""
import json, pathlib, importlib
cases = json.loads(pathlib.Path("triage_cases.json").read_text(encoding="utf-8"))["cases"]

def run(mod, name):
    ok_t = ok_m = 0; qs = 0; bad = []
    for c in cases:
        kind, _, missing, _ = mod.triage(c["inquiry"])
        qs += len(missing)
        t_ok = (kind == c["expect_type"]) if name == "triage" else True
        m_ok = sorted(missing) == c["expect_missing"]
        ok_t += t_ok; ok_m += m_ok
        if not (t_ok and m_ok):
            bad.append((c["id"], c["expect_type"], kind, c["expect_missing"], sorted(missing)))
    return ok_t, ok_m, qs, bad

import triage, baseline
for mod, name in ((triage, "triage"), (baseline, "checklist")):
    t, m, q, bad = run(mod, name)
    n = len(cases)
    print(f"\n{name:10} problem type {t}/{n}   questions right {m}/{n}   total questions asked {q}")
    for b in bad[:40]:
        print(f"   {b[0]}  type {b[1]} -> {b[2]}")
        if b[3] != b[4]:
            print(f"        want {b[3] or '[]'}\n        got  {b[4] or '[]'}")

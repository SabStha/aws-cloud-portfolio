"""Triage: what kind of problem is this, and what does the engineer still need to know?

Runs before any search. No AWS, no model: rules only.
Output is for the engineer at their desk, not for the customer.
The support knowledge lives in problem_types.json, not here.
"""
import json
import pathlib
import re

HERE = pathlib.Path(__file__).parent
RULES = json.loads((HERE / "problem_types.json").read_text(encoding="utf-8"))
TYPES = {t["key"]: t for t in RULES["problem_types"]}
FACT_CUES = RULES["fact_cues"]
LABELS = RULES["fact_labels"]
SOURCES = RULES["fact_sources"]
QUESTIONS = RULES["questions"]   # the wording sent to the customer, English and Japanese
VERSION_RE = re.compile(r"\b\d+\.\d+(\.\d+)?\b")


def _hit(cue, low):
    """A cue must start a word, so "collect" matches "collecting" but not "DemoCollector"."""
    if cue.isascii():
        return re.search(r"(?<![a-z0-9])" + re.escape(cue.lower()), low) is not None
    return cue in low


def classify(text):
    """Return the problem type with the most cues in the text, or None."""
    low = text.lower()
    scores = {k: sum(_hit(c, low) for c in t["cues"]) for k, t in TYPES.items()}
    best = max(scores, key=scores.get) if scores else None
    return best if best and scores[best] else None


def facts_present(text):
    """Return the set of facts the inquiry already states."""
    low = text.lower()
    found = {f for f, cues in FACT_CUES.items() if any(_hit(c, low) for c in cues)}
    if VERSION_RE.search(text):
        found.add("version")
    return found


def _why(entry):
    return entry["why"] if isinstance(entry, dict) else entry


def triage(text):
    """Return (problem type, known facts, and the gaps the engineer must close)."""
    kind = classify(text)
    needed = TYPES[kind]["facts"] if kind else RULES.get("unknown_fallback", {})
    have = facts_present(text)

    gaps = []
    for f, entry in needed.items():
        if f in have:
            continue
        if isinstance(entry, dict) and "only_if_text" in entry:
            if not any(_hit(cue, text.lower()) for cue in entry["only_if_text"]):
                continue                       # nothing in the text puts this fact in play
        condition = ""
        if isinstance(entry, dict) and "depends_on" in entry:
            dep = entry["depends_on"]
            if dep["fact"] in have:
                continue                       # we know what it depends on, so this is settled
            condition = dep["only_when"]       # unknown, so flag it as conditional
        gaps.append({"fact": f, "label": LABELS.get(f, f), "why": _why(entry),
                     "source": SOURCES.get(f, "customer"), "only_when": condition})
    return kind, sorted(have & set(needed)), gaps


def report(text):
    kind, known, gaps = triage(text)
    print("\n" + "-" * 76)
    print(text)
    print(f"  problem   {TYPES[kind]['label'] if kind else 'not recognised, falling back to the basics'}")
    print(f"  known     {', '.join(known) if known else 'nothing stated'}")
    if not gaps:
        print("  status    READY — every fact this problem needs is on the ticket")
        return
    print(f"  status    BLOCKED on {len(gaps)} fact{'s' if len(gaps) > 1 else ''}")
    for bucket, title in (("internal", "CHECK YOURSELF"), ("customer", "ASK THE CUSTOMER")):
        rows = [g for g in gaps if g["source"] == bucket]
        if not rows:
            continue
        print(f"\n  {title}")
        for g in rows:
            cond = f"   [only if {g['only_when']}]" if g["only_when"] else ""
            print(f"    {g['label']}{cond}")
            print(f"      {g['why']}")


if __name__ == "__main__":
    print(f"{len(TYPES)} problem types loaded")
    for c in [
        "After yesterday's update our logs stopped arriving. DemoCollector 2.4.4.",
        "DemoCollector 2.4.4 on Windows Server 2022, Pro licence, WMI collection of event logs. "
        "Stopped after the upgrade.",
        "The login screen does not appear after installing DemoCollector 2.4.4 on Windows Server 2022.",
        "Customer wants Teams notifications. DemoCollector Pro.",
        "The dashboard colours look wrong.",
    ]:
        report(c)

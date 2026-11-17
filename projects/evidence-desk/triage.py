"""Triage: what kind of problem is this, and do we have the facts to answer it?

Runs before any search. No AWS, no model: rules only.
The support knowledge lives in problem_types.json, not here.
"""
import json
import pathlib
import re

HERE = pathlib.Path(__file__).parent
RULES = json.loads((HERE / "problem_types.json").read_text(encoding="utf-8"))
TYPES = {t["key"]: t for t in RULES["problem_types"]}
FACT_CUES = RULES["fact_cues"]
QUESTIONS = RULES["questions"]
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
    """Return the set of facts the customer has already given."""
    low = text.lower()
    found = {f for f, cues in FACT_CUES.items() if any(_hit(c, low) for c in cues)}
    if VERSION_RE.search(text):
        found.add("version")
    return found


def triage(text):
    """Return (problem type, required facts, missing facts, questions to ask)."""
    kind = classify(text)
    # Unrecognised problem: still ask the facts every investigation needs.
    needed = TYPES[kind]["facts"] if kind else RULES.get("unknown_fallback", {})
    have = facts_present(text)
    missing = [f for f in needed if f not in have]
    asks = [(QUESTIONS[f][0], QUESTIONS[f][1], needed[f]) for f in missing]
    return kind, list(needed), missing, asks


def report(text):
    kind, needed, missing, asks = triage(text)
    print("\n" + text)
    print(f"  type     : {TYPES[kind]['label'] if kind else 'UNKNOWN — no problem type matched, asking the basics'}")
    print(f"  needs    : {', '.join(needed) or '-'}")
    print(f"  missing  : {', '.join(missing) or 'nothing'}")
    print(f"  verdict  : {'MISSING_INFORMATION' if missing else 'COMPLETE'}")
    for en, ja, why in asks:
        print(f"    - {en}\n      {ja}\n      why: {why}")


if __name__ == "__main__":
    print(f"{len(TYPES)} problem types loaded from problem_types.json")
    for c in [
        "After yesterday's update our logs stopped arriving. DemoCollector 2.4.4.",
        "DemoCollector 2.4.4 on Windows, agentless collection of Windows event logs. "
        "Logs stopped after I enabled a new input.",
        "Getting 401 unauthorized from the ingestion API on DemoCollector 2.4.4.",
        "The dashboard colours look wrong.",
    ]:
        report(c)

"""EvidenceDesk: one inquiry in, one of three things out.

  ANSWERED   the capability table settles it. No search, no model, always correct.
  READY      every fact the problem needs is known, so retrieval can run.
  BLOCKED    facts are missing. Says which, and who can supply each.
"""
import json
import pathlib
import re

import capability
import triage as tri

CAP = capability.CAP
FEATURE_CUES = CAP["feature_cues"]
TIER_CUES = CAP["tier_cues"]
PRODUCTS = list(CAP["products"])


def _name(text, cues):
    low = text.lower()
    for key, words in cues.items():
        if any(w in low for w in words):
            return key
    return None


def _product(text):
    low = text.lower()
    return next((p for p in PRODUCTS if p.lower() in low), None)


# Phrases that make an inquiry a question about possibility rather than a fault report.
# These win over topic words: "is X possible" is a capability question whatever X is.
CAPABILITY_INTENT = ["can we", "can i", "can you", "is it possible", "does it support", "do you support",
                     "wants", "want to", "would like", "asking for", "requesting", "is there a way",
                     "対応していますか", "できますか", "可能ですか", "希望", "要望"]


def ask(text):
    low = text.lower()
    intent = any(w in low for w in CAPABILITY_INTENT)
    kind, known, gaps = tri.triage(text)
    if intent and _name(text, FEATURE_CUES):
        kind = "feature_question"

    # A question about whether a feature exists is a lookup, not an investigation.
    if kind == "feature_question":
        feature = _name(text, FEATURE_CUES)
        product, tier = _product(text), _name(text, TIER_CUES)
        if feature and product:
            verdict, why, elsewhere = capability.check(feature, product, tier)
            return {"outcome": "ANSWERED", "verdict": verdict, "why": why,
                    "elsewhere": elsewhere, "source": "capability table"}
        missing = [n for n, v in (("the feature", feature), ("the product", product)) if not v]
        return {"outcome": "BLOCKED", "gaps": gaps,
                "note": "Name " + " and ".join(missing) + " and this is answerable without searching."}

    if not gaps:
        return {"outcome": "READY", "kind": kind, "known": known}
    return {"outcome": "BLOCKED", "kind": kind, "known": known, "gaps": gaps}


def show(text):
    r = ask(text)
    print("\n" + "-" * 76 + "\n" + text)
    print(f"  {r['outcome']}", end="")
    if r["outcome"] == "ANSWERED":
        print(f"  ({r['source']}, nothing searched)")
        print(f"    {r['verdict']}\n    {r['why']}")
        if r["verdict"].startswith("NOT") and r["elsewhere"]:
            print(f"    available on: {', '.join(r['elsewhere'])}")
        return
    print(f"  {tri.TYPES[r['kind']]['label'] if r.get('kind') else ''}")
    if r["outcome"] == "READY":
        print("    every fact this problem needs is on the ticket; retrieval can run")
        return
    if r.get("note"):
        print(f"    {r['note']}")
    for bucket, title in (("internal", "CHECK YOURSELF"), ("customer", "ASK THE CUSTOMER")):
        rows = [g for g in r["gaps"] if g["source"] == bucket]
        if rows:
            print(f"    {title}: " + ", ".join(
                g["label"] + (f" [only if {g['only_when']}]" if g["only_when"] else "") for g in rows))


if __name__ == "__main__":
    for c in [
        "Customer wants Teams notifications. DemoCollector Pro.",
        "Can we do syslog collection on DemoCollector Limited-Monitor?",
        "Customer is asking for generative AI analysis. DemoQuery Log licence.",
        "They want capacity forecasting on DemoCollector Pro.",
        "Customer wants port monitoring. DemoCollector Free.",
        "After yesterday's update our logs stopped arriving. DemoCollector 2.4.4.",
        "DemoCollector 2.4.4 on Windows Server 2022, Pro licence, WMI collection of event logs. Stopped after the upgrade.",
    ]:
        show(c)

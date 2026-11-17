"""What does putting triage in front of the pipeline buy, and what does it cost?

Runs the same 30 evidence fixtures through triage only. No AWS calls.

The gate rule under test: stop before retrieval only when a fact is missing
that ONLY THE CUSTOMER can supply. Product, version and licence tier are
things support can look up, so a gap there is a note to the engineer, not a
reason to stop.

Two numbers matter, and the second one decides whether this idea lives:
  stopped - questions that never reach the knowledge base
  harmed  - questions the fixtures say are ANSWERABLE that the gate stopped
A saving bought by discarding answerable questions is not a saving.
"""
import json
import pathlib

import triage as tri

TESTS = json.loads(pathlib.Path("fixtures/test_cases.json").read_text(encoding="utf-8"))["tests"]

# measured on the 29/30 run: 51 model calls and 11.4k tokens for 30 questions
CALLS_PER_Q = 51 / 30
TOKENS_PER_Q = 11400 / 30

stopped, harmed, through = [], [], []

print(f'{"test":<6} {"expected":<11} {"problem type":<20} {"gate":<8} needs from the customer')
for t in TESTS:
    # the caller already knows the version, so give triage the same knowledge
    text = t["question"] + " version " + str(t.get("version") or "")
    kind, known, gaps = tri.triage(text)
    customer = [g["fact"] for g in gaps if g["source"] == "customer"]
    internal = [g["fact"] for g in gaps if g["source"] == "internal"]
    if customer:
        stopped.append(t)
        verdict = "STOP"
        if t["expected"] == "ANSWER":
            harmed.append(t)
            verdict = "STOP!"
    else:
        through.append(t)
        verdict = "pass"
    print(f'{t["id"]:<6} {t["expected"]:<11} {str(kind):<20} {verdict:<8} '
          f'{", ".join(customer) or "-"}'
          + (f'   [engineer checks: {", ".join(internal)}]' if internal else ""))

n = len(TESTS)
print()
print(f"reached the knowledge base   {len(through)} / {n}")
print(f"stopped before any cost      {len(stopped)} / {n}")
print(f"  of those, expected ANSWER  {len(harmed)}   <-- harm")
print(f"projected saving             {round(len(stopped) * CALLS_PER_Q)} model calls, "
      f"{round(len(stopped) * TOKENS_PER_Q / 1000, 1)}k tokens")
print()
if harmed:
    print("VERDICT: this gate is not safe to wire in as it stands.")
    print("It stops questions the fixtures say are answerable:",
          ", ".join(t["id"] for t in harmed))
    print("Either the gate asks for facts the evidence does not actually need,")
    print("or those fixtures are answerable for a reason triage cannot see.")
else:
    print("VERDICT: the gate stopped no answerable question. Safe to wire in.")

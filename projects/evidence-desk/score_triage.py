"""Score triage against cases derived from the real corpus.

A case passes only if all three hold:
  1. the problem type is recognised
  2. every fact in must_ask is actually asked
  3. no fact in must_not_ask is asked
Rule 3 is the one that matters: a short first reply is a feature.
"""
import json
import pathlib

import importlib
import sys

tri = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else "triage")

HERE = pathlib.Path(__file__).parent
CASES = json.loads((HERE / "triage_cases.json").read_text(encoding="utf-8"))


def run():
    passed = 0
    customer_total = 0
    failures = []
    for c in CASES:
        kind, known, gaps = tri.triage(c["text"])
        asked = [g["fact"] for g in gaps]
        customer = [g["fact"] for g in gaps if g["source"] == "customer"]
        customer_total += len(customer)
        problems = []
        if kind != c["expect_kind"]:
            problems.append("type: got " + str(kind) + ", expected " + str(c["expect_kind"]))
        missing = [f for f in c["must_ask"] if f not in asked]
        if missing:
            problems.append("did not ask for: " + ", ".join(missing))
        extra = [f for f in c["must_not_ask"] if f in asked]
        if extra:
            problems.append("should not have asked for: " + ", ".join(extra))
        if problems:
            failures.append((c, problems, asked, customer))
        else:
            passed += 1

    for c, problems, asked, customer in failures:
        print("FAIL " + c["id"] + "  " + c["text"][:68])
        for p in problems:
            print("        " + p)
        print("        it asked: " + (", ".join(asked) or "nothing"))
        if c.get("trap"):
            print("        TRAP: " + c["trap"])
        print()

    print("ENGINE: " + tri.__name__)
    print("SCORE: " + str(passed) + "/" + str(len(CASES)))
    print("Questions put to the customer across all " + str(len(CASES)) +
          " inquiries: " + str(customer_total) +
          "  (" + str(round(customer_total / len(CASES), 1)) + " per inquiry)")


if __name__ == "__main__":
    run()

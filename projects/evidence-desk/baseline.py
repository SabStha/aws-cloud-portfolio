"""Baseline: the boring alternative. A fixed intake checklist, the same for every inquiry.

If this does nearly as well as triage.py, the problem types are not worth their cost.
That is a real possible outcome, and finding it out is the point.
"""
from triage import FACT_CUES, QUESTIONS, VERSION_RE, facts_present

# One list for everything, like a form a customer fills in before opening a ticket.
ALWAYS_ASK = ["product", "version", "os", "log_source", "collection_method", "recent_change"]


def triage(text):
    """Same shape as triage.triage, so the two can be scored against each other."""
    have = facts_present(text)
    missing = [f for f in ALWAYS_ASK if f not in have]
    asks = [(QUESTIONS[f][0], QUESTIONS[f][1], "always asked") for f in missing]
    return "fixed_checklist", list(ALWAYS_ASK), missing, asks


if __name__ == "__main__":
    for c in [
        "After yesterday's update our logs stopped arriving. DemoCollector 2.4.4.",
        "Getting 401 unauthorized from the ingestion API on DemoCollector 2.4.4.",
        "The dashboard colours look wrong.",
    ]:
        _, needed, missing, _ = triage(c)
        print(f"\n{c}\n  asks for : {', '.join(missing) or 'nothing'}  ({len(missing)} questions)")

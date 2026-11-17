"""baseline.py — the same job, done the way it is done today: a fixed checklist.

Every inquiry gets the same six questions, whatever it happens to say.

This is not a strawman. It is what a careful engineer writes when there is no
rulebook: the six things that turn out to be needed often enough that asking
for them up front feels safer than guessing. It uses the SAME classifier as
triage.py, so the only difference being measured is which questions get asked.
"""
from triage import LABELS, SOURCES, classify, facts_present

CHECKLIST = ["product", "version", "os", "licence_tier", "collection_method", "recent_change"]

WHY = "on the standard checklist, asked on every inquiry"


def triage(text):
    """Same signature as triage.triage, so one scorer can measure both."""
    have = facts_present(text)
    gaps = [{"fact": f, "label": LABELS.get(f, f), "why": WHY,
             "source": SOURCES.get(f, "customer"), "only_when": ""}
            for f in CHECKLIST if f not in have]
    return classify(text), sorted(have & set(CHECKLIST)), gaps


if __name__ == "__main__":
    for t in ["Ping monitoring cannot get a response from the F5.",
              "Licence registration failed with the new key file."]:
        kind, known, gaps = triage(t)
        print(t)
        print("   asks:", ", ".join(g["fact"] for g in gaps) or "nothing")

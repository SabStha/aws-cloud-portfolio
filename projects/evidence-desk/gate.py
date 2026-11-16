"""Evidence gate: decide ANSWER, UNRESOLVED or BLOCKED for one support question."""
import json
import pathlib

HERE = pathlib.Path(__file__).parent
DOCS = json.loads((HERE / "fixtures/synthetic_knowledge.json").read_text(encoding="utf-8"))["documents"]

BLOCKED_PHRASES = [
    "ignore previous instructions",   # TC-21: tries to override the rules
    "password",                       # TC-24: a credential pasted into the question
    "username",                       # your own addition
    "delete all",                     # TC-26: destroys data
    "attacker.invalid",               # TC-22: sends data to an unknown address
    "customer record",                # TC-27: bulk customer data
    "send the support email",         # TC-25: an action we never allow
    "you are now",                    # TC-28: tries to give the system a new role
    "secret access key",              # TC-29: something nobody should be shown
    "drop the production",            # TC-30: destroys the database
]

def gate(question, version, role="support"):
    """Return (status, reason, list of documents used as evidence)."""
    # TASK 1: your code goes here.

    q = question.lower()
    for phrase in BLOCKED_PHRASES:
        if phrase in q:
            return "BLOCKED", "blocked phrase: " + phrase, []

    # 1. Keep only documents this engineer may use
    allowed = [d for d in DOCS
               if d["version"] == version
               and d["review_status"] == "APPROVED"
               and d["audience"] == role]

    # 2. Keep only documents about this question
    q = question.lower()
    matches = [d for d in allowed
               if any(k.lower() in q for k in d["keywords"])]

    # 2b. Do any matched documents contradict each other?
    groups = [d["conflict_group"] for d in matches if "conflict_group" in d]
    if len(groups) != len(set(groups)):
        return "UNRESOLVED", "CONFLICTED ANSWERS", matches

    # 3. Decide
    if matches:
        return "ANSWER", "an approved document matches", matches
    return "UNRESOLVED", "not built yet", []



        # 0. Refuse dangerous requests before searching anything

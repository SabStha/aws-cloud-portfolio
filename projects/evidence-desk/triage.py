"""Triage: what kind of problem is this, and what does the engineer still need to know?

Runs before any search. No AWS, no model: rules only.
Output is for the engineer at their desk, not for the customer.
The support knowledge lives in problem_types.json, not here.

Optional local enrichment: if lsc_build/version_timeline.json and
parser_catalog.json are present (built from the local knowledge base), triage
also reports whether a mentioned version is newer than anything documented, and
which parser/collection method a named device uses. These files are NOT in the
repository; without them these two extras simply switch off.
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


# ---------------------------------------------------------------- optional local KB
def _load_opt(name):
    """Load a local, gitignored enrichment file if it exists; otherwise None."""
    p = HERE / "lsc_build" / name
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    except Exception:
        return None


VERSION_TL = _load_opt("version_timeline.json")
PARSER_CAT = _load_opt("parser_catalog.json")


def _vtuple(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except Exception:
        return None


_KNOWN_VERSIONS, _NEWEST = set(), None
if VERSION_TL:
    for _r in VERSION_TL.get("versions", []):
        _t = _vtuple(_r.get("version"))
        if _t:
            _KNOWN_VERSIONS.add(_t)
    _NEWEST = max(_KNOWN_VERSIONS) if _KNOWN_VERSIONS else None


def version_status(text):
    """Where does a version named in the text sit against the documented range?"""
    if not _NEWEST:
        return None
    m = VERSION_RE.search(text)
    t = _vtuple(m.group(0)) if m else None
    if not t:
        return None
    newest = ".".join(map(str, _NEWEST))
    if t > _NEWEST:
        return {"version": m.group(0), "status": "newer than any documented release", "newest": newest}
    if t in _KNOWN_VERSIONS:
        return {"version": m.group(0), "status": "a documented release", "newest": newest}
    return {"version": m.group(0), "status": "within the documented range", "newest": newest}


def _vendor_keys(vendor):
    head = re.split(r"ログ", vendor)[0]           # drop ログパーサ and after
    keys = {head} if len(head) >= 3 else set()
    for tok in re.split(r"[ _（(]", head):
        tok = tok.strip()
        if len(tok) >= 3:
            keys.add(tok)
    return keys


def log_source(text):
    """If the text names a device with a known parser, return its category/method."""
    if not PARSER_CAT:
        return None
    low = text.lower()
    for p in PARSER_CAT.get("parsers", []):
        for key in _vendor_keys(p.get("vendor", "")):
            hit = key.lower() in low if key.isascii() else key in text
            if hit:
                return {"vendor": key, "category": p.get("category"),
                        "methods": p.get("collection_methods", []), "ls_id": p.get("ls_id")}
    return None


# ---------------------------------------------------------------- core (unchanged)
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

    vs = version_status(text)
    if vs:
        print(f"  version   {vs['version']} is {vs['status']}  (newest documented: {vs['newest']})")
    ls = log_source(text)
    if ls:
        meth = ", ".join(ls["methods"]) or "not listed"
        print(f"  source    {ls['vendor']} -> {ls['category']} parser [{ls['ls_id']}]")
        print(f"            parser supports: {meth}  (which one THIS customer uses is still theirs to confirm)")

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
    extras = []
    if VERSION_TL:
        extras.append("version timeline (%d releases)" % len(VERSION_TL.get("versions", [])))
    if PARSER_CAT:
        extras.append("parser catalogue (%d parsers)" % PARSER_CAT.get("count", 0))
    print("%d problem types loaded%s" % (len(TYPES), (" + " + ", ".join(extras)) if extras else ""))
    for c in [
        "After yesterday's update our logs stopped arriving. DemoCollector 2.4.4.",
        "Logs from the FortiGate are not arriving. DemoCollector 2.3.6.",
        "Does it run on DemoCollector 2.6?",
        "Customer wants Teams notifications. DemoCollector Pro.",
        "The dashboard colours look wrong.",
    ]:
        report(c)

"""Answer 'does this exist for me, and am I inside its limits?' from a table.

No document search, no model. A whole class of support questions is a lookup.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).parent
CAP = json.loads((HERE / "capabilities.json").read_text(encoding="utf-8"))
PRODUCTS = CAP["products"]
FEATURES = {f["key"]: f for f in CAP["features"]}


def check(feature_key, product, tier=None, os=None):
    """Return (verdict, reason, where it is available instead)."""
    f = FEATURES.get(feature_key)
    if not f:
        return "UNKNOWN_FEATURE", f"No feature called {feature_key} in the table.", []
    if product not in PRODUCTS:
        return "UNKNOWN_PRODUCT", f"No product called {product}.", []

    elsewhere = [f"{p} {t}" for p, ts in f["available"].items() for t in ts]
    tiers = f["available"].get(product)
    if not tiers:
        return "NOT_AVAILABLE", f"{f['label']} does not exist for {product} on any licence.", elsewhere
    if tier and tier not in tiers:
        return ("NOT_IN_THIS_TIER",
                f"{f['label']} is not included in {product} {tier}. It needs one of: {", ".join(tiers)}.", elsewhere)

    if os:
        low = os.lower()
        supported = PRODUCTS[product]["os"]
        if supported and "windows" in low and not any("windows" in s.lower() for s in supported):
            return ("NOT_SUPPORTED_ON_OS",
                    f"{product} does not run on Windows. " + " ".join(PRODUCTS[product]["os_notes"]), elsewhere)

    notes = [p["requires"] for p in CAP["prerequisites"]
             if p["feature"] == feature_key
             and (p["os"] == "any" or (os and any(w in os.lower() for w in ("linux", "rhel", "alma"))))]
    return "AVAILABLE", ("Prerequisites: " + "; ".join(notes) if notes else "Included in this licence."), elsewhere


def limit(product, tier, what, amount=None):
    """Is the customer inside the quota for their licence? Returns (verdict, reason)."""
    cap = CAP["limits"].get(product, {}).get(tier, {}).get(what, "missing")
    label = CAP["limit_labels"].get(what, what)
    if cap == "missing":
        return "UNKNOWN_LIMIT", f"No limit recorded for {what} on {product} {tier}."
    if cap is None:
        return "UNLIMITED", f"{product} {tier} has no limit on {label}."
    if amount is None:
        return "LIMITED", f"{product} {tier} allows {cap} {label}."
    if amount > cap:
        return ("OVER_LIMIT",
                f"{product} {tier} allows {cap} {label}; {amount} were requested. "
                f"This is the licence limit, not a fault.")
    return "WITHIN_LIMIT", f"{amount} of {cap} {label} used."


if __name__ == "__main__":
    print("=== feature availability ===")
    for a in [("chat_alert", "DemoCollector", "Pro", None),
              ("file_collection", "DemoCollector", "Free", None),
              ("syslog_receive", "DemoCollector", "Limited-Monitor", None),
              ("complex_log_search", "DemoQuery", "Log", "Windows Server 2022"),
              ("wmi_collection", "DemoCollector", "Pro", "AlmaLinux 9")]:
        v, why, other = check(*a)
        print(f"\n{a[0]} · {a[1]} {a[2]} {a[3] or ''}\n  {v}\n  {why}")
        if v.startswith("NOT") and other:
            print(f"  available on: {', '.join(other)}")
    print("\n=== licence limits ===")
    for a in [("DemoCollector", "Free", "devices", 14),
              ("DemoCollector", "Free", "retention_days", 30),
              ("DemoCollector", "Pro", "devices", 400)]:
        v, why = limit(*a)
        print(f"\n{a[2]} = {a[3]} · {a[0]} {a[1]}\n  {v}\n  {why}")

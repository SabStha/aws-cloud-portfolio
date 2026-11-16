"""Run the 30 test questions through the real Knowledge Base and show what comes back."""
import json, pathlib, subprocess

KB = "LBOXPJZS9Z"
tests = json.loads(pathlib.Path("fixtures/test_cases.json").read_text(encoding="utf-8"))["tests"]
print(f'{"test":<6} {"expected":<10} {"want":<10} {"top result":<10} {"score":>5} {"2nd":>5}  right doc on top?')
for t in tests:
    if not t["version"]:
        print(f'{t["id"]:<6} {t["expected"]:<10} (no version: the gate stops before searching)')
        continue
    cfg = {"managedSearchConfiguration": {"numberOfResults": 3, "filter": {"andAll": [
        {"equals": {"key": "version", "value": t["version"]}},
        {"equals": {"key": "review_status", "value": "APPROVED"}},
        {"equals": {"key": "audience", "value": "support"}}]}}}
    out = subprocess.run(["aws", "bedrock-agent-runtime", "retrieve", "--profile", "stratus",
        "--knowledge-base-id", KB, "--retrieval-query", json.dumps({"text": t["question"]}),
        "--retrieval-configuration", json.dumps(cfg), "--output", "json"], capture_output=True, text=True)
    if out.returncode != 0:
        print(t["id"], "ERROR", out.stderr.strip()[:120]); continue
    r = json.loads(out.stdout)["retrievalResults"]
    docs = [x["location"]["s3Location"]["uri"].split("/")[-1][:-3] for x in r]
    sc = [x.get("score", 0) for x in r]
    top = docs[0] if docs else "-"; want = t["expected_source"] or "-"
    note = "" if want == "-" else ("yes" if top == want else "NO")
    print(f'{t["id"]:<6} {t["expected"]:<10} {want:<10} {top:<10} {sc[0] if sc else 0:5.2f} {sc[1] if len(sc) > 1 else 0:5.2f}  {note}')

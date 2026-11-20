"""Run the 30 contract tests against gate() and print a score."""
import json
import pathlib
from gate import gate

tests = json.loads((pathlib.Path(__file__).parent / "fixtures/test_cases.json").read_text(encoding="utf-8"))["tests"]
passed = 0
for t in tests:
    status, reason, used = gate(t["question"], t["version"])
    ok = status == t["expected"]
    passed += ok
    print(f'{"PASS" if ok else "FAIL"}  {t["id"]}  expected {t["expected"]:<10} got {status:<10} {t["question"][:50]}')
print(f"\nScore: {passed} / {len(tests)}")

"""Runs the phrasings in data/fail_closed.json through the rules interpreter and the engine.

Each must either ask the rep (needs_info) or produce exactly the quote listed. These were
fixed after review, so passing them is a regression check, not evidence of general coverage.
"""
import json
import sys
from pathlib import Path

from quoter.engine import build_quote
from quoter.interpret import RulesInterpreter

checks = json.loads((Path(__file__).parent / "data" / "fail_closed.json").read_text())["checks"]
interp = RulesInterpreter()
failed = 0
for c in checks:
    try:
        q = build_quote(interp(c["prompt"]))
        got = {"status": q.status, "product": q.product, "year1_total": q.year1_total,
               "contract_total": q.contract_total, "approvers": q.approvers,
               "auto_approve_eligible": q.auto_approve_eligible}
    except Exception as e:  # a crash is a failure, never a pass
        got = {"status": f"crash: {e!r}"}
    exp = c["expect"]
    ok = got["status"] == "needs_info" if exp == "needs_info" else all(got.get(k) == v for k, v in exp.items())
    failed += not ok
    print(("ok   " if ok else "FAIL ") + c["prompt"] + ("" if ok else f"\n     got {got}"))
print(f"\n{len(checks) - failed} of {len(checks)} pass")
sys.exit(1 if failed else 0)

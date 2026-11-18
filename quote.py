"""Quote one deal from a plain-English description.

  python3 quote.py "Halcyon Bank: Plus, 50 users, annual, 18% discount, close Dec 22."
  python3 quote.py --interpreter claude "..."
"""
import argparse, json
from quoter.engine import build_quote, render

ap = argparse.ArgumentParser()
ap.add_argument("prompt")
ap.add_argument("--interpreter", choices=["rules", "claude"], default="rules")
ap.add_argument("--json", action="store_true")
a = ap.parse_args()
if a.interpreter == "claude":
    from quoter.claude_interpreter import ClaudeInterpreter as I
else:
    from quoter.interpret import RulesInterpreter as I
spec = I()(a.prompt)
q = build_quote(spec)
print(json.dumps({"spec": spec.__dict__, "quote": q.to_dict()}, indent=1) if a.json else render(q, spec))

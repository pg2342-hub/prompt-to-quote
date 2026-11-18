"""Re-quotes every test deal under two versions of the price book and lists every quote that changes.

  python3 price_change.py   # pricing page before the Nov 3, 2026 launch vs at launch

This is the check a deal desk wants before a price-book change goes live: which
in-flight quotes move, and how.
"""
import json
from pathlib import Path
from quoter.engine import DealSpec, build_quote, load_book

ROOT = Path(__file__).resolve().parent
old, new = load_book(ROOT / "data/price_book_pre_launch.json"), load_book(ROOT / "data/price_book.json")
cases = [c for c in json.loads((ROOT / "data/cases.json").read_text())["cases"]]

def key(q):
    return (q.status, q.product, q.year1_total, tuple(q.approvers), tuple(sorted(f.code for f in q.flags)),
            tuple((c["reason"], c["credits"]) for c in q.credits))

rows = []
for c in cases:
    spec = DealSpec.from_dict(c["gold_spec"])
    a, b = build_quote(spec, old), build_quote(spec, new)
    if key(a) != key(b):
        diffs = []
        for name, x, y in [("status", a.status, b.status), ("product", a.product, b.product),
                           ("year 1", a.year1_total, b.year1_total), ("approvers", a.approvers, b.approvers),
                           ("flags", sorted(f.code for f in a.flags), sorted(f.code for f in b.flags)),
                           ("credits", [c_["reason"] for c_ in a.credits], [c_["reason"] for c_ in b.credits])]:
            if x != y:
                diffs.append(f"{name}: {x} -> {y}")
        rows.append(f"| {c['id']} | {c['prompt']} | {'; '.join(diffs)} |")
out = [f"# Price-book change: {old['version']} -> {new['version']}", "",
       f"{len(rows)} of {len(cases)} test quotes change.", "", "| Case | Deal | What changes |", "|---|---|---|"] + rows
(ROOT / "reports/price_change.md").write_text("\n".join(out) + "\n")
print("\n".join(out))

"""Precompute the demo page's example quotes, so the page shows a finished quote before Python loads.

    python3 scripts/build_examples.py

Runs each example prompt through the same RulesInterpreter and build_quote the page runs in the
browser, and writes the results into index.html between the <!-- examples --> markers. Safe to run twice.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from quoter.engine import build_quote  # noqa: E402
from quoter.interpret import RulesInterpreter  # noqa: E402

# (prompt, short label for the chip, what the example shows)
EXAMPLES = [
    ("Essential for Kite Data, 20 users, about 40,000 events a year, annual.", "Kite Data", "credits needed"),
    ("Plus for Halcyon Bank, 50 users, 18% discount, net 60, close Dec 22", "Halcyon Bank", "approvals"),
    ("Starter for Pike & Co, 34 users", "Pike & Co", "seat cap"),
    ("Essential for Quill Software, 15 users, billed monthly.", "Quill Software", "annual only"),
    ("Plus for Cobalt Energy, 40 users, 30,000 AI Actions a year, closing Dec 30.", "Cobalt Energy", "promotion"),
    ("Cask Systems is currently on Business, quote Essential for 20 users", "Cask Systems", "older plan"),
    ("Essential for Acme, 20 users, first year free", "Acme", "asks the rep"),
    ("Reliability Platform for Pinecrest Apps, 14 users, about 3,000 events a year, annual.", "Pinecrest Apps", "picks a tier"),
    ("Professional for 200 users at Vantage Media, annual, 35% off for a 3 year deal with price locked.", "Vantage Media", "big discount"),
]


def build() -> list[dict]:
    interp = RulesInterpreter()
    out = []
    for prompt, name, tag in EXAMPLES:
        spec = interp(prompt)
        out.append({"prompt": prompt, "name": name, "tag": tag,
                    "spec": spec.__dict__, "quote": build_quote(spec).to_dict()})
    return out


if __name__ == "__main__":
    page_path = ROOT / "index.html"
    page = page_path.read_text(encoding="utf-8")
    data = json.dumps(build(), separators=(",", ":")).replace("</", "<\\/")
    block = f'<!-- examples --><script id="examples" type="application/json">{data}</script><!-- /examples -->'
    new, n = re.subn(r"<!-- examples -->.*?<!-- /examples -->", lambda m: block, page, flags=re.S)
    if n != 1:
        sys.exit("index.html needs exactly one <!-- examples --> ... <!-- /examples --> block")
    page_path.write_text(new, encoding="utf-8")
    print(f"wrote {len(EXAMPLES)} example quotes into {page_path.name}")

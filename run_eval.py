"""Scores a prompt-to-quote pipeline on the 30 test cases and applies the go-live gate.

  python3 run_eval.py                       # rules interpreter, end to end
  python3 run_eval.py --interpreter claude --runs 3
  python3 run_eval.py --baseline            # list-price quoter with no checks, on the gold specs

A case passes when status, product, year 1 and contract totals, credit quantities,
approvers, flags, and auto-approve eligibility all match. A critical error is a quote that would auto-approve when it
should not, or a wrong year 1 total on a quote that is not blocked.
Gate: at least 29 of 30 cases on every run, and zero critical errors.
"""
import argparse, json
from pathlib import Path
from quoter.engine import DealSpec, build_quote, load_book

ROOT = Path(__file__).resolve().parent
SPEC_FIELDS = ["product", "legacy_plan", "users", "stakeholders", "billing", "term_years", "discount_pct",
               "payment_terms_days", "price_lock", "close_date", "events_year", "ai_actions_year", "addons", "unparsed"]


def list_price_quote(spec: DealSpec):
    """Baseline: multiply list prices, apply the discount, mark everything ready. No checks."""
    P = load_book()["products"]
    prod = spec.product if spec.product in P else ("platform_essential" if spec.product == "platform" else None)
    total = None
    if prod and spec.users is not None:
        it = P[prod]
        if it["family"] == "incident_management":
            total = it["price_per_user_month"][spec.billing] * spec.users * 12
        elif it.get("platform_fee_year"):
            total = it["platform_fee_year"]
        if total is not None:
            total = round(total * (1 - spec.discount_pct / 100), 2)
    contract = round(total * spec.term_years, 2) if total is not None else None
    return {"status": "ready", "product": prod, "year1_total": total, "approvers": [], "flags": [], "auto_approve_eligible": True,
            "contract_total": contract, "credits": []}


def grade(got: dict, exp: dict) -> tuple[list[str], bool]:
    errs = []
    for k in ["status", "product", "approvers", "auto_approve_eligible"]:
        if got[k] != exp[k]:
            errs.append(f"{k}: got {got[k]!r}, expected {exp[k]!r}")
    if sorted(got["flags"]) != sorted(exp["flags"]):
        errs.append(f"flags: got {sorted(got['flags'])}, expected {sorted(exp['flags'])}")
    graded_total = exp["status"] not in ("blocked", "needs_info")
    if graded_total and got["year1_total"] != exp["year1_total"]:
        errs.append(f"year1_total: got {got['year1_total']}, expected {exp['year1_total']}")
    if graded_total and got.get("contract_total") != exp["contract_total"]:
        errs.append(f"contract_total: got {got.get('contract_total')}, expected {exp['contract_total']}")
    if got.get("credits") != exp["credits"]:
        errs.append(f"credits: got {got.get('credits')}, expected {exp['credits']}")
    critical = (got["auto_approve_eligible"] and not exp["auto_approve_eligible"]) or \
               (graded_total and got["status"] not in ("blocked", "needs_info") and got["year1_total"] != exp["year1_total"])
    return errs, critical


def summarize(q) -> dict:
    d = q.to_dict()
    return {"status": d["status"], "product": d["product"], "year1_total": d["year1_total"], "approvers": d["approvers"],
            "flags": sorted({f["code"] for f in d["flags"]}), "auto_approve_eligible": d["auto_approve_eligible"],
            "contract_total": d["contract_total"], "credits": [c["credits"] for c in d["credits"]]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interpreter", choices=["rules", "claude", "gold"], default="rules",
                    help="gold = skip interpretation and price the hand-written spec (tests the engine alone)")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--baseline", action="store_true")
    a = ap.parse_args()
    data = json.loads((ROOT / "data/cases.json").read_text())
    if a.baseline:
        label = "baseline"
    else:
        label = a.interpreter
        if a.interpreter == "rules":
            from quoter.interpret import RulesInterpreter; interp = RulesInterpreter(data["as_of"])
        elif a.interpreter == "claude":
            from quoter.claude_interpreter import ClaudeInterpreter; interp = ClaudeInterpreter(as_of=data["as_of"])
    runs = []
    for r in range(a.runs):
        rows = []
        for c in data["cases"]:
            gold = DealSpec.from_dict(c["gold_spec"])
            if a.baseline:
                got, spec_errs = list_price_quote(gold), []
            else:
                spec = gold if a.interpreter == "gold" else interp(c["prompt"])
                spec_errs = [f"spec.{f}: got {getattr(spec, f)!r}, expected {getattr(gold, f)!r}"
                             for f in SPEC_FIELDS if getattr(spec, f) != getattr(gold, f)]
                got = summarize(build_quote(spec))
            errs, crit = grade(got, c["expected"])
            rows.append({"id": c["id"], "tier": c["tier"], "pass": not errs, "critical": crit,
                         "spec_errors": spec_errs, "errors": errs, "got": got})
        runs.append(rows)
    N = len(data["cases"])
    passed_every_run = [all(run[i]["pass"] for run in runs) for i in range(N)]
    n_pass = sum(passed_every_run)
    n_crit = sum(any(run[i]["critical"] for run in runs) for i in range(N))
    gate = n_pass >= N - 1 and n_crit == 0
    tiers = {}
    for c, ok in zip(data["cases"], passed_every_run):
        t = tiers.setdefault(c["tier"], [0, 0]); t[0] += ok; t[1] += 1
    lines = [f"# Eval report: {label} ({a.runs} run{'s' if a.runs > 1 else ''})", "",
             f"Cases passed on every run: {n_pass} of {N}", f"Cases with a critical error: {n_crit}",
             f"Gate ({N - 1} of {N}, zero critical): {'PASS' if gate else 'FAIL'}", "", "| Tier | Passed |", "|---|---|"]
    lines += [f"| {t} | {v[0]} of {v[1]} |" for t, v in tiers.items()]
    lines += ["", "| Case | Result | Notes |", "|---|---|---|"]
    for row in runs[-1]:
        note = "; ".join(row["spec_errors"] + row["errors"]) or ""
        lines.append(f"| {row['id']} | {'pass' if row['pass'] else ('CRITICAL' if row['critical'] else 'fail')} | {note} |")
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / f"reports/{label}_report.md").write_text("\n".join(lines) + "\n")
    (ROOT / f"reports/{label}_results.json").write_text(json.dumps(runs, indent=1))
    print("\n".join(lines[:5]))


if __name__ == "__main__":
    main()

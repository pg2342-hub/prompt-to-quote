"""Pricing engine and approval check.

The engine never reads the rep's words. It takes a structured DealSpec (from the
interpreter), prices it only from the price book, and checks it against the
approval policy. Every dollar on a quote traces to a price-book entry; anything the
book does not price comes back as a flag for deal desk instead of a number.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
PLATFORM_ORDER = ["platform_starter", "platform_essential", "platform_plus", "platform_ultimate"]


def load_book(path: Path | None = None) -> dict:
    return json.loads((path or DATA / "price_book.json").read_text())


def load_policy(path: Path | None = None) -> dict:
    return json.loads((path or DATA / "approval_policy.json").read_text())


@dataclass
class DealSpec:
    """What the interpreter must extract from the rep's prompt. Nothing else."""
    customer: str | None = None
    product: str | None = None          # a price-book key, "platform" (tier not named), or None
    legacy_plan: str | None = None      # "business", "enterprise", "operations_cloud"
    users: int | None = None            # full (responder) users
    stakeholders: int = 0
    billing: str = "annual"             # "annual" or "monthly"
    term_years: int = 1
    discount_pct: float = 0.0
    payment_terms_days: int = 30
    price_lock: bool = False
    close_date: str | None = None       # ISO date
    events_year: int | None = None
    ai_actions_year: int | None = None
    addons: list[str] = field(default_factory=list)  # unpriced SKU keys
    unparsed: list[str] = field(default_factory=list)  # terms the rep used that the interpreter could not read

    @classmethod
    def from_dict(cls, d: dict) -> "DealSpec":
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass
class Flag:
    code: str
    severity: str   # "info"; "check" (a person confirms, no approver added); "route" (adds an approver); "block" (cannot quote as asked); "ask" (missing input)
    message: str
    approvers: list[str] = field(default_factory=list)


@dataclass
class Quote:
    status: str
    product: str | None
    lines: list[dict]
    discount_pct: float
    year1_total: float | None
    contract_total: float | None
    credits: list[dict]
    approvers: list[str]
    flags: list[Flag]
    auto_approve_eligible: bool

    def to_dict(self) -> dict:
        d = asdict(self)
        d["flags"] = [asdict(f) for f in self.flags]
        return d


def _seats(spec: DealSpec) -> int | None:
    if spec.users is None:
        return None
    return spec.users + (spec.stakeholders or 0)


def _fits(tier: dict, seats: int, spec: DealSpec, use_bonus: bool = True) -> bool:
    cap = tier["seats_included"] + (tier.get("bonus_seats", 0) if use_bonus else 0)
    return (seats <= cap
            and (spec.events_year or 0) <= tier["events_year"]
            and (spec.ai_actions_year or 0) <= tier["ai_actions_year"])


def recommend_tier(spec: DealSpec, book: dict) -> str:
    """Smallest platform tier whose included allowances cover the deal with no credits."""
    seats = _seats(spec) or 0
    for key in PLATFORM_ORDER[:-1]:
        if _fits(book["products"][key], seats, spec):
            return key
    return "platform_ultimate"


def build_quote(spec: DealSpec, book: dict | None = None, policy: dict | None = None) -> Quote:
    book = book or load_book()
    policy = policy or load_policy()
    P = book["products"]
    flags: list[Flag] = []
    lines: list[dict] = []
    credits: list[dict] = []

    def flag(code, sev, msg, approvers=None):
        flags.append(Flag(code, sev, msg, approvers or []))

    # ---- inputs the engine cannot guess ----
    if spec.legacy_plan and spec.product:
        flag("LEGACY_MIGRATION", "route",
             f"Customer is moving from the '{spec.legacy_plan}' plan, which is no longer on the public price list; deal desk confirms how its current entitlements map to the new plan.",
             policy["nonstandard_terms"]["legacy_plan"])
    elif spec.legacy_plan:
        flag("LEGACY_PLAN", "route",
             f"'{spec.legacy_plan}' is no longer on the public price list; deal desk prices the renewal or the move to a current plan.",
             policy["nonstandard_terms"]["legacy_plan"])
    for term in spec.unparsed:
        flag("UNPARSED", "ask", f"The request mentions {term}, but it could not be read into the deal; restate it (for example '15% off', '40,000 events a year').")
    if not 0 <= (spec.discount_pct or 0) <= 100:
        flag("BAD_DISCOUNT", "block", f"A discount of {spec.discount_pct:g}% is outside 0 to 100%.")
    if spec.product is None and not spec.legacy_plan:
        flag("MISSING_PRODUCT", "ask", "Which plan? Professional (per user) or the Reliability Platform (Starter, Essential, Plus, Ultimate)?")
    if spec.users is None and spec.product != "platform_ultimate" and not spec.legacy_plan:
        flag("MISSING_SEATS", "ask", "How many users (responders), and how many stakeholders?")

    product = spec.product
    if product == "platform" and spec.users is not None:
        product = recommend_tier(spec, book)
        flag("TIER_RECOMMENDED", "check",
             f"Rep did not name a tier; {P[product]['name']} is the smallest tier whose included seats, events, and AI Actions cover this deal.")
        alt = None
        for key in PLATFORM_ORDER[:PLATFORM_ORDER.index(product)]:
            t = P[key]
            if _fits({**t, "seats_included": t.get("seat_cap") or 10**9, "bonus_seats": 0}, _seats(spec), spec):
                alt = key  # keeps the largest lower tier that fits with extra seats
        if alt:
            t = P[alt]
            extra = _seats(spec) - t["seats_included"] - t.get("bonus_seats", 0)
            per = f" at {t['extra_seat_credits']} credits each" if "extra_seat_credits" in t else ""
            flag("ALTERNATIVE_TIER", "check",
                 f"{t['name']} plus {extra} extra seats bought with credits{per} may cost less; compare once deal desk sets the credit rate.")

    seats = _seats(spec)
    d = spec.discount_pct or 0.0

    if (product in P and seats is not None) or product == "platform_ultimate":
        item = P[product]
        if item["family"] == "incident_management":
            if product == "im_free" and seats > item["max_users"]:
                flag("FREE_OVER_LIMIT", "block", f"Free covers up to {item['max_users']} users; this deal has {seats}. Quote Professional instead.")
            if spec.stakeholders:
                flag("UNPRICED_SKU", "route", "Stakeholder licenses for Professional are not on the public price list.",
                     policy["nonstandard_terms"]["unpriced_sku"])
            rate = item["price_per_user_month"][spec.billing]
            if product != "im_free" or seats <= item["max_users"]:
                lines.append({"sku": product, "description": f"{item['name']} ({spec.billing} billing)",
                              "qty": spec.users, "unit": "user/month", "unit_price": rate,
                              "amount_year": rate * spec.users * 12,
                              "source": f"price_book {book['version']}: {product}.price_per_user_month.{spec.billing}"})
            if spec.events_year or spec.ai_actions_year:
                flag("USAGE_ON_PER_USER_PLAN", "ask", f"{item['name']} has no event or AI Action allowance in the price book; did the customer mean the Reliability Platform, or an add-on such as AIOps or Advance?")
            if spec.billing == "monthly" and spec.term_years > 1:
                flag("MONTHLY_MULTI_YEAR", "info", "Monthly billing on a multi-year term; confirm the customer wants monthly rather than the annual rate.")
        else:  # platform
            if spec.billing == "monthly":
                flag("PLATFORM_MONTHLY", "block", "The Reliability Platform is billed annually, paid upfront; there is no monthly option.")
            if item.get("custom_pricing"):
                flag("CUSTOM_TIER", "route", f"{item['name']} has custom pricing; deal desk sets the platform fee.",
                     policy["nonstandard_terms"]["custom_tier"])
            else:
                lines.append({"sku": product, "description": f"{item['name']} platform fee (annual, upfront)",
                              "qty": 1, "unit": "year", "unit_price": item["platform_fee_year"],
                              "amount_year": item["platform_fee_year"],
                              "source": f"price_book {book['version']}: {product}.platform_fee_year"})
            if seats is not None:
                cap = item.get("seat_cap")
                base = item["seats_included"]
                bonus = item.get("bonus_seats", 0)
                if cap and seats > cap:
                    flag("SEAT_CAP", "block", f"{item['name']} has a {cap}-seat cap; this deal needs {seats} seats (stakeholders count as seats). Quote Essential instead.")
                else:
                    if seats > base + bonus:
                        extra = seats - base - bonus
                        if "extra_seat_credits" in item:
                            credits.append({"reason": f"{extra} extra seats", "credits": extra * item["extra_seat_credits"]})
                        else:
                            credits.append({"reason": f"{extra} seats above the {base} included", "credits": None})
                    if seats > base and bonus:
                        flag("BONUS_SEATS_RELIED", "route", item["bonus_note"] + f" (deal uses {min(seats - base, bonus)} bonus seats).",
                             ["deal_desk"])
            if spec.events_year and spec.events_year > item["events_year"]:
                credits.append({"reason": f"{spec.events_year - item['events_year']:,} events a year above the {item['events_year']:,} included", "credits": None})
            if spec.ai_actions_year and spec.ai_actions_year > item["ai_actions_year"]:
                promo = book["rules"]["ai_actions_promo"]
                if product in promo["tiers"] and spec.close_date and date.fromisoformat(spec.close_date) <= date.fromisoformat(promo["sign_by"]):
                    flag("PROMO_APPLIED", "route", f"The promotion adds AI Actions at no credits in year 1 (signed by {promo['sign_by']}), but PagerDuty does not publish how many; deal desk confirms it covers {spec.ai_actions_year - item['ai_actions_year']:,} more a year.",
                         ["deal_desk"])
                    if spec.term_years > 1:
                        credits.append({"reason": "AI Actions above the allowance in years 2+", "credits": None})
                else:
                    if product in promo["tiers"] and spec.close_date:
                        flag("PROMO_EXPIRED", "info", f"Close date {spec.close_date} is after {promo['sign_by']}, so the AI Actions promotion does not apply.")
                    elif product in promo["tiers"]:
                        flag("PROMO_NEEDS_CLOSE_DATE", "info", f"AI Actions above the allowance are free in year 1 only if signed by {promo['sign_by']}; no close date given.")
                    credits.append({"reason": f"{spec.ai_actions_year - item['ai_actions_year']:,} AI Actions a year above the {item['ai_actions_year']:,} included", "credits": None})
    elif product in P and seats is None:
        pass  # MISSING_SEATS already raised

    if credits:
        flag("CREDITS_NEEDED", "route", "Extra usage is bought with credits, and PagerDuty does not publish a price per credit; deal desk sets the rate.",
             policy["nonstandard_terms"]["credits_rate_needed"])
    for a in spec.addons:
        flag("UNPRICED_SKU", "route", f"{book['unpriced_skus'].get(a, a)}: deal desk prices it.", policy["nonstandard_terms"]["unpriced_sku"])

    # ---- commercial terms ----
    band = next((b for b in policy["discount_bands"] if d <= b["max_pct"]), policy["discount_bands"][-1])
    if band["approvers"] and 0 < d <= 100:
        flags.append(Flag("DISCOUNT", "route", f"{d:g}% discount needs {', '.join(band['approvers'])}.", band["approvers"]))
    if spec.payment_terms_days > policy["standard_payment_terms_days"]:
        flag("PAYMENT_TERMS", "route", f"Net {spec.payment_terms_days} is beyond standard net {policy['standard_payment_terms_days']}.",
             policy["nonstandard_terms"]["payment_terms_over_standard"])
    if spec.price_lock:
        flag("PRICE_LOCK", "route", "Multi-year price lock is a non-standard term.", policy["nonstandard_terms"]["multi_year_price_lock"])

    # ---- totals ----
    blocked = any(f.severity == "block" for f in flags)
    asking = any(f.severity == "ask" for f in flags)  # a quote that needs input shows no total a rep could forward
    priced = bool(lines) and not blocked and not asking and not any(f.code in ("CUSTOM_TIER", "LEGACY_PLAN") for f in flags)
    year1 = round(sum(l["amount_year"] for l in lines) * (1 - d / 100), 2) if priced else None
    contract = round(year1 * spec.term_years, 2) if year1 is not None else None

    order = ["sales_manager", "deal_desk", "finance", "cro"]
    approvers = sorted({a for f in flags for a in f.approvers}, key=order.index)
    sev = {f.severity for f in flags}
    status = ("needs_info" if "ask" in sev else "blocked" if "block" in sev
              else "needs_approval" if approvers else "ready")
    auto = status in ("ready", "needs_approval") and approvers in ([], ["sales_manager"]) \
        and not any((f.severity == "route" and f.code != "DISCOUNT") or f.severity == "check" for f in flags)
    return Quote(status, product if product in P else None, lines, d, year1, contract, credits, approvers, flags, auto)


def render(q: Quote, spec: DealSpec) -> str:
    out = [f"Quote for {spec.customer or '(customer not named)'}  |  status: {q.status.upper()}"]
    for l in q.lines:
        out.append(f"  {l['description']}: {l['qty']} x ${l['unit_price']:,} per {l['unit'].split('/')[-1]} -> ${l['amount_year']:,.0f}/yr   [{l['source']}]")
    if q.year1_total is not None:
        disc = f" after {q.discount_pct:g}% discount" if q.discount_pct else ""
        out.append(f"  Year 1 total{disc}: ${q.year1_total:,.2f}   Contract ({spec.term_years} yr): ${q.contract_total:,.2f}")
    for c in q.credits:
        out.append(f"  Credits: {c['reason']}" + (f" = {c['credits']:,} credits" if c["credits"] else "") + " (rate set by deal desk)")
    for f in q.flags:
        out.append(f"  [{f.severity}] {f.code}: {f.message}")
    out.append(f"  Approvers: {', '.join(q.approvers) or 'none'}   Auto-approve eligible after pilot month 1: {'yes' if q.auto_approve_eligible else 'no'}")
    return "\n".join(out)

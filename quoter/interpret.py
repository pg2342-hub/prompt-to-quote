"""Turns a rep's plain-English deal description into a DealSpec.

Two interpreters share one output schema:
- RulesInterpreter: offline, regex based. It was written with the test prompts in
  view, so its score shows the pipeline runs end to end, not that it generalizes.
- ClaudeInterpreter (claude_interpreter.py): a model fills the same schema by calling a
  strict tool. The model only extracts fields; it never prices.
Both fail closed: a commercial term they cannot read goes into `unparsed`, and the
engine then asks the rep instead of quoting without it.
"""
from __future__ import annotations

import difflib
import re
from datetime import date

from .engine import DealSpec

MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
ADDONS = {"aiops": "aiops", "advance": "advance", "live call routing": "lcr_addon",
          "status page": "status_pages", "runbook automation": "runbook_automation"}
PRODUCT_WORDS = {"Professional", "Essential", "Plus", "Starter", "Ultimate", "Free", "Reliability", "Platform",
                 "Business", "Enterprise", "Quote", "Renew", "Move", "New", "Put", "The", "Same", "Can", "Could",
                 "Please", "Need", "Renewal", "Draft", "Price", "Pricing", "Deal", "For", "Hey", "We", "I", "Our",
                 "Upsell", "Upgrade", "Downgrade", "Expansion", "Customer", "Logo", "PagerDuty", "Annual", "Monthly"}
UNKNOWN_PRODUCTS = {r"process automation": "Process Automation", r"\bjeli\b": "Jeli", r"copilot": "Copilot",
                    r"workflow automation": "Workflow Automation", r"customer service ops": "Customer Service Ops",
                    r"\bsso\b": "SSO", r"premium support": "premium support"}
WORD_NUMS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
QTY = r"(\d[\d,.]*\s*(?:k|m|million|thousand)?)"


def _num(s: str) -> int:
    s = s.replace(",", "").lower().strip()
    for suffix, mult in (("million", 10**6), ("thousand", 1000), ("m", 10**6), ("k", 1000)):
        if s.endswith(suffix):
            return int(round(float(s[: -len(suffix)].strip()) * mult))
    return int(float(s))


VOCAB = ["professional", "essential", "starter", "ultimate", "users", "responders", "stakeholders",
         "discount", "events", "annual", "monthly", "quarterly", "enterprise", "business"]


def _fix_typos(prompt: str) -> str:
    """Corrects one- or two-letter slips in the words the parser keys on ('Essentail', 'usres')."""
    def fix(m):
        w = m.group(0)
        if len(w) < 5 or w.lower() in VOCAB:
            return w
        hit = difflib.get_close_matches(w.lower(), VOCAB, n=1, cutoff=0.8)
        if not hit or sorted(hit[0]) != sorted(w.lower()) and abs(len(hit[0]) - len(w)) > 1:
            return w
        return hit[0].capitalize() if w[0].isupper() else hit[0]
    return re.sub(r"[A-Za-z]+", fix, prompt)


class RulesInterpreter:
    name = "rules"

    def __init__(self, as_of: str = "2026-11-18"):
        self.as_of = date.fromisoformat(as_of)

    def __call__(self, prompt: str) -> DealSpec:
        p = _fix_typos(prompt)
        low = p.lower()
        s = DealSpec()
        used: list[tuple[int, int]] = []   # spans of the prompt the parser understood

        def find(pattern, text=low, flags=0):
            m = re.search(pattern, text, flags)
            if m:
                used.append(m.span())
            return m

        def ask(what):
            if what not in s.unparsed:
                s.unparsed.append(what)

        # product; "from <old> to <new>" keeps the new plan, and an older Business or Enterprise plan is recorded
        TIERS = r"(professional|free|starter|essential|plus|ultimate|business|enterprise|operations cloud)"
        move = re.search(r"\bfrom\s+(?:the\s+|their\s+)?" + TIERS + r"(?:\s+plan)?(?:\s*\([^)]*\))?\s+(?:to|onto)\s+(?:the\s+)?" + TIERS, low)
        target = None
        if move:
            if move.group(1) in ("business", "enterprise", "operations cloud"):
                s.legacy_plan = move.group(1).replace(" ", "_")
            target = move.group(2)
            prod_text = low[move.start(2):move.end(2)]
        else:
            LEG = r"(business|enterprise|operations cloud)"
            m = re.search(r"\bfrom\s+(?:the\s+|their\s+)?" + LEG + r"\b", low) or \
                re.search(r"\b" + LEG + r"\s+(?:plan|customer|contract|renewal)\b", low) or \
                re.search(r"\b(?:on|currently|today|renew\w*)\s+(?:on\s+|the\s+|their\s+)*" + LEG + r"\b", low)
            if m:
                s.legacy_plan = m.group(1).replace(" ", "_")
            elif re.search(r"\b" + LEG + r"\b", low):
                ask("an older plan name (Business, Enterprise, or Operations Cloud) without saying whether the customer is on it")
            prod_text = low if not m else low.replace(m.group(0), " ")
        names = {"professional": "im_professional", "starter": "platform_starter", "essential": "platform_essential",
                 "plus": "platform_plus", "ultimate": "platform_ultimate", "free": "im_free"}
        if target in names:
            s.product = names[target]
        elif target:
            s.product = None
        elif "professional" in prod_text:
            s.product = "im_professional"
        elif re.search(r"\bfree\s+plan\b", prod_text):
            s.product = "im_free"
        elif re.search(r"\bstarter\b", prod_text):
            s.product = "platform_starter"
        elif re.search(r"\bessential\b", prod_text):
            s.product = "platform_essential"
        elif re.search(r"\bPlus\b(?!\s+\d)", p) and not move:
            s.product = "platform_plus"
        elif re.search(r"\bultimate\b", prod_text):
            s.product = "platform_ultimate"
        elif "reliability platform" in prod_text:
            s.product = "platform"

        # people
        m = find(r"(\d[\d,]*)\s+(?:[a-z]+\s+)?(?:users|responders|seats|people|engineers)\b", p, re.I)
        if m:
            s.users = _num(m.group(1))
        m = find(r"(\d[\d,]*)\s+stakeholders?\b(?:\s+licen[sc]es?)?")
        if m:
            s.stakeholders = _num(m.group(1))
        elif "stakeholder" in low:
            ask("stakeholders without a count")

        # billing and term
        if re.search(r"quarterly|semi-annual|biannual", low):
            ask("a billing frequency other than annual or monthly")
        s.billing = "monthly" if re.search(r"\bmonthly\b|billed (?:per|each) month", low) else "annual"
        m = find(r"\b(\d+|one|two|three|four|five)[- ]?(?:years?|yrs?)\b(?!\s*(?:1|one)\b)")
        mm = find(r"\b(\d+)[- ]?months?\b(?:\s+term|\s+deal|\s+contract)?")
        if m:
            s.term_years = int(m.group(1)) if m.group(1).isdigit() else WORD_NUMS[m.group(1)]
        elif mm and int(mm.group(1)) % 12 == 0:
            s.term_years = int(mm.group(1)) // 12
        elif mm:
            ask(f"a {mm.group(1)}-month term")
        elif re.search(r"multi[- ]year", low):
            ask("a multi-year term with no length")
        if re.search(r"years?\s+\d\s*(?:-|to|and)\s*\d|year\s+(?:1|one|2|two)\b", low):
            ask("terms that differ by year")

        # discount: exactly one percentage, stated as a discount
        pcts = re.findall(r"(\d+(?:\.\d+)?)\s*(?:%|percent\b)", low)
        if len(pcts) > 1 or re.search(r"\b(?:another|additional|extra)\s+\d", low):
            ask("more than one discount")
        elif pcts and re.search(r"discount|\boff\b", low):
            find(r"(\d+(?:\.\d+)?)\s*(?:%|percent\b)")
            s.discount_pct = float(pcts[0])
        elif pcts:
            ask("a percentage that is not clearly a discount")
        elif re.search(r"discount|\boff\b|\$", low) and not re.search(r"no discount|list price|at list", low):
            ask("a discount or price change")
        if re.search(r"\bfree\b(?!\s+plan)|waiv|\bcomp(?:ed|ing|ped)?\b|no charge|credit(?:ed)? back|\bat cost\b", low):
            ask("a free period, waived fee, or other price change")

        # payment terms
        m = find(r"\bnet\s*(\d+)")
        if m:
            s.payment_terms_days = int(m.group(1))
        elif re.search(r"\bnet\b|payment terms", low):
            ask("payment terms")
        s.price_lock = bool(re.search(r"\block(?:ed|s|ing)?\b", low))

        # close date: next occurrence after as_of unless a year is given
        LEAD = r"(?:clos(?:e|es|ing)|sign(?:s|ing|ed)?(?:\s+by)?)\s+(?:date\s+)?(?:on\s+|by\s+|is\s+)?"
        mo = dy = yr = None
        m = find(LEAD + r"([a-z]{3})[a-z]*\.?\s+(\d{1,2})(?:(?:st|nd|rd|th)?,?\s+(\d{4}))?")
        if m and m.group(1) in MONTHS:
            mo, dy, yr = MONTHS[m.group(1)], int(m.group(2)), m.group(3)
        elif m:
            used.pop()
            m = None
        if not m:
            m = find(LEAD + r"(\d{4})-(\d{1,2})-(\d{1,2})\b")
            if m:
                yr, mo, dy = m.group(1), int(m.group(2)), int(m.group(3))
        if not m:
            m = find(LEAD + r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")
            if m:
                mo, dy, yr = int(m.group(1)), int(m.group(2)), m.group(3)
                yr = ("20" + yr) if yr and len(yr) == 2 else yr
        if mo:
            try:
                y = int(yr) if yr else self.as_of.year
                if not yr and date(y, mo, dy) < self.as_of:
                    y += 1
                s.close_date = date(y, mo, dy).isoformat()
            except ValueError:
                ask("a close date")

        # usage: a yearly or monthly volume placed before the word; anything else asks
        def volume(word, label):
            m = find(QTY + r"\s+(?:signal intelligence\s+)?" + word)
            if not m:
                if re.search(word, low):
                    ask(label)
                return None
            try:
                v = _num(m.group(1))
            except ValueError:
                ask(label)
                return None
            tail = low[m.end():m.end() + 25]
            if re.match(r"\s*(?:a|per|each|/)\s*(?:day|week|hour|quarter)", tail) or re.match(r"\s*daily|\s*weekly", tail):
                ask(label + " per day, week, or quarter")
                return None
            if re.match(r"\s*(?:a|per|each|/)\s*mo", tail):
                v *= 12
            return v
        s.events_year = volume(r"events?\b", "an event volume")
        s.ai_actions_year = volume(r"(?:ai|agent) actions?\b", "an AI Actions volume")
        s.addons = [v for k, v in ADDONS.items() if k in low]
        for k, label in UNKNOWN_PRODUCTS.items():
            if re.search(k, low):
                ask(f"'{label}', a product the price book does not list")
        if re.search(r"add[- ]?ons?\b|bundle", low) and not s.addons:
            ask("an add-on that is not named in the price book")

        # any number the parser did not use means it missed something
        for m in re.finditer(r"\$?\d[\d,.]*\s*(?:k|m|million|thousand)?", low):
            if not any(a <= m.start() < b for a, b in used):
                ask(f"'{m.group(0).strip()}'")

        # customer: prefer a name after "for", "at", or "quote"; else the first run of capitalized words
        CAP = r"([A-Z][\w'-]*(?:\s+(?:&\s+)?[A-Z][\w'-]*)*)"
        runs = [m for m in re.finditer(r"\b(?:for|at|quote)\s+" + CAP, p)] + list(re.finditer(r"\b" + CAP, p))
        for m in runs:
            words = [w for w in m.group(1).split() if w not in PRODUCT_WORDS]
            if words and not re.match(r"^(AI|Actions|Dec|Jan|Feb|Mar|Apr|Nov|Oct)$", words[0]):
                s.customer = " ".join(words)
                break
        return s

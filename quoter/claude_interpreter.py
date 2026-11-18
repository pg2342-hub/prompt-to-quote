"""Live-model interpreter. Needs `pip install anthropic` and ANTHROPIC_API_KEY.

The model fills the DealSpec schema by calling a strict `record_deal` tool and nothing
else: it does not see prices and never computes a total. Not run where this was built
(no API key), so there are no live-model results in reports/.
"""
from __future__ import annotations

import os

from .engine import DealSpec, load_book


def _nullable(schema: dict) -> dict:
    return {"anyOf": [schema, {"type": "null"}]}


PROPS = {
    "customer": _nullable({"type": "string"}),
    "product": _nullable({"type": "string", "enum": [
        "im_free", "im_professional", "platform_starter", "platform_essential",
        "platform_plus", "platform_ultimate", "platform"]}),
    "legacy_plan": _nullable({"type": "string", "enum": ["business", "enterprise", "operations_cloud"]}),
    "users": _nullable({"type": "integer"}),
    "stakeholders": {"type": "integer"},
    "billing": {"type": "string", "enum": ["annual", "monthly"]},
    "term_years": {"type": "integer"},
    "discount_pct": {"type": "number"},
    "payment_terms_days": {"type": "integer"},
    "price_lock": {"type": "boolean"},
    "close_date": _nullable({"type": "string"}),
    "events_year": _nullable({"type": "integer"}),
    "ai_actions_year": _nullable({"type": "integer"}),
    "addons": {"type": "array", "items": {"type": "string", "enum": [
        "aiops", "advance", "lcr_addon", "status_pages", "runbook_automation"]}},
    "unparsed": {"type": "array", "items": {"type": "string"}},
}
TOOL = {
    "name": "record_deal",
    "description": "Record the structured deal the rep described. Call this exactly once.",
    "strict": True,
    "input_schema": {"type": "object", "properties": PROPS, "required": list(PROPS), "additionalProperties": False},
}

SYSTEM = """You turn a sales rep's deal description into a structured deal record for a quoting system.
Always answer by calling the record_deal tool once. Extract only what the rep said.
- Defaults when not stated: stakeholders 0, billing annual, term_years 1, discount_pct 0, payment_terms_days 30,
  price_lock false, addons [], everything else null.
- product: 'platform' when the rep asks for the Reliability Platform without naming a tier; null when no plan is named.
  When a customer moves from an older plan (Business, Enterprise, Operations Cloud), set legacy_plan to the old plan
  and product to the new one.
- Never infer a seat count or a plan the rep did not give; leave it null and the quoting system will ask.
- Convert event and AI Action volumes to a yearly number (x12 for monthly).
- If the rep mentions a discount, volume, term, or other commercial term you cannot turn into a field, put a
  short description of it in unparsed instead of guessing.
- close_date is an ISO date; resolve a month and day to the next occurrence after {as_of}.
Plans in this price book: {names}."""


class ClaudeInterpreter:
    name = "claude"

    def __init__(self, model: str = "claude-opus-5-5", as_of: str = "2026-11-18"):
        import anthropic  # imported here so the offline path needs no packages
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model, self.as_of = model, as_of
        self.names = ", ".join(v["name"] for v in load_book()["products"].values())

    def _ask(self, prompt: str):
        # Opus 5.5 always thinks, and max_tokens covers thinking plus the tool call, so leave room.
        # Extraction is simple, so low effort keeps it fast.
        return self.client.messages.create(
            model=self.model, max_tokens=16000,
            output_config={"effort": "low"},
            system=SYSTEM.format(names=self.names, as_of=self.as_of),
            tools=[TOOL],
            messages=[{"role": "user", "content": prompt}],
        )

    def __call__(self, prompt: str) -> DealSpec:
        for _ in range(2):  # tool_choice is auto, so retry once if no deal record comes back
            msg = self._ask(prompt)
            if msg.stop_reason in ("max_tokens", "refusal"):  # fail closed and say why
                return DealSpec(unparsed=[f"the whole request (the model stopped with '{msg.stop_reason}')"])
            block = next((b for b in msg.content if b.type == "tool_use" and b.name == "record_deal"), None)
            if block is not None:
                return DealSpec.from_dict(dict(block.input))
        # fail closed: an empty record makes the quote ask for everything
        return DealSpec(unparsed=["the whole request (the model did not return a deal record)"])

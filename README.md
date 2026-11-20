# Prompt to quote on PagerDuty's public price book

A small working version of a pilot plan I wrote (a separate PDF, not in this repo): a rep describes a deal in plain English, and the pipeline returns a priced quote, the approvals it needs, and anything it cannot price, using only PagerDuty's public price book (amounts as of November 3, 2026, the day the PD Reliability Platform became generally available) and an example approval policy.

All prices come from pagerduty.com/pricing. The approval policy is an example, because PagerDuty's real discount rules are not public, and every customer name is invented. Nothing here comes from PagerDuty's or Roadrunner's systems.

**Try it in your browser:** https://pg2342-hub.github.io/prompt-to-quote/ (runs the rules interpreter and the engine in the page with Pyodide; nothing is sent anywhere).

## Run it

```
python3 quote.py "Essential for Kite Data, 20 users, about 40,000 events a year, annual."
python3 run_eval.py                      # 30 test deals, end to end
python3 run_eval.py --interpreter gold   # pricing engine alone, on the hand-written deal records
python3 run_eval.py --baseline           # list price times quantity, nothing else
python3 price_change.py                  # which test quotes change between the pricing page before and at launch
python3 check_fail_closed.py             # 25 review phrasings that must ask the rep or quote correctly
```

Python 3.9+ and the standard library only. Reports go to `reports/`.

Example output:

```
Quote for Kite Data  |  status: NEEDS_APPROVAL
  PD Reliability Platform Essential platform fee (annual, upfront): 1 x $12,000 per year -> $12,000/yr   [price_book 2026-11-03: platform_essential.platform_fee_year]
  Year 1 total: $12,000.00   Contract (1 yr): $12,000.00
  Credits: 15,000 events a year above the 25,000 included (rate set by deal desk)
  [route] CREDITS_NEEDED: Extra usage is bought with credits, and PagerDuty does not publish a price per credit; deal desk sets the rate.
  Approvers: deal_desk   Auto-approve eligible after pilot month 1: no
```

The same deal fit inside Essential's allowance on the pricing page before launch (40,000 events); at launch the allowance became 25,000.

## How it works

1. **Interpret.** The rep's words become a deal record (plan, any older plan the customer is moving from, users, stakeholders, billing, term, discount, payment terms, close date, events, AI Actions, add-ons). This step only extracts fields. It never sees prices and never does arithmetic. A seat count or plan the rep did not give stays empty, and a commercial term the interpreter cannot read (for example "some discount TBD") is recorded as unread, so the quote asks the rep instead of going out without it.
2. **Price.** `quoter/engine.py` prices the record from `data/price_book.json`. Every dollar line cites the price-book entry it came from. Anything the book does not price (Ultimate, renewals of the older Business and Enterprise plans, AIOps, credits, which PagerDuty sells at an unpublished rate, and how many extra AI Actions the launch promotion includes) comes back as a flag for deal desk, never as a guessed number.
3. **Check.** The same engine applies the price book's own rules (Starter's 30-seat cap, stakeholders counting as seats, annual-upfront billing for the platform, the limited-time bonus seats, the AI Actions promotion for deals signed by January 15, 2027) and the example approval policy (discount bands, payment terms, price locks).
4. **Route.** The quote gets a status (ready, needs approval, blocked, or needs info), its approvers, and whether it could auto-approve once the pilot's first month is over. Only quotes at 10% off or less whose only other flags are informational qualify; a tier the engine chose itself, a cheaper path with credits, or anything sent to deal desk keeps a person in the loop.

There are two interpreters with the same output. `RulesInterpreter` runs offline and was written with the test prompts in view, so its score shows the pipeline works end to end, not that it handles any wording. `ClaudeInterpreter` has a model fill the same record by calling a strict `record_deal` tool (schema-checked arguments, no prices in its context); install `anthropic`, set `ANTHROPIC_API_KEY`, and run `python3 run_eval.py --interpreter claude --runs 3`. It has not been run (no API key where this was built), so there are no live-model results here.

## The test set

`data/cases.json` holds 30 deals, each with the rep's prompt, the deal record a correct interpreter would produce, and the expected quote. Expected outcomes were worked out by hand from the price book and the policy.

| Tier | Cases | What it covers |
|---|---|---|
| T1 clean quote | 7 | Professional annual and monthly, named platform tiers, a two-year term, the engine choosing a tier |
| T2 approvals and terms | 6 | Each discount band, net 45 and net 60, a three-year price lock |
| T3 price-book trap | 10 | Starter seat cap, monthly billing on the platform, events and AI Actions above the allowance, the promotion before and after its deadline, Ultimate, a Business renewal, Free above 5 users, an unpriced add-on, reliance on bonus seats |
| T4 missing input | 2 | No seat count, no plan |
| T5 other wording | 5 | Added after an independent review typed its own deals: "discount of 15%", "1.5M events", a move from Business to Essential, Starter beyond its bonus seats, and a discount with no number |

A case passes when the status, plan, year 1 and contract totals, credit quantities, approvers, flags, and auto-approve call all match. A critical error is a quote that would auto-approve when it should not, or a wrong year 1 total on a quote that is not blocked. The go-live gate is at least 29 of 30 on every run with zero critical errors.

## Results

| Pipeline | Cases passed | Critical errors | Gate |
|---|---|---|---|
| Rules interpreter + engine | 30 of 30 | 0 | Pass |
| Engine alone (hand-written records) | 30 of 30 | 0 | Pass |
| List price times quantity | 3 of 30 | 25 | Fail |

The list-price row is a floor, not a competitor: it has no approval routing at all, so most of its misses are missing approvals and flags rather than wrong prices. It is there to show that 27 of the 30 cases test something beyond multiplication.

## When the price book changes

The PD Reliability Platform became generally available on November 3, 2026, and the allowances on PagerDuty's pricing page changed at launch: Starter went from 10 seats to 5 plus 5 limited-time bonus seats, Essential from 20 to 25 seats and from 40,000 to 25,000 events, and the AI Actions promotion was added. `price_change.py` re-quotes every test deal under the pricing page before launch and at launch, and lists the 7 that change. The pre-launch book in `data/price_book_pre_launch.json` is reconstructed from a third-party pricing tracker's captures, as described in the file. The tracker's change log also says Starter gained a 30-seat cap in this change, but its diff page does not list it; this book keeps the cap, so case 14 is not counted as a change (without the cap, 8 of 30 change).

## Limits

- 30 hand-written deals is a test set for one price book, not a benchmark. A real version would be built from the customer's own recent quotes and reviewed with their deal desk.
- The approval policy is an example. A pilot replaces `data/approval_policy.json` with the customer's real rules in week 1.
- The rules interpreter covers the phrasings in the test set and asks the rep when it sees a discount, usage, payment, or term word it cannot read; it is a regex, not a language model, so unusual phrasings can still be misread. The Claude interpreter is the intended path. `python3 check_fail_closed.py` runs 25 phrasings that two independent reviews typed after the test set was built; the interpreter was fixed against them, so they are a regression check, not a held-out score. On 15 fresh deals a reviewer wrote without seeing the parser, it priced 5 correctly and asked the rep on the other 10, with no wrong quotes.
- The engine picks the smallest tier that covers the deal without credits. Because credit rates are not public, it can only point out a cheaper path with credits, not price it.
- Whether event allowances are counted per year comes from a third-party guide, not PagerDuty's page.
- The engine does not write the quote back to a CRM or generate an order form.

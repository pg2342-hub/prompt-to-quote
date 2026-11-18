# Writes data/cases.json. Expected outcomes were worked out by hand from the price book and the example policy.
import json
C = []
def case(tier, prompt, spec, status, product, year1, approvers, flags, auto=None):
    C.append({"id": len(C)+1, "tier": tier, "prompt": prompt, "gold_spec": spec,
              "expected": {"status": status, "product": product, "year1_total": year1,
                           "approvers": approvers, "flags": flags, "auto_approve_eligible": auto}})
T1, T2, T3, T4 = "T1 clean quote", "T2 approvals and terms", "T3 price-book trap", "T4 missing input"
T5 = "T5 other wording (added after review)"
case(T1, "Quote Northwind Freight 40 Professional users, annual billing, list price.",
     {"product": "im_professional", "users": 40}, "ready", "im_professional", 10080, [], [], True)
case(T1, "Brightline Health wants Professional for 12 users, billed monthly.",
     {"product": "im_professional", "users": 12, "billing": "monthly"}, "ready", "im_professional", 3600, [], [], True)
case(T1, "Move Beacon Retail onto the Reliability Platform: 22 responders and 6 stakeholders, about 18,000 events a year, 8% off, closing Dec 12.",
     {"product": "platform", "users": 22, "stakeholders": 6, "events_year": 18000, "discount_pct": 8, "close_date": "2026-12-12"}, "needs_approval", "platform_plus", 44160, ["sales_manager"], ["TIER_RECOMMENDED", "ALTERNATIVE_TIER", "DISCOUNT"], False)
case(T1, "Kestrel Payments: Plus, 44 users, 90k events a year, close Dec 19, 2 year term at list.",
     {"product": "platform_plus", "users": 44, "events_year": 90000, "term_years": 2, "close_date": "2026-12-19"}, "ready", "platform_plus", 48000, [], [], True)
case(T1, "Reliability Platform for Pinecrest Apps, 14 users, about 3,000 events a year, annual.",
     {"product": "platform", "users": 14, "events_year": 3000}, "ready", "platform_essential", 12000, [], ["TIER_RECOMMENDED", "ALTERNATIVE_TIER"], False)
case(T1, "Orbit Mobility, Professional, 75 users, annual, 5% off.",
     {"product": "im_professional", "users": 75, "discount_pct": 5}, "needs_approval", "im_professional", 17955, ["sales_manager"], ["DISCOUNT"], True)
case(T1, "Quote the Reliability Platform for Lumen Analytics: 30 responders plus 10 stakeholders, around 60,000 events a year, annual, close Dec 15.",
     {"product": "platform", "users": 30, "stakeholders": 10, "events_year": 60000, "close_date": "2026-12-15"}, "ready", "platform_plus", 48000, [], ["TIER_RECOMMENDED"], False)
case(T2, "Halcyon Bank: Plus, 50 users, annual, 18% discount, close Dec 22.",
     {"product": "platform_plus", "users": 50, "discount_pct": 18, "close_date": "2026-12-22"}, "needs_approval", "platform_plus", 39360, ["sales_manager", "deal_desk"], ["DISCOUNT"], False)
case(T2, "Granite Retail, Essential for 20 users, 25% off, net 60, closing Jan 9.",
     {"product": "platform_essential", "users": 20, "discount_pct": 25, "payment_terms_days": 60, "close_date": "2027-01-09"}, "needs_approval", "platform_essential", 9000, ["sales_manager", "deal_desk", "finance"], ["DISCOUNT", "PAYMENT_TERMS"], False)
case(T2, "Professional for 200 users at Vantage Media, annual, 35% off for a 3 year deal with price locked.",
     {"product": "im_professional", "users": 200, "discount_pct": 35, "term_years": 3, "price_lock": True}, "needs_approval", "im_professional", 32760, ["sales_manager", "deal_desk", "finance", "cro"], ["DISCOUNT", "PRICE_LOCK"], False)
case(T2, "Corvid Security: Essential, 10 users, 10% discount, annual.",
     {"product": "platform_essential", "users": 10, "discount_pct": 10}, "needs_approval", "platform_essential", 10800, ["sales_manager"], ["DISCOUNT"], True)
case(T2, "Meridian Foods Professional 30 users annual net 45.",
     {"product": "im_professional", "users": 30, "payment_terms_days": 45}, "needs_approval", "im_professional", 7560, ["finance"], ["PAYMENT_TERMS"], False)
case(T2, "Atlas Robotics Essential 25 seats annual 10.5% discount.",
     {"product": "platform_essential", "users": 25, "discount_pct": 10.5}, "needs_approval", "platform_essential", 10740, ["sales_manager", "deal_desk"], ["DISCOUNT"], False)
case(T3, "Starter for Ridgeway Logistics, 26 responders and 8 stakeholders.",
     {"product": "platform_starter", "users": 26, "stakeholders": 8}, "blocked", "platform_starter", 2800, [], ["SEAT_CAP"], False)
case(T3, "Essential for Quill Software, 15 users, billed monthly.",
     {"product": "platform_essential", "users": 15, "billing": "monthly"}, "blocked", "platform_essential", 12000, [], ["PLATFORM_MONTHLY"], False)
case(T3, "Plus for Harbor Insurance, 40 users, 30,000 AI Actions a year, closing Feb 3, 2027.",
     {"product": "platform_plus", "users": 40, "ai_actions_year": 30000, "close_date": "2027-02-03"}, "needs_approval", "platform_plus", 48000, ["deal_desk"], ["PROMO_EXPIRED", "CREDITS_NEEDED"], False)
case(T3, "Plus for Cobalt Energy, 40 users, 30,000 AI Actions a year, closing Dec 30.",
     {"product": "platform_plus", "users": 40, "ai_actions_year": 30000, "close_date": "2026-12-30"}, "needs_approval", "platform_plus", 48000, ["deal_desk"], ["PROMO_APPLIED"], False)
case(T3, "Essential for Kite Data, 20 users, about 40,000 events a year, annual.",
     {"product": "platform_essential", "users": 20, "events_year": 40000}, "needs_approval", "platform_essential", 12000, ["deal_desk"], ["CREDITS_NEEDED"], False)
case(T3, "Ultimate for Sterling Telecom, 600 users.",
     {"product": "platform_ultimate", "users": 600}, "needs_approval", "platform_ultimate", None, ["deal_desk"], ["CUSTOM_TIER", "CREDITS_NEEDED"], False)
case(T3, "Renew Wexford Media on their Business plan, 60 users.",
     {"legacy_plan": "business", "users": 60}, "needs_approval", None, None, ["deal_desk"], ["LEGACY_PLAN"], False)
case(T3, "Free plan for Juniper Co, 8 users.",
     {"product": "im_free", "users": 8}, "blocked", "im_free", None, [], ["FREE_OVER_LIMIT"], False)
case(T3, "Professional for 25 users at Alder Systems, annual, plus AIOps.",
     {"product": "im_professional", "users": 25, "addons": ["aiops"]}, "needs_approval", "im_professional", 6300, ["deal_desk"], ["UNPRICED_SKU"], False)
case(T3, "Starter for Fennel Health, 8 responders, annual.",
     {"product": "platform_starter", "users": 8}, "needs_approval", "platform_starter", 2800, ["deal_desk"], ["BONUS_SEATS_RELIED"], False)
case(T4, "Put together a quote for Larkspur AI on Professional, annual.",
     {"product": "im_professional"}, "needs_info", "im_professional", None, [], ["MISSING_SEATS"], False)
case(T4, "Quote Osprey Cloud 30 users, 10% off.",
     {"users": 30, "discount_pct": 10}, "needs_info", None, None, ["sales_manager"], ["MISSING_PRODUCT", "DISCOUNT"], False)
case(T5, "Essential for Foo Corp, 20 users, discount of 15%",
     {"product": "platform_essential", "users": 20, "discount_pct": 15}, "needs_approval", "platform_essential", 10200, ["sales_manager", "deal_desk"], ["DISCOUNT"], False)
case(T5, "Plus for Big Co, 45 users, 1.5M events a year",
     {"product": "platform_plus", "users": 45, "events_year": 1500000}, "needs_approval", "platform_plus", 48000, ["deal_desk"], ["CREDITS_NEEDED"], False)
case(T5, "Renewal: move Delta Freight from Business to Essential, 22 users, closing Dec 18",
     {"product": "platform_essential", "legacy_plan": "business", "users": 22, "close_date": "2026-12-18"}, "needs_approval", "platform_essential", 12000, ["deal_desk"], ["LEGACY_MIGRATION"], False)
case(T5, "Starter for Qux Media, 12 users",
     {"product": "platform_starter", "users": 12}, "needs_approval", "platform_starter", 2800, ["deal_desk"], ["BONUS_SEATS_RELIED", "CREDITS_NEEDED"], False)
case(T5, "Plus for Baz Health, 40 users, some discount TBD",
     {"product": "platform_plus", "users": 40, "unparsed": ["a discount"]}, "needs_info", "platform_plus", None, [], ["UNPARSED"], False)
# contract totals and credit quantities, by case id (None = credits needed, quantity set by deal desk)
EXTRA = {1: (10080, []), 2: (3600, []), 3: (44160, []), 4: (96000, []), 5: (12000, []), 6: (17955, []), 7: (48000, []),
         8: (39360, []), 9: (9000, []), 10: (98280, []), 11: (10800, []), 12: (7560, []), 13: (10740, []),
         14: (None, []), 15: (None, []), 16: (48000, [None]), 17: (48000, []), 18: (12000, [None]), 19: (None, [None]),
         20: (None, []), 21: (None, []), 22: (6300, []), 23: (2800, []), 24: (None, []), 25: (None, []),
         26: (10200, []), 27: (48000, [None]), 28: (12000, []), 29: (2800, [80]), 30: (None, [])}
for c in C:
    c["expected"]["contract_total"], c["expected"]["credits"] = EXTRA[c["id"]]
assert len(C) == 30, len(C)
json.dump({"as_of": "2026-11-18", "cases": C}, open("data/cases.json", "w"), indent=1)
print(len(C), "cases")

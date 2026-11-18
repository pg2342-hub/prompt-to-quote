# Eval report: baseline (1 run)

Cases passed on every run: 3 of 30
Cases with a critical error: 25
Gate (29 of 30, zero critical): FAIL

| Tier | Passed |
|---|---|
| T1 clean quote | 3 of 7 |
| T2 approvals and terms | 0 of 6 |
| T3 price-book trap | 0 of 10 |
| T4 missing input | 0 of 2 |
| T5 other wording (added after review) | 0 of 5 |

| Case | Result | Notes |
|---|---|---|
| 1 | pass |  |
| 2 | pass |  |
| 3 | CRITICAL | status: got 'ready', expected 'needs_approval'; product: got 'platform_essential', expected 'platform_plus'; approvers: got [], expected ['sales_manager']; auto_approve_eligible: got True, expected False; flags: got [], expected ['ALTERNATIVE_TIER', 'DISCOUNT', 'TIER_RECOMMENDED']; year1_total: got 11040.0, expected 44160; contract_total: got 11040.0, expected 44160 |
| 4 | pass |  |
| 5 | CRITICAL | auto_approve_eligible: got True, expected False; flags: got [], expected ['ALTERNATIVE_TIER', 'TIER_RECOMMENDED'] |
| 6 | fail | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['sales_manager']; flags: got [], expected ['DISCOUNT'] |
| 7 | CRITICAL | product: got 'platform_essential', expected 'platform_plus'; auto_approve_eligible: got True, expected False; flags: got [], expected ['TIER_RECOMMENDED']; year1_total: got 12000.0, expected 48000; contract_total: got 12000.0, expected 48000 |
| 8 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['sales_manager', 'deal_desk']; auto_approve_eligible: got True, expected False; flags: got [], expected ['DISCOUNT'] |
| 9 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['sales_manager', 'deal_desk', 'finance']; auto_approve_eligible: got True, expected False; flags: got [], expected ['DISCOUNT', 'PAYMENT_TERMS'] |
| 10 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['sales_manager', 'deal_desk', 'finance', 'cro']; auto_approve_eligible: got True, expected False; flags: got [], expected ['DISCOUNT', 'PRICE_LOCK'] |
| 11 | fail | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['sales_manager']; flags: got [], expected ['DISCOUNT'] |
| 12 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['finance']; auto_approve_eligible: got True, expected False; flags: got [], expected ['PAYMENT_TERMS'] |
| 13 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['sales_manager', 'deal_desk']; auto_approve_eligible: got True, expected False; flags: got [], expected ['DISCOUNT'] |
| 14 | CRITICAL | status: got 'ready', expected 'blocked'; auto_approve_eligible: got True, expected False; flags: got [], expected ['SEAT_CAP'] |
| 15 | CRITICAL | status: got 'ready', expected 'blocked'; auto_approve_eligible: got True, expected False; flags: got [], expected ['PLATFORM_MONTHLY'] |
| 16 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['deal_desk']; auto_approve_eligible: got True, expected False; flags: got [], expected ['CREDITS_NEEDED', 'PROMO_EXPIRED']; credits: got [], expected [None] |
| 17 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['deal_desk']; auto_approve_eligible: got True, expected False; flags: got [], expected ['PROMO_APPLIED'] |
| 18 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['deal_desk']; auto_approve_eligible: got True, expected False; flags: got [], expected ['CREDITS_NEEDED']; credits: got [], expected [None] |
| 19 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['deal_desk']; auto_approve_eligible: got True, expected False; flags: got [], expected ['CREDITS_NEEDED', 'CUSTOM_TIER']; credits: got [], expected [None] |
| 20 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['deal_desk']; auto_approve_eligible: got True, expected False; flags: got [], expected ['LEGACY_PLAN'] |
| 21 | CRITICAL | status: got 'ready', expected 'blocked'; auto_approve_eligible: got True, expected False; flags: got [], expected ['FREE_OVER_LIMIT'] |
| 22 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['deal_desk']; auto_approve_eligible: got True, expected False; flags: got [], expected ['UNPRICED_SKU'] |
| 23 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['deal_desk']; auto_approve_eligible: got True, expected False; flags: got [], expected ['BONUS_SEATS_RELIED'] |
| 24 | CRITICAL | status: got 'ready', expected 'needs_info'; auto_approve_eligible: got True, expected False; flags: got [], expected ['MISSING_SEATS'] |
| 25 | CRITICAL | status: got 'ready', expected 'needs_info'; approvers: got [], expected ['sales_manager']; auto_approve_eligible: got True, expected False; flags: got [], expected ['DISCOUNT', 'MISSING_PRODUCT'] |
| 26 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['sales_manager', 'deal_desk']; auto_approve_eligible: got True, expected False; flags: got [], expected ['DISCOUNT'] |
| 27 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['deal_desk']; auto_approve_eligible: got True, expected False; flags: got [], expected ['CREDITS_NEEDED']; credits: got [], expected [None] |
| 28 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['deal_desk']; auto_approve_eligible: got True, expected False; flags: got [], expected ['LEGACY_MIGRATION'] |
| 29 | CRITICAL | status: got 'ready', expected 'needs_approval'; approvers: got [], expected ['deal_desk']; auto_approve_eligible: got True, expected False; flags: got [], expected ['BONUS_SEATS_RELIED', 'CREDITS_NEEDED']; credits: got [], expected [80] |
| 30 | CRITICAL | status: got 'ready', expected 'needs_info'; auto_approve_eligible: got True, expected False; flags: got [], expected ['UNPARSED'] |

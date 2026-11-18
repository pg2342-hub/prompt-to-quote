# Price-book change: pre-launch (2026-11-02 capture) -> 2026-11-03

7 of 30 test quotes change.

| Case | Deal | What changes |
|---|---|---|
| 13 | Atlas Robotics Essential 25 seats annual 10.5% discount. | flags: ['CREDITS_NEEDED', 'DISCOUNT'] -> ['DISCOUNT']; credits: ['5 seats above the 20 included'] -> [] |
| 16 | Plus for Harbor Insurance, 40 users, 30,000 AI Actions a year, closing Feb 3, 2027. | flags: ['CREDITS_NEEDED'] -> ['CREDITS_NEEDED', 'PROMO_EXPIRED'] |
| 17 | Plus for Cobalt Energy, 40 users, 30,000 AI Actions a year, closing Dec 30. | flags: ['CREDITS_NEEDED'] -> ['PROMO_APPLIED']; credits: ['14,000 AI Actions a year above the 16,000 included'] -> [] |
| 18 | Essential for Kite Data, 20 users, about 40,000 events a year, annual. | status: ready -> needs_approval; approvers: [] -> ['deal_desk']; flags: [] -> ['CREDITS_NEEDED']; credits: [] -> ['15,000 events a year above the 25,000 included'] |
| 23 | Starter for Fennel Health, 8 responders, annual. | status: ready -> needs_approval; approvers: [] -> ['deal_desk']; flags: [] -> ['BONUS_SEATS_RELIED'] |
| 28 | Renewal: move Delta Freight from Business to Essential, 22 users, closing Dec 18 | flags: ['CREDITS_NEEDED', 'LEGACY_MIGRATION'] -> ['LEGACY_MIGRATION']; credits: ['2 seats above the 20 included'] -> [] |
| 29 | Starter for Qux Media, 12 users | flags: ['CREDITS_NEEDED'] -> ['BONUS_SEATS_RELIED', 'CREDITS_NEEDED'] |

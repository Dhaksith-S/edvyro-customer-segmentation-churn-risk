# Scoring specification v1.0

This deterministic index measures the weight of specified prioritization indicators. It is **not a churn probability, trained machine-learning model, or causal estimate**. No weights or thresholds were optimized against labels. Rules were formulated after viewing the source and its obvious cohort structure; retrospective results are in-sample and are not independent validation.

| signal | feature | condition | maximum | reason | eligibility | missing_treatment |
| --- | --- | --- | --- | --- | --- | --- |
| Tenure | TenureMonths | 0 <= months < 6: 35; 6 <= months <= 12: 25; 12 < months <= 24: 10; >24: 0 | 35 | Early lifecycle needs onboarding; fixed planning assumption | All three core inputs valid; otherwise no score | Null score; Unscored; data review |
| Commitment | ContractType | Month-to-Month: 45; One Year: 20; Two Year: 0 | 45 | Shorter commitment permits an easier exit; association not causation | All three core inputs valid; otherwise no score | Null score; Unscored; data review |
| Charge exposure | MonthlyCharges | INR >=100: 20; 70 <= INR <100: 10; 0 <= INR <70: 0 | 20 | Absolute bill exposure may warrant a value review; affordability is unknown | All three core inputs valid; otherwise no score | Null score; Unscored; data review |

`RiskScore = TenurePoints + ContractPoints + ChargePoints`, with theoretical range 0-100. Eligibility requires nonnegative integer tenure, a known contract, and finite nonnegative monthly charges. There is no special missing-value discount; incomplete customers receive `Unscored`, with an explicit explanation. High valid charges are not capped as data errors.

Bands: **Low 0-29, Medium 30-59, High 60-100**. These are fixed planning cutoffs: 30 reflects moderate indicator accumulation; 60 requires multiple material contributions or flexible commitment plus another signal. They do not come from capacity analysis, expected loss, or probability calibration. Not every integer total is attainable because points are discrete.

Contract receives the greatest maximum weight (45) as an assumption about ease of exit; tenure receives 35 as an onboarding/lifecycle assumption; charge exposure receives 20 as a modest value-review indicator. INR 70 and 100 split this file's three price levels (49.99, 79.99, 149.99). These are dataset-specific fixed thresholds, not statistical quantiles or validated affordability cutoffs. Charges partly proxy subscription tier; tenure and contract are correlated, so indicators may double-count related account characteristics.

Tenure bands: 0-5, 6-12, 13-24, and 25+ completed months. Six months marks early onboarding, 12 months a first-year review, and 24 months a longer relationship. These are business heuristics, not discovered natural clusters. Spending bands share the score's charge cutoffs. Primary segments use contract, then a first-year split for flexible accounts; every retained record receives exactly one primary segment (including Data review when necessary).

Payment method is descriptive because no failure/friction evidence supports penalizing a method. Support tickets are a real observed behavior, used for service-review analysis, but their timing relative to churn is unverifiable. Age, gender, identifiers, churn, and total charges never enter the score. `Churned` is used only after scoring. Before prospective deployment, verify point-in-time availability for every input.

Observed score range: 20-80. In this sample, risk bands reproduce the contract cohorts exactly: high = monthly contracts, medium = one-year, low = two-year. The rule index provides no demonstrated outcome separation beyond contract alone. No holdout/temporal experiment is claimed, and ROC-AUC is omitted because n=15 and complete contract/outcome confounding would make a single impressive number misleading. Unit tests validate software and edge cases, not business predictive utility.

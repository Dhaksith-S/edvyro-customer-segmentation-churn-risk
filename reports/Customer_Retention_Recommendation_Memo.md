# Customer Retention Recommendation Memo

**To:** Subscription Customer Success and Retention Team (fictional training scenario)  
**From:** Dhaksith-S | EdVyro Data Analytics Internship, Task 4  
**Date:** 28 October 2026  
**Decision:** Prioritize a service/onboarding investigation; validate prospectively before deploying a retention queue.

## Executive summary

The 15-record synthetic sample contains 7 churned customers (46.67%) and 8 retained customers. All seven monthly-contract records are churned; none of the eight longer-contract records is churned. Six of the seven monthly customers are in their first year. Their service histories warrant investigation, but the data do not prove that contract flexibility or support demand caused churn.

The fixed 0-100 index places 7 customers in High, four in Medium, and four in Low. High-band recorded monthly charges total INR 409.93; **all seven are already labelled churned**, so there are **0 retained high-band accounts** available for retention outreach in this file. These charges are historical exposure, not currently recoverable monthly recurring revenue. Retained accounts' recorded monthly charges total INR 859.92; neither amount is a forecast of revenue saved.

## Business objective

Give a fictional subscription team an auditable way to describe customer cohorts, investigate service experience, and design a future prioritization pilot. This sample supports a learning demonstration and hypotheses, not a production churn forecast or a claim of retention lift.

## Data and methodology

The supplied EdVyro CSV has 15 unique synthetic accounts and 11 source fields. The source guide defines charges in INR and support tickets over the previous 90 days. No missing values, duplicates, invalid values, or billing-identity discrepancies were observed. Every record is retained; hashed synthetic IDs replace raw IDs in public exports. Actual CSV contract categories override the generic source guide's examples.

Primary segments are mutually exclusive: flexible contracts in their first year (<=12 months), flexible contracts beyond their first year, one-year commitments, and two-year commitments. Tenure, spending, payment, and risk bands are separate analytical dimensions. Groups below five accounts are flagged as small samples.

The risk index sums tenure (0-35), commitment (0-45), and monthly-charge exposure (0-20). Low is 0-29, Medium 30-59, High 60-100. Points are fixed business assumptions, not fitted coefficients. Payment categories have no penalty; support counts are descriptive because their timing is uncertain. Churn, age, gender, total charges and identifiers are excluded. Missing core inputs yield no score rather than a reassuring zero.

## Key findings and priority segments

| Primary segment | Count | Share (%) | Churn (%) | Mean tenure (mo) | Mean index (pts) | Charges (INR/mo) |
| --- | --- | --- | --- | --- | --- | --- |
| Flexible - first year | 6 | 40.00 | 100.00 | 5.83 | 76.67 | 329.94 |
| Flexible - beyond first year | 1 | 6.67 | 100.00 | 14.00 | 65.00 | 79.99 |
| Annual commitment | 4 | 26.67 | 0.00 | 19.75 | 35.00 | 259.96 |
| Two-year commitment | 4 | 26.67 | 0.00 | 38.50 | 20.00 | 599.96 |

The six first-year flexible customers have a mean tenure of 5.83 months, 4.50 support tickets in the prior 90 days, and INR 329.94 in recorded monthly charges. The single flexible customer beyond the first year has tenure 14 months, three tickets, and INR 79.99 in monthly charges; one account cannot establish a population pattern.

The four one-year customers have no observed churn and average 1.50 tickets; the four two-year customers also have no observed churn and average 0.50 tickets. Zero observed churn in four records is weak evidence of low future risk. All four highest-price Enterprise customers are two-year customers and retained, so higher monthly charges are not demonstrated here to predict churn. The charge indicator remains an explicit unvalidated assumption.

## Recommended action matrix

| Priority | Audience | Observed issue | Intervention hypothesis | Rationale | KPI | Validation required |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Six first-year flexible records; future comparable active customers | 6/6 churned; mean 4.50 tickets | Review support themes and onboarding; pilot assisted onboarding in a new active cohort | Early lifecycle and service demand coincide with churn | 90-day churn; repeat-ticket rate; customer effort | Verify support timestamps; randomize active eligible customers to assistance or usual service |
| 2 | One flexible account beyond first year | 1/1 churned; three tickets | Qualitative exit/service review; consent-based win-back research if appropriate | Understand an individual case before generalizing | Interview completion; unresolved issue themes | No inferred effect from n=1; use a larger prospective cohort |
| 3 | Four one-year retained accounts | 0/4 churned; mean 1.50 tickets | Test a value and service review near a verified renewal date | Moderate index and a real retained cohort justify monitoring | Renewal rate; incremental retained margin | Collect renewal dates first; controlled outreach with holdout |
| 4 | Four two-year retained accounts | 0/4 churned; mean 0.50 tickets | Maintain service standards and feedback sampling | Avoid unnecessary discounting of apparently stable accounts | Service satisfaction; opt-outs; gross margin | Randomized light-touch feedback pilot; monitor cost |

Payment-method comparisons can inform interviews, but this file has no failed-payment or billing-friction evidence. Do not target UPI or debit-card customers solely because of their payment method. Contract extension and discounts require customer consent and a controlled test; no intervention is assumed effective.

## Measurement plan

First collect a dated account snapshot, outcome window, event timestamps, renewal dates, contact permissions, acquisition channel, service-resolution status, intervention cost, and margin. Verify that all score inputs precede the outcome; remove fields that fail this check. Exclude already-churned accounts from a retention queue and assess win-back separately.

On a larger set of eligible active customers, preregister the index and outreach rules before observing future labels. Randomize at customer level within contract and tenure strata to assistance versus usual service, preserving a no-contact holdout. Set a fixed 90-day outcome window and measure intention-to-treat churn difference, confidence intervals, support recurrence, complaint/opt-out rates, intervention cost, and incremental retained margin net of discounts. Estimate sample size from a defensible baseline and a business-relevant effect; neither is known here. Compare index prioritization with contract-only and random/capacity-matched baselines. Keep any future tuning separate from an untouched evaluation cohort. No lift, ROI, or forecast is estimated from this sample.

## Limitations

Fifteen synthetic accounts do not represent a sampled customer population. The label balance is 7/8; all monthly-contract labels are Yes and all longer contracts No, causing complete confounding. Risk bands exactly reproduce these contract cohorts and add no demonstrated outcome information beyond contract. Retrospective separation is not independent validation; rules were devised after source inspection, without label-based fitting. No temporal holdout is possible because timestamps and an exact outcome horizon are absent.

Tenure, contract and tier are correlated. Price is not affordability; total charges are mechanically redundant. Support counts may include events after churn and are excluded from scoring. Even core account snapshots need temporal checks before prospective use. No channel, usage, satisfaction, margin, contact consent or actual response data exists. Subgroups of one to four accounts are particularly unstable; 0% and 100% are descriptions, not reliable probabilities. The index is neither calibrated nor causal. Data rights for original materials are separate from this project's code license.

## Conclusion

Start with an onboarding and service investigation, then run a dated, controlled pilot on new active accounts. Monitor the eight retained accounts without equating a low index to guaranteed retention. Use the transparent rules as a testable starting point, and require prospective evidence before operational adoption.

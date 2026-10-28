# Data quality and provenance report

Generated from the supplied source, not hand-edited records. Analysis date: 28 October 2026.

## Inspection

The source contains **15 rows and 11 columns**, 0 exact duplicate rows and 0 duplicate IDs. All 15 IDs are present. Missing source cells: 0. The original file is unchanged; its SHA-256 is `1d5048cad41e8abbefd5fab04cc7dd6579234a292a8f59f85d7d072f37fabdce`.

| Column | Inferred dtype | Missing |
| --- | --- | --- |
| CustomerID | object | 0 |
| Gender | object | 0 |
| Age | int64 | 0 |
| TenureMonths | int64 | 0 |
| SubscriptionType | object | 0 |
| MonthlyCharges | float64 | 0 |
| TotalCharges | float64 | 0 |
| ContractType | object | 0 |
| SupportTickets | int64 | 0 |
| PaymentMethod | object | 0 |
| Churn | object | 0 |

## Numeric validity

| Field | min | max |
| --- | --- | --- |
| Age | 23.00 | 60.00 |
| TenureMonths | 2.00 | 48.00 |
| MonthlyCharges | 49.99 | 149.99 |
| TotalCharges | 99.98 | 7199.52 |
| SupportTickets | 0.00 | 6.00 |

No observed negative, non-finite, fractional count, or implausible age values. Every `TotalCharges` equals `TenureMonths * MonthlyCharges` within INR 0.01 (0 mismatches). This identity suggests a simplified billing construction; total charges add no independent behavior and are excluded from scoring. No extreme values were deleted, capped, or winsorized. Fifteen records are insufficient to distinguish rare valid values from anomalies reliably.

## Categories and balance

| Field | Value | Customers |
| --- | --- | --- |
| Gender | Female | 8 |
| Gender | Male | 7 |
| SubscriptionType | Basic | 7 |
| SubscriptionType | Pro | 4 |
| SubscriptionType | Enterprise | 4 |
| ContractType | Month-to-Month | 7 |
| ContractType | One Year | 4 |
| ContractType | Two Year | 4 |
| PaymentMethod | Credit Card | 6 |
| PaymentMethod | UPI | 4 |
| PaymentMethod | Bank Transfer | 3 |
| PaymentMethod | Debit Card | 2 |
| Churn | No | 8 |
| Churn | Yes | 7 |

The outcome has 7 churned (46.67%) and 8 retained (53.33%) records. This is only mild class imbalance, with substantial uncertainty due to sample size. No undocumented category spelling variants were observed. Representative de-identified records are in `outputs/customer_segments.csv` and the notebook.

## Implemented cleaning decisions

1. Require all 11 source columns; fail visibly if the schema is incomplete.
2. Trim identifiers and text; normalize recognized category case to the actual CSV vocabulary. Unknown values become null and are logged, never guessed. Blank strings become null.
3. Parse numeric fields; replace negative, missing, infinite, nonnumeric values, fractional month/ticket/age counts, and ages above 120 with null. High positive charges are retained because no business maximum is documented.
4. Exclude missing identifiers. Remove exact duplicates after normalization. Exclude **all** conflicting rows for the same ID because no timestamp establishes the latest record. Log source row numbers and actions without publishing original IDs.
5. Never impute tenure, contract, or charges. Incomplete accounts remain in the customer table, with null score and `Unscored` band. Missing tenure/contract gives the primary segment `Data review`. Other missing fields do not alter the score. Missing labels do not prevent scoring but are excluded from churn-rate denominators.
6. Hash synthetic identifiers with SHA-256 (12 hex characters, prefixed `SYN-`); omit raw identifiers, age, gender, total charges, and charge-difference diagnostics from public customer exports. This is pseudonymization, not a promise of anonymization for real data.
7. Record every cleaning event in `outputs/cleaning_log.csv`; this source produced **0 events** and **15 retained/scored/labelled customers**. No source values needed correction and no customers were removed.

## Source interpretation and publication

The supplied Task 1 Markdown calls the records synthetic. Page 3 of the supplied 11-page source library defines tenure in completed months, amounts in INR, support counts over the previous 90 days, and churn during an observation period. Its generic field names and contract examples conflict with this file; actual CSV names and categories take precedence. The user's Task 4 brief takes precedence over the Task 1 Markdown.

No observation date, churn date, support event date, payment-failure field, usage log, satisfaction score, acquisition date, gross margin, or intervention outcome exists. Timing of support tickets and account snapshots relative to churn cannot be verified. Support is therefore descriptive only. Even tenure, contract and charges require a verified pre-outcome snapshot before prospective use. The PDF's print date is not a customer observation date.

No explicit dataset redistribution license was found in the supplied references. Original source documents and CSV remain local and Git-ignored. Public analysis uses selected factual outputs and attributes the source; MIT does not cover EdVyro material. See `data/README.md` for retrieval and rights. No unrelated internship projects were edited.

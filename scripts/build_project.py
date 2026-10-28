"""Generate analytical documentation, notebook, and a typeset memo from actual results."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import json
import html
import re
import nbformat as nbf
import pandas as pd
from src.pipeline import run_pipeline
from src.segmentation import SEGMENTS,summarize
from src.scoring import RULES

def write(path, text):
    p=ROOT/path; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text.strip()+'\n',encoding='utf-8')

def mdtable(frame):
    # No tabulate dependency; preserve numeric precision appropriate for presentation.
    cols=list(frame.columns)
    rows=['| '+' | '.join(cols)+' |','| '+' | '.join(['---']*len(cols))+' |']
    for row in frame.itertuples(index=False,name=None):
        rows.append('| '+' | '.join('NA' if pd.isna(v) else f'{v:.2f}' if isinstance(v,float) else str(v) for v in row)+' |')
    return '\n'.join(rows)

def document(df,profile,log):
    n=len(df); churn=int(df.Churned.sum()); charge=df.MonthlyCharges.sum()
    high=df[df.RiskBand.eq('High')]; retained=df[df.Churned.eq(0)]; active_high=high[high.Churned.eq(0)]
    seg=summarize(df); bands=summarize(df,'RiskBand')
    facts={'customers':n,'churned':churn,'churn_pct':100*churn/n,'monthly_charge_sum_inr':round(charge,2),
           'high_risk_customers':len(high),'high_risk_charge_sum_inr':round(high.MonthlyCharges.sum(),2),
           'retained_high_risk_customers':len(active_high),'retained_monthly_charge_sum_inr':round(retained.MonthlyCharges.sum(),2),
           'mean_tenure_months':df.TenureMonths.mean(),'score_min':int(df.RiskScore.min()),'score_max':int(df.RiskScore.max())}
    write('outputs/key_findings.json',json.dumps(facts,indent=2))
    ranges=pd.DataFrame(profile['numeric']).T.reset_index().rename(columns={'index':'Field'})
    quality=f'''# Data quality and provenance report

Generated from the supplied source, not hand-edited records. Analysis date: 28 October 2026.

## Inspection

The source contains **{n} rows and {profile['columns']} columns**, {profile['exact_duplicate_rows']} exact duplicate rows and {profile['duplicate_customer_ids']} duplicate IDs. All {n} IDs are present. Missing source cells: {sum(profile['missing'].values())}. The original file is unchanged; its SHA-256 is `{profile['source_sha256']}`.

{mdtable(pd.DataFrame({'Column':list(profile['dtypes']),'Inferred dtype':list(profile['dtypes'].values()),'Missing':[profile['missing'][c] for c in profile['dtypes']]}))}

## Numeric validity

{mdtable(ranges)}

No observed negative, non-finite, fractional count, or implausible age values. Every `TotalCharges` equals `TenureMonths * MonthlyCharges` within INR 0.01 ({profile['charge_identity_mismatches']} mismatches). This identity suggests a simplified billing construction; total charges add no independent behavior and are excluded from scoring. No extreme values were deleted, capped, or winsorized. Fifteen records are insufficient to distinguish rare valid values from anomalies reliably.

## Categories and balance

{mdtable(pd.DataFrame([{'Field':c,'Value':v,'Customers':count} for c,values in profile['categories'].items() for v,count in values.items()]))}

The outcome has {churn} churned ({100*churn/n:.2f}%) and {n-churn} retained ({100*(n-churn)/n:.2f}%) records. This is only mild class imbalance, with substantial uncertainty due to sample size. No undocumented category spelling variants were observed. Representative de-identified records are in `outputs/customer_segments.csv` and the notebook.

## Implemented cleaning decisions

1. Require all 11 source columns; fail visibly if the schema is incomplete.
2. Trim identifiers and text; normalize recognized category case to the actual CSV vocabulary. Unknown values become null and are logged, never guessed. Blank strings become null.
3. Parse numeric fields; replace negative, missing, infinite, nonnumeric values, fractional month/ticket/age counts, and ages above 120 with null. High positive charges are retained because no business maximum is documented.
4. Exclude missing identifiers. Remove exact duplicates after normalization. Exclude **all** conflicting rows for the same ID because no timestamp establishes the latest record. Log source row numbers and actions without publishing original IDs.
5. Never impute tenure, contract, or charges. Incomplete accounts remain in the customer table, with null score and `Unscored` band. Missing tenure/contract gives the primary segment `Data review`. Other missing fields do not alter the score. Missing labels do not prevent scoring but are excluded from churn-rate denominators.
6. Hash synthetic identifiers with SHA-256 (12 hex characters, prefixed `SYN-`); omit raw identifiers, age, gender, total charges, and charge-difference diagnostics from public customer exports. This is pseudonymization, not a promise of anonymization for real data.
7. Record every cleaning event in `outputs/cleaning_log.csv`; this source produced **{len(log)} events** and **{len(df)} retained/scored/labelled customers**. No source values needed correction and no customers were removed.

## Source interpretation and publication

The supplied Task 1 Markdown calls the records synthetic. Page 3 of the supplied 11-page source library defines tenure in completed months, amounts in INR, support counts over the previous 90 days, and churn during an observation period. Its generic field names and contract examples conflict with this file; actual CSV names and categories take precedence. The user's Task 4 brief takes precedence over the Task 1 Markdown.

No observation date, churn date, support event date, payment-failure field, usage log, satisfaction score, acquisition date, gross margin, or intervention outcome exists. Timing of support tickets and account snapshots relative to churn cannot be verified. Support is therefore descriptive only. Even tenure, contract and charges require a verified pre-outcome snapshot before prospective use. The PDF's print date is not a customer observation date.

No explicit dataset redistribution license was found in the supplied references. Original source documents and CSV remain local and Git-ignored. Public analysis uses selected factual outputs and attributes the source; MIT does not cover EdVyro material. See `data/README.md` for retrieval and rights. No unrelated internship projects were edited.
'''
    write('reports/Data_Quality_Report.md',quality)
    rules=pd.DataFrame(RULES)
    rules['eligibility']='All three core inputs valid; otherwise no score'
    rules['missing_treatment']='Null score; Unscored; data review'
    rules.to_csv(ROOT/'outputs/scoring_specification.csv',index=False)
    write('reports/Scoring_Methodology.md',f'''# Scoring specification v1.0

This deterministic index measures the weight of specified prioritization indicators. It is **not a churn probability, trained machine-learning model, or causal estimate**. No weights or thresholds were optimized against labels. Rules were formulated after viewing the source and its obvious cohort structure; retrospective results are in-sample and are not independent validation.

{mdtable(rules)}

`RiskScore = TenurePoints + ContractPoints + ChargePoints`, with theoretical range 0-100. Eligibility requires nonnegative integer tenure, a known contract, and finite nonnegative monthly charges. There is no special missing-value discount; incomplete customers receive `Unscored`, with an explicit explanation. High valid charges are not capped as data errors.

Bands: **Low 0-29, Medium 30-59, High 60-100**. These are fixed planning cutoffs: 30 reflects moderate indicator accumulation; 60 requires multiple material contributions or flexible commitment plus another signal. They do not come from capacity analysis, expected loss, or probability calibration. Not every integer total is attainable because points are discrete.

Contract receives the greatest maximum weight (45) as an assumption about ease of exit; tenure receives 35 as an onboarding/lifecycle assumption; charge exposure receives 20 as a modest value-review indicator. INR 70 and 100 split this file's three price levels (49.99, 79.99, 149.99). These are dataset-specific fixed thresholds, not statistical quantiles or validated affordability cutoffs. Charges partly proxy subscription tier; tenure and contract are correlated, so indicators may double-count related account characteristics.

Tenure bands: 0-5, 6-12, 13-24, and 25+ completed months. Six months marks early onboarding, 12 months a first-year review, and 24 months a longer relationship. These are business heuristics, not discovered natural clusters. Spending bands share the score's charge cutoffs. Primary segments use contract, then a first-year split for flexible accounts; every retained record receives exactly one primary segment (including Data review when necessary).

Payment method is descriptive because no failure/friction evidence supports penalizing a method. Support tickets are a real observed behavior, used for service-review analysis, but their timing relative to churn is unverifiable. Age, gender, identifiers, churn, and total charges never enter the score. `Churned` is used only after scoring. Before prospective deployment, verify point-in-time availability for every input.

Observed score range: {facts['score_min']}-{facts['score_max']}. In this sample, risk bands reproduce the contract cohorts exactly: high = monthly contracts, medium = one-year, low = two-year. The rule index provides no demonstrated outcome separation beyond contract alone. No holdout/temporal experiment is claimed, and ROC-AUC is omitted because n=15 and complete contract/outcome confounding would make a single impressive number misleading. Unit tests validate software and edge cases, not business predictive utility.
''')
    memo=f'''# Customer Retention Recommendation Memo

**To:** Subscription Customer Success and Retention Team (fictional training scenario)\x20\x20
**From:** Dhaksith-S | EdVyro Data Analytics Internship, Task 4\x20\x20
**Date:** 28 October 2026\x20\x20
**Decision:** Prioritize a service/onboarding investigation; validate prospectively before deploying a retention queue.

## Executive summary

The 15-record synthetic sample contains {churn} churned customers ({100*churn/n:.2f}%) and {n-churn} retained customers. All seven monthly-contract records are churned; none of the eight longer-contract records is churned. Six of the seven monthly customers are in their first year. Their service histories warrant investigation, but the data do not prove that contract flexibility or support demand caused churn.

The fixed 0-100 index places {len(high)} customers in High, four in Medium, and four in Low. High-band recorded monthly charges total INR {high.MonthlyCharges.sum():,.2f}; **all seven are already labelled churned**, so there are **{len(active_high)} retained high-band accounts** available for retention outreach in this file. These charges are historical exposure, not currently recoverable monthly recurring revenue. Retained accounts' recorded monthly charges total INR {retained.MonthlyCharges.sum():,.2f}; neither amount is a forecast of revenue saved.

## Business objective

Give a fictional subscription team an auditable way to describe customer cohorts, investigate service experience, and design a future prioritization pilot. This sample supports a learning demonstration and hypotheses, not a production churn forecast or a claim of retention lift.

## Data and methodology

The supplied EdVyro CSV has 15 unique synthetic accounts and 11 source fields. The source guide defines charges in INR and support tickets over the previous 90 days. No missing values, duplicates, invalid values, or billing-identity discrepancies were observed. Every record is retained; hashed synthetic IDs replace raw IDs in public exports. Actual CSV contract categories override the generic source guide's examples.

Primary segments are mutually exclusive: flexible contracts in their first year (<=12 months), flexible contracts beyond their first year, one-year commitments, and two-year commitments. Tenure, spending, payment, and risk bands are separate analytical dimensions. Groups below five accounts are flagged as small samples.

The risk index sums tenure (0-35), commitment (0-45), and monthly-charge exposure (0-20). Low is 0-29, Medium 30-59, High 60-100. Points are fixed business assumptions, not fitted coefficients. Payment categories have no penalty; support counts are descriptive because their timing is uncertain. Churn, age, gender, total charges and identifiers are excluded. Missing core inputs yield no score rather than a reassuring zero.

## Key findings and priority segments

{mdtable(seg[['PrimarySegment','Customers','CustomerPct','ObservedChurnPct','AvgTenureMonths','AvgRiskScore','MonthlyChargeSumINR']].rename(columns={'PrimarySegment':'Primary segment','Customers':'Count','CustomerPct':'Share (%)','ObservedChurnPct':'Churn (%)','AvgTenureMonths':'Mean tenure (mo)','AvgRiskScore':'Mean index (pts)','MonthlyChargeSumINR':'Charges (INR/mo)'}))}

The six first-year flexible customers have a mean tenure of {df.loc[df.PrimarySegment.eq('Flexible - first year'),'TenureMonths'].mean():.2f} months, {df.loc[df.PrimarySegment.eq('Flexible - first year'),'SupportTickets'].mean():.2f} support tickets in the prior 90 days, and INR {df.loc[df.PrimarySegment.eq('Flexible - first year'),'MonthlyCharges'].sum():.2f} in recorded monthly charges. The single flexible customer beyond the first year has tenure 14 months, three tickets, and INR 79.99 in monthly charges; one account cannot establish a population pattern.

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
'''
    write('reports/Customer_Retention_Recommendation_Memo.md',memo)
    make_dictionary()
    return facts,memo

def make_dictionary():
    definitions={
        'AnalysisID':'SHA-256-derived synthetic ID (12 hex chars); no raw customer ID.',
        'TenureMonths':'Completed months; finite nonnegative integer, null if invalid.',
        'SubscriptionType':'Actual Basic, Pro, Enterprise label; descriptive, not a score input.',
        'ContractType':'Actual Month-to-Month, One Year, Two Year; score and segment input.',
        'PaymentMethod':'Credit Card, Bank Transfer, UPI, Debit Card; descriptive only.',
        'MonthlyCharges':'Fictional monthly amount in INR; null if invalid; not current MRR.',
        'SupportTickets':'Nonnegative integer count in prior 90 days; timing versus churn unknown; descriptive only.',
        'PrimarySegment':'Exactly one contract/lifecycle segment; Data review if tenure/contract invalid.',
        'TenureBand':'New 0-5; Developing 6-12; Established 13-24; Long-term 25+ months; Unknown.',
        'SpendingBand':'Low <70; Medium 70-<100; High >=100 INR; Unknown.',
        'ScoreEligible':'Boolean: all three core risk inputs valid.',
        'EvaluationEligible':'Boolean: core inputs valid and churn label known.',
        'RiskScore':'Nullable integer assumption-based index 0-100; not a probability.',
        'RiskBand':'Low 0-29; Medium 30-59; High 60-100; Unscored.',
        'TenurePoints':'Nullable integer 0,10,25,35; tenure contribution.',
        'ContractPoints':'Nullable integer 0,20,45; contract contribution.',
        'ChargePoints':'Nullable integer 0,10,20; monthly-charge contribution.',
        'ScoreExplanation':'Plain-text conditions and awarded points, including zero; missing-input reason.',
        'Churned':'Nullable outcome: Yes->1, No->0. Retrospective evaluation only.',
        'Definition':'Primary segment rule, or note identifying overlapping analytical cohort.',
        'Customers':'Number of retained source records in cohort.',
        'CustomerPct':'100 * cohort customers / all retained customers, in percent.',
        'LabeledCustomers':'Cohort rows with known Churned; denominator for observed churn.',
        'ChurnedCustomers':'Sum of known Churned labels in cohort.',
        'ObservedChurnPct':'100 * churned / labelled; null if no labels.',
        'AvgTenureMonths':'Mean known tenure, in months.',
        'AvgMonthlyChargesINR':'Mean known recorded monthly charges, in INR.',
        'MonthlyChargeSumINR':'Sum of known recorded charges, in INR; includes churned; null if all missing.',
        'RetainedMonthlyChargeSumINR':'Known monthly charges for Churned=0, INR; not verified active MRR.',
        'HighRiskChargeSumINR':'Known monthly charges for High band, INR; not expected loss or savable revenue.',
        'ScoredCustomers':'Number of cohort rows with a non-null score.',
        'AvgRiskScore':'Mean non-null risk index, points.',
        'MinRiskScore':'Minimum non-null risk index, points.',
        'MedianRiskScore':'Median non-null risk index, points.',
        'MaxRiskScore':'Maximum non-null risk index, points.',
        'HighRiskCustomers':'Count of High band accounts.',
        'AvgSupportTickets90Days':'Mean known support ticket count; previous 90 days.',
        'SmallSample':'Boolean: cohort has fewer than five records; heuristic caution flag.',
        'source_row':'1-based original CSV line number including header.',
        'field':'Source column with cleaning event; record for exact duplicate.',
        'action':'Documented normalization, missing/invalid, or exclusion decision.',
        'signal':'Scoring signal name.', 'feature':'Source field used for signal.',
        'condition':'Exact point-awarding thresholds.', 'maximum':'Maximum points contributed by signal.',
        'reason':'Business-assumption rationale, not fitted evidence.',
        'eligibility':'Conditions needed to calculate the score.',
        'missing_treatment':'Null score and Unscored band; no silent imputation.',
    }
    for source,desc in {'CustomerID':'Original synthetic unique ID, local only.', 'Gender':'Source category, excluded from prioritization and public customer exports.', 'Age':'Source age in years, excluded from prioritization and public customer exports.', 'TotalCharges':'Source cumulative INR amount; mechanically tenure times monthly charges in supplied sample; local only.', 'Churn':'Original Yes/No outcome; mapped to Churned.', 'ChargeDifference':'Local-only TotalCharges minus tenure*monthly charge, rounded to INR 0.01.'}.items(): definitions[source]=desc
    rows=pd.DataFrame([{'Field':k,'Definition':v} for k,v in definitions.items()])
    rows.to_csv(ROOT/'outputs/data_dictionary.csv',index=False)
    write('reports/Data_Dictionary.md','# Data dictionary\n\nNull numeric CSV cells mean unknown, not zero. Percent fields use 0-100 units. Means exclude nulls. Summary labels are mutually exclusive within a single dimension; different dimensions overlap and must not be added together.\n\n'+mdtable(rows)+'\n\n`outputs/data_profile.json` records original row/column counts, inferred dtypes, missing counts, raw category frequencies, numeric minima/maxima, duplicate counts, source SHA-256, retained/scored/evaluated row counts, and billing-identity discrepancy count. `key_findings.json` contains same-named aggregate counts, charge sums in INR, tenure mean in months, and index bounds derived from exported rows. `docs/data.json` mirrors the customer export schema. `customer_segments.csv` and `customer_risk_scores.csv` intentionally share a complete reproducible input/output schema.')

def make_notebook():
    cells=[]
    def md(s): cells.append(nbf.v4.new_markdown_cell(s.strip()))
    def code(s): cells.append(nbf.v4.new_code_cell(s.strip()))
    md('# Customer Segmentation and Churn Risk\n\nEdVyro Data Analytics Internship - Task 4 | Dhaksith-S\n\n## 1. Project introduction\nThis analysis turns a small synthetic subscription sample into auditable customer cohorts and an explainable prioritization index. The three deliverables are this notebook, the customer segment table, and the recommendation memo. Scores are not churn probabilities.')
    md('## 2. Business problem\nWhich groups warrant service investigation, and how could a future retention team prioritize active customers? Historical churn and current retention eligibility must be distinguished. We do not estimate intervention effects from these data.')
    code('''from pathlib import Path
import sys
ROOT = Path.cwd() if (Path.cwd() / 'src').is_dir() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
import pandas as pd
from IPython.display import display, Image
from src.pipeline import locate_source, run_pipeline
from src.preprocessing import profile_data
from src.segmentation import summarize, SEGMENTS
from src.scoring import RULES, calculate_risk_score, assign_risk_band, explain_risk_score
raw = pd.read_csv(locate_source())
df, profile, cleaning_log = run_pipeline(root=ROOT)
pd.set_option('display.max_columns', 25)
def chart(name): display(Image(filename=str(ROOT / 'reports/figures' / (name + '.png'))))
print('Environment: Python', sys.version.split()[0])
print(f'Source: {raw.shape[0]} customers, {raw.shape[1]} columns; {len(df)} retained records')''')
    md('## 3. Dataset overview\nThe supplied Task 1 brief identifies synthetic records. The source library defines charges in INR and support tickets in the previous 90 days. Actual CSV categories take precedence over the generic guide. Original source remains unchanged and is excluded from the public repository; see `data/README.md` for authorized retrieval. Public examples omit raw IDs and demographics.')
    code("display(pd.DataFrame({'dtype':raw.dtypes.astype(str), 'missing':raw.isna().sum()}))\ndisplay(df[['AnalysisID','TenureMonths','ContractType','MonthlyCharges','SupportTickets','Churned']].head())\ndisplay(raw.select_dtypes('number').describe())")
    md('## 4. Data quality assessment\nCheck original missingness, duplicate IDs, full-row duplicates, categories, numeric ranges, and the billing identity. Counts are inspected before normalization. See the full quality report for exclusion and missing-value rules.')
    code("print('Missing cells:', sum(profile['missing'].values()))\nprint('Exact duplicates:', profile['exact_duplicate_rows'], 'Duplicate IDs:', profile['duplicate_customer_ids'])\nprint('Billing identity mismatches:', profile['charge_identity_mismatches'])\ndisplay(pd.DataFrame([{'Column':k,'Value':v,'Count':n} for k,vs in profile['categories'].items() for v,n in vs.items()]))")
    md('## 5. Cleaning and preprocessing\nText is trimmed and recognized categories canonicalized. Impossible numeric values become null. Exact duplicates are removed; conflicting IDs are quarantined entirely. Core inputs are never imputed: incomplete records remain Unscored. Missing labels are excluded from evaluation denominators. No source customer needed correction or removal in this run.')
    code("display(cleaning_log)\nprint(f'Cleaning events: {len(cleaning_log)}; scored: {df.ScoreEligible.sum()}; labelled/scored: {df.EvaluationEligible.sum()}')")
    md('## 6. Exploratory data analysis\nThese are cross-sectional observed associations, with no exact observation date or outcome horizon. Category plots annotate churned/labelled counts so tiny denominators remain visible.')
    code("for name in ['churn_distribution','tenure_distribution','churn_by_contract','churn_by_payment']: chart(name)\nprint(f'Churn: {df.Churned.sum()}/{df.Churned.notna().sum()} = {100*df.Churned.mean():.2f}%')\nprint(f'Mean tenure: {df.TenureMonths.mean():.2f} months; median {df.TenureMonths.median():.0f} months')")
    md('Interpretation: all seven monthly-contract customers are churned; all eight longer-contract customers are retained. The 46.67% churn share describes this synthetic sample only. Payment contrasts are confounded by contract and tenure and do not justify payment-method penalties. Tenure spans 2-48 months; observed support counts are 0-6.')
    md('## 7. Feature selection\n**Scoring inputs:** tenure (lifecycle), contract (commitment), monthly charges (absolute bill exposure). **Behavioral descriptive input:** support tickets (service demand). **Other descriptive cohorts:** payment and subscription tier. Support timing relative to churn is unknown, so tickets never enter the score. Exclude age/gender (unnecessary demographics), IDs, churn, and total charges (mechanically redundant). Even core account fields need verified pre-churn snapshots before production use.')
    md('## 8. Feature engineering\nTenure: 0-5, 6-12, 13-24, 25+ months. The 6/12/24 boundaries represent onboarding and annual review heuristics. Spending: <70, 70-<100, >=100 INR. These fixed thresholds separate the three source price tiers, not learned affordability groups. Hash synthetic IDs, map Yes/No outcome to 1/0, and preserve missingness.')
    code("display(df[['AnalysisID','TenureBand','SpendingBand','SubscriptionType','SupportTickets']])")
    md('## 9. Customer segmentation methodology\nPrimary segments are mutually exclusive account cohorts. A flexible contract is split at the end of the first year; annual and two-year commitments form separate groups. Missing tenure or contract produces Data review. Analytical tenure/payment/risk dimensions overlap across dimensions and are presented separately.')
    code("display(pd.DataFrame(SEGMENTS.items(), columns=['Primary segment','Definition']))\nassert df.PrimarySegment.notna().all()\nassert summarize(df).Customers.sum() == len(df)")
    md('## 10. Segment distribution analysis\nCounts, charge sums, observed outcomes, tenure, service demand, and the full score range are available for each primary segment. Groups with fewer than five accounts are explicitly flagged.')
    code("display(summarize(df))\nchart('segment_counts')")
    md('Interpretation: the first-year flexible cohort contains six accounts. The other flexible cohort contains one, and both commitment cohorts contain four each. The singleton cannot support a general claim; the zero-churn commitment groups are also too small to imply protection.')
    md('## 11. Explainable churn-risk scoring\nIndex v1.0 sums fixed assumption-based contributions. No fitting, optimization, or calibrated probabilities are involved. Contract receives at most 45, tenure 35, charges 20. Payment, support, demographics, total charges and churn are absent from the implementation. Correlated account features can double-count the same underlying pattern. See the machine-readable scoring specification.')
    code("display(pd.DataFrame(RULES))\nprint('Theoretical index range: 0-100; observed:', df.RiskScore.min(), '-', df.RiskScore.max())\nchart('risk_distribution')")
    md('Interpretation: actual index values span 20-80 points. Discrete point rules leave gaps in the attainable range. The 20-point charge signal is a hypothesis: the most expensive accounts in this sample are all retained.')
    md('## 12. Risk-band assignment\nLow <30, Medium 30-59, High >=60. These operational planning cutoffs express accumulating indicators, not fitted decision thresholds or outreach capacity. Missing core inputs yield Unscored. They require prospective validation.')
    code("display(summarize(df,'RiskBand'))\nchart('segment_risk_heatmap')\nchart('scores_by_contract')\nchart('scores_by_tenure')")
    md('Interpretation: seven High, four Medium and four Low accounts are present. The heatmap shows that each primary cohort occupies a single risk band in this particular sample. Contract alone gives the same band partition, so the extra signals have no demonstrated incremental outcome value here.')
    md('## 13. Score-level explanations\nEvery row exports the exact component contributions and an explanation. Zero contributions are shown. Independent reproduction needs only tenure, contract, and charges; outcomes can be changed without affecting scores.')
    code("display(df[['AnalysisID','TenurePoints','ContractPoints','ChargePoints','RiskScore','ScoreExplanation']])\nr = df.iloc[0].to_dict()\nassert calculate_risk_score(r) == calculate_risk_score({**r,'Churn':'No','Churned':0})\nprint(explain_risk_score(r))")
    md('## 14. Retrospective churn validation\nOnly after scoring do we compare labels. Rules were developed after inspecting this small source; no independent holdout or temporal validation is claimed. ROC-AUC is deliberately omitted because n=15 and complete contract/outcome confounding would overstate apparent evidence. Software correctness is tested separately.')
    code("chart('risk_band_churn')\ndisplay(summarize(df,'RiskBand')[['RiskBand','LabeledCustomers','ChurnedCustomers','ObservedChurnPct','SmallSample']])\ndisplay(pd.crosstab(df.ContractType,df.Churned))")
    md('Interpretation: High has 7/7 churned; Medium 0/4; Low 0/4. High separates observed outcomes, while Low versus Medium does not. These 0%/100% rates are unstable descriptions of a teaching sample. Support and churn share an unverifiable timeline, and no causal interpretation is justified.')
    md('## 15. Customer priority analysis\nRank retained accounts separately from already-churned records. Charge sums include historical monthly amounts unless explicitly restricted. They are neither expected loss nor verified current recurring revenue.')
    code("chart('charge_exposure')\nretained = df.loc[df.Churned.eq(0)].sort_values(['RiskScore','MonthlyCharges'],ascending=False)\ndisplay(retained[['AnalysisID','PrimarySegment','RiskScore','RiskBand','MonthlyCharges']])\nprint('Retained High accounts:', len(retained.loc[retained.RiskBand.eq('High')]))\nprint('Recorded charge sum, all accounts (INR):', round(df.MonthlyCharges.sum(),2))\nprint('Recorded High-band charge sum (INR):', round(df.loc[df.RiskBand.eq('High'),'MonthlyCharges'].sum(),2))\nprint('Recorded retained-account charges (INR):', round(retained.MonthlyCharges.sum(),2))")
    md('Interpretation: INR 409.93 belongs to already-churned High-band accounts, so none is a current high-priority retention candidate. The eight retained accounts have INR 859.92 in recorded monthly charges. The sample cannot estimate recoverable revenue or treatment ROI.')
    md('## 16. Recommended retention interventions\nInvestigate onboarding and support themes for the six first-year flexible records; review the singleton case qualitatively. Collect renewal dates before any one-year renewal pilot. Maintain service and feedback for two-year accounts. Do not penalize payment methods without failed-payment evidence. The [recommendation memo](../reports/Customer_Retention_Recommendation_Memo.md) contains the full action matrix, target audiences, KPIs and experiment plan. On a larger dated active cohort, preregister rules and compare randomized assistance against usual service over 90 days, including margin, complaints and opt-out guardrails.')
    md('## 17. Limitations and risks\nSynthetic n=15, mildly imbalanced 7/8 labels, tiny subgroups, complete contract/label confounding, correlated indicators, unknown snapshot times and outcome horizon. No usage, satisfaction, payment failures, contact permissions, margin or intervention outcomes. No probability calibration or external validation. Account fields may be post-outcome snapshots; temporal verification is mandatory before prospective use. Source rights are distinct from the original code license. Do not substitute real customer data into the public report.')
    md('## 18. Conclusion\nThis project supplies reproducible cohorts, point-level explanations and a testable operational hypothesis. Observed High-band separation adds no established predictive value beyond contract. Start with service investigation and a controlled prospective pilot, keeping already-churned customers out of a retention queue.')
    code("for file in ['customer_segments.csv','customer_risk_scores.csv','segment_summary.csv','data_dictionary.csv','scoring_specification.csv']:\n    assert (ROOT/'outputs'/file).is_file()\nexported=pd.read_csv(ROOT/'outputs/customer_segments.csv')\nassert len(exported)==len(df) and exported.AnalysisID.is_unique\nassert exported.RiskScore.tolist()==df.RiskScore.tolist()\nprint(f'Export checks passed for {len(exported)} customers. Required artifacts are present.')")
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3 (project .venv)','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.11'}})
    target=ROOT/'notebooks/Customer_Segmentation_and_Churn_Risk.ipynb'; target.parent.mkdir(exist_ok=True)
    nbf.write(nb,target)

def make_pdf(memo):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='MemoBody',fontName='Helvetica',fontSize=9.3,leading=14,spaceAfter=8,textColor=colors.HexColor('#243248')))
    styles.add(ParagraphStyle(name='MemoTitle',fontName='Helvetica-Bold',fontSize=25,leading=29,spaceAfter=17,textColor=colors.HexColor('#12354b')))
    styles.add(ParagraphStyle(name='MemoHeading',fontName='Helvetica-Bold',fontSize=13,leading=18,spaceBefore=13,spaceAfter=8,textColor=colors.HexColor('#14647b'),keepWithNext=True))
    styles.add(ParagraphStyle(name='Cell',fontName='Helvetica',fontSize=7,leading=10,spaceAfter=0))
    def markup(s): return re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',html.escape(s))
    blocks=memo.strip().split('\n\n'); story=[]
    for block in blocks:
        if block.startswith('# '): story.append(Paragraph(markup(block[2:]),styles['MemoTitle']))
        elif block.startswith('## '):
            if block.startswith('## Measurement plan'): story.append(PageBreak())
            story.append(Paragraph(markup(block[3:]),styles['MemoHeading']))
        elif block.startswith('|'):
            lines=block.splitlines(); rows=[[Paragraph(markup(x.strip()),styles['Cell']) for x in line.strip('|').split('|')] for line in lines if not re.match(r'^\|\s*-',line)]
            count=len(rows[0])
            widths=([32,67,60,98,73,73,96] if 'Priority' in lines[0] else [115,35,45,50,75,75,104]) if count==7 else [499/count]*count
            table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dceef3')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f3f6fa'),colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#90bdc9'))]))
            story.extend([table,Spacer(1,10)])
        else: story.append(Paragraph(markup(block).replace('\n','<br/>'),styles['MemoBody']))
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#c8d7e4')); canvas.line(48,43,547,43)
        canvas.setFont('Helvetica',8); canvas.setFillColor(colors.HexColor('#536779'))
        canvas.drawString(48,30,'EdVyro Task 4 | Synthetic sample | Retrospective analysis')
        canvas.drawRightString(547,30,f'{doc.page}')
    doc=SimpleDocTemplate(str(ROOT/'reports/Customer_Retention_Recommendation_Memo.pdf'),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=43,bottomMargin=58,title='Customer Retention Recommendation Memo',author='Dhaksith-S')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)

if __name__=='__main__':
    df,profile,log=run_pipeline()
    facts,memo=document(df,profile,log)
    make_notebook(); make_pdf(memo)
    print(json.dumps(facts,indent=2))

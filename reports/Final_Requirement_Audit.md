# Task 4 final requirement audit

All mandatory deliverables and the optional interactive report are complete. Verified on 28 October 2026.

| Requirement | Result and evidence |
| --- | --- |
| Inspect dataset and references | 15 rows / 11 source columns; full profile and provenance in Data_Quality_Report.md and outputs/data_profile.json |
| Profile and clean reproducibly | src/preprocessing.py, logged normalization/exclusion rules, outputs/cleaning_log.csv; no source corrections needed |
| Select useful account/behavior features | Tenure, commitment and charges scored; support-ticket behavior and payment/tier analyzed descriptively; timing/feature rationale documented |
| Explain segments | Four observed primary contract/lifecycle cohorts; analytical tenure, spending, payment and risk dimensions kept separate |
| Assign exactly one primary segment | All 15 retained records assigned; data-review fallback and population reconciliation tested |
| Transparent risk index | src/scoring.py implements the fixed 0-100 index with separate contributions and explanations |
| Reproduce every calculation | All scoring inputs and awarded contributions exported in both customer tables; independent reproduction test passes |
| Document weights and bands | reports/Scoring_Methodology.md and outputs/scoring_specification.csv; Low 0-29, Medium 30-59, High 60-100 |
| Validate edge cases | Missing/invalid inputs, all thresholds, extremes, duplicates, single-class/empty inputs, unknown categories and deterministic output tested |
| Exclude outcome from inputs | Churn and all excluded fields can change without changing score; outcome used only for retrospective evaluation |
| Complete analysis notebook | All 18 requested sections; 14 code cells executed, 11 embedded charts, no saved cell errors or unexplained warnings |
| Customer segment table | outputs/customer_segments.csv, segment_summary.csv and customer_risk_scores.csv; data dictionary and additional cohort summaries included |
| Recommendation memo | Markdown and visually verified three-page PDF; numeric findings, priority audiences, action matrix, KPIs and controlled measurement plan |
| Evidence-based findings | 7/15 churned, 7 High (all already churned), 4 Medium, 4 Low; no causal, calibrated or independent-validation claim |
| Automated tests | 104 passed, 0 failed/errors/skipped; machine-readable aggregate and detailed validation report included |
| README | Immediate links to all mandatory deliverables, findings, method, source retrieval, setup, execution, tests, live report and limitations |
| Git | Isolated project repository, main branch, authenticated account noreply identity; unrelated parent repository not altered |
| New public GitHub repository | https://github.com/Dhaksith-S/edvyro-customer-segmentation-churn-risk; PUBLIC and main pushed |
| Public supporting links | Unauthenticated HTTP/content checks for notebook, CSVs, memo, PDF, preview and report assets; GitHub README rendered |
| Optional interactive report | https://dhaksith-s.github.io/edvyro-customer-segmentation-churn-risk/; HTTPS, main:/docs, local static assets, no paid dependencies |
| Website interaction and mobile checks | Five filters, reset, empty state, score inspection, chart/data updates, navigation, errors and 360px layout tested |
| Credentials/source rights | Staged release scan passes; environment, raw CSV and source reference documents excluded; hashed synthetic IDs; separate source rights and original-code MIT license |

The optional Excel workbook was omitted: the required CSVs, complete dictionary, notebook and interactive report provide the needed review access. PyMuPDF supplied visual rendering because Poppler is not installed. Browser validation uses Chromium; no exhaustive assistive-technology or cross-browser certification is claimed. No custom hosted analytical CI run is claimed; all automated tests were actually run locally, and the built-in Pages deployment is verified separately.

Scientific limits remain material: n=15 synthetic records, tiny cohorts, complete contract/outcome confounding, uncertain point-in-time feature availability, no exact outcome dates, and no intervention/margin evidence. These constrain inference rather than software completion. The score must be tested on a larger, dated active cohort before use in retention operations.

**One submission URL:** https://github.com/Dhaksith-S/edvyro-customer-segmentation-churn-risk

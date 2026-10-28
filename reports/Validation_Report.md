# Validation evidence

Analysis and local validation completed on 28 October 2026, using project-local Python 3.11.9 on Windows. Exact package versions are recorded in `requirements-lock.txt`; `requirements.txt` supplies compatible installation ranges.

## Automated checks

Command: `python -m pytest -q --junitxml=tmp/test-results.xml` (using the project virtual environment).

**104 tests executed; 104 passed; 0 failed; 0 errors; 0 skipped.** The machine-readable aggregate is in `reports/validation_summary.json`. Local JUnit XML and full-page browser screenshots stay in ignored `tmp/`; they contain machine-specific metadata and are not published.

Coverage includes missing identifiers, duplicate/conflicting records, nonnumeric/negative/infinite charges, missing/negative/fractional tenure, unexpected categories, missing labels, normalization, empty frames, all-retained/all-churned outcomes, single primary assignment, reconciliation, safe export fields and complete field definitions. Scoring tests cover every rule threshold, band cutoffs, reproducibility, absent core inputs, unknown categories, exact explanation-point sums, theoretical 0/100 extremes and no target/excluded-feature leakage. One parameter-combination test additionally traverses 144 account-signal combinations; this is part of the 104 tests, not 144 additional test cases.

The first run found a CSV percentage-rounding discrepancy (100.0001% after four-decimal rounding). Summary precision was increased to eight decimals and the full suite passed. Optional pytest cache creation encountered a OneDrive rename conflict; the cache plugin is disabled in `pytest.ini`. No business rules or outcomes were altered to make tests pass.

## Notebook execution

`python scripts/execute_notebook.py` ran **all 14 code cells** across the requested 18 analytical sections, saved outputs, and completed without cell exceptions. Eleven labelled charts are embedded. Notebook tests parse and validate the notebook, confirm every code cell has an execution count, check chart outputs, verify source/processed population evidence, and reconcile exported scores. The execution script is run explicitly; the saved-artifact test is not described as a second execution.

The Windows event-loop policy is set explicitly to avoid a ZeroMQ compatibility warning. The installed kernel launcher emits a notice about its default local TCP transport outside the notebook; saved analytical cell outputs have no warnings or tracebacks. No remote kernel service was configured. Kernel connection files remain runtime-managed and are not committed.

## Browser checks

Real headless Chromium tests run against a temporary local HTTP server. All six chart panels render; script/style/data/icon assets load with no unexpected browser console errors. Every category in each of five filters is checked against independently selected Python data. Table IDs, count/share, churn numerator/denominator, charge sums, segment and score counts, and retained High-band counts reconcile with the filtered population. Combined impossible filters produce a clear empty state; reset restores all 15 customers. Selecting an account displays its exported score explanation. A simulated data-load failure displays a recovery message.

The 360px viewport has no page-level horizontal overflow; the wide customer table scrolls within its own labelled region. Filter interaction works at mobile width. Desktop and mobile screenshots were inspected; the public preview is `reports/figures/report_preview.png`. These checks establish functionality and basic responsiveness; they are not a formal screen-reader certification or exhaustive cross-browser audit. No hosted CI run is claimed; automated scripts and local results are included, and GitHub Pages requires no custom build workflow.

## Public release verification

Public repository: <https://github.com/Dhaksith-S/edvyro-customer-segmentation-churn-risk>. Visibility is PUBLIC, the default branch is `main`, and the project uses an isolated local Git repository and the authenticated account's verified GitHub noreply identity.

Live report: <https://dhaksith-s.github.io/edvyro-customer-segmentation-churn-risk/>. GitHub Pages serves `main:/docs`; HTTPS is enforced. The built-in Pages deployment completed successfully. `scripts/verify_public.py` performs 14 unauthenticated HTTP checks, verifies seven supporting-material links, compares text content after Git line-ending normalization, and checks binary PDF/PNG bytes exactly. It also confirms live baseline metrics, all five filters, reset, empty state, navigation, 360px width, no unexpected app console errors, GitHub README rendering, and notebook-page accessibility. Machine-readable evidence is in `reports/public_verification.json`. No sign-in is required.

## PDF checks

The memo is three A4 pages generated with ReportLab. Every page was rasterized with PyMuPDF and visually inspected after final changes. Human-readable table headings, units, consistent colors, repeated headers, margins and page footers are present. Measurement planning starts on page 3. No clipped text, broken glyphs, overlapping cells or orphaned section headings were observed. PyMuPDF is the available renderer; Poppler is not installed on this workstation.

## Reproducibility and publication controls

The upstream source returned HTTP 200 with 1,173 bytes and an exact SHA-256 match to the supplied local file. `scripts/download_data.py` successfully saved a verified copy to Git-ignored `data/raw/`. No source values were changed and all 15 accounts remain. `pip check` reports no broken requirements. Public CSVs include all three score inputs and component contributions, allowing score reproduction without redistributing the original source.

Raw CSV, supplied source Markdown/PDF, environment folders, local test evidence and caches are ignored. Synthetic public IDs are hashed; raw identifiers, customer-level demographics, total charges and credentials are excluded from analytical exports. `scripts/audit_release.py` scans staged content for common credential formats, private paths and oversized/source files before commits. Original code/writing and third-party source rights are documented separately.

## Scientific limits

Software tests do not validate predictive utility, causality, calibration, retention lift or ROI. The sample has only 15 synthetic records; contract and outcome are completely confounded, and risk bands reproduce contract cohorts. Rules were developed after source inspection without statistical fitting, and evaluation is retrospective in-sample. No temporal holdout or independent validation is claimed. Every prospective recommendation requires new dated active-customer data and a controlled test.

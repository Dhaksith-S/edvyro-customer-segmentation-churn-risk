# Source data and rights

The supplied `customer_churn_sample.csv` has 15 synthetic subscription customers and 11 columns. The local task brief identifies the file as synthetic. The source library's analytics section defines charges as fictional INR amounts and support tickets as a count in the previous 90 days. Its generic snake_case schema and monthly/quarterly/annual contract examples do not match this CSV exactly; the actual CSV uses `Month-to-Month`, `One Year`, and `Two Year`.

Original source: <https://edvyro.in/datasets/customer_churn_sample.csv>. Reference: <https://edvyro.in/datasets/source-materials/task-source-library#analytics>. Inspected on 28 October 2026 alongside the supplied local Markdown and 11-page PDF. The local Markdown describes Task 1; this project implements the user's Task 4 requirements.

No explicit dataset redistribution license was found in the supplied materials. This repository therefore does not mirror the original CSV, supplied Markdown, or PDF. The MIT license covers original project code and writing only; EdVyro retains rights to its materials. Analysis exports contain selected factual/derived fields with hashed synthetic IDs, and omit raw IDs, age, gender, and total charges. They do not grant an upstream dataset license. Do not substitute real customer records into a public report.

To reproduce from source, run `python scripts/download_data.py` or place your authorized supplied CSV in `data/raw/customer_churn_sample.csv`. The downloader verifies the exact supplied file's SHA-256 before saving it. If the upstream file changes, obtain the original supplied file instead of disabling the integrity check. Raw source stays ignored by Git. Existing public outputs also contain every scoring input, so reviewers can independently reproduce each score without obtaining the original CSV.

`outputs/data_profile.json` records the original checksum and inspection results. `reports/Data_Quality_Report.md` documents all decisions, assumptions, and field mappings.

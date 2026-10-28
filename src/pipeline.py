"""One reproducible path from a supplied CSV to all analytical outputs."""
from pathlib import Path
import hashlib
import json
import pandas as pd
from src.preprocessing import clean_data,profile_data
from src.segmentation import enrich_customers,summarize
from src.exports import export_outputs
from src.visualization import create_figures

ROOT=Path(__file__).resolve().parents[1]

def locate_source(source=None):
    candidates=[Path(source)] if source else [ROOT/'data/raw/customer_churn_sample.csv',ROOT/'customer_churn_sample.csv']
    for p in candidates:
        if p.is_file(): return p
    raise FileNotFoundError('Supply --input path/to/customer_churn_sample.csv, or run scripts/download_data.py. See data/README.md.')

def run_pipeline(source=None, root=ROOT, figures=True):
    root=Path(root); source=locate_source(source)
    raw=pd.read_csv(source); profile=profile_data(raw)
    clean,log=clean_data(raw); scored=enrich_customers(clean)
    out=root/'outputs'; out.mkdir(parents=True,exist_ok=True)
    records=export_outputs(scored,out)
    log.to_csv(out/'cleaning_log.csv',index=False)
    profile['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    profile['retained_rows']=len(scored); profile['scored_rows']=int(scored.ScoreEligible.sum())
    profile['evaluated_rows']=int(scored.EvaluationEligible.sum())
    profile['charge_identity_mismatches']=int(clean.ChargeDifference.abs().gt(.01).sum())
    (out/'data_profile.json').write_text(json.dumps(profile,indent=2,allow_nan=False),encoding='utf-8')
    if figures: create_figures(scored,root/'reports/figures')
    # Only de-identified selected factual analysis fields; no raw IDs or demographics.
    (root/'docs').mkdir(exist_ok=True)
    (root/'docs/data.json').write_text(json.dumps(records,indent=2,allow_nan=False),encoding='utf-8')
    return scored,profile,log

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--input'); args=p.parse_args()
    df,profile,log=run_pipeline(args.input)
    print(f'Processed {len(df)} customers; {len(log)} cleaning events.')

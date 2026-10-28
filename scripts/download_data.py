"""Download the authorized teaching source with exact-byte integrity checking."""
from pathlib import Path
import hashlib
import json
import requests
root=Path(__file__).resolve().parents[1]
expected=json.loads((root/'outputs/data_profile.json').read_text())['source_sha256']
r=requests.get('https://edvyro.in/datasets/customer_churn_sample.csv',timeout=30)
r.raise_for_status()
if hashlib.sha256(r.content).hexdigest()!=expected:
    raise SystemExit('Source checksum differs. Use the original supplied CSV; no file was written.')
target=root/'data/raw/customer_churn_sample.csv'; target.parent.mkdir(parents=True,exist_ok=True)
target.write_bytes(r.content); print(f'Verified source saved to {target}')

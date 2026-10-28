"""Inspect only staged project files; report filenames, never matching secret values."""
import re
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
names=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=root).decode().split('\0')
names=[n for n in names if n]
failures=[]
patterns=[re.compile(rb'gh[pousr]_[A-Za-z0-9]{20,}'),re.compile(rb'github_pat_[A-Za-z0-9_]{20,}'),
          re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(rb'sk-[A-Za-z0-9]{24,}')]
for name in names:
    p=root/name
    data=subprocess.check_output(['git','show',f':{name}'],cwd=root)
    if any(pattern.search(data) for pattern in patterns):failures.append(f'Credential-like content: {name}')
    if any(s in name.split('/') for s in ['.venv','raw','__pycache__']) or p.name.startswith('.env'):
        failures.append(f'Private/dependency path: {name}')
    if len(data)>10_000_000:failures.append(f'Oversized file: {name}')
    if p.name in ['customer_churn_sample.csv','data-analytics-task-1.md','EdVyro Internship Task Source Library.pdf']:
        failures.append(f'Source material: {name}')
if failures:raise SystemExit('\n'.join(failures))
print(f'Release audit passed: {len(names)} staged files; no credential-pattern matches, source originals, private paths, or files over 10 MB.')

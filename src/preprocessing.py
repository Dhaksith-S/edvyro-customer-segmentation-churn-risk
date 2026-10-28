"""Strict, logged cleaning. Never silently impute risk inputs or conflicting IDs."""
from __future__ import annotations
import hashlib
import numpy as np
import pandas as pd

CATEGORIES = {
    'Gender': ['Female', 'Male'],
    'SubscriptionType': ['Basic', 'Pro', 'Enterprise'],
    'ContractType': ['Month-to-Month', 'One Year', 'Two Year'],
    'PaymentMethod': ['Credit Card', 'Bank Transfer', 'UPI', 'Debit Card'],
    'Churn': ['Yes', 'No'],
}
NUMERIC = ['Age', 'TenureMonths', 'MonthlyCharges', 'TotalCharges', 'SupportTickets']
REQUIRED = ['CustomerID', *NUMERIC, *CATEGORIES]

def profile_data(df: pd.DataFrame) -> dict:
    """JSON-serializable audit of original values, before normalization."""
    ranges = {}
    for c in NUMERIC:
        if c in df:
            values = pd.to_numeric(df[c], errors='coerce')
            finite = values.loc[np.isfinite(values)]
            ranges[c] = {'min': float(finite.min()) if len(finite) else None,
                         'max': float(finite.max()) if len(finite) else None}
    return {
        'rows': len(df), 'columns': len(df.columns),
        'dtypes': {c: str(t) for c, t in df.dtypes.items()},
        'missing': {c: int(v) for c, v in df.isna().sum().items()},
        'exact_duplicate_rows': int(df.duplicated().sum()),
        'duplicate_customer_ids': int(df.CustomerID.duplicated().sum()) if 'CustomerID' in df else None,
        'categories': {c: {str(k): int(v) for k, v in df[c].value_counts(dropna=False).items()}
                       for c in CATEGORIES if c in df},
        'numeric': ranges,
    }

def clean_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    missing = set(REQUIRED) - set(raw.columns)
    if missing:
        raise ValueError(f'Missing required columns: {sorted(missing)}')
    df = raw[REQUIRED].copy().reset_index(drop=True)
    issues = []
    def log(mask, field, action):
        for i in df.index[mask]:
            issues.append({'source_row': int(i)+2, 'field': field, 'action': action})
    # Only documented normalization; do not invent category equivalences.
    for c in ['CustomerID', *CATEGORIES]:
        original = df[c].astype('string')
        normalized = original.str.strip().replace('', pd.NA)
        if c in CATEGORIES:
            mapping = {v.casefold(): v for v in CATEGORIES[c]}
            normalized = normalized.str.casefold().map(mapping).astype('string')
        log(original.notna() & normalized.notna() & original.ne(normalized).fillna(False), c, 'canonicalized')
        if c in CATEGORIES:
            log(normalized.isna(), c, 'missing or unrecognized; kept unknown')
        df[c] = normalized
    for c in NUMERIC:
        original = df[c]
        values = pd.to_numeric(original, errors='coerce').astype(float)
        invalid = ~np.isfinite(values) | (values < 0)
        if c in ['Age', 'TenureMonths', 'SupportTickets']:
            invalid |= values.mod(1).ne(0)
        if c == 'Age':
            invalid |= values > 120
        log(invalid, c, 'missing/invalid; set null, no imputation')
        df[c] = values.mask(invalid)
    missing_ids = df.CustomerID.isna()
    log(missing_ids, 'CustomerID', 'excluded; missing identifier')
    df = df.loc[~missing_ids].copy()
    exact = df.duplicated()
    log(exact, 'record', 'excluded; exact duplicate after normalization')
    df = df.loc[~exact].copy()
    conflicts = df.CustomerID.duplicated(keep=False)
    log(conflicts, 'CustomerID', 'excluded all conflicting records; cannot determine latest')
    df = df.loc[~conflicts].copy()
    df['AnalysisID'] = df.CustomerID.map(lambda s: 'SYN-' + hashlib.sha256(s.encode()).hexdigest()[:12])
    # Keep incomplete accounts in the table but never treat an absent indicator as low risk.
    risk_inputs = ['TenureMonths', 'ContractType', 'MonthlyCharges']
    df['ScoreEligible'] = df[risk_inputs].notna().all(axis=1)
    df['EvaluationEligible'] = df.Churn.notna() & df.ScoreEligible
    df['Churned'] = df.Churn.map({'Yes': 1, 'No': 0}).astype('Int64')
    # Billing consistency is diagnostic only; no invented correction or churn predictor.
    df['ChargeDifference'] = (df.TotalCharges - df.MonthlyCharges*df.TenureMonths).round(2)
    return df.reset_index(drop=True), pd.DataFrame(issues, columns=['source_row','field','action'])

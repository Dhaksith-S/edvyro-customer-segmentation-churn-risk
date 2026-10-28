"""Mutually exclusive primary account cohorts; overlapping dimensions stay separate."""
import pandas as pd
from src.scoring import calculate_risk_score, assign_risk_band, explain_risk_score, contributions

SEGMENTS = {
    'Flexible - first year': 'Month-to-Month contract and tenure <=12 months',
    'Flexible - beyond first year': 'Month-to-Month contract and tenure >12 months',
    'Annual commitment': 'One Year contract at any known tenure',
    'Two-year commitment': 'Two Year contract at any known tenure',
    'Data review': 'Missing/unknown tenure or contract',
}

def tenure_band(tenure):
    if pd.isna(tenure): return 'Unknown'
    return 'New (0-5)' if tenure < 6 else 'Developing (6-12)' if tenure <= 12 else 'Established (13-24)' if tenure <= 24 else 'Long-term (25+)'

def assign_customer_segment(customer):
    t, c = customer.get('TenureMonths'), customer.get('ContractType')
    if pd.isna(t) or pd.isna(c) or t < 0: return 'Data review'
    if c == 'Month-to-Month': return 'Flexible - first year' if t <= 12 else 'Flexible - beyond first year'
    return {'One Year':'Annual commitment','Two Year':'Two-year commitment'}.get(c,'Data review')

def enrich_customers(df):
    out = df.copy()
    # Explicit lists preserve an empty frame's schema.
    records = out.to_dict('records')
    out['PrimarySegment'] = [assign_customer_segment(r) for r in records]
    out['TenureBand'] = [tenure_band(r['TenureMonths']) for r in records]
    out['SpendingBand'] = ['Unknown' if pd.isna(r['MonthlyCharges']) else 'High (>=100 INR)' if r['MonthlyCharges'] >=100 else 'Medium (70-<100 INR)' if r['MonthlyCharges'] >=70 else 'Low (<70 INR)' for r in records]
    out['RiskScore'] = pd.array([calculate_risk_score(r) for r in records],dtype='Int64')
    out['RiskBand'] = [assign_risk_band(r['RiskScore']) for r in out.to_dict('records')]
    out['ScoreExplanation'] = [explain_risk_score(r) for r in records]
    for key in ['TenurePoints','ContractPoints','ChargePoints']:
        out[key] = pd.array([(contributions(r) or {}).get(key) for r in records],dtype='Int64')
    return out

def summarize(df, group='PrimarySegment'):
    rows=[]
    for key, g in df.groupby(group, dropna=False, sort=True):
        labeled = g.Churned.dropna()
        high = g.RiskBand.eq('High')
        retained = g.Churned.eq(0).fillna(False)
        rows.append({group:key,'Definition':SEGMENTS.get(key,'Analytical cohort; not a primary segment'),
                     'Customers':len(g),'CustomerPct':100*len(g)/len(df) if len(df) else 0,
                     'LabeledCustomers':len(labeled),'ChurnedCustomers':int(labeled.sum()),
                     'ObservedChurnPct':100*float(labeled.mean()) if len(labeled) else None,
                     'AvgTenureMonths':g.TenureMonths.mean(),'AvgMonthlyChargesINR':g.MonthlyCharges.mean(),
                     'MonthlyChargeSumINR':g.MonthlyCharges.sum(min_count=1),
                     'RetainedMonthlyChargeSumINR':g.loc[retained,'MonthlyCharges'].sum(min_count=1) if retained.any() else 0,
                     'HighRiskChargeSumINR':g.loc[high,'MonthlyCharges'].sum(min_count=1) if high.any() else 0,
                     'ScoredCustomers':int(g.RiskScore.notna().sum()),'AvgRiskScore':g.RiskScore.mean(),
                     'MinRiskScore':g.RiskScore.min(),'MedianRiskScore':g.RiskScore.median(),'MaxRiskScore':g.RiskScore.max(),
                     'HighRiskCustomers':int(high.sum()),'AvgSupportTickets90Days':g.SupportTickets.mean(),
                     'SmallSample':len(g)<5})
    return pd.DataFrame(rows).sort_values(['HighRiskCustomers','Customers'],ascending=False).reset_index(drop=True) if rows else pd.DataFrame(columns=[group,'Customers'])

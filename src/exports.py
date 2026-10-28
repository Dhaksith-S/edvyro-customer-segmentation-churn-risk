"""Data exports share one safe, de-identified customer schema."""
import json
from pathlib import Path
import pandas as pd
from src.segmentation import summarize

PUBLIC_COLUMNS = ['AnalysisID','TenureMonths','SubscriptionType','ContractType','PaymentMethod','MonthlyCharges',
                  'SupportTickets','PrimarySegment','TenureBand','SpendingBand','ScoreEligible','EvaluationEligible',
                  'RiskScore','RiskBand','TenurePoints','ContractPoints','ChargePoints','ScoreExplanation','Churned']

def export_outputs(df, destination):
    dest=Path(destination); dest.mkdir(parents=True,exist_ok=True)
    safe=df[PUBLIC_COLUMNS]
    safe.to_csv(dest/'customer_segments.csv',index=False,float_format='%.2f')
    safe.to_csv(dest/'customer_risk_scores.csv',index=False,float_format='%.2f')
    for group, filename in [('PrimarySegment','segment_summary'),('RiskBand','risk_band_summary'),('ContractType','contract_summary'),('TenureBand','tenure_summary'),('PaymentMethod','payment_summary')]:
        summarize(df,group).to_csv(dest/f'{filename}.csv',index=False,float_format='%.8f')
    data=json.loads(safe.to_json(orient='records'))
    return data

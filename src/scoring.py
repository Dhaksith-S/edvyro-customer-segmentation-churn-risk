"""Fixed expert-assumption index v1; not a trained model or probability."""
from __future__ import annotations
import math
import pandas as pd

SCORE_VERSION = '1.0'
INPUTS = ('TenureMonths', 'ContractType', 'MonthlyCharges')
RULES = [
    {'signal':'Tenure', 'feature':'TenureMonths', 'condition':'0 <= months < 6: 35; 6 <= months <= 12: 25; 12 < months <= 24: 10; >24: 0', 'maximum':35, 'reason':'Early lifecycle needs onboarding; fixed planning assumption'},
    {'signal':'Commitment', 'feature':'ContractType', 'condition':'Month-to-Month: 45; One Year: 20; Two Year: 0', 'maximum':45, 'reason':'Shorter commitment permits an easier exit; association not causation'},
    {'signal':'Charge exposure', 'feature':'MonthlyCharges', 'condition':'INR >=100: 20; 70 <= INR <100: 10; 0 <= INR <70: 0', 'maximum':20, 'reason':'Absolute bill exposure may warrant a value review; affordability is unknown'},
]

def _number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) and value >= 0 else None
    except (TypeError, ValueError):
        return None

def contributions(customer) -> dict[str, int] | None:
    tenure, charges = _number(customer.get('TenureMonths')), _number(customer.get('MonthlyCharges'))
    contract = customer.get('ContractType')
    if tenure is None or tenure % 1 != 0 or charges is None or pd.isna(contract) or contract not in ['Month-to-Month','One Year','Two Year']:
        return None
    return {
        'TenurePoints': 35 if tenure < 6 else 25 if tenure <= 12 else 10 if tenure <= 24 else 0,
        'ContractPoints': {'Month-to-Month':45,'One Year':20,'Two Year':0}[contract],
        'ChargePoints': 20 if charges >= 100 else 10 if charges >= 70 else 0,
    }

def calculate_risk_score(customer) -> int | None:
    parts = contributions(customer)
    return None if parts is None else max(0, min(100, sum(parts.values())))

def assign_risk_band(score) -> str:
    if score is None or pd.isna(score):
        return 'Unscored'
    if not isinstance(score, (int, float)) or not math.isfinite(float(score)) or score < 0 or score > 100:
        raise ValueError('Score must be between 0 and 100')
    return 'High' if score >= 60 else 'Medium' if score >= 30 else 'Low'

def explain_risk_score(customer) -> str:
    parts = contributions(customer)
    if parts is None:
        return 'Unscored: tenure, contract, or monthly charges missing/invalid; data review required.'
    return (f"Tenure {float(customer['TenureMonths']):g} months: +{parts['TenurePoints']}; "
            f"contract {customer['ContractType']}: +{parts['ContractPoints']}; "
            f"monthly charge INR {float(customer['MonthlyCharges']):.2f}: +{parts['ChargePoints']}; "
            f"total {sum(parts.values())}/100. Assumption-based index, not a probability.")

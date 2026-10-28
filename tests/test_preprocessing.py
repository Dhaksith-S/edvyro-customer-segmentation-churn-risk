import json
import numpy as np
import pandas as pd
import pytest
from src.preprocessing import clean_data,profile_data
from src.segmentation import enrich_customers

@pytest.mark.parametrize('identifier',[None,'','   '])
def test_missing_identifiers_excluded(frame,identifier):
    frame.loc[0,'CustomerID']=identifier
    clean,log=clean_data(frame)
    assert len(clean)==0 and log.action.str.contains('missing identifier').any()

def test_exact_duplicates_removed(frame):
    clean,log=clean_data(pd.concat([frame,frame],ignore_index=True))
    assert len(clean)==1 and log.action.str.contains('exact duplicate').sum()==1

def test_conflicting_ids_all_quarantined(frame):
    other=frame.copy();other.loc[0,'TenureMonths']=14
    clean,log=clean_data(pd.concat([frame,other],ignore_index=True))
    assert clean.empty and log.action.str.contains('conflicting').sum()==2

@pytest.mark.parametrize('field,value',[('TenureMonths',None),('TenureMonths',-1),('TenureMonths',2.5),('MonthlyCharges',-1),('MonthlyCharges','bad'),('MonthlyCharges',np.inf),('ContractType','Quarterly')])
def test_invalid_core_inputs_never_look_low_risk(frame,field,value):
    frame[field]=frame[field].astype(object);frame.loc[0,field]=value
    clean,log=clean_data(frame); scored=enrich_customers(clean)
    assert len(scored)==1 and not scored.ScoreEligible.iloc[0]
    assert pd.isna(scored.RiskScore.iloc[0]) and scored.RiskBand.iloc[0]=='Unscored'
    assert len(log)>0

@pytest.mark.parametrize('field,value',[('PaymentMethod','Cash'),('PaymentMethod',None),('Churn',None),('Churn','Maybe'),('SubscriptionType','Trial'),('Gender','Unrecognized'),('Age',-1),('Age',121),('SupportTickets',2.5)])
def test_unknown_descriptive_values_do_not_block_score(frame,field,value):
    frame[field]=frame[field].astype(object);frame.loc[0,field]=value
    clean,log=clean_data(frame)
    assert clean.ScoreEligible.iloc[0] and len(log)>0
    assert pd.isna(clean[field].iloc[0])
    if field=='Churn': assert not clean.EvaluationEligible.iloc[0]

def test_recognized_case_and_whitespace_normalize(frame):
    frame.loc[0,'ContractType']=' month-to-month ';frame.loc[0,'Churn']=' YES '
    clean,log=clean_data(frame)
    assert clean.ContractType.iloc[0]=='Month-to-Month' and clean.Churned.iloc[0]==1
    assert len(log)==2

def test_incomplete_schema_fails(frame):
    with pytest.raises(ValueError,match='Missing required'):clean_data(frame.drop(columns='TenureMonths'))

def test_invalid_numeric_profile_is_serializable(frame):
    frame['MonthlyCharges']='bad'
    profile=profile_data(frame)
    assert profile['numeric']['MonthlyCharges']['min'] is None
    json.dumps(profile,allow_nan=False)

def test_no_silent_billing_rewrite(frame):
    frame.loc[0,'TotalCharges']=100
    clean,_=clean_data(frame)
    assert clean.TotalCharges.iloc[0]==100 and abs(clean.ChargeDifference.iloc[0])>0

import re
import itertools
import pandas as pd
import pytest
from src.scoring import calculate_risk_score,contributions,assign_risk_band,explain_risk_score

@pytest.mark.parametrize('tenure,points',[(0,35),(5,35),(6,25),(12,25),(13,10),(24,10),(25,0),(1000,0)])
def test_tenure_boundaries(customer,tenure,points):
    customer.update(TenureMonths=tenure,ContractType='Two Year',MonthlyCharges=0)
    assert calculate_risk_score(customer)==points

@pytest.mark.parametrize('charge,points',[(0,0),(69.99,0),(70,10),(99.99,10),(100,20),(99999,20)])
def test_charge_boundaries(customer,charge,points):
    customer.update(TenureMonths=25,ContractType='Two Year',MonthlyCharges=charge)
    assert calculate_risk_score(customer)==points

@pytest.mark.parametrize('contract,points',[('Month-to-Month',45),('One Year',20),('Two Year',0)])
def test_contract_awards(customer,contract,points):
    customer.update(TenureMonths=25,ContractType=contract,MonthlyCharges=0)
    assert calculate_risk_score(customer)==points

@pytest.mark.parametrize('score,band',[(0,'Low'),(29,'Low'),(30,'Medium'),(59,'Medium'),(60,'High'),(100,'High'),(None,'Unscored'),(float('nan'),'Unscored')])
def test_band_boundaries(score,band):assert assign_risk_band(score)==band

@pytest.mark.parametrize('score',[-1,101,float('inf'),'High'])
def test_bad_scores_fail(score):
    with pytest.raises(ValueError):assign_risk_band(score)

@pytest.mark.parametrize('field,value',[('TenureMonths',None),('TenureMonths',-1),('TenureMonths',1.5),('MonthlyCharges',None),('MonthlyCharges',float('inf')),('MonthlyCharges',-1),('ContractType','Quarterly'),('ContractType',pd.NA)])
def test_missing_and_unknown_safe(customer,field,value):
    customer[field]=value
    assert calculate_risk_score(customer) is None and explain_risk_score(customer).startswith('Unscored:')

def test_min_max_reproducible_and_explanations(customer):
    seen=[]
    for t,c,m in itertools.product([0,5,6,12,13,24,25,72],['Month-to-Month','One Year','Two Year'],[0,69.99,70,99.99,100,500]):
        r={**customer,'TenureMonths':t,'ContractType':c,'MonthlyCharges':m}
        score=calculate_risk_score(r);seen.append(score)
        assert score==calculate_risk_score(r) and 0<=score<=100
        assert sum(contributions(r).values())==score
        assert sum(map(int,re.findall(r'\+(\d+)',explain_risk_score(r))))==score
    assert min(seen)==0 and max(seen)==100

@pytest.mark.parametrize('field,value',[('Churn','No'),('Churned',1),('SupportTickets',999),('PaymentMethod','UPI'),('TotalCharges',0),('Age',95),('Gender','Male'),('CustomerID','DIFFERENT')])
def test_no_target_or_excluded_feature_leakage(customer,field,value):
    assert calculate_risk_score(customer)==calculate_risk_score({**customer,field:value})

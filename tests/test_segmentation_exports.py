from pathlib import Path
import pandas as pd
import pytest
from src.preprocessing import clean_data
from src.segmentation import enrich_customers,assign_customer_segment,summarize,tenure_band
from src.exports import export_outputs,PUBLIC_COLUMNS

@pytest.mark.parametrize('t,c,expected',[(0,'Month-to-Month','Flexible - first year'),(12,'Month-to-Month','Flexible - first year'),(13,'Month-to-Month','Flexible - beyond first year'),(24,'One Year','Annual commitment'),(48,'Two Year','Two-year commitment'),(None,'One Year','Data review'),(12,'Quarterly','Data review')])
def test_segment_boundary(t,c,expected):assert assign_customer_segment({'TenureMonths':t,'ContractType':c})==expected

@pytest.mark.parametrize('t,expected',[(0,'New (0-5)'),(5,'New (0-5)'),(6,'Developing (6-12)'),(12,'Developing (6-12)'),(13,'Established (13-24)'),(24,'Established (13-24)'),(25,'Long-term (25+)'),(None,'Unknown')])
def test_tenure_dimension(t,expected):assert tenure_band(t)==expected

@pytest.mark.parametrize('label',['No','Yes',None])
def test_single_class_or_no_labels_safe(frame,label):
    frame.loc[0,'Churn']=label
    scored=enrich_customers(clean_data(frame)[0]);summary=summarize(scored)
    assert scored.RiskScore.iloc[0]==70
    assert summary.LabeledCustomers.iloc[0]==(0 if label is None else 1)
    if label is None: assert pd.isna(summary.ObservedChurnPct.iloc[0])
    else: assert summary.ObservedChurnPct.iloc[0]==(100 if label=='Yes' else 0)

def test_empty_pipeline_schema_and_exports(frame,tmp_path):
    clean,log=clean_data(frame.iloc[:0]);scored=enrich_customers(clean)
    assert scored.empty and summarize(scored).empty and log.empty
    data=export_outputs(scored,tmp_path)
    assert data==[] and list(pd.read_csv(tmp_path/'customer_segments.csv'))==PUBLIC_COLUMNS

def test_output_population_reconciles():
    root=Path(__file__).resolve().parents[1]
    rows=pd.read_csv(root/'outputs/customer_segments.csv')
    summary=pd.read_csv(root/'outputs/segment_summary.csv')
    bands=pd.read_csv(root/'outputs/risk_band_summary.csv')
    assert len(rows)==15 and rows.AnalysisID.is_unique
    assert set(PUBLIC_COLUMNS)==set(rows.columns)
    assert not {'CustomerID','Gender','Age','TotalCharges'}&set(rows.columns)
    assert rows.PrimarySegment.notna().all()
    assert summary.Customers.sum()==len(rows) and summary.CustomerPct.sum()==pytest.approx(100)
    assert summary.ChurnedCustomers.sum()==rows.Churned.sum()==7
    for s in [summary,bands]:assert s.MonthlyChargeSumINR.sum()==pytest.approx(rows.MonthlyCharges.sum())
    assert rows.MonthlyCharges.sum()==pytest.approx(1269.85)
    assert rows.loc[rows.RiskBand.eq('High'),'MonthlyCharges'].sum()==pytest.approx(409.93)
    assert len(rows.loc[rows.RiskBand.eq('High')&rows.Churned.eq(0)])==0
    assert rows.RiskScore.equals(rows[['TenurePoints','ContractPoints','ChargePoints']].sum(axis=1))

def test_public_scores_reproduce_without_source():
    from src.scoring import calculate_risk_score
    root=Path(__file__).resolve().parents[1]
    rows=pd.read_csv(root/'outputs/customer_risk_scores.csv')
    assert [calculate_risk_score(r) for r in rows.to_dict('records')]==rows.RiskScore.tolist()

def test_dictionary_covers_all_csv_columns():
    root=Path(__file__).resolve().parents[1]
    fields=set(pd.read_csv(root/'outputs/data_dictionary.csv').Field)
    for file in (root/'outputs').glob('*.csv'):
        if file.name=='data_dictionary.csv':continue
        assert set(pd.read_csv(file).columns)<=fields, file.name

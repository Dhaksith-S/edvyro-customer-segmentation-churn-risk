"""Consistent, fully labelled retrospective figures, including sparse/empty cohorts."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from src.segmentation import summarize

def create_figures(df, destination):
    dest=Path(destination); dest.mkdir(parents=True,exist_ok=True)
    sns.set_theme(style='whitegrid',font_scale=1.05,rc={'axes.spines.top':False,'axes.spines.right':False})
    colors=['#176b87','#7262b5','#0c8c81']
    paths={}
    def save(name, fig):
        fig.tight_layout(); path=dest/f'{name}.png'; fig.savefig(path,dpi=150,bbox_inches='tight'); plt.close(fig); paths[name]=path
    fig,ax=plt.subplots(figsize=(7,4)); counts=df.Churned.value_counts().reindex([0,1],fill_value=0)
    ax.bar(['Retained','Churned'],counts,color=colors[:2]); ax.set(title='Observed churn in the synthetic sample',ylabel='Customers (count)'); ax.set_ylim(0,max(1,counts.max()+1))
    for i,n in enumerate(counts): ax.text(i,n+.1,str(n),ha='center')
    save('churn_distribution',fig)
    fig,ax=plt.subplots(figsize=(7,4)); ax.hist(df.TenureMonths.dropna(),bins=[0,6,13,25,49,73],color=colors[0],edgecolor='white')
    ax.set(title='Customer tenure at observation',xlabel='Tenure (months)',ylabel='Customers (count)'); save('tenure_distribution',fig)
    for group,name in [('ContractType','churn_by_contract'),('PaymentMethod','churn_by_payment')]:
        s=summarize(df,group); fig,ax=plt.subplots(figsize=(8,4))
        if not s.empty:
            ax.barh(s[group].fillna('Unknown'),s.ObservedChurnPct,color=colors[0]); ax.set_xlim(0,115)
            for i,r in s.iterrows(): ax.text((r.ObservedChurnPct or 0)+1,i,f'{r.ChurnedCustomers}/{r.LabeledCustomers}',va='center')
        ax.set(title=f'Observed churn by {"contract" if group=="ContractType" else "payment method"}',xlabel='Observed churn (%) - annotations show churned / labelled customers'); save(name,fig)
    s=summarize(df); fig,ax=plt.subplots(figsize=(9,4))
    if not s.empty: ax.barh(s.PrimarySegment,s.Customers,color=colors[0])
    ax.set(title='Mutually exclusive primary customer segments',xlabel='Customers (count)'); save('segment_counts',fig)
    fig,ax=plt.subplots(figsize=(7,4)); ax.hist(df.RiskScore.dropna().astype(float),bins=range(0,111,10),color=colors[1],edgecolor='white')
    ax.axvline(30,color=colors[0],linestyle='--',label='Medium starts at 30'); ax.axvline(60,color=colors[2],linestyle='--',label='High starts at 60'); ax.legend(fontsize=9)
    ax.set(title='Rule-based risk index distribution (not probability)',xlabel='Risk index (0-100 points)',ylabel='Customers (count)',xlim=(0,100)); save('risk_distribution',fig)
    s=summarize(df,'RiskBand'); fig,ax=plt.subplots(figsize=(7,4))
    s=s.set_index('RiskBand').reindex(['Low','Medium','High']) if not s.empty else s
    if not s.empty:
        ax.bar(s.index,s.ObservedChurnPct,color=colors)
        for i,(_,r) in enumerate(s.iterrows()):
            if pd.notna(r.LabeledCustomers): ax.text(i,(r.ObservedChurnPct or 0)+2,f'{int(r.ChurnedCustomers)}/{int(r.LabeledCustomers)}',ha='center')
    ax.set(title='Retrospective churn by rule-based risk band',ylabel='Observed churn (%)',ylim=(0,115)); save('risk_band_churn',fig)
    fig,ax=plt.subplots(figsize=(9,4)); ct=pd.crosstab(df.PrimarySegment,df.RiskBand).reindex(columns=['Low','Medium','High'],fill_value=0)
    if ct.size: sns.heatmap(ct,annot=True,fmt='d',cmap='Blues',cbar_kws={'label':'Customers (count)'},ax=ax)
    ax.set(title='Segment and risk-band membership',xlabel='Risk band',ylabel='Primary segment'); save('segment_risk_heatmap',fig)
    fig,ax=plt.subplots(figsize=(7,4)); s=summarize(df,'RiskBand')
    if not s.empty: ax.bar(s.RiskBand,s.MonthlyChargeSumINR,color=colors[2])
    ax.set(title='Recorded monthly-charge sums, including churned accounts',ylabel='Sum of monthly charges (INR)',xlabel='Risk band'); save('charge_exposure',fig)
    for group,name in [('ContractType','scores_by_contract'),('TenureBand','scores_by_tenure')]:
        fig,ax=plt.subplots(figsize=(9,4))
        for i,(label,g) in enumerate(df.groupby(group,dropna=False,sort=True)):
            ax.scatter(g.RiskScore.astype(float),[i]*len(g),s=75,color=colors[1],alpha=.65)
            ax.text(101,i,f'n={len(g)}',va='center',fontsize=9)
        groups=[str(k) for k,_ in df.groupby(group,dropna=False,sort=True)]
        ax.set_yticks(range(len(groups)),groups); ax.set(xlim=(-3,110),xlabel='Risk index (points; overlapping markers possible)',title=f'Risk index by {"contract" if group=="ContractType" else "tenure cohort"}')
        save(name,fig)
    return paths

/* All analytic elements consume the same filtered rows. No remote dependencies. */
'use strict';
const REPOSITORY = 'https://github.com/Dhaksith-S/edvyro-customer-segmentation-churn-risk';
let records = [], current = [];
const $ = id => document.getElementById(id);
const fmt = (v, digits=0) => Number(v).toLocaleString('en-IN', {minimumFractionDigits:digits, maximumFractionDigits:digits});
const safe = value => String(value ?? 'Unknown').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const sum = (rows, key) => rows.reduce((n,r)=>n+(Number.isFinite(r[key]) ? r[key] : 0),0);
const known = (rows,key) => rows.filter(r=>Number.isFinite(r[key]));
function groups(rows,key,order) {
  const keys = order || [...new Set(rows.map(r=>r[key] ?? 'Unknown'))].sort();
  return keys.map(k=>[k,rows.filter(r=>(r[key] ?? 'Unknown')===k)]);
}
function bars(id, items, maximum=100) {
  $(id).innerHTML = items.length ? items.map(({name,value,text,kind=''})=>`<div class="bar" role="img" aria-label="${safe(name)}: ${safe(text)}"><div class="bar-head"><span>${safe(name)}</span><span>${safe(text)}</span></div><div class="track" aria-hidden="true"><div class="fill ${safe(kind)}" style="width:${Math.max(0,Math.min(100,maximum ? value/maximum*100 : 0))}%"></div></div></div>`).join('') : '<p class="footnote">No matching customers.</p>';
}
function explain(id) {
  const r=current.find(r=>r.AnalysisID===id); if(!r) return;
  $('explanation').innerHTML=`<p><strong>${safe(r.AnalysisID)} · ${safe(r.RiskScore)} / 100 points</strong></p><p>${safe(r.ScoreExplanation)}</p><p>${r.Churned===1 ? 'Already churned: historical investigation or separate win-back research; exclude from an active retention queue.' : r.Churned===0 ? 'Retained in this snapshot. Current status and contact permission must be verified before outreach.' : 'Outcome unknown: verify account status before deciding outreach eligibility.'}</p>`;
}
function render() {
  const filters=[...$('filters').querySelectorAll('select')];
  current=records.filter(r=>filters.every(f=>!f.value||r[f.name]===f.value));
  const rows=current, n=rows.length, labeled=known(rows,'Churned'), churn=sum(labeled,'Churned');
  const scored=known(rows,'RiskScore');
  $('count').textContent=fmt(n); $('share').textContent=`${fmt(records.length ? 100*n/records.length : 0,1)}% of full sample`;
  $('churn').textContent=labeled.length?`${fmt(100*churn/labeled.length,1)}%`:'—';
  $('churn-denom').textContent=`${fmt(churn)} churned / ${fmt(labeled.length)} labelled`;
  $('score').textContent=scored.length?fmt(sum(scored,'RiskScore')/scored.length,1):'—';
  $('charges').textContent=known(rows,'MonthlyCharges').length ? fmt(sum(rows,'MonthlyCharges'),2) : '—';
  $('active').textContent=fmt(rows.filter(r=>r.RiskBand==='High'&&r.Churned===0).length);
  $('status').textContent=`Showing ${n} of ${records.length} synthetic customers.${n>0&&n<5?' Small sample: fewer than five matching accounts.':''}`;
  $('empty').hidden=!!n;
  bars('segment-chart',groups(rows,'PrimarySegment').map(([name,g])=>({name,value:g.length,text:`${g.length} (${fmt(n ? 100*g.length/n : 0,1)}%)${g.length<5?' · small n':''}`})),n);
  const bandGroups=groups(rows,'RiskBand',['Low','Medium','High']);
  bars('risk-chart',bandGroups.map(([name,g])=>{const l=known(g,'Churned'), c=sum(l,'Churned');return {name,value:l.length?100*c/l.length:0,text:l.length?`${c}/${l.length} · ${fmt(100*c/l.length,1)}%${g.length<5?' · small n':''}`:'0 labelled · no rate',kind:name.toLowerCase()};}));
  const scores=groups(scored,'RiskScore',[...new Set(scored.map(r=>r.RiskScore))].sort((a,b)=>a-b));
  bars('score-chart',scores.map(([s,g])=>({name:`${s} points`,value:g.length,text:`${g.length} customer${g.length===1?'':'s'}`,kind:'medium'})),n);
  bars('revenue-chart',bandGroups.map(([name,g])=>({name,value:sum(g,'MonthlyCharges'),text:`INR ${fmt(sum(g,'MonthlyCharges'),2)} · n=${g.length}`,kind:name.toLowerCase()})),sum(rows,'MonthlyCharges'));
  bars('contract-chart',groups(rows,'ContractType').map(([name,g])=>{const l=known(g,'Churned'),c=sum(l,'Churned');return {name,value:l.length?100*c/l.length:0,text:l.length?`${c}/${l.length} · ${fmt(100*c/l.length,1)}%`:'No labelled accounts'};}));
  const tenure=groups(rows,'TenureBand',['New (0-5)','Developing (6-12)','Established (13-24)','Long-term (25+)']).filter(([,g])=>g.length);
  const demand=tenure.map(([name,g])=>{const l=known(g,'SupportTickets'),mean=l.length?sum(l,'SupportTickets')/l.length:0;return {name,value:mean,text:`${l.length?fmt(mean,2):'—'} tickets · n=${l.length}`,kind:'low'};});
  bars('tenure-chart',demand,Math.max(1,...demand.map(d=>d.value)));
  const sorted=[...rows].sort((a,b)=>(a.Churned===0?0:1)-(b.Churned===0?0:1)||(b.RiskScore??-1)-(a.RiskScore??-1)||(b.MonthlyCharges??0)-(a.MonthlyCharges??0));
  $('customers').innerHTML=sorted.map(r=>`<tr><td><button class="account-button" data-id="${safe(r.AnalysisID)}">${safe(r.AnalysisID)}</button></td><td>${safe(r.PrimarySegment)}</td><td>${r.RiskScore??'—'}</td><td><span class="pill ${safe(r.RiskBand.toLowerCase())}">${safe(r.RiskBand)}</span></td><td>${Number.isFinite(r.MonthlyCharges)?fmt(r.MonthlyCharges,2):'—'}</td><td>${r.Churned===1?'Already churned':r.Churned===0?'Retained':'Unknown'}</td></tr>`).join('') || '<tr><td colspan="6">No matching customers.</td></tr>';
  if(sorted.length) explain(sorted[0].AnalysisID); else $('explanation').textContent='No account is selected. Reset filters to inspect scores.';
}
document.querySelectorAll('[data-file]').forEach(a=>a.href=`${REPOSITORY}/blob/main/${a.dataset.file}`);
$('repository').href=REPOSITORY;
$('filters').addEventListener('change',render);
$('reset').addEventListener('click',()=>{$('filters').reset();render();});
$('customers').addEventListener('click',e=>{const b=e.target.closest('[data-id]');if(b)explain(b.dataset.id);});
fetch('data.json').then(r=>{if(!r.ok)throw new Error(`Data HTTP ${r.status}`);return r.json();}).then(data=>{
  records=data;
  [...$('filters').querySelectorAll('select')].forEach(f=>{[...new Set(data.map(r=>r[f.name]))].filter(v=>v!==null).sort().forEach(v=>f.add(new Option(v,v)));});
  render();
}).catch(()=>{$('error').hidden=false;$('status').textContent='Unable to load analysis data. Downloadable supporting materials remain available.';});

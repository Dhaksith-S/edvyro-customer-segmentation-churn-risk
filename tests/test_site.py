"""Real browser checks against a local HTTP server; data assertions use Python exports."""
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import json
import os
from pathlib import Path
from threading import Thread
import pytest
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'docs/data.json').read_text())

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

@pytest.fixture(scope='module')
def site_url():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT/'docs')))
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown();server.server_close();thread.join()

@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as p:
        kwargs={'headless':True}
        # Use an existing installed Chromium on this Windows workstation.
        if os.name=='nt':
            candidates=list((Path(os.environ['LOCALAPPDATA'])/'ms-playwright').glob('chromium-*/chrome-win64/chrome.exe'))
            if candidates:kwargs['executable_path']=str(sorted(candidates)[-1])
        b=p.chromium.launch(**kwargs)
        yield b
        b.close()

@pytest.fixture
def page(browser,site_url):
    p=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
    p.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    response=p.goto(site_url);assert response.status==200
    p.wait_for_function("document.getElementById('count').textContent === '15'")
    yield p
    p.close()
    assert errors==[], errors

def assert_population(page,rows):
    n=len(rows);assert page.locator('#count').inner_text()==str(n)
    assert page.locator('#share').inner_text()==f'{100*n/len(DATA):.1f}% of full sample'
    labeled=[r for r in rows if r['Churned'] is not None]
    churn=sum(r['Churned'] for r in labeled)
    expected=f'{100*churn/len(labeled):.1f}%' if labeled else '—'
    assert page.locator('#churn').inner_text()==expected
    expected_charge=f"{sum(r['MonthlyCharges'] for r in rows):,.2f}" if n else '—'
    assert page.locator('#charges').inner_text()==expected_charge
    scored=[r for r in rows if r['RiskScore'] is not None]
    expected_score=f"{sum(r['RiskScore'] for r in scored)/len(scored):.1f}" if scored else '—'
    assert page.locator('#score').inner_text()==expected_score
    assert page.locator('#active').inner_text()==str(sum(r['RiskBand']=='High' and r['Churned']==0 for r in rows))
    visible=page.locator('#customers [data-id]').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.id)')
    assert set(visible)=={r['AnalysisID'] for r in rows}
    assert len(visible)==n
    risk_text=page.locator('#risk-chart .bar-head span:last-child').all_inner_texts()
    charge_text=page.locator('#revenue-chart .bar-head span:last-child').all_inner_texts()
    for i,band in enumerate(['Low','Medium','High']):
        g=[r for r in rows if r['RiskBand']==band]
        l=[r for r in g if r['Churned'] is not None]
        c=sum(r['Churned'] for r in l)
        assert (f'{c}/{len(l)}' if l else '0 labelled') in risk_text[i]
        assert charge_text[i]==f"INR {sum(r['MonthlyCharges'] for r in g):,.2f} · n={len(g)}"
    if n:
        segment_counts=page.locator('#segment-chart .bar-head span:last-child').all_inner_texts()
        assert sum(int(t.split()[0]) for t in segment_counts)==n
        score_counts=page.locator('#score-chart .bar-head span:last-child').all_inner_texts()
        assert sum(int(t.split()[0]) for t in score_counts)==n
    assert page.locator('#empty').is_visible()==(n==0)

def test_initial_metrics_assets_and_charts(page):
    assert_population(page,DATA)
    for chart in ['segment','risk','score','revenue','contract','tenure']:
        assert page.locator(f'#{chart}-chart .bar').count()>0
    assert page.locator('h1').is_visible()
    assert page.locator('a[data-file]').count()==7

@pytest.mark.parametrize('selector,key',[('#contract','ContractType'),('#tenure','TenureBand'),('#payment','PaymentMethod'),('#risk','RiskBand'),('#segment','PrimarySegment')])
def test_every_filter_value_updates_common_population(page,selector,key):
    for value in sorted(set(r[key] for r in DATA)):
        page.locator(selector).select_option(value)
        assert_population(page,[r for r in DATA if r[key]==value])
    page.locator('#reset').click();assert_population(page,DATA)

def test_combined_filters_empty_state_and_reset(page):
    page.locator('#contract').select_option('Two Year');page.locator('#risk').select_option('High')
    assert_population(page,[])
    assert 'No matching customers' in page.locator('#customers').inner_text()
    page.locator('#reset').click();assert_population(page,DATA)
    assert all(value=='' for value in page.locator('#filters select').evaluate_all('(nodes)=>nodes.map(n=>n.value)'))

def test_score_explanation_interaction(page):
    target=DATA[0];page.locator(f'[data-id="{target["AnalysisID"]}"]').click()
    assert target['ScoreExplanation'] in page.locator('#explanation').inner_text()
    assert 'Already churned' in page.locator('#explanation').inner_text()

def test_mobile_layout_and_visual_evidence(page):
    (ROOT/'tmp').mkdir(exist_ok=True)
    page.screenshot(path=str(ROOT/'tmp/report-desktop.png'),full_page=True)
    page.screenshot(path=str(ROOT/'tmp/report-preview.png'))
    page.set_viewport_size({'width':360,'height':800})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    assert 'patterns to' in page.locator('h1').inner_text()
    assert 'accounts. One' in page.locator('.study-note strong').inner_text()
    assert page.locator('#reset').is_visible()
    page.screenshot(path=str(ROOT/'tmp/report-mobile.png'),full_page=True)
    # Filter interactions remain usable at the required narrow width.
    page.locator('#contract').select_option('One Year')
    assert_population(page,[r for r in DATA if r['ContractType']=='One Year'])

def test_data_load_failure_is_visible(browser,site_url):
    p=browser.new_page();p.route('**/data.json',lambda route:route.abort())
    p.goto(site_url);p.wait_for_selector('#error',state='visible')
    assert 'could not load' in p.locator('#error').inner_text()
    assert p.locator('#repository').get_attribute('href').startswith('https://github.com/')
    p.close()

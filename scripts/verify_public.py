"""Unauthenticated HTTP, asset, data and browser smoke verification of the live release."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import subprocess
import requests
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
REPO='https://github.com/Dhaksith-S/edvyro-customer-segmentation-churn-risk'
LIVE='https://dhaksith-s.github.io/edvyro-customer-segmentation-churn-risk/'
REVISION=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
FILES=['README.md','notebooks/Customer_Segmentation_and_Churn_Risk.ipynb','outputs/customer_segments.csv',
       'outputs/segment_summary.csv','outputs/customer_risk_scores.csv','reports/Customer_Retention_Recommendation_Memo.md',
       'reports/Customer_Retention_Recommendation_Memo.pdf','reports/figures/report_preview.png']

def canonical(content,path):
    # Git normalizes text to LF; binary artifacts must remain byte-for-byte identical.
    return content if Path(path).suffix in {'.pdf','.png'} else content.replace(b'\r\n',b'\n')

def check(path):
    # Immutable commit URLs avoid stale CDN responses for a recently updated main ref.
    url=REPO if path=='' else f'https://raw.githubusercontent.com/Dhaksith-S/edvyro-customer-segmentation-churn-risk/{REVISION}/{path}'
    response=requests.get(url,timeout=30);response.raise_for_status()
    if path:
        assert hashlib.sha256(canonical(response.content,path)).digest()==hashlib.sha256(canonical((ROOT/path).read_bytes(),path)).digest(),path
    return {'url':url,'http_status':response.status_code,'bytes':len(response.content)}

def main(write_report=True):
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(check,['',*FILES]))
    for asset in ['', 'style.css','app.js','data.json','icon.svg']:
        response=requests.get(LIVE+asset,timeout=30);response.raise_for_status()
        if asset:assert canonical(response.content,asset)==canonical((ROOT/'docs'/asset).read_bytes(),asset),asset
        results.append({'url':response.url,'http_status':response.status_code,'bytes':len(response.content)})
    with sync_playwright() as p:
        kwargs={'headless':True}
        if os.name=='nt':
            paths=list((Path(os.environ['LOCALAPPDATA'])/'ms-playwright').glob('chromium-*/chrome-win64/chrome.exe'))
            if paths:kwargs['executable_path']=str(sorted(paths)[-1])
        browser=p.chromium.launch(**kwargs);page=browser.new_page(viewport={'width':1440,'height':1000})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        assert page.goto(LIVE).status==200
        page.wait_for_function("document.getElementById('count').textContent === '15'")
        assert page.locator('#churn').inner_text()=='46.7%'
        assert page.locator('#active').inner_text()=='0'
        assert page.locator('#segment-chart .bar').count()==4
        for field in ['contract','tenure','payment','risk','segment']:
            options=page.locator(f'#{field} option').all()
            assert len(options)>1
            page.locator(f'#{field}').select_option(index=1)
            assert int(page.locator('#count').inner_text())>0
            page.locator('#reset').click()
        page.locator('#contract').select_option('Two Year');page.locator('#risk').select_option('High')
        assert page.locator('#empty').is_visible()
        page.locator('#reset').click();assert page.locator('#count').inner_text()=='15'
        page.locator('nav a[href="#methodology"]').click()
        assert page.evaluate('location.hash')=='#methodology'
        page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(ROOT/'tmp/live-report-desktop.png'),full_page=True)
        page.set_viewport_size({'width':360,'height':800})
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        assert 'patterns to' in page.locator('h1').inner_text()
        assert 'accounts. One' in page.locator('.study-note strong').inner_text()
        page.screenshot(path=str(ROOT/'tmp/live-report-mobile.png'))
        links=[a.get_attribute('href') for a in page.locator('[data-file]').all()]
        for url in links:
            r=requests.get(url,timeout=30);r.raise_for_status()
            assert 'Sign in to GitHub' not in r.text[:1000]
        assert errors==[],errors
        # Public GitHub README/notebook pages must be accessible without a signed-in browser.
        response=page.goto(REPO);assert response.status==200
        assert page.locator('article').count()>=1
        assert 'Customer Segmentation' in page.locator('article').inner_text()
        page.screenshot(path=str(ROOT/'tmp/public-repository.png'))
        response=page.goto(REPO+'/blob/main/notebooks/Customer_Segmentation_and_Churn_Risk.ipynb')
        assert response.status==200
        browser.close()
    output={'repository':REPO,'verified_source_commit':REVISION,'report':LIVE,'anonymous_http_checks':results,
            'live_browser_checks':{'baseline_metrics':True,'five_filters':True,'reset':True,'empty_state':True,
                                   'mobile_360px':True,'navigation':True,'no_console_errors':True,
                                   'readme_rendered':True,'notebook_page_accessible':True,'seven_deliverable_links_http_200':True}}
    if write_report:
        (ROOT/'reports/public_verification.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    print(f'Public verification passed: {len(results)} unauthenticated HTTP checks, seven deliverable links, live filters/reset/empty state/mobile/navigation and GitHub README.')
    print(LIVE)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--check-only',action='store_true')
    main(write_report=not parser.parse_args().check_only)

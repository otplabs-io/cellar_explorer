#!/usr/bin/env python3
"""Smoke test for the app, run before every publish (src/restock.py publish) and by hand:
    python tests/app_smoke.py http://localhost:8800/
Loads the home page at phone and desktop sizes and checks that it works the way a guest uses it: the globe draws
and labels its countries, a tap flies into a country, the dock count matches the catalog, the wine list shows every
match, search suggests, the drinking window filters, and every sheet page, PDF and map the catalog links to is there.
Exits 1 with the reasons if anything fails."""
import json,sys,time,urllib.request
from playwright.sync_api import sync_playwright
URL=(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8800/').rstrip('/')+'/'
fails=[]
def check(ok,what):
    if not ok: fails.append(what)
    return ok
cat=json.load(urllib.request.urlopen(URL+'data/catalog.json'))
n=len(cat['items'])
check(n>0,'the catalog has no wines')
# every file the app links to
missing=[]
for w in cat['items']:
    if not w.get('id'): continue
    for f in ('','sheet.pdf'):
        try: urllib.request.urlopen(urllib.request.Request(URL+f"sheets/{w['id']}/{f}",method='HEAD'))
        except Exception: missing.append(f"sheets/{w['id']}/{f}")
check(not missing,f'{len(missing)} sheet files missing, e.g. {missing[:3]}')
with sync_playwright() as p:
    b=p.chromium.launch()
    for name,vp,touch in (('phone',dict(width=390,height=844),True),('desktop',dict(width=1360,height=900),False)):
        ctx=b.new_context(viewport=vp,is_mobile=touch,has_touch=touch); pg=ctx.new_page(); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
        pg.goto(URL)
        try: pg.wait_for_function("document.querySelectorAll('#map .lab text').length>0",timeout=15000)
        except Exception:
            check(False,f'{name}: the home page never drew the map. Errors in the page: {errs[:3] or "none"}'); ctx.close(); continue
        dock=pg.evaluate("parseInt(document.querySelector('#nMatch').textContent)")
        check(dock==n,f'{name}: the dock says {dock} wines, the catalog has {n}')
        check(pg.evaluate("document.querySelectorAll('#map path.rg').length")>0,f'{name}: the globe drew no countries with wine')
        top=pg.evaluate("document.querySelector('#map .lab text[data-id]')?.dataset.id")
        if check(top,f'{name}: no country label to tap'):
            pg.click(f'#map .lab text[data-id="{top}"]')
            try: pg.wait_for_function(f"location.hash.includes('p={top}')&&document.querySelector('#crumbs b')",timeout=5000)
            except Exception: check(False,f'{name}: tapping {top} did not open it')
            time.sleep(2.5)
            check(pg.evaluate("document.querySelectorAll('#map .lab text').length")>0,f'{name}: {top} shows no place labels')
        pg.goto(URL+'#/wines'); time.sleep(.8)
        rows=pg.evaluate("document.querySelectorAll('#results .wine').length")
        check(rows==n,f'{name}: the wine list shows {rows} of {n} wines')
        pg.goto(URL+'#/'); time.sleep(.5)
        pg.fill('#q','pinot'); time.sleep(.4)
        check(pg.evaluate("document.querySelectorAll('#sugg li').length")>0,f'{name}: search suggested nothing for "pinot"')
        pg.fill('#q',''); pg.goto(URL+'#/?yr=2030'); time.sleep(.6)
        yr=pg.evaluate("parseInt(document.querySelector('#nMatch').textContent)")
        check(0<yr<=n,f'{name}: the drinking window for 2030 left {yr} wines')
        sheet=next((w['id'] for w in cat['items'] if w.get('id')),None)
        if sheet:
            pg.goto(URL+f'sheets/{sheet}/'); time.sleep(.5)
            check(pg.evaluate("document.body.innerText.length")>200,f'{name}: the phone sheet for {sheet} is empty')
        check(not errs,f'{name}: errors in the page: {errs[:3]}')
        ctx.close()
    b.close()
if fails:
    print('App check FAILED:'); [print('  -',f) for f in fails]; sys.exit(1)
print(f'App check passed: {n} wines, phone and desktop.')

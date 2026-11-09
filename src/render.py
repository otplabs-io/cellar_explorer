#!/usr/bin/env python3
"""Render a wine file to a two-sided Letter PDF. No AI and no network.
Usage: python src/render.py wines/<id>/wine.json [--year 2027]
Output: build/<id>/sheet.pdf, page-1.png, page-2.png, sheet.html (feeds the PDF), sheet.web.html (self-contained, for screens), report.json, canvas/"""
import argparse,json,os,re,sys
from pathlib import Path
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import blocks as B
ROOT=B.ROOT
ap=argparse.ArgumentParser(); ap.add_argument('wine'); ap.add_argument('--year',type=int,help='highlight this year on the drinking window'); ap.add_argument('--out'); ap.add_argument('--theme',help='proof this theme, ignoring the wine\'s own color overrides; needs --out')
a=ap.parse_args()
wp=os.path.abspath(a.wine); import records; cfg=records.load_wine(wp); c=cfg['content']; wid=cfg.get('id') or os.path.basename(os.path.dirname(wp))
if a.year and c.get('window'): c['window'][2]=a.year
if a.theme:
    if not a.out: sys.exit('--theme renders a proof, so give it an --out folder outside build/<id>/')
    cfg={k:v for k,v in cfg.items() if k not in B.TOK['themes']['white']}; cfg['theme']=a.theme
OUT=os.path.abspath(a.out or os.path.join(ROOT,'build',wid)); os.makedirs(OUT,exist_ok=True)
import sheetprep; prof=sheetprep.prepare(cfg)
th=B.Theme(cfg); MAP=open(os.path.join(os.path.dirname(wp),cfg.get('map_file','map.svg'))).read()
PG=B.TOK['page']
FRONT=B.page(PG['front_gap'],PG['front_line'],[B.hero(th,c),B.facts_row(c),B.taste_row(th,c),B.serve_row(th,c,prof),B.pairing_row(th,c),B.story_row(c,prof)])
BACK=B.page(PG['back_gap'],PG['back_line'],[B.place_header(c,prof),B.map_block(MAP),B.notes_row(c),B.credits_footer(c,prof)])
FD=Path(ROOT,'design-system','fonts').as_uri()+'/'  # as_uri handles spaces in the folder path
FONT=''.join(f"@font-face{{font-family:'Nunito Sans';font-weight:{w};src:url(\"{FD}nunito-sans-latin-{w}-normal.woff2\")}}" for w in (400,600,700,800))
FONT+=f"@font-face{{font-family:'Nunito Sans';font-style:italic;font-weight:400;src:url(\"{FD}nunito-sans-latin-400-italic.woff2\")}}"
FONT+=''.join(f"@font-face{{font-family:'Poppins';font-weight:{w};src:url(\"{FD}poppins-latin-{w}-normal.woff2\")}}" for w in (600,700,800))
html=f'<!doctype html><html><head><meta charset="utf-8"><title>{c["title"]}</title><style>{FONT}@page{{size:8.5in 11in;margin:0}}html,body{{margin:0;padding:0}}.pg{{width:{PG["width_px"]}px;height:{PG["height_px"]}px;overflow:hidden;break-after:page}}</style></head><body><div class="pg">{FRONT}</div><div class="pg">{BACK}</div></body></html>'
hp=os.path.join(OUT,'sheet.html'); open(hp,'w').write(html)
# Web copy: one self-contained file with the fonts inlined, for screens now and the app bundle later.
# The PDF is always built from sheet.html above, so this file can change without touching make verify.
import base64
FDIR=os.path.join(ROOT,'design-system','fonts'); WEBFONT=FONT
for f in sorted(os.listdir(FDIR)):
    if f.endswith('.woff2'): WEBFONT=WEBFONT.replace(FD+f,'data:font/woff2;base64,'+base64.b64encode(open(os.path.join(FDIR,f),'rb').read()).decode())
assert 'file:' not in WEBFONT
SCREEN=f"@media screen{{html{{background:{B.PANEL}}}.pg{{margin:24px auto;outline:1px solid {B.ROLE['page_edge']}}}}}"
web=html.replace('<meta charset="utf-8">','<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',1).replace(FONT,WEBFONT+SCREEN,1)
open(os.path.join(OUT,'sheet.web.html'),'w').write(web)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    br=p.chromium.launch(); pg=br.new_page(viewport={'width':816,'height':2112},device_scale_factor=1.6)
    pg.goto(Path(hp).as_uri()); pg.wait_for_timeout(800); pg.evaluate('document.fonts.ready')
    over=pg.evaluate("""()=>[...document.querySelectorAll('.sheet-page')].map(r=>{const t=r.getBoundingClientRect(),b=[...r.children].map(k=>({block:k.dataset.block,bottom:Math.round(k.getBoundingClientRect().bottom-t.top),spill:Math.max(0,...[...k.querySelectorAll('*')].filter(e=>e.tagName=='svg'||!e.closest('svg')).map(e=>Math.round(e.getBoundingClientRect().bottom-k.getBoundingClientRect().bottom)))}));return{scrollHeight:r.scrollHeight,blocks:b}})""")
    fonts=pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family+' '+f.weight+' '+f.style)")
    # two pieces of text drawn on top of each other (a long one-word label in a tight row); SVG text is left to the map checks
    clash=pg.evaluate("""()=>{const R=[],w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
      while(n=w.nextNode()){const t=n.textContent.trim();if(!t||n.parentElement.closest('svg'))continue;const r=document.createRange();r.selectNodeContents(n);
        for(const b of r.getClientRects())if(b.width>0)R.push([t,b.left,b.right,b.top,b.bottom,n]);}
      const out=[];for(let i=0;i<R.length;i++)for(let j=i+1;j<R.length;j++){const a=R[i],b=R[j];
        const ov=Math.min(a[4],b[4])-Math.max(a[3],b[3]);   // tall display type has a deep line box, so text must share most of a line
        if(a[5]!==b[5]&&a[1]<b[2]-1&&b[1]<a[2]-1&&ov>.4*Math.min(a[4]-a[3],b[4]-b[3]))out.push(a[0]+' / '+b[0]);}return [...new Set(out)];}""")
    pg.locator('.pg').nth(0).screenshot(path=os.path.join(OUT,'page-1.png')); pg.locator('.pg').nth(1).screenshot(path=os.path.join(OUT,'page-2.png'))
    pg.pdf(path=os.path.join(OUT,'sheet.pdf'),width='8.5in',height='11in',print_background=True,prefer_css_page_size=True); br.close()
text=re.sub(r'<svg.*?</svg>','',FRONT+BACK,flags=re.S); plain=re.sub(r'<[^>]+>',' ',text)
issues=[]
if B.TOK['themes'][th.name]['status']!='approved' and not a.theme: issues.append(f'theme "{th.name}" is proposed, not approved. Use --theme with --out to proof it.')
for i,o in enumerate(over,1):
    if o['scrollHeight']>1056: issues.append(f'page {i} overflows by {o["scrollHeight"]-1056}px; blocks end at {o["blocks"]}. Cut copy in the last blocks. Never shrink type.')
    else:   # a block can also run into the bottom margin without growing the page
        floor=PG['height_px']-PG['margin_px']; low=[b for b in o['blocks'] if b['bottom']>floor]
        spill=[b for b in o['blocks'] if b.get('spill',0)>1]
        if spill: issues.append(f'page {i}: text spills out of {", ".join(b["block"] for b in spill)} by {max(b["spill"] for b in spill)}px. Cut copy (in the hero, the intro first). Never shrink type.')
        if low: issues.append(f'page {i}: {", ".join(b["block"] for b in low)} runs {max(b["bottom"] for b in low)-floor}px into the bottom margin; blocks end at {o["blocks"]}. Cut copy. Never shrink type.')
hits=re.findall(r'(?i)\$\s?\d|\bprices?\b|\bpricing\b|\bpremium\b|\bexpensive\b|\bcosts?\b|\bretail\b|\bmarket value\b',plain)
if clash: issues.append(f'text overlaps: {clash}. Shorten a label. Never shrink type.')
if hits: issues.append(f'pricing language: {sorted(set(hits))}')
if '—' in plain: issues.append('em dash in copy')
if re.search(r'(?i)not only\b.*\bbut also',plain): issues.append('"not only...but also" in copy')
if not fonts: issues.append('no fonts loaded')
json.dump({'wine':wid,'issues':issues,'pages':over,'fonts':fonts},open(os.path.join(OUT,'report.json'),'w'),ensure_ascii=False,indent=1)
# Design canvas copies, for wines someone wants to edit by hand
os.makedirs(os.path.join(OUT,'canvas','project'),exist_ok=True)
GF='https://fonts.googleapis.com/css2?family=Nunito+Sans:ital,wght@0,400;0,600;0,700;0,800;1,400&amp;family=Poppins:wght@600;700;800&amp;display=swap'
def dc(t,r): return f"""<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<title>{t}</title>\n<script src="./support.js"></script>\n</head>\n<body>\n<x-dc>\n<helmet>\n<link rel="stylesheet" href="{GF}">\n<style>\nbody{{margin:0}}\n</style>\n</helmet>\n{r}\n</x-dc>\n<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":816,"height":1056}}}}'>\nclass Component extends DCLogic {{\nrenderVals() {{ return {{}}; }}\n}}\n</script>\n</body>\n</html>\n"""
open(os.path.join(OUT,'canvas','project','Main.dc.html'),'w').write(dc(c['title']+': the wine',FRONT)); open(os.path.join(OUT,'canvas','project','Where-It-Grows.dc.html'),'w').write(dc(c['title']+': where it grows',BACK))
print(json.dumps({'pdf':os.path.join(OUT,'sheet.pdf'),'issues':issues},ensure_ascii=False))
sys.exit(1 if issues else 0)

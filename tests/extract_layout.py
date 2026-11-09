#!/usr/bin/env python3
"""Dump the box, type and color of every text element to reference/layout.json. A spec for any rebuild in another stack."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H=os.path.join(ROOT,'build','la-boudriotte-2019','sheet.html')
JS="""()=>{const out=[];document.querySelectorAll('.sheet-page').forEach((pg,pi)=>{const o=pg.getBoundingClientRect();pg.querySelectorAll('h1,h2,p,span,footer,text').forEach(e=>{const t=(e.textContent||'').trim();if(!t||(e.tagName!=='text'&&e.children.length&&![...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())))return;const r=e.getBoundingClientRect(),s=getComputedStyle(e),b=e.closest('[data-block]');out.push({page:pi+1,block:b?b.dataset.block:null,tag:e.tagName.toLowerCase(),text:t.slice(0,140),x:+(r.left-o.left).toFixed(2),y:+(r.top-o.top).toFixed(2),w:+r.width.toFixed(2),h:+r.height.toFixed(2),font:s.fontFamily.replace(/"/g,''),size:s.fontSize,weight:s.fontWeight,style:s.fontStyle,line:s.lineHeight,color:e.tagName==='text'?e.getAttribute('fill'):s.color,letter:s.letterSpacing})})});return out}"""
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':816,'height':2112}); pg.goto(Path(H).as_uri()); pg.wait_for_timeout(800); d=pg.evaluate(JS); v=b.version; b.close()
seen=set(); o=[]
for x in d:
    k=(x['page'],x['text'],x['x'],x['y'])
    if k in seen: continue
    seen.add(k); o.append(x)
json.dump(o,open(os.path.join(ROOT,'reference','layout.json'),'w'),ensure_ascii=False,indent=0); print(len(o),'text elements',v)

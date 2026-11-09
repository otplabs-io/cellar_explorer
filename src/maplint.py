#!/usr/bin/env python3
"""Check a map's labels in Chromium, so a draft only needs a look when something is wrong.

  maplint.py wines/<id> [--svg map.svg]

Measures every label with the real font and reports:
  - clipped: a label that runs past the edge of its panel;
  - overlap: two labels in one panel whose boxes overlap by more than a small share of the smaller one.
Halo copies of a label (the same text drawn twice at one spot) count once. Exits 1 if anything is found."""
import argparse,json,os,re,sys
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERLAP=0.02   # share of the smaller box; with the 2px minimum below, calibrated on every locked map
JS='''() => {
  const out=[]; const seen=new Set();
  const panelOf=t=>{for(let g=t.parentElement;g;g=g.parentElement){const f=g.firstElementChild; if(g.tagName==='g'&&f&&f.tagName==='rect'&&f.getAttribute('width')) return g;} return null};
  const panels=[]; const pid=g=>{let i=panels.indexOf(g); if(i<0){panels.push(g); i=panels.length-1} return i};
  for(const t of document.querySelectorAll('svg text')){
    const s=(t.textContent||'').trim(); if(!s) continue;
    const key=s+'|'+t.getAttribute('x')+'|'+t.getAttribute('y'); if(seen.has(key)) continue; seen.add(key);
    const p=panelOf(t); const b=t.getBoundingClientRect(); const r=p?p.firstElementChild.getBoundingClientRect():null;
    out.push({text:s,x:+t.getAttribute('x'),y:+t.getAttribute('y'),anchor:t.getAttribute('text-anchor')||'start',panel:p?pid(p):-1,box:[b.left,b.top,b.right,b.bottom],frame:r?[r.left,r.top,r.right,r.bottom]:null});
  }
  // boxes drawn on top: a group whose first child is a filled rect (a panel, an inset, a legend card)
  const frames=[...document.querySelectorAll('svg rect')].filter(r=>{const f=r.getAttribute('fill'); const b=r.getBoundingClientRect(); return f&&f!=='none'&&b.width>30&&b.height>30});
  const texts=[...document.querySelectorAll('svg text')];
  for(const o of out){ o.covered=[]; }
  let i=0; const keyed={};
  for(const t of texts){const s=(t.textContent||'').trim(); const k=s+'|'+t.getAttribute('x')+'|'+t.getAttribute('y'); if(!(k in keyed)) keyed[k]=t;}
  for(const o of out){
    const t=keyed[o.text+'|'+o.x+'|'+o.y]; if(!t) continue;
    for(const g of frames){
      if(!(t.compareDocumentPosition(g)&Node.DOCUMENT_POSITION_FOLLOWING)) continue;
      const r=g.getBoundingClientRect(), b=o.box;
      const w=Math.min(b[2],r.right)-Math.max(b[0],r.left), h=Math.min(b[3],r.bottom)-Math.max(b[1],r.top);
      if(w>1&&h>1) o.covered.push(Math.round(w));
    }
  }
  return out;}'''
def area(b): return max(0,b[2]-b[0])*max(0,b[3]-b[1])
def inter(a,b): return area([max(a[0],b[0]),max(a[1],b[1]),min(a[2],b[2]),min(a[3],b[3])])
def lint(wdir,svg=None,detail=False,page=None):
    """page: an open Playwright page to reuse, so a batch of maps (src/mapproof.py) starts Chromium once."""
    draft=os.path.join(wdir,'map.draft.html')
    html=open(draft,encoding='utf-8').read() if os.path.exists(draft) else '<!doctype html><meta charset="utf-8"><body></body>'
    if svg:
        body=open(os.path.join(wdir,svg),encoding='utf-8').read()
        html=re.sub(r'<svg.*</svg>',lambda m:body,html,count=1,flags=re.S) if '<svg' in html else html.replace('<body>','<body>'+body)
    if page:
        page.set_content(html); page.evaluate('document.fonts.ready'); labels=page.evaluate(JS)
    else:
        with sync_playwright() as p:
            b=p.chromium.launch(); pg=b.new_page(viewport={'width':1200,'height':1000})
            pg.set_content(html); pg.evaluate('document.fonts.ready'); labels=pg.evaluate(JS); b.close()
    # a label wholly outside its panel is hidden on purpose (an override at -500,-500)
    labels=[l for l in labels if not l['frame'] or inter(l['box'],l['frame'])>0]
    found=[]; det=[]
    for l in labels:
        f=l['frame']
        if f and (l['box'][0]<f[0]-0.5 or l['box'][1]<f[1]-0.5 or l['box'][2]>f[2]+0.5 or l['box'][3]>f[3]+0.5):
            det.append(dict(kind='clipped',text=l['text'],panel=l['panel'],at=[l['x'],l['y'],l['anchor']],
                            move=[round((f[0]-l['box'][0]+3) if l['box'][0]<f[0] else -(l['box'][2]-f[2]+3) if l['box'][2]>f[2] else 0,1),
                                  round((f[1]-l['box'][1]+3) if l['box'][1]<f[1] else -(l['box'][3]-f[3]+3) if l['box'][3]>f[3] else 0,1)]))
            found.append(f"clipped: {l['text']!r} runs past panel {l['panel']} by {max(f[0]-l['box'][0],f[1]-l['box'][1],l['box'][2]-f[2],l['box'][3]-f[3]):.1f}px")
    for l in labels:
        if l.get('covered'):
            det.append(dict(kind='covered',text=l['text'],panel=l['panel'],at=[l['x'],l['y'],l['anchor']],px=max(l['covered'])))
            found.append(f"covered: {l['text']!r} runs {max(l['covered'])}px under a box drawn on top")
    for i,a in enumerate(labels):
        for c in labels[i+1:]:
            if a['panel']!=c['panel']: continue
            small=min(area(a['box']),area(c['box'])) or 1
            iw=min(a['box'][2],c['box'][2])-max(a['box'][0],c['box'][0]); ih=min(a['box'][3],c['box'][3])-max(a['box'][1],c['box'][1])
            if iw>=2 and ih>=2 and inter(a['box'],c['box'])/small>OVERLAP:   # a real overlap, not boxes brushing by a pixel
                det.append(dict(kind='overlap',text=[a['text'],c['text']],panel=a['panel'],at=[[a['x'],a['y'],a['anchor']],[c['x'],c['y'],c['anchor']]],boxes=[[round(v) for v in a['box']],[round(v) for v in c['box']]]))
                found.append(f"overlap: {a['text']!r} and {c['text']!r} in panel {a['panel']}")
    return det if detail else found
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('wine_dir'); ap.add_argument('--svg'); ap.add_argument('--detail',action='store_true'); a=ap.parse_args()
    f=lint(a.wine_dir,a.svg,a.detail)
    print(json.dumps(dict(map=a.svg or 'map.draft.svg',problems=f),ensure_ascii=False))
    sys.exit(1 if f else 0)

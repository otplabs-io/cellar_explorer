#!/usr/bin/env python3
"""The phone view of a pour sheet: the same record, components and tokens as the PDF, reflowed into one column.
Usage: python src/mobile.py wines/<id>/wine.json [--out file.html]
The app's site build (src/site.py) calls render() for every wine and links the page to the shared stylesheet in
build/site/assets/. The printed sheet is untouched: render.py still builds the PDF from sheet.html."""
import argparse,html as H,json,os,re,sys
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import blocks as B, records, sheetprep
from blocks import ts,section_head,INK,SOFT,PANEL,HOT_TEXT,RULE
VIEWER="""(()=>{const d=document.getElementById('viewer'),pane=document.getElementById('mvPane'),btn=document.getElementById('mapOpen');let z=1,open=false;
const size=()=>{const s=pane.firstElementChild; if(s){s.style.width=(z*100)+'%'; s.style.height='auto';}};
function show(){if(!pane.firstElementChild) pane.appendChild(btn.querySelector('svg').cloneNode(true)); z=1; size(); d.showModal(); open=true; history.pushState({map:1},'');}
function hide(fromBack){if(!open) return; open=false; d.close(); if(!fromBack) history.back();}
btn.onclick=show; document.getElementById('mvClose').onclick=()=>hide(false);
d.addEventListener('cancel',e=>{e.preventDefault(); hide(false);}); addEventListener('popstate',()=>hide(true));
document.getElementById('mvIn').onclick=()=>{z=Math.min(4,z*1.5); size();}; document.getElementById('mvOut').onclick=()=>{z=Math.max(1,z/1.5); size();};})();"""   # the map, full size, in a window over the sheet: Close, the back button or Esc return to it
_TREE=None
def records_tree():
    global _TREE
    if _TREE is None:   # the places the Appellation Atlas has a page for
        p=os.path.join(B.ROOT,'regions','bundled','places.json')
        _TREE={k:dict(name=v[0]) for k,v in json.load(open(p,encoding='utf-8'))['places'].items()} if os.path.exists(p) else {}
    return _TREE
ROCKS=json.load(open(os.path.join(B.ROOT,'regions','rock-types.json'),encoding='utf-8'))['families']
def _site():
    p=os.path.join(B.ROOT,'app','site.local.json')   # your own settings, kept out of git
    return json.load(open(p if os.path.exists(p) else os.path.join(B.ROOT,'app','site.json'),encoding='utf-8'))
ATLAS_URL=_site()['atlas_url']
ROCK_WORDS={'chalk':'chalk','albariza':'chalk','marl':'marl','limestone':'limestone','calcareous':'limestone','volcanic':'volcanic','basalt':'volcanic','tuff':'volcanic','lava':'volcanic',
            'granite':'granite','schist':'schist','slate':'schist','llicorella':'schist','galestro':'schist','gneiss':'schist','gravel':'gravel','pebble':'gravel','sandstone':'sandstone',
            'sand':'sand','alluvi':'alluvium','loess':'loess','clay':'clay','shale':'shale'}
def soil_why(text):
    """What the rocks a soil note names mean for the vines, in the order it names them, from regions/rock-types.json."""
    t=text.lower(); seen=[]
    for w,f in sorted(ROCK_WORDS.items(),key=lambda x:min([i for i in [t.find(x[0])] if i>=0] or [9e9])):
        i=t.find(w)
        if i<0 or f in seen: continue
        if w=='sand' and t[i:i+9]=='sandstone': continue
        seen.append(f)
    F={x['id']:x for x in ROCKS}
    return [F[f]['effect'] for f in seen if f in F and F[f]['effect']][:3]
def render(wp,assets='../../assets',home='../../'):
    cfg=records.load_wine(wp); c=cfg['content']; prof=sheetprep.prepare(cfg); th=B.Theme(cfg)
    wid=cfg.get('id') or os.path.basename(os.path.dirname(wp))
    MAP=open(os.path.join(os.path.dirname(wp),cfg.get('map_file','map.svg'))).read()
    MAP=re.sub(r'(<svg[^>]*?) width="\d+" height="\d+"',r'\1',MAP,count=1)   # let the map scale to the screen
    sec=lambda cls,inner:f'<section class="{cls}">{inner}</section>'
    hero=f'''<section class="m-hero" style="background: {th.tint}">
<div class="m-hero-text"><p class="m-eyebrow" style="{ts('eyebrow')}; color: {HOT_TEXT}">{c['eyebrow']}</p>
<h1 class="m-title" style="{ts('sheet_title',size=38)}">{c['title']}</h1>
<p class="m-sub" style="{ts('subtitle')}">{c['subtitle']}</p><p style="{ts('producer')}">{c['producer']}</p></div>
<div class="m-bottle">{B.bottle(th,c['bottle_label'])}</div>
{f'<p class="m-intro" style="{ts("intro")}">{c["intro"]}</p>' if c.get('intro') else ''}</section>'''
    facts=sec('m-facts',(B.blend(c['blend']) if c.get('blend') else '')+''.join(B.fact(*f) for f in c['facts']))
    taste=sec('m-block',section_head('Taste profile')+'<div class="m-dots">'+''.join(B.taste_dots(th,*d) for d in c['taste'])+f'</div><p class="m-note" style="{ts("caption")}; color: {SOFT}">{c["taste_note"]}</p>')
    flav=sec('m-block',section_head('What you may smell and taste')+'<div class="m-icons">'+''.join(B.flavor(th,*f) for f in c['flavors'])+'</div>'+(f'<p class="m-note" style="{ts("body")}">{c["flavor_note"]}</p>' if c.get('flavor_note') else ''))
    w=c.get('window'); cells=[x for x in prof['serve_cells'] if c.get(x[2])]; g=B.L['serve']
    cell=lambda head,ic,txt:f'<div>{section_head(head)}<div class="m-serve-cell">{B.icon(ic,g["icon"],th.icons)}<p style="{ts("serve")}">{txt}</p></div></div>'
    serve=f'''<section class="m-panel" style="background: {PANEL}"><div>{section_head('When to drink it')}{B.drink_window(th,w[0],w[1],w[2]) if w else ''}<p class="m-note" style="{ts('window_note')}">{c['window_note']}</p></div>
<div class="m-serve">{''.join(cell(h,ic,c[k]) for h,ic,k in cells)}</div></section>'''
    pairs=sec('m-block',section_head('What to eat with it')+'<div class="m-pairs">'+''.join(B.pairing(th,*p) for p in c['pairs'])+'</div>'+(f'<p class="m-note" style="{ts("body")}">{c["pair_note"]}</p>' if c.get('pair_note') else ''))
    sig=prof['story'].get('signature'); lab=prof['story']['labels']
    sig=sig if sig and (c.get('level') or c.get('show_signature')) else None
    story=(sec('m-block m-sig',section_head(c.get('ladder_title',sig['title']))+B.SIGNATURES[sig['component']](c,sig)+f'<p class="m-note" style="{ts("ladder_note")}; color: {SOFT}; text-align: center">{c["ladder_note"]}</p>') if sig else '')
    story+=sec('m-block',section_head(c.get('family_title',lab['family']))+f'<p style="{ts("story")}">{c["family"]}</p>')
    story+=sec('m-block',section_head(c.get('vintage_title',lab['vintage']))+f'<p style="{ts("story")}">{c["vintage"]}</p>')
    sub=c.get('place_subtitle',prof['place']['subtitle'])
    node=(cfg.get('region') or {}).get('node'); T=records_tree()
    atlas=f'<a class="m-atlas" href="{ATLAS_URL}#/{node}">More on {H.escape(T[node]["name"])} in the Appellation Atlas ›</a>' if ATLAS_URL and node and node in T else ''
    place=f'''<section class="m-place"><h2 class="m-page-title" style="{ts('page_title')}">{c.get('place_title',prof['place']['title'])}</h2>{f'<p style="{ts("place_subtitle")}; color: {SOFT}">{sub}</p>' if sub else ''}
<button type="button" class="m-map" id="mapOpen" aria-label="Open the map full size">{MAP}</button><p class="m-hint" style="{ts('caption')}; color: {SOFT}">Tap the map to open it full size.</p>{atlas}</section>'''
    why=lambda k,v:(lambda ws:f'<p class="m-soil" style="{ts("notes")}">{H.escape(" ".join(ws))}</p>' if ws else '')(soil_why(v)) if 'soil' in k.lower() else ''   # what those rocks do, as plain sentences
    notes=''.join(sec('m-block',section_head(k)+f'<p style="{ts("notes")}">{v}</p>'+why(k,v)) for k,v in c['place'])
    mc=prof['map']['credit']
    foot=f'<footer class="m-credits" style="{ts("footer")}; color: {SOFT}">{mc+" " if mc else ""}{c["credits"]}</footer>'
    links=f'<p class="m-links"><a href="sheet.pdf" download>Save the PDF</a><a href="sheet.web.html">Printable sheet</a></p>'
    title=H.escape(re.sub(r'<[^>]+>','',c['title']))
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><link rel="icon" href="{assets}/cellar-explorer-32.png" type="image/png" sizes="32x32"><link rel="icon" href="{assets}/cellar-explorer.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="{assets}/cellar-explorer-180.png"><link rel="stylesheet" href="{assets}/app.css"></head>
<body class="m-body" style="color: {INK}; {B.PB}; font-size: {B.n(B.TY['page_base']['size'])}px">
<nav class="m-top"><a class="m-back" href="{home}" onclick="if(history.length>1&&document.referrer.indexOf(location.host)>-1){{history.back();return false}}">‹ Cellar</a><span class="m-top-title">{title}</span><a class="m-pdf" href="sheet.pdf" download>PDF</a></nav>
<main class="m-sheet" data-wine="{wid}">{hero}{facts}{taste}{flav}{serve}{pairs}{story}{place}{notes}{foot}{links}</main>
<dialog class="m-viewer" id="viewer" aria-label="The map, full size"><div class="mv-bar"><button type="button" class="mv-close" id="mvClose">✕ Close</button>
<span class="mv-zoom"><button type="button" id="mvOut" aria-label="Zoom out">−</button><button type="button" id="mvIn" aria-label="Zoom in">+</button></span></div><div class="mv-pane" id="mvPane"></div></dialog>
<script>{VIEWER}</script></body></html>'''
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('wine'); ap.add_argument('--out'); a=ap.parse_args()
    out=a.out or os.path.join(B.ROOT,'build',os.path.basename(os.path.dirname(os.path.abspath(a.wine))),'sheet.mobile.html')
    open(out,'w',encoding='utf-8').write(render(os.path.abspath(a.wine),assets='../site/assets')); print(out)

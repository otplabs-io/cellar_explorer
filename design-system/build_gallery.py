#!/usr/bin/env python3
"""Render the design system review sheet: tokens, type, every icon at print sizes and in grayscale,
every catalog component, and each color theme proofed on La Boudriotte's front page.
Icons are grouped by their place in the aroma lexicon (see icons.json). Grayscale is not shown, since it is not a requirement.
Writes design-system/gallery.png, plus one PNG per section in build/gallery/ for easier review."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(ROOT,'src'))
import blocks as B
from playwright.sync_api import sync_playwright
T=B.TOK; INK,SOFT=B.INK,B.SOFT; OUT=os.path.join(ROOT,'build','gallery'); os.makedirs(OUT,exist_ok=True)
WINE=os.path.join(ROOT,'wines','la-boudriotte-2019','wine.json'); import records; cfg=records.load_wine(WINE); c=cfg['content']; import profiles; PROF=profiles.for_wine(cfg); CHAMP=profiles.for_node('france/champagne')
THEMES=[k for k in T['themes'] if not k.startswith('$')]
# Proof every theme on the real front page. Proposed themes need --theme, which ignores the wine's own color overrides.
for t in THEMES:
    d=os.path.join(OUT,'proof',t)
    r=subprocess.run([sys.executable,os.path.join(ROOT,'src','render.py'),WINE,'--theme',t,'--out',d],capture_output=True,text=True)
    if r.returncode: sys.exit(f'theme proof {t} failed: {r.stdout[-400:]}')
FD=Path(ROOT,'design-system','fonts').as_uri()+'/'
FONT=''.join(f"@font-face{{font-family:'Nunito Sans';font-weight:{w};src:url(\"{FD}nunito-sans-latin-{w}-normal.woff2\")}}" for w in (400,600,700,800))+f"@font-face{{font-family:'Nunito Sans';font-style:italic;font-weight:400;src:url(\"{FD}nunito-sans-latin-400-italic.woff2\")}}"+''.join(f"@font-face{{font-family:'Poppins';font-weight:{w};src:url(\"{FD}poppins-latin-{w}-normal.woff2\")}}" for w in (600,700,800))
note=lambda t:f'<p style="margin:2px 0 10px;font-size:12.5px;color:{SOFT};max-width:900px">{t}</p>'
H=lambda t,sub='':f'<h2 style="font-family:Poppins;font-size:19px;font-weight:700;margin:30px 0 4px;padding-top:12px;border-top:1.5px solid {INK}">{t}</h2>'+(note(sub) if sub else '')
H3=lambda t:f'<h3 style="font-family:Poppins;font-size:14px;font-weight:700;margin:16px 0 6px">{t}</h3>'
gray=lambda h:f'<span style="filter:grayscale(1);display:flex">{h}</span>'
def L(h):
    h=h.lstrip('#'); x=[int(h[i:i+2],16)/255 for i in (0,2,4)]; x=[v/12.92 if v<=0.03928 else ((v+0.055)/1.055)**2.4 for v in x]; return 0.2126*x[0]+0.7152*x[1]+0.0722*x[2]
cr=lambda a,b:(max(L(a),L(b))+0.05)/(min(L(a),L(b))+0.05)
sw=lambda n,v,sub=None:f'<div style="width:118px"><div style="height:40px;background:{v};border:1px solid #CFC7B5"></div><div style="font-size:11px;font-weight:700;margin-top:3px">{n}</div><div style="font-size:10.5px;color:{SOFT}">{sub or v}</div></div>'
swatches=lambda d:'<div style="display:flex;flex-wrap:wrap;gap:10px">'+''.join(sw(k,v) for k,v in d.items() if not k.startswith('$'))+'</div>'
sec={}
# ---- color
roles={k:f'{v} {T["color"][v]}' for k,v in T['role'].items() if not k.startswith('$')}
sec['color']=H('Color','Palette, then the roles components ask for. Coral means this wine, here, now, and is never decoration.')+swatches(T['color'])+H3('Roles')+'<div style="display:flex;flex-wrap:wrap;gap:10px">'+''.join(sw(k,T['color'][v],v) for k,v in T['role'].items() if not k.startswith('$'))+'</div>'+H3('Map')+swatches(T['map'])+H3('Subregions (Burgundy, Bordeaux)')+swatches(T['subregion'])+H3('Plot tints')+swatches({str(i+1):v for i,v in enumerate(T['plot_tints'])})
# ---- type
def trow(k,s):
    spec=f"{T['font'][s.get('family','body')]['family']} {s.get('weight',400)}, {s['size']} px"+(f", line {s['line']}" if 'line' in s and s['line']<5 else '')+(f", tracking {s['tracking']}" if 'tracking' in s else '')
    return f'<div style="display:grid;grid-template-columns:150px 1fr;gap:12px;align-items:baseline;padding:3px 0;border-bottom:1px solid #EEE9DD"><span style="font-size:11px;color:{SOFT}">{k}<br>{spec}</span><span style="{B.ts(k) if k in T["type"] else ""}">{"La Boudriotte" if s["size"]>=30 else "Chassagne-Montrachet Premier Cru, 2019"}</span></div>'
mtyp=''.join(f'<div style="display:grid;grid-template-columns:150px 1fr;gap:12px;align-items:baseline;padding:3px 0;border-bottom:1px solid #EEE9DD"><span style="font-size:11px;color:{SOFT}">{k}<br>{T["font"][s.get("family","body")]["family"]} {s["weight"]}, {s["size"]} px</span><span style="font-family:{T["font"][s.get("family","body")]["family"]};font-size:{s["size"]}px;font-weight:{s["weight"]}">Chassagne-Montrachet</span></div>' for k,s in T['map_type'].items() if not k.startswith('$'))
sec['type']=H('Type','Every text style in tokens.json, set at its real size. Sheet styles first, then map styles.')+''.join(trow(k,s) for k,s in T['type'].items() if not k.startswith('$') and not k.startswith('bottle'))+H3('Map')+mtyp
# ---- icons
meta=json.load(open(os.path.join(ROOT,'design-system','icons.json')))['icons']; byid={i['id']:i for i in meta}
def cell(i):
    tag=f'<span style="font-size:10px;font-weight:800;letter-spacing:.6px;color:{SOFT};border:1px solid {SOFT};padding:0 4px">PROPOSED</span>' if i.get('status')=='proposed' else f'<span style="font-size:10px;color:{SOFT}">approved</span>'
    return f'<div style="width:140px;display:flex;flex-direction:column;align-items:center;gap:3px"><div style="display:flex;align-items:flex-end;gap:6px">{B.icon(i["id"],50)}{B.icon(i["id"],38)}</div><span style="font-size:12px;font-weight:700;text-align:center">{i["label"]}</span><span style="font-size:10.5px;color:{SOFT}">{i["family"]}/{i["id"]}</span>{tag}</div>'
grid=lambda L:'<div style="display:flex;flex-wrap:wrap;gap:14px 8px">'+''.join(cell(i) for i in L)+'</div>'
fam=lambda f:grid([i for i in meta if i['family']==f])
clusters={}
for i in meta:
    if i['family']=='flavor': clusters.setdefault(i['lexicon'][0] if i.get('lexicon') else 'outside the lexicon',[]).append(i)
lexsec=''.join(H3(k.replace('/',': ').capitalize())+grid(v) for k,v in clusters.items())
pairs=[]; seen=set()
for i in meta:
    for o in i.get('tell_alike',[]):
        k=tuple(sorted((i['id'],o)))
        if k not in seen: seen.add(k); pairs.append(k)
pcell=lambda a,b:f'<div style="display:flex;flex-direction:column;align-items:center;gap:3px;width:150px"><div style="display:flex;gap:8px">{B.icon(a,38)}{B.icon(b,38)}</div><span style="font-size:10.5px;color:{SOFT};text-align:center">{a} · {b}</span></div>'
nprop=sum(i.get('status')=='proposed' for i in meta)
sec['icons']=H('Icons',f'Each icon at 50 px and 38 px, grouped by its first place in the aroma lexicon. The {nprop} marked proposed are new and wait for your approval. Every icon passes make check-icons. No approved icon was redrawn.')+lexsec+H3('Pairing')+fam('pairing')+H3('Serving')+fam('serving')+H3('Tell-alike pairs at 38 px')+note('Each pair must be told apart at 38 px, by shape or color.')+'<div style="display:flex;flex-wrap:wrap;gap:12px">'+''.join(pcell(a,b) for a,b in pairs)+'</div>'
# ---- components
th=B.Theme(cfg)
comp=lambda name,html,w=None,sub='':f'<div style="margin:0 0 18px"><div style="font-size:11.5px;font-weight:800;letter-spacing:.6px;color:{SOFT};margin-bottom:5px">{name.upper()}{(" · "+sub) if sub else ""}</div><div style="{f"width:{w}px;" if w else ""}font-family:\'Nunito Sans\';font-size:14px;line-height:1.42;color:{INK}">{html}</div></div>'
mapsvg=open(os.path.join(ROOT,'wines','la-boudriotte-2019','map.svg')).read()
sec['components']=H('Components','Every component in components.md, built from blocks.py with La Boudriotte data and the white theme.')+'<div style="display:grid;grid-template-columns:1fr 1fr;column-gap:40px">'+''.join([
 comp('section_head',B.section_head('What to eat with it')),
 comp('taste_dots','<div style="display:flex;flex-direction:column;gap:7px">'+''.join(B.taste_dots(th,*d) for d in c['taste'])+'</div>',360,'1 to 5, fixed scale'),
 comp('flavor','<div style="display:flex;gap:6px">'+''.join(B.flavor(th,*f) for f in c['flavors'][:3])+'</div>'),
 comp('pairing','<div style="display:flex;gap:18px">'+''.join(B.pairing(th,*p) for p in c['pairs'][:3])+'</div>'),
 comp('fact','<div style="display:flex;gap:24px">'+''.join(B.fact(*f) for f in c['facts'][:3])+'</div>'),
 comp('drink_window',B.drink_window(th,*c['window']),400,f'current year {c["window"][2]} in coral'),
 comp('bottle',B.bottle(th,c['bottle_label'])),
 comp('quality_ladder',B.quality_ladder(c['level'])+f'<p style="margin:6px 0 0;font-size:11px;color:{SOFT}">White on coral is 4.28:1. See components.md.</p>',220),
 comp('dosage_scale',B.dosage_scale('Brut',CHAMP['story']['signature']),220,'Champagne profile, Brut active'),
 ])+'</div>'+''.join([
 comp('hero',B.hero(th,c),736),comp('facts_row',B.facts_row(c),736),comp('taste_row',B.taste_row(th,c),736),comp('serve_row',B.serve_row(th,c,PROF),736),
 comp('pairing_row',B.pairing_row(th,c),736),comp('story_row',B.story_row(c,PROF),736),comp('place_header',B.place_header(c,PROF),736),
 comp('map_block',f'<div style="width:368px;height:376px;overflow:hidden"><div style="transform:scale(.5);transform-origin:0 0">{B.map_block(mapsvg)}</div></div>',None,'locked map at half size, see maps.md'),
 comp('notes_row',B.notes_row(c),736),comp('credits_footer',B.credits_footer(c,PROF),736)])
# ---- themes
def trow_(t):
    d=T['themes'][t]; tt=B.Theme({'theme':t})
    stat=f'<span style="font-size:10px;font-weight:800;letter-spacing:.6px;color:{SOFT};border:1px solid {SOFT};padding:0 4px">{d["status"].upper()}</span>'
    nums=f'Eyebrow on tint {cr(B.HOT_TEXT,d["tint"]):.2f}:1. Accent vs coral {cr(d["accent"],B.HOT):.2f}:1. Bottle vs disc {cr(d["bottle"],d["disc"]):.2f}:1.'
    strip=f'<div style="display:flex;gap:18px;align-items:center;background:#fff">{B.bottle(tt,c["bottle_label"])}<div style="width:330px;display:flex;flex-direction:column;gap:7px">{"".join(B.taste_dots(tt,*x) for x in c["taste"][:3])}<div style="margin-top:6px">{B.drink_window(tt,*c["window"])}</div></div>{B.icon("decant",38,tt.icons)}</div>'
    img=Path(OUT,'proof',t,'page-1.png').as_uri()
    sws=''.join(f'<span style="display:inline-flex;align-items:center;gap:4px;margin-right:10px;font-size:11px"><span style="width:14px;height:14px;background:{d[k]};border:1px solid #CFC7B5;display:inline-block"></span>{k} {d[k]}</span>' for k in ('accent','tint','disc','bottle','wine'))
    return f'<div style="display:grid;grid-template-columns:260px 1fr;gap:20px;margin:14px 0 22px"><div><img src="{img}" style="width:260px;border:1px solid #CFC7B5"></div><div><div style="font-family:Poppins;font-size:16px;font-weight:700">{t} {stat}</div><div style="margin:4px 0 10px">{sws}</div><p style="font-size:12px;color:{SOFT};margin:0 0 10px">{nums}</p>{strip}</div></div>'
prop=[t for t in THEMES if T['themes'][t]['status']!='approved']
sec['themes']=H('Color themes',f'Each theme is proofed on La Boudriotte\'s front page only to show color. Still proposed: {", ".join(prop) or "none"}. A proposed theme fails a normal render until you approve it. Each row: the front page, then the themed parts at full size. Sparkling uses the Champagne bottle.')+''.join(trow_(t) for t in THEMES)
html=f"""<!doctype html><meta charset="utf-8"><style>{FONT}body{{margin:0;background:#fff;color:{INK};font-family:'Nunito Sans';font-size:14px}}</style>
<div style="width:1100px;padding:32px;box-sizing:border-box">
<h1 style="font-family:Poppins;font-size:34px;font-weight:800;margin:0">Pour Sheets design system</h1><p style="margin:4px 0 0;color:{SOFT}">Tokens, icons and components from the approved La Boudriotte sheet, plus the proposals waiting for approval: the icons and themes marked proposed.</p>
{''.join(f'<section id="{k}">{v}</section>' for k,v in sec.items())}
</div>"""
p_=os.path.join(OUT,'gallery.html'); open(p_,'w').write(html)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1100,'height':1200},device_scale_factor=1.5); pg.goto(Path(p_).as_uri()); pg.wait_for_timeout(800); pg.evaluate('document.fonts.ready')
    pg.screenshot(path=os.path.join(ROOT,'design-system','gallery.png'),full_page=True)
    for k in sec: pg.locator(f'#{k}').screenshot(path=os.path.join(OUT,f'{k}.png'))
    b.close()
print('design-system/gallery.png and build/gallery/*.png')

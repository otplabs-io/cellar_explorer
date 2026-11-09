#!/usr/bin/env python3
"""Render icon review sheets for Chris, one PNG per chunk, in build/review/.
Flavor chunks (2 to 8) follow lexicon groups. Pairing chunks (p1 to p3) list icon ids.
Each proposed icon is numbered and shown large, then as it prints on a sheet. Approved icons in the
same chunk are shown unnumbered for comparison. Usage: build_review.py [chunk ...]"""
import json,os,sys
from pathlib import Path
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.join(ROOT,'src'))
import blocks as B
from playwright.sync_api import sync_playwright
OUT=os.path.join(ROOT,'build','review'); os.makedirs(OUT,exist_ok=True)
CHUNKS={2:('Citrus, green, stone and tropical fruit',['citrus fruit','green fruit','green and yellow fruit','stone fruit','tropical fruit']),
        3:('Red fruit, black fruit and fruit ripeness',['red fruit','black fruit','fruit ripeness']),
        4:('Floral, herbaceous and herbal',['floral','herbaceous','herbal']),
        5:('Spice, mineral, malolactic and other primary notes',['spice','other','mineral','malolactic conversion']),
        6:('Oak and yeast',['oak','yeast']),
        7:('Tertiary notes in white and oxidised wines',['white wine','deliberately oxidised wines']),
        8:('Tertiary notes in red wines',['red wine'])}
PAIR={'p1':('Pairings: meat',['meat','lamb','pork','duck','chicken','braise','game','barbecue','burger']),
      'p2':('Pairings: fish and shellfish',['salmon','white-fish','oyster','scallop','lobster','sushi','mussels','shrimp','caviar']),
      'p3':('Pairings: dishes, cheese and nuts',['pasta','pizza','risotto','mushroom','fried','spicy','roast-vegetables','cheese','blue-cheese','soft-cheese','goat-cheese','nuts','dark-chocolate']),
      'n1':('New flavor icons and foie gras',['tar','truffle','black-olive','garrigue','dried-herbs','lavender','beeswax','honey','quince','apple','saffron','saline','tea','barrel','foie-gras'])}
ALL={i['id']:i for i in json.load(open(os.path.join(ROOT,'design-system','icons.json')))['icons']}
meta=[i for i in ALL.values() if i['family']=='flavor']
th=B.Theme({}); INK,SOFT=B.INK,B.SOFT
FD=Path(ROOT,'design-system','fonts').as_uri()+'/'
FONT=''.join(f"@font-face{{font-family:'Nunito Sans';font-weight:{w};src:url(\"{FD}nunito-sans-latin-{w}-normal.woff2\")}}" for w in (400,600,700,800))+''.join(f"@font-face{{font-family:'Poppins';font-weight:{w};src:url(\"{FD}poppins-latin-{w}-normal.woff2\")}}" for w in (600,700,800))
def card(i,num,pair=False):
    tag=f'<span style="font-family:Poppins;font-size:20px;font-weight:800">{num}</span>' if num else f'<span style="font-size:11px;font-weight:800;letter-spacing:.6px;color:{SOFT}">APPROVED</span>'
    lex=', '.join(x.replace('/',' / ') for x in i.get('lexicon',[])) or 'outside the lexicon'
    alike=f'<div style="font-size:11.5px;color:{SOFT}">Tell apart from: {", ".join(i["tell_alike"])}</div>' if i.get('tell_alike') else ''
    return (f'<div style="border:1px solid #CFC7B5;padding:10px 12px 12px;{"" if num else "background:#F6F3EC;"}display:flex;flex-direction:column;gap:6px">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline">{tag}<span style="font-size:11px;color:{SOFT}">{i["id"]}</span></div>'
            f'<div style="display:flex;align-items:flex-end;gap:14px">{B.icon(i["id"],128)}<div style="background:#fff;padding:4px">{B.pairing(th,i["id"],i["label"]) if pair else B.flavor(th,i["id"],i["label"])}</div></div>'
            f'<div style="font-family:Poppins;font-size:15px;font-weight:700">{i["label"]}</div>'
            f'<div style="font-size:12px">Covers: {", ".join(i["terms"])}</div>'+('' if pair else f'<div style="font-size:11.5px;color:{SOFT}">Lexicon: {lex}</div>')+f'{alike}</div>')
want=[a if a[0] in 'pn' else int(a) for a in sys.argv[1:]] or list(CHUNKS)+list(PAIR)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1180,'height':900},device_scale_factor=1.5)
    for n in want:
        num=0; body=''
        if n in PAIR:
            title,ids=PAIR[n]; cells=''
            for k in ids:
                i=ALL[k]
                if i['status']=='proposed': num+=1; i['_n']=num
                cells+=card(i,i.get('_n'),i['family']=='pairing')
            body=f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:18px">{cells}</div>'
        else: title,groups=CHUNKS[n]
        for g in ([] if n in PAIR else groups):
            items=[i for i in meta if i.get('group')==g]
            if not items: sys.exit(f'chunk {n}: no icons in group "{g}"')
            cells=''
            for i in items:
                if i['status']=='proposed': num+=1; i['_n']=num
                cells+=card(i,i.get('_n'))
            body+=f'<h2 style="font-family:Poppins;font-size:16px;font-weight:700;margin:22px 0 8px">{g[0].upper()+g[1:]}</h2><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">{cells}</div>'
        head=(f'<h1 style="font-family:Poppins;font-size:26px;font-weight:800;margin:0">{title if n in PAIR else f"Chunk {n} of 8: {title}"}</h1>'
              f'<p style="margin:4px 0 0;color:{SOFT};font-size:13px">{num} proposed icons, numbered. Each shows the icon at 128 px, then at the size it prints on a sheet with its label{" in the pairing circle" if str(n).startswith("p") else ", and pairing icons in the pairing circle" if n in PAIR else ""}. Shaded cards are already approved and shown for comparison.</p>')
        f=os.path.join(OUT,f'chunk-{n}.html')
        open(f,'w').write(f'<!doctype html><meta charset="utf-8"><style>{FONT}body{{margin:24px;background:#fff;color:{INK};font-family:\'Nunito Sans\';font-size:14px;line-height:1.35}}</style>{head}{body}')
        pg.goto(Path(f).as_uri()); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(300)
        pg.screenshot(path=os.path.join(OUT,f'chunk-{n}.png'),full_page=True); print(f'chunk {n}: {num} proposed')
    b.close()

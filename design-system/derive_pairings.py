#!/usr/bin/env python3
"""Rank pairing icon categories by how much of the cellar they serve.
Groups the cellar export into styles, looks up each style's sourced classic pairings in
pairing_sources.json, and weights every pairing by the style's bottle count, split evenly
across its pairings. Prints the ranking, the running share and the styles with no source.
Writes build/pairings.json. Usage: derive_pairings.py [cellar csv]"""
import csv,collections,json,os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV=sys.argv[1] if len(sys.argv)>1 else os.path.join(ROOT,'cellar','cellar-2026-11-03.csv')
SRC=json.load(open(os.path.join(ROOT,'design-system','pairing_sources.json'),encoding='utf-8'))
ICONS={i['id'] for i in json.load(open(os.path.join(ROOT,'design-system','icons.json'),encoding='utf-8'))['icons']}
def style(r):
    T,L,V=r['Type'],r['Locale'],r['Varietal']; has=lambda *xs:any(x in L for x in xs)
    if 'Fortified' in T: return 'Fortified'
    if 'Sweet' in T: return 'Sweet white'
    if 'Sparkling' in T: return 'Champagne' if has('Champagne') else 'Other sparkling'
    if T.startswith('Rosé'): return 'Rosé'
    if T=='Orange': return 'Orange'
    if T.startswith('White'):
        if has('Burgundy'): return 'White Burgundy'
        if V=='Chardonnay': return 'New World Chardonnay'
        if V=='Chenin Blanc': return 'Loire Chenin, dry'
        if V=='Riesling': return 'Riesling, dry and off-dry'
        if has('Rioja'): return 'White Rioja'
        if has('Rhône') or V=='White Rhone Blend': return 'White Rhône'
        if V in ('Sémillon-Sauvignon Blanc Blend','Sauvignon Blanc'): return 'White Bordeaux and Sauvignon'
        if has('Jura'): return 'Vin jaune'
        return 'Other white'
    if has('Burgundy'): return 'Red Burgundy'
    if V=='Pinot Noir': return 'New World Pinot Noir'
    if has('Pomerol','Saint-Émilion'): return 'Right Bank Bordeaux'
    if has('Bordeaux'): return 'Left Bank Bordeaux'
    if has('Brunello'): return 'Brunello'
    if V=='Nebbiolo': return 'Barolo'
    if has('Amarone'): return 'Amarone'
    if has('Tuscany'): return 'Tuscan reds and Super Tuscans'
    if has('Rioja','Ribera'): return 'Rioja and Ribera del Duero'
    if has('Northern Rhône'): return 'Northern Rhône Syrah'
    if has('Rhône') or V in ('Red Rhone Blend','Grenache Blend'): return 'Southern Rhône and Grenache blends'
    if V.startswith('Zinfandel') or V=='Carignane': return 'Zinfandel and Carignane'
    if has('USA','Argentina') and V in ('Cabernet Sauvignon','Red Bordeaux Blend','Merlot','Red Blend','Cabernet Franc'): return 'New World Cabernet and blends'
    return 'Other red'
rows=list(csv.DictReader(open(CSV,encoding='utf-8')))
bottles=collections.Counter(); wines=collections.defaultdict(list)
for r in rows: s=style(r); bottles[s]+=int(r['Quantity']); wines[s].append(f"{r['Vintage'].replace('1001','NV')} {r['Wine']}")
missing=[s for s in bottles if s not in SRC['styles']]
if missing: sys.exit(f'styles missing from pairing_sources.json: {missing}')
weight=collections.Counter(); reach=collections.defaultdict(set); foods=collections.defaultdict(set)
for s,n in bottles.items():
    P=SRC['styles'][s]
    for food,cat,src in P:
        if cat not in SRC['categories']: sys.exit(f'unknown category {cat} in {s}')
        if src not in SRC['sources']: sys.exit(f'unknown source {src} in {s}')
        weight[cat]+=n/len(P); reach[cat].add(s); foods[cat].add(food)
total=sum(n for s,n in bottles.items() if SRC['styles'][s]); gap=sum(n for s,n in bottles.items() if not SRC['styles'][s])
out=[]; cum=0
for cat,w in weight.most_common():
    cum+=w; b=sum(bottles[s] for s in reach[cat])
    out.append(dict(id=cat,label=SRC['categories'][cat],icon=SRC['icons'][cat],exists=SRC['icons'][cat] in ICONS,weight=round(w,1),share=round(100*w/total,1),cumulative=round(100*cum/total,1),bottles_reached=b,styles=sorted(reach[cat],key=lambda s:-bottles[s]),foods=sorted(foods[cat])))
print(f'{sum(bottles.values())} bottles in {len(bottles)} styles. {gap} bottles are in styles with no source yet.')
print(f"{'rank':>4} {'icon':18} {'have':4} {'share':>6} {'cum':>6} {'bottles':>7}")
for i,o in enumerate(out,1): print(f"{i:4d} {o['id']:18} {'yes' if o['exists'] else '':4} {o['share']:5.1f}% {o['cumulative']:5.1f}% {o['bottles_reached']:7d}")
print('no source:',', '.join(f'{s} ({bottles[s]})' for s in sorted(bottles,key=lambda s:-bottles[s]) if not SRC['styles'][s]))
os.makedirs(os.path.join(ROOT,'build'),exist_ok=True)
json.dump(dict(categories=out,styles={s:dict(bottles=bottles[s],wines=wines[s],pairings=SRC['styles'][s]) for s in sorted(bottles,key=lambda s:-bottles[s])}),open(os.path.join(ROOT,'build','pairings.json'),'w'),indent=1,ensure_ascii=False)

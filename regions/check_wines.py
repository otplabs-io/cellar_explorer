#!/usr/bin/env python3
"""Check every wine and producer record. Exit 1 on any failure.
Records must match schema/wine.schema.json and schema/producer.schema.json, and use the shared vocabularies:
flavors are flavor icon ids from design-system/icons.json, pairs are pairing icon ids (or the flavor icons the pairing
list reuses), the producer exists, and the region and grown_in ids resolve in the region tree.
Each wines/<id>/wine.json needs a "region" block:
  node       a stable id from regions/tree.json, the deepest place the label supports. A country is fine.
  tier       optional, the rank the label states within that place, such as "Premier Cru". When the node lists tiers,
             it must be one of them.
  vineyard   optional, a name below the appellation that the tree doesn't hold: a Burgundy climat, a lieu-dit,
             an Einzellage, a Barolo MGA.
  grown_in   optional, a stable id for where the vines grow when that differs from the label's place, with a source.
  placed_by  "label" (the place is on the label), "source" (a cited source, not the label) or "judgment".
  note       optional.
The check also reports when a node rests on a secondary source, so a sheet doesn't imply more than it can support."""
import glob,json,os,re,sys
import jsonschema
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T=json.load(open(os.path.join(ROOT,'regions','tree.json'),encoding='utf-8'))['nodes']
R=json.load(open(os.path.join(ROOT,'regions','redirects.json'),encoding='utf-8'))['redirects']
REG=json.load(open(os.path.join(ROOT,'regions','ids.json'),encoding='utf-8'))['ids']
SEC={f[:-5] for f in os.listdir(os.path.join(ROOT,'regions','sources')) if json.load(open(os.path.join(ROOT,'regions','sources',f),encoding='utf-8'))['source'].get('tier')=='secondary'}
def resolve(i,seen=()):
    if i in T: return i
    if i in R and i not in seen: return resolve(R[i],seen+(i,))
    return None
def chain(i):
    while i: yield i; i=T[i]['parent']
SCHEMA={k:json.load(open(os.path.join(ROOT,'schema',k+'.schema.json'),encoding='utf-8')) for k in ('wine','producer')}
ICONS=json.load(open(os.path.join(ROOT,'design-system','icons.json'),encoding='utf-8'))['icons']
FLAVOR={i['id'] for i in ICONS if i['family']=='flavor'}
PAIR={i['id'] for i in ICONS if i['family']=='pairing'}|set(json.load(open(os.path.join(ROOT,'design-system','pairing_sources.json'),encoding='utf-8'))['icons'].values())
TASTE_MIN={'red':('Body','Tannin','Acidity'),'white':('Sweetness','Body','Acidity','Oak'),'sparkling':('Sweetness','Body','Acidity','Mousse')}
LOCKED={'la-boudriotte-2019'}   # the approved reference sheet; never edited
CITE=re.compile(r"\b(critics?|reviewers?|says?|said by|per [A-Z]|according to|calls (it|for it)|(Wine )?Advocate|Vinous|Decanter|Suckling|Parker|Jancis|Burghound|Meadows|Spectator|Enthusiast|Galloni|importer|tech(nical)? sheet|no (tasting )?note|was found|own (advice|words|notes?)|our estimate|estimated?|(?<!Trois )sources?|read from|credits?|tasting notes|notes? (on|from)|puts it|finds|no pin|maps the vineyard)\b",re.I)
CITE2=re.compile(r"\b[A-Z][\w’']+(’s|'s)? (notes?|credits|describes|calls|finds|rates|advice|words|view)\b")   # 'Chanson notes', 'Ridge’s note'
def copy_fields(c):
    for k in ('intro','vintage','taste_note','flavor_note','pair_note','window_note','serve','decant','glass'):
        if isinstance(c.get(k),str): yield k,c[k]
    for i,pl in enumerate(c.get('place',[])): yield f'place {i}',' '.join(x for x in pl if isinstance(x,str))
    for i,f in enumerate(c.get('facts',[])): yield f'fact {i}',' '.join(x for x in f if isinstance(x,str))
    for i,t in enumerate(c.get('taste',[])): yield f'taste {i}',' '.join(x for x in t if isinstance(x,str))
fails=[]; notes=[]
def schema(kind,obj,who):
    for e in sorted(jsonschema.Draft202012Validator(SCHEMA[kind]).iter_errors(obj),key=lambda e:list(e.path)):
        fails.append(f"{who}: {'/'.join(str(x) for x in e.path) or '(top)'}: {e.message}")
producers={}
for f in sorted(glob.glob(os.path.join(ROOT,'producers','*','producer.json'))):
    pid=os.path.basename(os.path.dirname(f)); p=json.load(open(f,encoding='utf-8')); producers[pid]=p
    schema('producer',p,'producer '+pid)
    if p.get('id')!=pid: fails.append(f'producer {pid}: id {p.get("id")!r} must match its folder')
    if p.get('region') and not resolve(p['region']): fails.append(f"producer {pid}: region {p['region']!r} is not in the tree")
    if not os.path.exists(os.path.join(os.path.dirname(f),'sources.md')): fails.append(f'producer {pid}: no sources.md')
seen_ct={}
for f in sorted(glob.glob(os.path.join(ROOT,'wines','*','wine.json'))):
    w=os.path.basename(os.path.dirname(f)); rec=json.load(open(f,encoding='utf-8')); r=rec.get('region')
    if 'TODO' in open(f,encoding='utf-8').read(): notes.append(f'{w}: scaffold, still being written'); continue
    schema('wine',rec,w)
    if rec.get('id')!=w: fails.append(f'{w}: id {rec.get("id")!r} must match its folder')
    if not os.path.exists(os.path.join(os.path.dirname(f),'sources.md')): fails.append(f'{w}: no sources.md')
    idn=rec.get('identity') or {}; c=rec.get('content') or {}
    if idn.get('producer') and idn['producer'] not in producers: fails.append(f"{w}: producer {idn['producer']!r} has no producers/{idn['producer']}/producer.json")
    for k,_ in c.get('flavors',[]):
        if k not in FLAVOR: fails.append(f'{w}: flavor {k!r} is not a flavor icon')
    for k,_ in c.get('pairs',[]):
        if k not in PAIR: fails.append(f'{w}: pairing {k!r} is not a pairing icon')
    # every applicable taste row is filled, a best estimate when nothing definitive exists (Chris, 2026-11-05)
    rows={label for _,label,_ in c.get('taste',[])}
    need=TASTE_MIN.get(idn.get('style'),())
    if missing:=[x for x in need if x not in rows]: fails.append(f"{w}: a {idn['style']} sheet needs taste rows {missing}")
    # sheet copy never names a source or says one is missing; that lives in sources.md (Chris, 2026-11-05)
    if w not in LOCKED:
        for where,text in list(copy_fields(c))+[(k,' '.join(v) if isinstance(v,list) else v) for k,v in rec.items() if k.endswith('_note') and isinstance(v,(str,list))]:
            if m:=CITE.search(text) or CITE2.search(text): fails.append(f"{w}: {where} cites a source inline ({m.group(0)!r}); move it to sources.md")
    if idn.get('style') in ('sparkling','dessert','fortified') and not idn.get('color'): fails.append(f"{w}: a {idn['style']} wine needs identity.color")
    for ct in idn.get('cellartracker',[]):
        if ct in seen_ct: fails.append(f'{w}: CellarTracker id {ct} is also claimed by {seen_ct[ct]}')
        seen_ct[ct]=w
    if not r: fails.append(f'{w}: no "region" block'); continue
    n=resolve(r.get('node',''))
    if not n:
        why='retired' if REG.get(r.get('node'),{}).get('retired') else 'unknown'
        fails.append(f"{w}: region node {r.get('node')!r} is {why}; add a redirect or fix the record"); continue
    if n!=r['node']: notes.append(f"{w}: {r['node']} redirects to {n}; update the record")
    if r.get('placed_by') not in ('label','source','judgment'): fails.append(f'{w}: placed_by must be label, source or judgment')
    tiers=T[n].get('tiers')
    if r.get('tier') and tiers and r['tier'] not in tiers: fails.append(f"{w}: tier {r['tier']!r} isn't one of {tiers} for {T[n]['name']}")
    if r.get('grown_in') and not resolve(r['grown_in']): fails.append(f"{w}: grown_in {r['grown_in']!r} is not in the tree")
    if any(T[a].get('source') in SEC or set(T[a].get('sources',[]))&SEC for a in chain(n)): notes.append(f'{w}: {T[n]["name"]} rests on a secondary source')
    # what the region profile asks of the record
    sys.path.insert(0,os.path.join(ROOT,'src')); import profiles
    prof=profiles.for_node(n); sig=prof['story'].get('signature')
    if sig and c.get('level'):
        allowed=sig.get('tiers') or [t for t,_ in sig.get('terms',[])] or ([T[n]['name']] if sig['component']=='ava_nest' else [])
        if c['level'] not in allowed: fails.append(f"{w}: level {c['level']!r} isn't one of {allowed} in the {sig['component']}")
    if prof['map'].get('engine')=='villages':
        if not rec.get('map_villages') and not rec.get('map_villages_note'): fails.append(f'{w}: the village map needs map_villages, or map_villages_note saying why none are named')
        for node,_ in rec.get('map_villages',[]):
            if not resolve(node) or not T[resolve(node)].get('commune'): fails.append(f'{w}: map village {node!r} is not a village with a commune code in the tree')
    for head,_,key in prof['serve_cells']:
        if not c.get(key): notes.append(f'{w}: no {key!r} text, so the {head} cell drops out')
    path=' > '.join(T[a]['name'] for a in reversed(list(chain(n))))
    print(f"{w}: {path}" + (f", {r['tier']}" if r.get('tier') else '') + (f", {r['vineyard']}" if r.get('vineyard') else '') + f" (from the {r['placed_by']})")
for x in notes: print('note', x)
for x in fails: print('FAIL', x)
sys.exit(1 if fails else 0)

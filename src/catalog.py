#!/usr/bin/env python3
"""Build build/catalog.json, the one file the browse page filters.
One entry per CellarTracker wine in the cellar (archived bottles are left out), joining the inventory, the wine
record when there is one, the region tree and the icon vocabularies. A wine with a record carries its full profile:
structure dots, aromas, pairings and its sheet. A wine without one carries a basic card from the inventory data.
No price ever enters the inventory, so none can reach the catalog."""
import datetime,glob,json,os,re,sqlite3,sys
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
ROOT=os.path.dirname(HERE)
import records,inventory
TREE=json.load(open(os.path.join(ROOT,'regions','tree.json'),encoding='utf-8'))['nodes']
ICONS={i['id']:i for i in json.load(open(os.path.join(ROOT,'design-system','icons.json'),encoding='utf-8'))['icons']}
PS=json.load(open(os.path.join(ROOT,'design-system','pairing_sources.json'),encoding='utf-8'))
PAIR_CAT={icon:cat for cat,icon in PS['icons'].items()}
STYLE={'Red':'red','White':'white','Rosé':'rosé','Orange':'orange','White - Sparkling':'sparkling','Rosé - Sparkling':'sparkling','Red - Sparkling':'sparkling',
       'White - Sweet/Dessert':'dessert','Red - Sweet/Dessert':'dessert','Rosé - Sweet/Dessert':'dessert','White - Fortified':'fortified','Red - Fortified':'fortified','White - Off-dry':'white'}
def up(i):
    while i: yield i; i=TREE[i]['parent']
def region(node,tier=None,vineyard=None):
    if not node: return None
    chain=list(reversed(list(up(node))))
    return dict(node=node,tier=tier,vineyard=vineyard,path=chain,names=[TREE[i]['name'] for i in chain],country=TREE[chain[0]]['name'])
def num(x):
    try: return float(x)
    except (TypeError,ValueError): return None
def year(x):
    try: y=int(x); return None if y>=9999 or y<1000 else y
    except (TypeError,ValueError): return None
def build():
    db=inventory.connect()
    recs={}
    for f in glob.glob(os.path.join(ROOT,'wines','*','wine.json')):
        if 'TODO' in open(f,encoding='utf-8').read(): continue   # a scaffold still being written
        rec=records.load_wine(f)
        for ct in (rec.get('identity') or {}).get('cellartracker',[]): recs[ct]=rec
    items={}
    for b in db.execute("select * from bottles where status='cellar' order by key"):
        d=json.loads(b['data']); iw=b['iwine']
        it=items.get(iw)
        if it: it['sizes'].append(dict(size=b['size'],quantity=b['quantity'])); it['quantity']+=b['quantity']; continue
        rec=recs.get(iw)
        v=d.get('Vintage',''); vintage='NV' if v in ('1001','') else (int(v) if v.isdigit() else v)
        it=dict(iwine=iw,sizes=[dict(size=b['size'],quantity=b['quantity'])],quantity=b['quantity'],
                vintage=vintage,cellartracker=dict(wine=d.get('Wine'),producer=d.get('Producer'),type=d.get('Type'),varietal=d.get('Varietal'),locale=d.get('Locale'),
                                                   community_score=num(d.get('CScore'))),
                location=' '.join(x for x in (d.get('Location'),d.get('Bin')) if x) or None)
        if rec:
            idn=rec['identity']; c=rec['content']; r=rec['region']; p=records.producer(idn['producer'])
            it.update(status='sheet',record=rec['id'],name=idn['name'],producer=p['name'],style=idn['style'],color=idn.get('color') or {'red':'red','white':'white','rosé':'rosé','orange':'orange'}.get(idn['style']),
                      grapes=[g['name'] for g in idn['grapes']],alcohol=idn.get('alcohol'),region=region(TREE.get(r['node']) and r['node'],r.get('tier'),r.get('vineyard')),
                      structure={label.lower():dots for dots,label,_ in c['taste']},
                      aromas=[dict(id=k,label=lbl,stage=ICONS[k].get('stage'),group=ICONS[k].get('group')) for k,lbl in c['flavors']],
                      pairings=[dict(id=k,label=lbl,category=PAIR_CAT.get(k,k)) for k,lbl in c['pairs']],
                      window=dict(start=c['window'][0],end=c['window'][1],source='sheet') if c.get('window') else None,   # some sheets have no sourced window
                      intro=c.get('intro'),theme=rec.get('theme','white'),
                      sheet=dict(pdf=f"build/{rec['id']}/sheet.pdf",web=f"build/{rec['id']}/sheet.web.html",ready=os.path.exists(os.path.join(ROOT,'build',rec['id'],'sheet.pdf'))))
        else:
            ct=d.get('Type','')
            it.update(status='card',record=None,name=d.get('Wine'),producer=d.get('Producer'),style=STYLE.get(ct,ct.split(' - ')[0].lower() or None),color=(d.get('Color') or '').lower() or None,
                      grapes=[d.get('Varietal')] if d.get('Varietal') else [],alcohol=None,region=region(b['region_node'],b['region_tier']),
                      structure=None,aromas=[],pairings=[],
                      window=dict(start=year(d.get('BeginConsume')),end=year(d.get('EndConsume')),source='cellartracker') if year(d.get('BeginConsume')) or year(d.get('EndConsume')) else None,
                      intro=None,theme=None,sheet=None)
        items[iw]=it
    wines=sorted(items.values(),key=lambda x:((x['region'] or {}).get('country') or '',x['producer'] or '',str(x['vintage'])))
    count=lambda f:sorted(((k,n) for k,n in __import__('collections').Counter(x for w in wines for x in f(w)).items()),key=lambda kv:-kv[1])
    facets=dict(style=count(lambda w:[w['style']] if w['style'] else []),country=count(lambda w:[w['region']['country']] if w['region'] else []),
                grape=count(lambda w:w['grapes']),aroma=count(lambda w:[a['id'] for a in w['aromas']]),pairing=count(lambda w:[p['category'] for p in w['pairings']]))
    out=dict(generated=datetime.datetime.now().isoformat(timespec='seconds'),wines=len(wines),bottles=sum(w['quantity'] for w in wines),
             with_sheet=sum(1 for w in wines if w['status']=='sheet'),facets=facets,items=wines)
    os.makedirs(os.path.join(ROOT,'build'),exist_ok=True)
    json.dump(out,open(os.path.join(ROOT,'build','catalog.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    return out
if __name__=='__main__':
    o=build(); print(f"{o['wines']} wines, {o['bottles']} bottles, {o['with_sheet']} with a sheet. build/catalog.json")

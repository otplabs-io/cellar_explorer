#!/usr/bin/env python3
"""Render regions/tree.json as one browsable, searchable page: build/regions/region-tree.html.
Shows each place's official designation in its country's own terms, marks Chris's own entries,
and counts the cellar's bottles at each place (from build/region-coverage.json)."""
import json,os,re,unicodedata
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T=json.load(open(os.path.join(ROOT,'regions','tree.json'),encoding='utf-8'))['nodes']
COV=json.load(open(os.path.join(ROOT,'build','region-coverage.json'),encoding='utf-8'))
SRC={f[:-5]:json.load(open(os.path.join(ROOT,'regions','sources',f),encoding='utf-8'))['source'] for f in os.listdir(os.path.join(ROOT,'regions','sources'))}
norm=lambda s:re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip()
docg={norm(e['name']) for e in json.load(open(os.path.join(ROOT,'regions','sources','it-groups.json'),encoding='utf-8'))['entries'] if e['kind']=='DOCG'}
LOCAL={'france':('AOC','IGP'),'italy':('DOC','IGT'),'spain':('DO','IGP'),'portugal':('DOC','IGP'),'germany':('PDO','Landwein'),'austria':('PDO','Landwein'),'greece':('PDO','PGI'),'hungary':('PDO','PGI')}
def tag(v):
    c=v['id'].split('/')[0]; o=v.get('official') or []
    if 'PDO' in o:
        if c=='italy': return 'DOCG' if norm(v['name']) in docg else 'DOC'
        return LOCAL.get(c,('PDO','PGI'))[0]
    if 'PGI' in o: return LOCAL.get(c,('PDO','PGI'))[1]
    for k in ('AVA','DOC','IG','GI','sub-GI','sub-appellation','regional appellation','appellation','enduring GI'):
        if k in o: return {'enduring GI':'GI','regional appellation':'appellation'}.get(k,k)
    return ''
SECONDARY={k for k,s in SRC.items() if s.get('tier')=='secondary'}
bottles={}
for p in COV['cellar']:
    n=p['node']
    while n: bottles[n]=bottles.get(n,0)+p['bottles']; n=T[n]['parent']
roots=[i for i,v in T.items() if v['parent'] is None]
order={'united-states':0,'france':1,'italy':2,'spain':3}
roots.sort(key=lambda i:(order.get(i,9),-bottles.get(i,0),T[i]['name']))
ids=[]; index={}
def walk(i):
    index[i]=len(ids); ids.append(i)
    kids=sorted(T[i]['children'],key=lambda k:(T[k].get('source')!='chris',T[k]['name'].lower()))
    for k in kids: walk(k)
for r in roots: walk(r)
rows=[]
for i in ids:
    v=T[i]; src=v.get('source') or ''
    rows.append([v['name'],index[v['parent']] if v['parent'] else -1,tag(v),', '.join(v.get('tiers',[])),1 if src=='chris' else 0,bottles.get(i,0),1 if (src in SECONDARY or any(s in SECONDARY for s in v.get('sources',[]))) else 0,'; '.join(a for a in v.get('also',[]) if a and a!=v['name'])[:120]])
countries=len(roots); total=len(ids); cellar=sum(p['bottles'] for p in COV['cellar'])
DATA=json.dumps(rows,ensure_ascii=False,separators=(',',':'))
html=open(os.path.join(ROOT,'regions','tree_page_template.html'),encoding='utf-8').read()
html=html.replace('__DATA__',DATA).replace('__TOTAL__',f'{total:,}').replace('__COUNTRIES__',str(countries)).replace('__BOTTLES__',str(cellar))
os.makedirs(os.path.join(ROOT,'build','regions'),exist_ok=True)
open(os.path.join(ROOT,'build','regions','region-tree.html'),'w',encoding='utf-8').write(html)
print(f'{total} places, {countries} countries, {len(DATA)//1024} KB of data')

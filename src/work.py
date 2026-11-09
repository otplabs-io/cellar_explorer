#!/usr/bin/env python3
"""The work queue for the /bottle command: which cellar wines still need a sheet, which can be built now, and what
happened to each. State lives in data/pour.db (table work), next to the inventory.

  work.py status                     counts by state, and the regions waiting for a profile
  work.py list [--ready] [--region ID] [--limit N]
  work.py next [--region ID]         the next ready wine, as JSON, marked in progress
  work.py show IWINE                 one wine's brief, as JSON
  work.py done IWINE WINE_ID         a sheet went live
  work.py skip IWINE "reason"        set aside, with the reason (a missing source, an unclear label)
  work.py reset IWINE                back to the queue

A wine is ready when its region's profile has a map engine whose "covers" list includes the wine's place. Other
wines stay as basic cards in the app until their region is built. Order: most bottles first, then region."""
import argparse,datetime,glob,json,os,re,sqlite3,sys,unicodedata
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
ROOT=os.path.dirname(HERE)
import inventory,profiles,catalog
def norm(s): return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode().lower())
STATE=os.path.join(ROOT,'cellar','work-state.json')   # a copy of the work table in git: data/pour.db is not, and set-aside reasons can't be rebuilt
def db():
    d=inventory.connect()
    d.execute('create table if not exists work(iwine text primary key, status text, wine_id text, note text, updated text)')
    if not d.execute('select count(*) from work').fetchone()[0] and os.path.exists(STATE):   # a fresh database: bring the states back
        for r in json.load(open(STATE,encoding='utf-8'))['wines']: d.execute('insert into work values (?,?,?,?,?)',(r['iwine'],r['status'],r.get('wine_id'),r.get('note'),r.get('updated')))
        d.commit()
    return d
def save(d):
    rows=[dict(r) for r in d.execute('select * from work order by iwine')]
    json.dump(dict(comment='The /bottle queue states from data/pour.db, kept in git. work.py loads them into a fresh database.',wines=rows),open(STATE,'w',encoding='utf-8'),indent=1,ensure_ascii=False)
def records():
    out={}
    for f in glob.glob(os.path.join(ROOT,'wines','*','wine.json')):
        r=json.load(open(f,encoding='utf-8'))
        for ct in (r.get('identity') or {}).get('cellartracker',[]): out[ct]=r['id']
    return out
def producers():
    out={}
    for f in glob.glob(os.path.join(ROOT,'producers','*','producer.json')):
        p=json.load(open(f,encoding='utf-8'))
        for n in [p['name']]+p.get('also',[]): out[norm(n)]=p['id']
    return out
def coverage(node,style):
    """The profile chain for a place, and whether its map engine covers it and its sheet suits the wine's style."""
    if not node: return None,False
    prof=profiles.for_node(node); cov=prof['map'].get('covers',[]); chain=set(profiles.chain(node))
    return prof,bool(prof['map'].get('engine')) and any(c in chain for c in cov) and style in prof.get('styles',[style])
def wines(d):
    have=records(); prods=producers(); st={r['iwine']:dict(r) for r in d.execute('select * from work')}; out={}
    for b in d.execute("select * from bottles where status='cellar' order by key"):
        iw=b['iwine']; row=json.loads(b['data'])
        if iw in out: out[iw]['bottles']+=b['quantity']; out[iw]['sizes'].append(b['size']); continue
        ct=row.get('Type',''); style=catalog.STYLE.get(ct,ct.split(' - ')[0].lower())
        prof,ready=coverage(b['region_node'],style)
        w=st.get(iw,{})
        status='done' if iw in have else w.get('status') or ('ready' if ready else 'waiting')
        if status in ('ready','waiting') and w.get('status') in ('in_progress','skipped'): status=w['status']
        out[iw]=dict(iwine=iw,status=status,wine_id=have.get(iw) or w.get('wine_id'),note=w.get('note'),bottles=b['quantity'],sizes=[b['size']],
                     vintage=row.get('Vintage','').replace('1001','NV'),wine=row.get('Wine'),producer=row.get('Producer'),producer_record=prods.get(norm(row.get('Producer'))),
                     type=row.get('Type'),style=style,color=row.get('Color'),varietal=row.get('Varietal'),locale=row.get('Locale'),
                     region=b['region_node'],tier=b['region_tier'],region_path=profiles.tree()[b['region_node']]['path'] if b['region_node'] else None,
                     profiles=prof['$used'] if prof else [],map_engine=prof['map'].get('engine') if prof and ready else None,
                     window_cellartracker=[row.get('BeginConsume'),row.get('EndConsume')])
    return sorted(out.values(),key=lambda w:(-w['bottles'],w['region_path'] or '',w['wine'] or ''))
def mark(d,iw,status,wine_id=None,note=None):
    d.execute('insert or replace into work values (?,?,?,?,?)',(iw,status,wine_id,note,datetime.datetime.now().isoformat(timespec='seconds'))); d.commit(); save(d)
if __name__=='__main__':
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True)
    sp.add_parser('status')
    l=sp.add_parser('list'); l.add_argument('--ready',action='store_true'); l.add_argument('--region'); l.add_argument('--limit',type=int,default=50)
    n=sp.add_parser('next'); n.add_argument('--region')
    s=sp.add_parser('show'); s.add_argument('iwine')
    x=sp.add_parser('done'); x.add_argument('iwine'); x.add_argument('wine_id')
    k=sp.add_parser('skip'); k.add_argument('iwine'); k.add_argument('reason')
    r=sp.add_parser('reset'); r.add_argument('iwine')
    a=ap.parse_args(); d=db(); W=wines(d)
    inreg=lambda w,reg:not reg or (w['region'] and reg in profiles.chain(w['region']))
    if a.cmd=='status':
        from collections import Counter
        c=Counter(w['status'] for w in W); print(', '.join(f'{k}: {v}' for k,v in sorted(c.items())))
        wait=Counter('/'.join((w['region_path'] or 'unplaced').split('/')[:2]) for w in W if w['status']=='waiting')
        print('Waiting for a region profile:',', '.join(f'{k} {v}' for k,v in wait.most_common(12)))
    elif a.cmd=='list':
        for w in [w for w in W if (not a.ready or w['status']=='ready') and inreg(w,a.region)][:a.limit]:
            print(f"{w['status']:11} {w['iwine']:>8} {w['bottles']}x {w['vintage']} {w['wine']}  [{w['region_path']}]")
    elif a.cmd=='next':
        w=next((w for w in W if w['status']=='ready' and inreg(w,a.region)),None)
        if not w: sys.exit('Nothing ready'+(f' in {a.region}' if a.region else '')+'. Run work.py status.')
        mark(d,w['iwine'],'in_progress'); w['status']='in_progress'; print(json.dumps(w,ensure_ascii=False,indent=1))
    elif a.cmd=='show':
        w=next((w for w in W if w['iwine']==a.iwine),None) or sys.exit(f'{a.iwine} is not in the cellar')
        print(json.dumps(w,ensure_ascii=False,indent=1))
    elif a.cmd=='done': mark(d,a.iwine,'done',a.wine_id); print(f'{a.iwine} done: {a.wine_id}')
    elif a.cmd=='skip': mark(d,a.iwine,'skipped',None,a.reason); print(f'{a.iwine} skipped: {a.reason}')
    elif a.cmd=='reset': d.execute('delete from work where iwine=?',(a.iwine,)); d.commit(); print(f'{a.iwine} back in the queue')

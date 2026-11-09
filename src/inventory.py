#!/usr/bin/env python3
"""The cellar inventory, kept in data/pour.db (SQLite) and rebuilt from the exports in cellar/.

  inventory.py import <export.csv> [--date YYYY-MM-DD]   compare an export with the cellar and apply it
  inventory.py rebuild                                   replay every export in cellar/ in date order
  inventory.py status                                    counts, and the bottles waiting for a sheet
  inventory.py replace                                   place every bottle again, after the tree or the placer changes

An import keeps a dated UTF-8 copy of the export in cellar/, then compares it with the bottles in the cellar:
bottles new to the export are added (or brought back, if they were archived), bottles missing from it are archived
with the date, and quantities are updated. Nothing is deleted. Price columns are dropped on the way in, so no price
reaches the database. A bottle is one CellarTracker wine (iWine) in one bottle size."""
import argparse,csv,datetime,hashlib,html,io,json,os,re,sqlite3,sys
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
ROOT=os.path.dirname(HERE)
DB=os.path.join(ROOT,'data','pour.db'); CELLAR=os.path.join(ROOT,'cellar')
PRICE=re.compile(r'price|value|cost|paid|purchase|auction|valuation|\$',re.I)
def xlsx_text(path):
    """The first sheet of an Excel workbook as CSV text, read with the standard library (an .xlsx is zipped XML)."""
    import zipfile,xml.etree.ElementTree as ET
    ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    z=zipfile.ZipFile(path); names=z.namelist()
    shared=[''.join(t.text or '' for t in si.iter('{%s}t'%ns['m'])) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',ns)] if 'xl/sharedStrings.xml' in names else []
    sheet=sorted(n for n in names if re.match(r'xl/worksheets/sheet\d+\.xml$',n))[0]
    col=lambda ref:sum((ord(c)-64)*26**i for i,c in enumerate(reversed(re.match(r'[A-Z]+',ref).group())))-1
    rows=[]
    for r in ET.fromstring(z.read(sheet)).iter('{%s}row'%ns['m']):
        cells={}
        for c in r.findall('m:c',ns):
            t=c.get('t'); v=c.find('m:v',ns); x=v.text if v is not None else ''.join(i.text or '' for i in c.iter('{%s}t'%ns['m']))
            if t=='s' and x: x=shared[int(x)]
            elif x and re.fullmatch(r'-?\d+\.0',x): x=x[:-2]   # whole numbers stored as floats
            cells[col(c.get('r'))]=x or ''
        if cells: rows.append([cells.get(i,'') for i in range(max(cells)+1)])
    out=io.StringIO(); csv.writer(out,quoting=csv.QUOTE_ALL,lineterminator='\r\n').writerows(rows); return out.getvalue()
def read_export(path):
    if path.lower().endswith(('.xlsx','.xlsm')): text=xlsx_text(path)
    else:
      raw=open(path,'rb').read()
      for enc in ('utf-8-sig','cp1252','latin-1'):
        try: text=raw.decode(enc); break
        except UnicodeDecodeError: continue
    text=html.unescape(text).replace('​','')
    rows=list(csv.DictReader(io.StringIO(text)))
    if not rows or 'iWine' not in rows[0]: sys.exit(f'{path}: not a CellarTracker export (no iWine column)')
    dropped=[k for k in rows[0] if PRICE.search(k)]
    rows=[{k:v for k,v in r.items() if k not in dropped} for r in rows]
    if dropped:   # the saved copy must not hold prices either
        out=io.StringIO(); w=csv.DictWriter(out,fieldnames=list(rows[0]),quoting=csv.QUOTE_ALL,lineterminator='\r\n')
        w.writeheader(); w.writerows(rows); text=out.getvalue()
    return text,rows,dropped
def key(r): return f"{r['iWine']}|{r.get('Size') or '750ml'}"
def connect():
    os.makedirs(os.path.dirname(DB),exist_ok=True)
    db=sqlite3.connect(DB); db.row_factory=sqlite3.Row
    db.executescript('''
      create table if not exists bottles(key text primary key, iwine text, size text, status text, quantity integer,
        data text, region_node text, region_tier text, first_seen text, last_seen text, archived_on text);
      create table if not exists imports(id integer primary key, file text, date text, sha text, added integer,
        returned integer, archived integer, changed integer, unchanged integer, dropped_columns text);''')
    return db
def snapshot(text,date):
    """Keep a UTF-8 copy of the export, named by date, so `rebuild` can replay the imports in order.
    Returns its path; an export identical to the latest copy reuses that copy."""
    sha=hashlib.sha256(text.encode()).hexdigest()
    files=sorted(f for f in os.listdir(CELLAR) if f.endswith('.csv'))
    if files and hashlib.sha256(open(os.path.join(CELLAR,files[-1]),'rb').read()).hexdigest()==sha: return os.path.join(CELLAR,files[-1]),sha
    name=f'cellar-{date}.csv'; n=2
    while os.path.exists(os.path.join(CELLAR,name)): name=f'cellar-{date}-{n}.csv'; n+=1
    open(os.path.join(CELLAR,name),'w',encoding='utf-8',newline='').write(text); return os.path.join(CELLAR,name),sha
def apply(db,rows,date,file,sha,dropped,quiet=False,commit=True):
    import places
    P=places.Placer()
    now={key(r):r for r in rows}
    have={r['key']:r for r in db.execute('select * from bottles')}
    added=returned=archived=changed=unchanged=0; log=[]
    for k,r in now.items():
        q=int(r.get('Quantity') or 0); node,tier,_=P.place(r.get('Locale',''),r.get('Wine',''))
        data=json.dumps(r,ensure_ascii=False)
        if k not in have:
            db.execute('insert into bottles values (?,?,?,?,?,?,?,?,?,?,?)',(k,r['iWine'],r.get('Size'),'cellar',q,data,node,tier,date,date,None)); added+=1; log.append(('added',r,q))
        else:
            h=have[k]
            if h['status']=='archived': returned+=1; log.append(('back',r,q))
            elif h['quantity']!=q: changed+=1; log.append(('quantity',r,f"{h['quantity']} to {q}"))
            else: unchanged+=1
            db.execute('update bottles set status=?,quantity=?,data=?,region_node=?,region_tier=?,last_seen=?,archived_on=null where key=?',('cellar',q,data,node,tier,date,k))
    for k,h in have.items():
        if k not in now and h['status']=='cellar':
            db.execute('update bottles set status=?,archived_on=? where key=?',('archived',date,k)); archived+=1; log.append(('archived',json.loads(h['data']),h['quantity']))
    db.execute('insert into imports(file,date,sha,added,returned,archived,changed,unchanged,dropped_columns) values (?,?,?,?,?,?,?,?,?)',
               (os.path.relpath(file,ROOT),date,sha,added,returned,archived,changed,unchanged,json.dumps(dropped)))
    if not commit: db.rollback(); return dict(added=added,returned=returned,archived=archived,changed=changed,unchanged=unchanged,log=log)   # a dry run
    db.commit()
    if not quiet:
        print(f'{os.path.relpath(file,ROOT)} ({date}): {added} added, {returned} back from the archive, {archived} archived, {changed} with a new quantity, {unchanged} unchanged.')
        if dropped: print('Dropped price columns:',', '.join(dropped))
        for what,r,x in log:
            v=r.get('Vintage','').replace('1001','NV'); print(f"  {what:8} {v} {r.get('Wine','')} ({r.get('Size','')}): {x}")
    return dict(added=added,returned=returned,archived=archived,changed=changed,unchanged=unchanged)
def records_by_ct():
    import glob
    out={}
    for f in glob.glob(os.path.join(ROOT,'wines','*','wine.json')):
        rec=json.load(open(f,encoding='utf-8'))
        for ct in (rec.get('identity') or {}).get('cellartracker',[]): out[ct]=rec['id']
    return out
def queue(db):
    """Bottles in the cellar with no wine record yet: what the bottle command builds next. Written to build/queue.json."""
    have=records_by_ct(); q=[]
    for r in db.execute("select * from bottles where status='cellar' order by key"):
        if r['iwine'] not in have:
            d=json.loads(r['data']); q.append(dict(iwine=r['iwine'],size=r['size'],quantity=r['quantity'],wine=d.get('Wine'),vintage=d.get('Vintage','').replace('1001','NV'),locale=d.get('Locale'),region=r['region_node'],tier=r['region_tier']))
    seen=set(); uq=[x for x in q if not (x['iwine'] in seen or seen.add(x['iwine']))]
    os.makedirs(os.path.join(ROOT,'build'),exist_ok=True)
    json.dump(dict(comment='Wines in the cellar that have no wine record yet, one per CellarTracker wine.',wines=uq),open(os.path.join(ROOT,'build','queue.json'),'w',encoding='utf-8'),indent=1,ensure_ascii=False)
    return uq
if __name__=='__main__':
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True)
    i=sp.add_parser('import'); i.add_argument('csv'); i.add_argument('--date',default=datetime.date.today().isoformat())
    sp.add_parser('rebuild'); sp.add_parser('status'); sp.add_parser('replace')
    a=ap.parse_args()
    if a.cmd=='import':
        text,rows,dropped=read_export(a.csv); path,sha=snapshot(text,a.date); db=connect()
        last=db.execute('select sha from imports order by id desc limit 1').fetchone()
        if last and last['sha']==sha: print(f'{os.path.relpath(path,ROOT)} matches the last import. Nothing changed.')
        else: apply(db,rows,a.date,path,sha,dropped)
        print(f'{len(queue(db))} wines wait for a sheet (build/queue.json).')
    elif a.cmd=='rebuild':
        if os.path.exists(DB): os.remove(DB)
        db=connect()
        files=sorted(f for f in os.listdir(CELLAR) if f.endswith('.csv'))
        for f in files:
            m=re.search(r'(\d{4}-\d{2}-\d{2})',f); p=os.path.join(CELLAR,f)
            text,rows,dropped=read_export(p); apply(db,rows,m.group(1),p,hashlib.sha256(text.encode()).hexdigest(),dropped,quiet=True)
        print(f'Rebuilt from {len(files)} exports. {len(queue(db))} wines wait for a sheet.')
    elif a.cmd=='replace':   # place every bottle again on the current tree, keeping everything else
        import places; P=places.Placer(); db=connect(); moved=0
        for b in db.execute('select key,data,region_node,region_tier from bottles').fetchall():
            r=json.loads(b['data']); node,tier,_=P.place(r.get('Locale',''),r.get('Wine',''))
            if (node,tier)!=(b['region_node'],b['region_tier']):
                moved+=1; print(f"  {r.get('Vintage','')} {r.get('Wine','')}: {b['region_node']} -> {node}")
                db.execute('update bottles set region_node=?,region_tier=? where key=?',(node,tier,b['key']))
        db.commit(); print(f'{moved} bottles moved.'); queue(db)
    else:
        db=connect()
        for s,n,q in db.execute('select status,count(*),sum(quantity) from bottles group by status'): print(f'{s}: {n} listings, {q} bottles')
        print(f'{len(queue(db))} wines wait for a sheet (build/queue.json).')

#!/usr/bin/env python3
"""Restock: take a new CellarTracker export into the app safely. The /restock command runs these steps in order.

  restock.py check <export.csv|.xlsx>          read the file and show what would change, writing nothing
  restock.py apply <export> [--yes]            import it, rebuild the catalog, list the new wines and whether they can be built
  restock.py publish                           build the site in a new folder, test it, then switch the app to it
  restock.py rollback                          switch the app back to the previous build
  restock.py status                            which build is live, and the ones kept for rollback

`check` and `apply` stop when the export would archive a large share of the cellar (more than 20%, or more than 10
listings): that is almost always a filtered or partial export. `apply --yes` goes ahead after the user has said so.
`publish` never touches the live site until the new one has passed `check_wines.py` and `tests/app_smoke.py`. The live
site is build/site, a link to build/site-<time>; the server reads through the link, so the switch needs no restart.
Exit codes: 0 done, 1 the file or a check failed, 3 waiting for the user to confirm."""
import argparse,datetime,hashlib,json,os,shutil,socket,subprocess,sys,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
ROOT=os.path.dirname(HERE); BUILD=os.path.join(ROOT,'build'); LIVE=os.path.join(BUILD,'site'); PY=sys.executable
import inventory,work,profiles,catalog
NEED=['iWine','Wine','Vintage','Quantity','Locale','Type']
WANT=['Size','Producer','Varietal','BeginConsume','EndConsume','Color']
KEEP=3   # builds kept: the live one and two to roll back to
def nice(r): return f"{(r.get('Vintage') or '').replace('1001','NV')} {r.get('Wine','')}".strip()
def examine(path):
    """Read the export and work out what an import would do, without writing anything."""
    if not os.path.exists(path): return dict(result='invalid',problems=[f'No file at {path}.'])
    try: text,rows,dropped=inventory.read_export(path)
    except SystemExit as e: return dict(result='invalid',problems=[str(e)])
    except Exception as e: return dict(result='invalid',problems=[f'Could not read {os.path.basename(path)}: {e}'])
    cols=list(rows[0]) if rows else []; problems=[]; notes=[]
    miss=[c for c in NEED if c not in cols]
    if miss: problems.append('Missing columns: '+', '.join(miss)+'. Export "My Cellar" from CellarTracker as CSV, with every column.')
    if not rows: problems.append('The file has no wines in it.')
    if problems: return dict(result='invalid',problems=problems)
    if [c for c in WANT if c not in cols]: notes.append('Columns not in this export (sheets will have less to go on): '+', '.join(c for c in WANT if c not in cols))
    bad=[nice(r) for r in rows if not (r.get('iWine') or '').strip().isdigit()]
    if bad: problems.append(f'{len(bad)} rows have no CellarTracker wine id (iWine), e.g. {bad[:3]}')
    badq=[nice(r) for r in rows if not str(r.get('Quantity') or '0').strip().isdigit()]
    if badq: problems.append(f'{len(badq)} rows have a quantity that is not a whole number, e.g. {badq[:3]}')
    keys=[inventory.key(r) for r in rows]; dup=sorted({k for k in keys if keys.count(k)>1})
    if dup: problems.append(f'{len(dup)} wines appear twice in the same bottle size, e.g. {dup[:3]}')
    if problems: return dict(result='invalid',problems=problems)
    db=inventory.connect(); sha=hashlib.sha256(text.encode()).hexdigest()
    last=db.execute('select sha from imports order by id desc limit 1').fetchone()
    if last and last['sha']==sha: return dict(result='unchanged',rows=len(rows),dropped=dropped,notes=notes)
    cellar=db.execute("select count(*) from bottles where status='cellar'").fetchone()[0]
    d=inventory.apply(db,rows,datetime.date.today().isoformat(),path,sha,dropped,quiet=True,commit=False)
    limit=max(10,int(cellar*.2)); big=cellar and d['archived']>limit
    # the wines that are new to the app: where they land on the region tree, and whether a sheet can be built now
    import places; P=places.Placer(); T=profiles.tree(); new=[]; seen=set()
    for what,r,q in d['log']:
        if what not in ('added','back') or r['iWine'] in seen: continue
        seen.add(r['iWine']); node,tier,_=P.place(r.get('Locale',''),r.get('Wine',''))
        style=catalog.STYLE.get(r.get('Type',''),(r.get('Type') or '').split(' - ')[0].lower())
        _,ready=work.coverage(node,style); depth=len(T[node]['path'].split('/')) if node else 0
        new.append(dict(iwine=r['iWine'],wine=nice(r),locale=r.get('Locale'),place=node,ready=ready,
                        flag=None if node and depth>2 else ('could not be placed on the region tree' if not node else f'placed only as far as {T[node]["name"]}')))
    return dict(result='confirm' if big else 'ok',rows=len(rows),cellar=cellar,dropped=dropped,notes=notes,limit=limit,new=new,
                **{k:d[k] for k in ('added','returned','archived','changed','unchanged')},
                gone=[f'{nice(r)} ({r.get("Size","")})' for w,r,q in d['log'] if w=='archived'],
                quantity=[f'{nice(r)}: {q}' for w,r,q in d['log'] if w=='quantity'])
def report(x):
    if x['result']=='invalid':
        print('This file can not be imported:'); [print('  -',p) for p in x['problems']]; return
    if x['result']=='unchanged': print(f"This export matches the last import ({x['rows']} rows). Nothing would change."); return
    print(f"{x['rows']} listings in the export, {x['cellar']} in the cellar now.")
    print(f"Would add {x['added']}, bring back {x['returned']} from the archive, archive {x['archived']}, change {x['changed']} quantities; {x['unchanged']} unchanged.")
    if x['dropped']: print('Price columns dropped on the way in:',', '.join(x['dropped']))
    for n in x['notes']: print('Note:',n)
    if x['new']:
        print(f"New to the app ({len(x['new'])} wines):")
        for w in x['new']: print(f"  {w['iwine']:>8}  {w['wine']}  [{w['place'] or 'no place'}]  {'can be built now' if w['ready'] else 'waits for a region profile'}{'  NOTE: '+w['flag'] if w['flag'] else ''}")
    if x['gone']:
        print('Gone from the export (archived, not deleted):'); [print('  ',g) for g in x['gone'][:15]]
        if len(x['gone'])>15: print(f"   and {len(x['gone'])-15} more")
    if x['quantity']: print('New quantities:'); [print('  ',q) for q in x['quantity']]
    if x['result']=='confirm': print(f"STOP: this would archive {x['archived']} listings, more than the {x['limit']} allowed without asking. A filtered or partial export? Rerun apply with --yes only if the user confirms.")
def cmd_check(a):
    x=examine(a.file); report(x); print('RESULT:',x['result']); return {'invalid':1,'confirm':3}.get(x['result'],0)
def cmd_apply(a):
    x=examine(a.file); report(x)
    if x['result']=='invalid': print('RESULT: invalid'); return 1
    if x['result']=='confirm' and not a.yes: print('RESULT: confirm'); return 3
    if x['result']!='unchanged':
        text,rows,dropped=inventory.read_export(a.file); date=datetime.date.today().isoformat(); path,sha=inventory.snapshot(text,date); db=inventory.connect()
        inventory.apply(db,rows,date,path,sha,dropped,quiet=True); print('Imported as',os.path.relpath(path,ROOT))
    db=inventory.connect(); inventory.queue(db); catalog.build() if hasattr(catalog,'build') else subprocess.run([PY,os.path.join(HERE,'catalog.py')],check=True)
    d=work.db(); W=work.wines(d); work.save(d)
    ready=[w for w in W if w['status']=='ready']; waiting=[w for w in W if w['status']=='waiting']
    print(f"Queue: {len(ready)} ready to build, {len(waiting)} waiting for a region profile.")
    for w in ready: print(f"  ready    {w['iwine']:>8}  {w['vintage']} {w['wine']}")
    for w in waiting: print(f"  waiting  {w['iwine']:>8}  {w['vintage']} {w['wine']}  [{w['region_path']}]")
    print('RESULT: applied'); return 0
def free_port():
    s=socket.socket(); s.bind(('127.0.0.1',0)); p=s.getsockname()[1]; s.close(); return p
def builds(): return sorted(d for d in os.listdir(BUILD) if d.startswith('site-') and os.path.isdir(os.path.join(BUILD,d)))
def point(target):
    """Switch build/site to build/<target> in one step (a new link renamed over the old one)."""
    tmp=os.path.join(BUILD,'.site-next');
    if os.path.lexists(tmp): os.remove(tmp)
    os.symlink(target,tmp); os.replace(tmp,LIVE)
def live():
    return os.readlink(LIVE) if os.path.islink(LIVE) else None
def cmd_publish(a):
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S'); name='site-'+stamp; stage=os.path.join(BUILD,name)
    if os.path.isdir(LIVE) and not os.path.islink(LIVE):   # the first publish: the old build becomes a kept build
        old='site-'+datetime.datetime.fromtimestamp(os.path.getmtime(LIVE)).strftime('%Y%m%d-%H%M%S')+'-0'
        os.rename(LIVE,os.path.join(BUILD,old)); point(old); print('build/site is now a link to',old)
    cur=os.path.join(BUILD,live()) if live() else None
    os.makedirs(stage)
    if cur and os.path.isdir(os.path.join(cur,'geo')):   # reuse the map views: they take minutes and change only when the places do
        for dp,dn,fn in os.walk(os.path.join(cur,'geo')):
            out=os.path.join(stage,os.path.relpath(dp,cur)); os.makedirs(out,exist_ok=True)
            for f in fn: os.link(os.path.join(dp,f),os.path.join(out,f))
    def fail(msg):   # the failed build is kept apart, so it can be looked at but never rolled back to
        for old in [d for d in os.listdir(BUILD) if d.startswith('failed-')]: shutil.rmtree(os.path.join(BUILD,old))
        os.rename(stage,os.path.join(BUILD,'failed-'+stamp))
        print('PUBLISH FAILED:',msg); print(f'The live site was not changed. The failed build is in build/failed-{stamp} for a look.'); print('RESULT: failed'); return 1
    print('Building into build/'+name)
    if subprocess.run([PY,os.path.join(HERE,'site.py'),'--out',stage]).returncode: return fail('the site build stopped with an error')
    if subprocess.run([PY,os.path.join(ROOT,'regions','check_wines.py')]).returncode: return fail('check_wines.py found a problem in a wine record')
    port=free_port(); srv=subprocess.Popen([PY,os.path.join(HERE,'serve.py'),'--local','--port',str(port),'--root',stage],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try: socket.create_connection(('127.0.0.1',port),timeout=.2).close(); break
            except OSError: time.sleep(.1)
        ok=subprocess.run([PY,os.path.join(ROOT,'tests','app_smoke.py'),f'http://127.0.0.1:{port}/']).returncode==0
    finally: srv.terminate(); srv.wait()
    if not ok: return fail('the app check failed on the new build')
    point(name); print('Live: build/site ->',name)
    for old in builds()[:-KEEP]:
        if old!=name: shutil.rmtree(os.path.join(BUILD,old)); print('Removed an old build:',old)
    json.dump(dict(live=name,published=datetime.datetime.now().isoformat(timespec='seconds')),open(os.path.join(BUILD,'published.json'),'w'),indent=1)
    print('RESULT: published'); return 0
def cmd_rollback(a):
    cur=live(); bs=builds()
    if not cur or cur not in bs or bs.index(cur)==0: print('There is no earlier build to go back to.'); return 1
    prev=bs[bs.index(cur)-1]; point(prev); print(f'Live: build/site -> {prev} (was {cur})'); return 0
def cmd_status(a):
    print('Live:',live() or ('build/site (a plain folder, not published by restock yet)' if os.path.isdir(LIVE) else 'nothing'))
    for b in builds(): print('  kept:',b,'(live)' if b==live() else '')
    return 0
if __name__=='__main__':
    sys.stdout.reconfigure(line_buffering=True)   # keep this script's lines in order with the steps it runs
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True)
    c=sp.add_parser('check'); c.add_argument('file')
    p=sp.add_parser('apply'); p.add_argument('file'); p.add_argument('--yes',action='store_true',help='the user confirmed a large archive')
    sp.add_parser('publish'); sp.add_parser('rollback'); sp.add_parser('status')
    a=ap.parse_args(); sys.exit(dict(check=cmd_check,apply=cmd_apply,publish=cmd_publish,rollback=cmd_rollback,status=cmd_status)[a.cmd](a))

#!/usr/bin/env python3
"""Map coverage proof: draw every place a map engine covers, with no wine facts, and run the label and clip checks.

  mapproof.py status                       coverage by country and engine, now and at git HEAD
  mapproof.py run [--only PREFIX] [--new] [--jobs N] [--all]
                                           draw and check each covered EU PDO/PGI and US AVA place
  mapproof.py exclude                      mark each covered place that did not pass as uncovered, with its reason
  mapproof.py report                       the places left uncovered, and why (writes docs/MAP_COVERAGE.md)

A place is covered by the same rule as work.coverage: its profile has a map engine and a "covers" node on its path.
For each covered place the tool writes a stand-in wine under build/mapproof/<place>/ with only the region and the
engine's map key (map_ava, map_zone, map_appellation), draws it with MAP_NO_PNG=1 (SVG only), and runs maplint on the
draft. Results go to build/mapproof/report.json. --new limits the run to places that were not covered at git HEAD.
Places a profile leaves uncovered on purpose say why in that profile's "$why"."""
import argparse,collections,csv,glob,json,os,re,sqlite3,subprocess,sys,tempfile,unicodedata
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
ROOT=os.path.dirname(HERE); CA=os.path.join(ROOT,'data','cache'); OUT=os.path.join(ROOT,'build','mapproof')
import profiles
T=profiles.tree()
EU={'austria':'AT','belgium':'BE','bulgaria':'BG','croatia':'HR','cyprus':'CY','czechia':'CZ','denmark':'DK','france':'FR','germany':'DE','greece':'GR','hungary':'HU',
    'italy':'IT','luxembourg':'LU','malta':'MT','netherlands':'NL','portugal':'PT','romania':'RO','slovakia':'SK','slovenia':'SI','spain':'ES'}
def norm(s): return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode().lower())
def jl(p): return json.load(open(p,encoding='utf-8'))
def target(n):
    """The places this proof is for: EU PDOs and PGIs, and US AVAs."""
    c=n.split('/')[0]; off=set(T[n].get('official') or [])
    return (c in EU and bool(off&{'PDO','PGI'})) or (c=='united-states' and 'AVA' in off)
def covered(n,for_node=profiles.for_node):
    p=for_node(n); cov=p['map'].get('covers',[]); ch=set(profiles.chain(n))
    return p['map'].get('engine') if p['map'].get('engine') and any(c in ch for c in cov) else None
def at_head():
    """Coverage with the profiles as committed at git HEAD."""
    d=tempfile.mkdtemp(); subprocess.run(f'git -C "{ROOT}" archive HEAD regions/profiles | tar -x -C "{d}"',shell=True,check=True)
    old=profiles.DIR; profiles.DIR=os.path.join(d,'regions','profiles')
    try: return {n:covered(n) for n in T}
    finally: profiles.DIR=old
# ------ what each engine needs to draw a place
_C={}
def once(k,f):
    if k not in _C: _C[k]=f()
    return _C[k]
def eu_files():   # eAmbrosia id -> dossier number, which is the PDO dataset's PDOid
    def load():
        d={}
        for f in glob.glob(os.path.join(ROOT,'regions','sources','eu-*.json')):
            for e in jl(f)['entries']: d[e['id']]=e.get('file')
        return d
    return once('euf',load)
def pdo_ids(): return once('pdo',lambda:{p for (p,) in sqlite3.connect(os.path.join(CA,'eu-pdo','EU_PDO.gpkg')).execute('select PDOid from EU_PDO')})
def avas(): return once('ava',lambda:{norm(f['properties']['name']):f['properties']['name'] for f in jl(os.path.join(CA,'avas.geojson'))['features'] if f.get('geometry') and not f['properties'].get('removed')})
def eu_national(): return once('eun',lambda:jl(os.path.join(CA,'eu-maps','_national.json'))['appellations'])
TIER=re.compile(r'\s*\(?\b(DOCG|DOC|IGT|IGP)\)?$')
def oc_national(): return once('ocn',lambda:jl(os.path.join(CA,'oc-maps','_national.json'))['appellations'])
def names(n): return [T[n]['name']]+T[n].get('also',[])
def need(n,prof):
    """The stand-in wine's map keys for place n under its merged profile, or (None, reason)."""
    M=prof['map']; eng=M.get('engine')
    if eng=='avas':
        hit=next((avas()[norm(x)] for x in names(n) if norm(x) in avas()),None)
        return ({'map_ava':hit},None) if hit else (None,'no AVA boundary of this name in the UC Davis data')
    if eng=='zones' and M.get('zone_store')=='eu':
        f=eu_files().get(T[n].get('eu_id')); rs=M.get('region_slug')
        hit=[a for a in eu_national() if a.get('pdo_id')==f and f] or [a for a in eu_national() if a['region']==rs and norm(a['name']) in map(norm,names(n))]
        hit=[a for a in hit if a['region']==rs] or hit
        if hit: return {'map_zone':hit[0]['slug']},None
        if 'PDO' not in (T[n].get('official') or []): return None,'a PGI: the EU PDO boundaries dataset holds PDOs only'
        if f and f not in pdo_ids(): return None,'not in the EU PDO boundaries dataset (Candiago et al. 2022)'
        return None,f'not in the {rs} zone store'
    if eng=='zones':   # Italy: Orazio Campoli's store
        if n in M.get('zone_slugs',{}): return {'map_zone':M['zone_slugs'][n]},None   # a name the store spells another way
        want={norm(TIER.sub('',x)) for x in names(n)}
        hit=[a for a in oc_national() if want&{norm(TIER.sub('',x)) for x in [a['name']]+TIER.sub('',a['name']).split(' / ')}]
        if len(hit)>1: hit=[a for a in hit if a['tier']==({'PGI':'IGT'}.get((T[n].get('official') or [''])[0],a['tier']))] or hit
        if hit: return {'map_zone':hit[0]['slug']},None
        return None,'no zone of this name in the Italian Wine Map data'
    if eng=='appellations':   # the INAO name, among the delimitations of the departments the profile draws
        def load():
            out=set()
            for dep,dn in M.get('departments') or [M['department']]:
                p=os.path.join(CA,f'c{dep}.json')
                if not os.path.exists(p): continue
                for f in jl(p)['features']:
                    d=os.path.join(CA,f"d{f['properties']['code']}.json")
                    if os.path.exists(d): out|=set(jl(d))
            return out
        inao=once(('inao',tuple(map(tuple,M.get('departments') or [M['department']]))),load)
        want={norm(x) for x in names(n)}|{norm(a) for a,i in M.get('aliases',{}).items() if i==n}
        hit=[a for a in inao if norm(a) in want or {norm(x) for x in a.split(' ou ')}&want]
        if not hit: hit=[a for a in inao if any(norm(a).startswith(w) and norm(a)[len(w):] in ('vintranquille','vindouxnaturel','rouge','blanc') for w in want)]
        if len(hit)>1: hit=[a for a in hit if norm(a) in {norm(x) for x in names(n)}] or hit   # an exact name beats a longer one that shares it (Entre-deux-Mers, not Entre-deux-Mers Haut-Benauge)
        if len(hit)>1: hit=[a for a in hit if a in M.get('panel2_appellations',[])] or [a for a in hit if a.endswith('Vin Tranquille')] or hit   # the still wine, as the profile names it
        if len(hit)==1: return {'map_appellation':hit[0]},None
        return None,('no INAO delimitation of this name in the departments the profile draws' if not hit else f'several INAO names match: {sorted(hit)}')
    return None,f'the proof does not draw {eng} maps'
# ------ draw and check
def stand_in(n,keys):
    d=os.path.join(OUT,n.replace('/','__')); os.makedirs(d,exist_ok=True)
    w=dict(id='proof-'+n.replace('/','-'),region=dict(node=n,placed_by='judgment'),content={},**keys)
    p=os.path.join(d,'wine.json'); json.dump(w,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1); return d,p
_PG=None
TIMEOUT=int(os.environ.get('MAPPROOF_TIMEOUT',2400))   # seconds: a first draw fills the INAO parcel cache, which is slow
KEEP=bool(os.environ.get('MAPPROOF_KEEP'))   # MAPPROOF_KEEP=1 keeps passing drafts to look at
def page():
    global _PG
    if _PG is None:
        from playwright.sync_api import sync_playwright
        pw=sync_playwright().start(); _PG=pw.chromium.launch().new_page(viewport={'width':1200,'height':1000})
    return _PG
MAXGB=float(os.environ.get('MAPPROOF_MAXGB',4))
def draw(p):
    """map.py on one stand-in wine. It is stopped past TIMEOUT seconds, or past MAXGB of memory, since this Mac has 8 GB
    and a draw that swaps never finishes. Returns the finished process, or the reason it was stopped."""
    import psutil,tempfile,time
    with tempfile.TemporaryFile('w+') as so,tempfile.TemporaryFile('w+') as se:
        pr=subprocess.Popen([sys.executable,os.path.join(HERE,'map.py'),p],stdout=so,stderr=se,text=True,env=dict(os.environ,MAP_NO_PNG='1'))
        ps=psutil.Process(pr.pid); t0=time.time(); why=None
        while pr.poll() is None:
            try: gb=ps.memory_info().rss/1e9
            except psutil.Error: gb=0
            if gb>MAXGB: why=f'needed over {MAXGB:g} GB of memory to draw'
            elif time.time()-t0>TIMEOUT: why=f'took over {TIMEOUT//60} minutes to draw'
            if why: pr.kill(); pr.wait(); return why
            time.sleep(.5)
        so.seek(0); se.seek(0); return subprocess.CompletedProcess(pr.args,pr.returncode,so.read(),se.read())
def one(n):
    import maplint
    prof=profiles.for_node(n); keys,why=need(n,prof); eng=prof['map'].get('engine')
    if not keys: return n,dict(engine=eng,status='no-target',reason=why)
    d,p=stand_in(n,keys)
    for f in ('map.draft.svg','map.draft.html'):
        if os.path.exists(os.path.join(d,f)): os.remove(os.path.join(d,f))
    r=draw(p)
    if isinstance(r,str): return n,dict(engine=eng,keys=keys,status='error',reason=r)
    if r.returncode or not os.path.exists(os.path.join(d,'map.draft.svg')):
        err=(r.stderr.strip().splitlines() or ['no output'])[-1]
        return n,dict(engine=eng,keys=keys,status='error',reason=err[:300])
    probs=maplint.lint(d,page=page())
    if not probs and not KEEP:   # a passing draft isn't needed again: drop it, so a full run stays small
        for f in ('map.draft.svg','map.draft.html'): os.remove(os.path.join(d,f))
    return n,dict(engine=eng,keys=keys,status='fail' if probs else 'pass',problems=probs)
def run(a):
    now={n:covered(n) for n in T}; base=at_head() if a.new else {}
    todo=[n for n in T if (target(n) or a.places) and now[n] and not base.get(n) and (not a.only or any(n==x or n.startswith(x.rstrip('/')+'/') for x in a.only.split(',')))]
    rp=os.path.join(OUT,'report.json'); rep=jl(rp) if os.path.exists(rp) else {}
    if not a.all: todo=[n for n in todo if rep.get(n,{}).get('status')!='pass' or a.force]
    todo.sort(key=lambda n:profiles.for_node(n)['map'].get('engine')=='appellations')   # the slow first draws last
    print(f'{len(todo)} places to draw',flush=True)
    from multiprocessing import Pool
    done=0
    with Pool(a.jobs) as pool:
        for n,res in pool.imap_unordered(one,todo):
            rep[n]=res; done+=1
            if res['status']!='pass': print(f"{res['status']:9} {n}: {res.get('reason') or '; '.join(res.get('problems',[]))[:200]}",flush=True)
            json.dump(rep,open(rp,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
            if done%25==0: print(f'  {done}/{len(todo)}',flush=True)
    json.dump(rep,open(rp,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    c=collections.Counter(rep[n]['status'] for n in todo); print(dict(c))
def status(a):
    now={n:covered(n) for n in T}; base=at_head()
    rows=collections.defaultdict(lambda:[0,0,0,0])
    for n in T:
        c=n.split('/')[0]; r=rows[c]; r[0]+=bool(base[n]); r[1]+=bool(now[n])
        if target(n): r[2]+=1; r[3]+=bool(now[n])
    print(f"all places: HEAD {sum(bool(v) for v in base.values())}, now {sum(bool(v) for v in now.values())} of {len(T)}")
    print('by engine now:',dict(collections.Counter(v for v in now.values() if v)),' HEAD:',dict(collections.Counter(v for v in base.values() if v)))
    tb=sum(1 for n in T if target(n) and base[n]); tn=sum(1 for n in T if target(n) and now[n]); tt=sum(1 for n in T if target(n))
    print(f'EU PDO/PGI and US AVA places: HEAD {tb}, now {tn} of {tt}')
    for c,r in sorted(rows.items(),key=lambda kv:-kv[1][2]):
        if r[2]: print(f'  {c:16} targets {r[3]:4}/{r[2]:4}   all places HEAD {r[0]:4} now {r[1]:4}')
WHY={'a PGI':'A PGI with no boundary in the local data: the EU PDO boundaries dataset holds PDOs only.',
     'not in the EU PDO':'Not in the EU PDO boundaries dataset (Candiago et al. 2022), so the local data has no shape for it.',
     'no AVA':'No AVA boundary of this name in the UC Davis AVA data.',
     'no zone of this name':'No zone of this name in the Italian Wine Map data.',
     'no INAO':'No INAO delimitation of this name in the departments its region profile draws.'}
def why_of(res,n=None):
    if res['status']=='no-target' and n and not target(n): return 'Not an EU PDO or PGI or a US AVA: a country, state, region, group or sub-zone, with no shape of its own in the map data.'
    if res['status']=='no-target': return next((v for k,v in WHY.items() if res['reason'].startswith(k)),res['reason'][0].upper()+res['reason'][1:]+'.')
    if res['status']=='error': return f"The map engine could not draw it ({res['reason']})."
    return 'Its draft map failed the label check: '+'; '.join(res['problems'])+'.'
def exclude(a):
    """Write a profile and a $why for every covered place whose proof did not pass, so it stays waiting with its reason.
    A place with nothing under it that draws gets covers []. A category node (IGT, Landwein, PGIs) whose places all fail
    for one reason gets one such file. A place with places under it that draw (a country, a region) covers just those
    children, so the place itself is left out and they stay in."""
    rep=jl(os.path.join(OUT,'report.json')); base=at_head()
    bad={n:why_of(r,n) for n,r in rep.items() if r['status']!='pass' and covered(n)}
    memo={}
    def alive(k):   # k stays covered: it passed, or was covered before this work, or a place under it is alive
        if k not in memo: memo[k]=bool(covered(k)) and (rep.get(k,{}).get('status')=='pass' or bool(base.get(k)) or k not in bad and k not in rep) or any(alive(c) for c in T[k]['children'])
        return memo[k]
    kids=collections.defaultdict(list)
    for n in T:
        if target(n) and T[n]['parent']: kids[T[n]['parent']].append(n)
    where={}
    for n,w in bad.items():
        p=T[n]['parent']
        if target(n) and p and p not in bad and not target(p) and all(bad.get(k)==w for k in kids[p]) and not any(alive(k) for k in T[p]['children']): where[p]=w
        else: where[n]=w
    shut={n for n in where if not any(alive(k) for k in T[n]['children'])}
    where={n:w for n,w in where.items() if not any(x in shut and x!=n for x in profiles.chain(n))}   # under a place with covers [] it needs no file
    for n,w in sorted(where.items()):
        f=os.path.join(profiles.DIR,n+'.json'); d=jl(f) if os.path.exists(f) else {}
        if n in shut: d['$why']=w; d.setdefault('map',{})['covers']=[]
        else: d['$why']=w+' The places under it that draw stay covered.'; d.setdefault('map',{})['covers']=[k for k in T[n]['children'] if alive(k)]
        os.makedirs(os.path.dirname(f),exist_ok=True); json.dump(d,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=1); open(f,'a').write('\n')
    print(f'{len(where)} profiles mark {len(bad)} places uncovered')
def report(a):
    """Every target place left uncovered, with the reason: a profile's $why, or what the data lacks."""
    rp=os.path.join(OUT,'report.json'); rep=jl(rp) if os.path.exists(rp) else {}
    out=collections.defaultdict(list)
    for n in T:
        if not target(n) or covered(n): continue
        why=None
        for i in reversed(profiles.chain(n)):
            f=os.path.join(profiles.DIR,i+'.json')
            if os.path.exists(f) and jl(f).get('$why') and (i==n or jl(f).get('map',{}).get('covers')==[]): why=jl(f)['$why']; break   # a parent that still covers its children explains only itself
        out[why or "Its region's profile leaves it out, and this work did not change that: Burgundy's parcel engine draws a village and its climats, with no layout yet for regional appellations or the Grand Auxerrois. Not drawn or tested."].append(n)
    lines=['# Map coverage: places left uncovered','',f'Written by `src/mapproof.py report`. A place is covered when a profile names a map engine and a covers node on its path (`work.coverage`). Every place newly covered on 2026-11-06 was drawn and passed `maplint` (`src/mapproof.py run --new --places`). A country, state, region or group has no map of its own, so it stays uncovered while the places under it that draw are covered (its profile lists them in `covers`). These EU PDOs and PGIs and US AVAs were left out, by reason.','']
    for why,ns in sorted(out.items(),key=lambda kv:-len(kv[1])):
        lines+= [f'## {why} ({len(ns)})','',', '.join(f'{T[n]["name"]} (`{n}`)' for n in sorted(ns)),'']
    open(os.path.join(ROOT,'docs','MAP_COVERAGE.md'),'w',encoding='utf-8').write('\n'.join(lines))
    print('\n'.join(f'{len(v):4}  {k}' for k,v in sorted(out.items(),key=lambda kv:-len(kv[1]))))
if __name__=='__main__':
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True)
    sp.add_parser('status'); sp.add_parser('report'); sp.add_parser('exclude')
    r=sp.add_parser('run'); r.add_argument('--only'); r.add_argument('--new',action='store_true'); r.add_argument('--jobs',type=int,default=1,help='parallel draws. Keep 1 on an 8 GB Mac: one draw can take 1 to 4 GB')
    r.add_argument('--all',action='store_true',help='redraw places that already passed'); r.add_argument('--places',action='store_true',help='every newly covered place, not only PDOs, PGIs and AVAs: countries, regions and groups count as covered too'); r.add_argument('--force',action='store_true')
    a=ap.parse_args(); {'status':status,'run':run,'report':report,'exclude':exclude}[a.cmd](a)

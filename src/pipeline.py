#!/usr/bin/env python3
"""The sheet pipeline: research notes in, a checked sheet out, with as little hand work as possible.

  pipeline.py brief IWINE              what is already known: the cellar row, the place, the producer, shared research, the pattern
  pipeline.py scaffold IWINE [--id ID] [--like WINE_ID]
                                       write wines/<id>/wine.json from the nearest finished sheet; every field left to write says TODO
  pipeline.py check FILE...            validate research notes against schema/research.schema.json
  pipeline.py sources WINE_ID          write wines/<id>/sources.md from research/wines/<id>.json and the shared files it uses
  pipeline.py build WINE_ID [--map] [--lock]
                                       draw the map (--map), check its labels, lock it (--lock), render, report, run check-wines

Research lives in research/: wines/<id>.json for one wine, vintages/<region node>/<year>.json and places/<region node>.json
shared by every wine from there. The research agents in .claude/agents write them. Never touches la-boudriotte-2019."""
import argparse,copy,datetime,glob,json,os,re,shutil,subprocess,sys,unicodedata
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
ROOT=os.path.dirname(HERE); RES=os.path.join(ROOT,'research'); PY=os.path.join(ROOT,'.venv','bin','python')
import profiles,work
LOCKED={'la-boudriotte-2019'}
YEAR=datetime.date.today().year
GUIDE="A guide, not a measurement of this bottle."
TASTE_MIN={'red':['Sweetness','Body','Acidity','Tannin'],'white':['Sweetness','Body','Acidity','Oak'],'sparkling':['Sweetness','Body','Acidity','Mousse']}
TODO='TODO'
def slug(s): return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())).strip('-')
STOP={'premier','cru','1er','grand','les','le','la','de','du','des','d','l','domaine','chateau','the','and','et'}
def words(s): return set(slug(s).split('-'))-STOP
def load(p): return json.load(open(p,encoding='utf-8'))
def save(p,d): os.makedirs(os.path.dirname(p),exist_ok=True); json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=1); open(p,'a').write('\n')
def brief_of(iw):
    w=next((w for w in work.wines(work.db()) if w['iwine']==iw),None)
    if not w: sys.exit(f'{iw} is not in the cellar')
    return w
def records():
    out=[]
    for f in glob.glob(os.path.join(ROOT,'wines','*','wine.json')):
        r=load(f)
        if r.get('id') in LOCKED or not r.get('region') or TODO in json.dumps(r,ensure_ascii=False): continue   # finished sheets only
        r['_mtime']=os.path.getmtime(f); out.append(r)
    return out
def ancestors(node): return list(profiles.chain(node)) if node else []
def pattern_for(w):
    """The finished sheet nearest this wine: same producer, then the deepest shared place, then the newest."""
    mine=ancestors(w['region']); best=None
    for r in records():
        if w['iwine'] in r['identity'].get('cellartracker',[]): continue
        theirs=ancestors(r['region']['node']); depth=sum(1 for a in mine if a in theirs)
        same_wine=bool(words(r['identity']['name'])) and words(r['identity']['name'])<=words(w['wine'] or '')   # another vintage of this wine
        score=(10 if r['identity'].get('producer')==w.get('producer_record') else 0)+(5 if same_wine else 0)+depth+(0.5 if r['identity']['style']==w['style'] else 0)+(0.25 if r['identity']['style'] in ('red','white') else 0)
        if not best or (score,r['_mtime'])>best[0]: best=((score,r['_mtime']),r)
    return best[1] if best else None
def shared(node,vintage):
    """Shared research for this place and year, deepest first."""
    out=[]
    for a in ancestors(node):
        for kind,p in (('vintage',f'vintages/{a}/{vintage}'),('place',f'places/{a}')):
            if os.path.exists(os.path.join(RES,p+'.json')): out.append((kind,p))
    return out
def window_note(s,e,y=YEAR):
    if y<s: return f"Give it time. Best {s} to {e}."
    if y>e: return f"Past its best years, {s} to {e}. Open it soon."
    if e-y<=1: return f"Drink it soon. Best {s} to {e}."
    return f"In its window now. Best {s} to {e}."
def ct_year(x):
    try: y=int(x); return y if 1900<y<2200 else None
    except (TypeError,ValueError): return None
def suggest_id(w):
    prod=w.get('producer_record') or slug(w['producer'] or '')
    name=w['wine'] or ''
    for p in [w['producer'] or '']+[x for x in (w['producer'] or '').split() if len(x)>3]: name=re.sub('^'+re.escape(p),'',name,flags=re.I).strip()
    name=re.sub(r'\b(1er|premier|grand) cru\b','',name,flags=re.I)
    return '-'.join(x for x in (prod,slug(name),str(w['vintage']).lower()) if x)
def cmd_brief(a):
    w=brief_of(a.iwine); pat=pattern_for(w); node=w['region']; prof=profiles.for_node(node) if node else {}
    lines=[f"{w['vintage']} {w['wine']} ({w['producer']}). iWine {w['iwine']}, {w['bottles']} bottle(s), {w['type']}, {w['varietal']}.",
           f"Locale: {w['locale']}",f"Place: {w['region_path']} ({node}), tier {w['tier']}. Map engine: {w['map_engine']}. Profiles: {', '.join(w['profiles'])}.",
           f"CellarTracker window: {w['window_cellartracker'][0]} to {w['window_cellartracker'][1]}.",
           f"Taste rows needed: {', '.join(TASTE_MIN.get(w['style'],[]))}.",
           f"Suggested id: {suggest_id(w)}"]
    if w.get('producer_record'):
        p=load(os.path.join(ROOT,'producers',w['producer_record'],'producer.json')); lines.append(f"Producer record: {p['id']}. {p.get('story','')}")
        sib=[r['id'] for r in records() if r['identity'].get('producer')==p['id']]
        if sib: lines.append('Other sheets from this producer: '+', '.join(sorted(sib)))
    else: lines.append('Producer record: none yet. Research the house and write producers/<id>/.')
    sh=shared(node,w['vintage'])
    lines.append('Shared research: '+(', '.join(f'research/{p}.json' for _,p in sh) if sh else 'none for this place and year'))
    if os.path.exists(os.path.join(RES,'wines',suggest_id(w)+'.json')): lines.append(f'Wine research exists: research/wines/{suggest_id(w)}.json')
    if pat: lines.append(f"Pattern: {pat['id']} ({pat['region']['node']}, {pat['identity']['style']})")
    sig=(prof.get('story') or {}).get('signature')
    if sig: lines.append(f"Signature: {sig['component']}"+(f", tiers {sig.get('tiers')}" if sig.get('tiers') else ''))
    print('\n'.join(lines))
def cmd_scaffold(a):
    w=brief_of(a.iwine); wid=a.id or suggest_id(w); out=os.path.join(ROOT,'wines',wid,'wine.json')
    if wid in LOCKED: sys.exit('That is the locked reference.')
    if os.path.exists(out) and not a.force: sys.exit(f'{out} exists; pass --force to replace it')
    pat=load(os.path.join(ROOT,'wines',a.like,'wine.json')) if a.like else pattern_for(w)
    if not pat: sys.exit('No finished sheet to pattern on; pass --like')
    d=copy.deepcopy(pat); d.pop('_mtime',None); same=pat['region']['node']==w['region']
    style=w['style']; v=w['vintage']; vint=int(v) if str(v).isdigit() else 'NV'
    grapes=[{'name':w['varietal'],'share':100}] if w['varietal'] and 'blend' not in w['varietal'].lower() else [{'name':TODO,'share':100}]
    d['id']=wid; d['sheet_title']=TODO
    for k in ('target','short'):
        if k in d: d[k]=TODO
    if not same: d.pop('overrides',None)
    if not same:   # map details belong to the pattern's place
        for k in [k for k in d if k.startswith('map_') and k!='map_file']:
            d[k]=[] if k=='map_villages' else [TODO] if isinstance(d[k],list) else TODO
    d['identity']={'name':TODO,'producer':w.get('producer_record') or TODO,'vintage':vint,'style':style,'grapes':grapes,'alcohol':None,'cellartracker':[w['iwine']]}
    if style in ('sparkling','dessert','fortified'): d['identity']['color']=(w['color'] or '').lower() or TODO
    d['region']={'node':w['region'],'placed_by':'label'}
    if w['tier']: d['region']['tier']=w['tier']
    c=d['content']; pc=pat['content']
    keep={'eyebrow','serve','decant','glass'} if pat['identity']['style']==style else set()   # serving advice differs by style
    if w['tier'] and pc.get('level')==w['tier']: keep|={'level','ladder_note'}
    for k in list(c):
        if k in keep: continue
        if k=='place': c[k]=[[h,TODO] for h,_ in pc['place']]
        elif k=='facts': c[k]=[[h,TODO,TODO] for h,_,_ in pc['facts']]
        elif k=='taste':
            labels=[l for _,l,_ in pc['taste']]; labels+= [l for l in TASTE_MIN.get(style,[]) if l not in labels]
            c[k]=[[0,l,TODO] for l in labels]
        elif k in ('flavors','pairs'): c[k]=[[TODO,TODO]]
        elif k=='taste_note': c[k]=GUIDE
        elif k in ('flavor_note','pair_note'): c[k]=''
        elif k=='window': pass
        elif k=='bottle_label': c[k]=[TODO,TODO,str(vint)]
        elif isinstance(c[k],str): c[k]=TODO
        elif isinstance(c[k],list): c[k]=[TODO]
    s,e=(ct_year(x) for x in w['window_cellartracker'])
    if s and e: c['window']=[s,e,YEAR]; c['window_note']=window_note(s,e)
    else: c['window']=[0,0,YEAR]; c['window_note']=TODO+': estimate a window (see bottle.md)'
    if w['tier'] and 'level' not in keep: c['level']=w['tier']; c['ladder_note']=TODO
    save(out,d)
    def todo(x,path=''):
        if isinstance(x,dict): return [p for k,v in x.items() for p in todo(v,f'{path}.{k}' if path else k)]
        if isinstance(x,list): return [p for i,v in enumerate(x) for p in todo(v,f'{path}[{i}]')]
        return [path] if isinstance(x,str) and x.startswith(TODO) else []
    left=todo(d)
    print(f"Wrote {os.path.relpath(out,ROOT)} from {pat['id']}{'' if same else ' (another place: overrides dropped, check the map fields)'}.")
    print('Map fields kept: '+', '.join(k for k in d if k not in ('id','identity','region','content','overrides','theme','map_file','sheet_title','bottle')))
    print('Left to write: '+', '.join(left))
def schema_errors(p):
    import jsonschema
    S=load(os.path.join(ROOT,'schema','research.schema.json')); d=load(p); errs=[]
    for e in jsonschema.Draft202012Validator(S).iter_errors(d): errs.append(f"{'/'.join(map(str,e.path)) or '(top)'}: {e.message}")
    for i,c in enumerate(d.get('claims',[])):
        for s in c['source']:
            if s not in d['sources'] and s not in ('estimate','reading'): errs.append(f'claims/{i}: source {s!r} is not in sources')
    for u in d.get('uses',[]):
        if not os.path.exists(os.path.join(RES,u+'.json')): errs.append(f'uses: research/{u}.json does not exist')
    return errs
def cmd_check(a):
    bad=0
    for p in a.files:
        e=schema_errors(p); bad+=bool(e)
        print(f"{p}: {'ok' if not e else ''}"); [print('  '+x) for x in e]
    sys.exit(1 if bad else 0)
KIND={'producer':'Producer','importer':'Importer','merchant':'Merchant','critic':'Critic','vintage report':'Vintage report','official':'Official','reference':'Reference','cellartracker':'CellarTracker','label':'Label','general':'General'}
def cmd_sources(a):
    p=os.path.join(RES,'wines',a.wine_id+'.json')
    if a.wine_id in LOCKED: sys.exit('That is the locked reference.')
    e=schema_errors(p)
    if e: sys.exit('\n'.join(e))
    d=load(p); rec=load(os.path.join(ROOT,'wines',a.wine_id,'wine.json')); idn=rec['identity']
    files=[('this wine',d)]+[(u,load(os.path.join(RES,u+'.json'))) for u in d.get('uses',[])]
    prod=load(os.path.join(ROOT,'producers',idn['producer'],'producer.json'))
    L=[f"# {prod['name']} {idn['name']} {idn['vintage']}: sources","",f"Read on {d['read']}. House facts are in `producers/{prod['id']}/sources.md`."+
       (" Shared research: "+', '.join(f'`research/{u}.json`' for u in d.get('uses',[]))+'.' if d.get('uses') else ''),"","## Sources",""]
    for where,f in files:
        for k,s in f['sources'].items():
            L.append(f"- **{s['name']}** ({s['kind']})"+(f", {s['url']}" if s.get('url') else '')+(f". About {s['about']}" if s.get('about') else '')+(f". {s['note']}" if s.get('note') else '')+('' if where=='this wine' else f" [{where}]"))
    L+=["","## Claims","","| Claim | Source | Strength |","|---|---|---|"]
    cell=lambda x:x.replace('|','/').replace('\n',' ')
    for where,f in files:
        for c in f['claims']:
            src='; '.join(f['sources'][s]['name'] if s in f['sources'] else s.capitalize() for s in c['source'])
            if c.get('quote'): src+=f": “{c['quote']}”"
            kinds=sorted({KIND[f['sources'][s]['kind']] for s in c['source'] if s in f['sources']}) or ['Reasoning']
            st=c['strength']; st=f"**{st}**" if st in ('Weak','Estimate','Medium') else st
            claim=c['claim']+(f" ({c['vintage']})" if c.get('vintage') else '')
            L.append(f"| {cell(claim)} | {cell(src)} | {'/'.join(kinds)}. {st}"+(f". {cell(c['note'])}" if c.get('note') else '')+" |")
    eng=profiles.for_node(rec['region']['node'])['map']
    if eng.get('credit'): L.append(f"| Map | {cell(eng['credit'])} | Strong for boundaries |")
    conf=[x for _,f in files for x in f.get('conflicts',[])]; gaps=[x for _,f in files for x in f.get('gaps',[])]
    if conf: L+=["","## Conflicts",""]+[f"- {x}" for x in conf]
    if gaps: L+=["","## Not found",""]+[f"- {x}" for x in gaps]
    out=a.out or os.path.join(ROOT,'wines',a.wine_id,'sources.md'); open(out,'w',encoding='utf-8').write('\n'.join(L)+'\n')
    weak=[c for _,f in files for c in f['claims'] if c['strength'] in ('Weak','Estimate')]
    print(f"Wrote {os.path.relpath(out,ROOT)}: {sum(len(f['claims']) for _,f in files)} claims, {len(weak)} weak or estimated.")
    for c in weak: print(f"  weak: {c['claim']}")
def cmd_claims(a):
    """One line per claim, for writing copy: topic, claim, strength, and the shared files it uses."""
    d=load(os.path.join(RES,'wines',a.wine_id+'.json'))
    for where,f in [('',d)]+[(u,load(os.path.join(RES,u+'.json'))) for u in d.get('uses',[])]:
        if where: print(f'== {where}'+(f"  sheet: {f['sheet']}" if f.get('sheet') else ''))
        for c in f['claims']: print(f"{c['topic']}: {c['claim']}"+(f" ({c['vintage']})" if c.get('vintage') else '')+f" [{c['strength'][0]}]")
    if d.get('conflicts'): print('CONFLICTS: '+' | '.join(d['conflicts']))
def cmd_fill(a):
    """Merge a draft into wines/<id>/wine.json: {"record": top-level keys, "identity": ..., "content": ..., "claims": reading or
    estimate claims to add to the research file}. Then write sources.md."""
    wid=a.wine_id; wp=os.path.join(ROOT,'wines',wid,'wine.json'); d=load(wp); dr=load(a.draft)
    for k,v in dr.get('record',{}).items():
        if v is None: d.pop(k,None)
        else: d[k]=v
    d['identity'].update(dr.get('identity',{})); d.setdefault('region',{}).update(dr.get('region',{}))
    for k,v in dr.get('content',{}).items():
        if v is None: d['content'].pop(k,None)
        else: d['content'][k]=v
    save(wp,d)
    rp=os.path.join(RES,'wines',wid+'.json'); r=load(rp)
    have={c['claim'] for c in r['claims']}
    r['claims']+=[c for c in dr.get('claims',[]) if c['claim'] not in have]; save(rp,r)
    if dr.get('producer'): write_producer(dr['producer'],r)
    a.out=None; cmd_sources(a)
def write_producer(p,r):
    """A new producer record and its sources.md, from the wine's research claims about the house."""
    pd=os.path.join(ROOT,'producers',p['id'])
    if os.path.exists(os.path.join(pd,'producer.json')): return
    save(os.path.join(pd,'producer.json'),p)
    cl=[c for c in r['claims'] if c['topic'] in ('producer','history')]
    L=[f"# {p['name']}: sources","",f"Read on {r['read']}, for `wines/{r['id']}`.","","| Claim | Source | Strength |","|---|---|---|"]
    for c in cl: L.append(f"| {c['claim'].replace('|','/')} | {'; '.join(r['sources'][s]['name']+(' ('+r['sources'][s]['url']+')' if r['sources'][s].get('url') else '') if s in r['sources'] else s for s in c['source'])} | {c['strength']} |")
    open(os.path.join(pd,'sources.md'),'w',encoding='utf-8').write('\n'.join(L)+'\n'); print(f"Wrote producers/{p['id']}")
def run(*args): r=subprocess.run([PY,*args],cwd=ROOT,capture_output=True,text=True); return r.returncode,r.stdout+r.stderr
def cmd_build(a):
    wid=a.wine_id; W=f'wines/{wid}/wine.json'; wd=os.path.join(ROOT,'wines',wid)
    if wid in LOCKED: sys.exit('That is the locked reference; use make verify.')
    import maplint
    if a.map:
        rc,o=run('src/map.py',W)
        if rc: sys.exit('map failed:\n'+o[-1500:])
        probs=maplint.lint(wd); print('map draft:',', '.join(probs) if probs else 'labels clean')
        if a.lock:
            if probs and not a.force: sys.exit('Not locked: fix the labels through overrides, or pass --force after looking at map.draft.png')
            shutil.copy(os.path.join(wd,'map.draft.svg'),os.path.join(wd,'map.svg')); print('map locked')
    elif os.path.exists(os.path.join(wd,'map.svg')):
        probs=maplint.lint(wd,'map.svg')
        if probs: print('map.svg:',', '.join(probs))
    rc,o=run('src/render.py',W,'--year',str(YEAR))
    rep=os.path.join(ROOT,'build',wid,'report.json')
    if rc or not os.path.exists(rep): sys.exit('render failed:\n'+o[-1500:])
    r=load(rep); print('render issues:',r['issues'] or 'none', '| pdf:',os.path.relpath(r['wine'].get('pdf',''),ROOT) if isinstance(r.get('wine'),dict) and r['wine'].get('pdf') else f'build/{wid}/sheet.pdf')
    rc,o=run('regions/check_wines.py')
    mine=[l for l in o.splitlines() if l.startswith(('FAIL','note')) and wid in l]
    print('check-wines:',('\n  '+'\n  '.join(mine)) if mine else 'clean')
    sys.exit(1 if r['issues'] or any(l.startswith('FAIL') for l in mine) else 0)
if __name__=='__main__':
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True)
    b=sp.add_parser('brief'); b.add_argument('iwine')
    s=sp.add_parser('scaffold'); s.add_argument('iwine'); s.add_argument('--id'); s.add_argument('--like'); s.add_argument('--force',action='store_true')
    c=sp.add_parser('check'); c.add_argument('files',nargs='+')
    o=sp.add_parser('sources'); o.add_argument('wine_id'); o.add_argument('--out')
    u=sp.add_parser('build'); u.add_argument('wine_id'); u.add_argument('--map',action='store_true'); u.add_argument('--lock',action='store_true'); u.add_argument('--force',action='store_true')
    sp.add_parser('claims').add_argument('wine_id')
    f=sp.add_parser('fill'); f.add_argument('wine_id'); f.add_argument('draft')
    a=ap.parse_args(); dict(fill=cmd_fill,claims=cmd_claims,brief=cmd_brief,scaffold=cmd_scaffold,check=cmd_check,sources=cmd_sources,build=cmd_build)[a.cmd](a)

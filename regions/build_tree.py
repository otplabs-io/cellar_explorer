#!/usr/bin/env python3
"""Build the region tree. Chris's hierarchy (regions/hierarchy.md) is the frame and is never changed. The lists in
regions/sources/ (made by fetch_sources.py) add every officially registered place that the frame doesn't name,
under the right parent. Writes:
  regions/tree.json         every node: id (stable), path, name, parent, children, tiers, also-names, kind, source
  regions/ids.json          the id registry, so a place keeps its id when it moves or the tree is rebuilt
  regions/hierarchy-full.md the whole tree in the same indented form as Chris's hierarchy, for reading
  build/region-coverage.json official names checked against the tree, and where each cellar wine lands
and prints a short report. Usage: build_tree.py [cellar csv]"""
import csv,json,os,re,sys,unicodedata
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=os.path.join(ROOT,'regions','sources')
TIERS={'Village','Premier Cru','Grand Cru'}
slug=lambda s:re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',s.replace('œ','oe').replace('Œ','Oe').replace('æ','ae')).encode('ascii','ignore').decode().lower()).strip('-')
def norm(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    s=re.sub(r"['’`]",' ',s).replace('.','').replace('-',' ').replace('/',' ')
    s=re.sub(r'\b(aoc|aop|doc|docg|do|dop|igp|igt|pdo|pgi|ava|vqa)\b','',s)
    return re.sub(r'\s+',' ',s).strip()

# ---------------------------------------------------------------- the frame
def parse(md):
    nodes={}; stack=[]
    for line in md.splitlines():
        if line.startswith('## '):
            name=line[3:].strip(); nid=slug(name); nodes[nid]=dict(id=nid,name=name,parent=None,depth=0,source='chris'); stack=[nid]; continue
        m=re.match(r'^( *)- (.+)$',line)
        if not m: continue
        depth=len(m.group(1))//2+1; text=m.group(2).strip()
        p=re.match(r'^(.*?)\s*\((.*)\)$',text); name,extra=(p.group(1),p.group(2)) if p else (text,None)
        stack=stack[:depth]; parent=stack[-1]; nid=parent+'/'+slug(name)
        n=dict(id=nid,name=name,parent=parent,depth=depth,source='chris')
        if extra:
            parts=[x.strip() for x in extra.split(',')]
            if set(parts)<=TIERS: n['tiers']=parts
            else: n['also']=[extra]
        nodes[nid]=n; stack.append(nid)
    return nodes
class Tree:
    def __init__(s,nodes): s.n=nodes
    def kids(s,i): return [k for k,v in s.n.items() if v['parent']==i]
    def sub(s,i):
        out=[]; q=[i]
        while q:
            x=q.pop(0); out.append(x); q+=s.kids(x)
        return out
    def names(s,i):
        v=s.n[i]; out={norm(v['name'])}|{norm(a) for a in v.get('also',[])}
        for part in re.split(r' & | \(|\)',v['name']):
            if part.strip(): out.add(norm(part))
        return out
    def find(s,root,name,also=()):
        """A node under root already named name. Nearest to root wins."""
        want=({norm(name)}|{norm(a) for a in also})-{''}
        for i in s.sub(root):
            v=s.n[i]
            if (({norm(v['name'])}|{norm(a) for a in v.get('also',[])})-{''})&want: return i
        return None
    def child(s,parent,name):
        for k in s.kids(parent):
            if norm(name) in s.names(k) or norm(name)==norm(s.n[k]['name']): return k
        return None
    def add(s,parent,name,kind=None,source=None,also=(),**extra):
        i=parent+'/'+slug(name)
        while i in s.n: i+='-2'
        s.n[i]=dict(id=i,name=name,parent=parent,depth=s.n[parent]['depth']+1,source=source,**({'kind':kind} if kind else {}),**({'also':list(also)} if also else {}),**extra)
        return i
    def path(s,root,names,source,kind='group'):
        """Walk names down from root, reusing a child with the same name anywhere below, creating what's missing."""
        cur=root
        for nm in names:
            k=s.child(cur,nm) or s.find(cur,nm)
            cur=k or s.add(cur,nm,kind=kind,source=source)
        return cur
    def place(s,root,parent,name,kind,source,also=(),**extra):
        """Annotate the node if the tree already has the name under root; otherwise add it under parent.
        Other names count only for names transliterated from another script."""
        name=name.strip()
        if not re.search(r'[A-Za-z]',name) and any(re.search(r'[A-Za-z]',a) for a in also):   # show a romanized name
            lat=next(a for a in also if re.search(r'[A-Za-z]',a)); also=[name]+[a for a in also if a!=lat]; name=lat
        hit=s.find(root,SAME[name]) if name in SAME else s.find(root,name)
        if hit and name in SAME: s.n[hit].setdefault('also',[]); s.n[hit]['also']+= [name] if name not in s.n[hit]['also'] else []
        if not hit and also:
            h=s.find(root,name,also)
            # an alternate name counts when it's a fuller form of the same place (Moulis, Moulis-en-Médoc),
            # not when the existing place is only part of the new name (Verduno inside Verduno Pelaverga)
            if h and not (norm(s.n[h]['name'])!=norm(name) and norm(s.n[h]['name']) in norm(name)): hit=h
        if hit:
            v=s.n[hit]; v.setdefault('official',[]);
            if kind not in v['official']: v['official'].append(kind)
            v.setdefault('sources',[]);
            if source not in v['sources']: v['sources'].append(source)
            for k,x in extra.items(): v.setdefault(k,x)
            return hit
        # a combined frame node such as "La Mancha & Valdepeñas" takes its parts as children
        for i in s.sub(root):
            if ' & ' in s.n[i]['name'] and norm(name) in {norm(p) for p in s.n[i]['name'].split(' & ')}:
                parent=i; break
        return s.add(parent,name,kind=kind,source=source,also=also,official=[kind],**extra)
def load(id_): return json.load(open(os.path.join(SRC,id_+'.json'),encoding='utf-8'))

# Names whose reference list spells them differently or omits them. Each region follows from the appellation's
# official name or area. Placed by Claude on 2026-11-03; listed in regions/sources.md.
HAND={'france':{'Blaye':['Bordeaux','Right Bank'],'Côtes de Blaye':['Bordeaux','Right Bank'],'Côtes de Bordeaux':['Bordeaux'],'Graves supérieures':['Bordeaux','Left Bank'],
  'Sainte-Foy-Bordeaux':['Bordeaux','Entre-Deux-Mers'],'Vin de Savoie':['Savoie'],'Roussette de Savoie':['Savoie'],'Seyssel':['Savoie'],'Bugey':['Bugey'],'Roussette du Bugey':['Bugey'],
  'Corse':['Corsica'],'Côtes de Bergerac':['South West France','Bergerac'],'Côtes de Duras':['South West France'],'Corrèze':['South West France'],'Rosé des Riceys':['Champagne'],
  'Languedoc':['Languedoc-Roussillon'],'Cabernet de Saumur':['Loire Valley'],'Bourg':['Bordeaux','Right Bank']},
 'italy':{"Val d'Arno di Sopra":'Tuscany','Asolo Montello':'Veneto','Casauria':'Abruzzo','Lambrusco Salamino di Santa Croce':'Emilia-Romagna','Pantelleria':'Sicily','Lessini Durello':'Veneto',
  'Terre di Pisa':'Tuscany','Curtefranca':'Lombardy','Riviera del Garda Classico':'Lombardy','Colline Teramane Montepulciano d’Abruzzo':'Abruzzo','Canelli':'Piedmont','Custoza':'Veneto',
  "Colli d'Imola":'Emilia-Romagna','Rimini':'Emilia-Romagna','Terre Alfieri':'Piedmont','Terre di Cosenza':'Calabria','Dogliani':'Piedmont','Vin Santo di Carmignano':'Tuscany',
  'Ortona':'Abruzzo','Strevi':'Piedmont','Terre di Offida':'Marche','Alba':'Piedmont','I Terreni di Sanseverino':'Marche','Valdinievole':'Tuscany',"Bonarda dell'Oltrepò Pavese":'Lombardy',
  'Cagliari':'Sardinia','Valli Ossolane':'Piedmont','San Torpè':'Tuscany',"Pinot nero dell'Oltrepò Pavese":'Lombardy','Sangue di Giuda':'Lombardy','Serrapetrona':'Marche',
  'Casavecchia di Pontelatone':'Campania','Colline Joniche Tarantine':'Puglia','Terratico di Bibbona':'Tuscany','Terre del Colleoni':'Lombardy','Grance Senesi':'Tuscany',
  'Vigneti della Serenissima':'Veneto','Terre di Casole':'Tuscany','San Ginesio':'Marche','Grottino di Roccanova':'Basilicata','S. Anna di Isola Capo Rizzuto':'Calabria',
  'Valdichiana toscana':'Tuscany','Portofino':'Liguria','Toscano':'Tuscany'}}
# Official names for places Chris's hierarchy already has under a shorter name. His name stays; the official one becomes an alternate.
SAME={'Oak Knoll District of Napa Valley':'Oak Knoll District','North Fork of Long Island':'North Fork','The Hamptons, Long Island':'The Hamptons',
      'Conegliano Valdobbiadene - Prosecco':'Conegliano Valdobbiadene Prosecco Superiore','Collio Goriziano':'Collio'}
# ---------------------------------------------------------------- merge each country
def france(T):
    root='france'; g=load('fr-groups'); idx={}; order=g['entries']
    for e in order: idx.setdefault(norm(e['name']),e['path'])
    communes={norm(T.n[i]['name']):i for i in T.sub(root) if T.n[i].get('tiers')}
    # the list names each Côte d'Or grand cru right after its village
    gc_village={}; last=None
    for e in order:
        if len(e['path'])>2 and 'côte de' in e['path'][2]:
            k=norm(e['name'])
            if k in communes: last=communes[k]
            elif last: gc_village[k]=last
    for k in ('corton','corton charlemagne','charlemagne'): gc_village[k]='france/burgundy/cote-d-or/cote-de-beaune/aloxe-corton'
    VIGN={"Vignoble d'Alsace":['Alsace'],'Vignoble de Lorraine':['Lorraine'],'Vignoble de Bergerac':['South West France','Bergerac'],'Vignoble du Limousin':['South West France'],
          'Vignobles du Beaujolais et du Lyonnais':['Beaujolais'],'Vignoble de Savoie':['Savoie'],'Vignoble du Bugey':['Bugey'],'Vignoble du Jura':['Jura'],
          'Vignoble de la vallée du Rhône':['Rhône Valley'],'Vignoble de Provence':['Provence']}
    BASSIN={'Bassin Champagne':['Champagne'],'Bassin Charentes Cognac':['Charentes'],'Bassin Corse':['Corsica'],'Bassin Languedoc Roussillon':['Languedoc-Roussillon'],
            'Bassin Sud-Ouest':['South West France'],'Bassin Val-de-Loire Centre':['Loire Valley']}
    SUB={'vignoble du Blayais et du Bourgeais':['Bordeaux','Right Bank'],"vignoble de l'Entre-deux-Mers":['Bordeaux','Entre-Deux-Mers'],'vignoble des Graves':['Bordeaux','Left Bank'],
         'vignoble du Libournais':['Bordeaux','Right Bank'],'vignoble du Médoc':['Bordeaux','Left Bank'],'vignoble du Sauternais':['Bordeaux','Sauternes & Barsac'],
         'vignoble de la côte de Nuits':['Burgundy',"Côte d'Or",'Côte de Nuits'],'vignoble de la côte de Beaune':['Burgundy',"Côte d'Or",'Côte de Beaune'],
         'vignobles de la côte chalonnaise':['Burgundy','Côte Chalonnaise'],'vignoble du Mâconnais':['Burgundy','Mâconnais']}
    for e in load('eu-fr')['entries']:
        k=norm(e['name']); p=idx.get(k)
        if e['kind']=='PGI': parent=T.path(root,['IGP (vins de pays)'],'eu')
        elif k.startswith('alsace grand cru'): parent=T.path(root,['Alsace','Alsace Grand Cru'],'eu')
        elif k in gc_village: parent=gc_village[k]
        elif e['name'] in HAND['france']: parent=T.path(root,HAND['france'][e['name']],'claude')
        elif p is None: parent=T.path(root,['Other AOCs, region not yet set'],'eu')
        elif len(p)>2 and p[2] in SUB: parent=T.path(root,SUB[p[2]],'fr-groups')
        elif len(p)>2 and 'Basse-Bourgogne' in p[2]: parent=T.path(root,['Burgundy','Chablis' if 'chablis' in k else 'Grand Auxerrois'],'fr-groups')
        elif len(p)>1 and p[1] in VIGN: parent=T.path(root,VIGN[p[1]],'fr-groups')
        elif len(p)>1 and p[1]=='Vignoble de Bordeaux': parent=T.path(root,['Bordeaux'],'fr-groups')
        elif len(p)>1 and p[1]=='Vignoble de Bourgogne': parent=T.path(root,['Burgundy'],'fr-groups')
        elif p[0] in BASSIN: parent=T.path(root,BASSIN[p[0]],'fr-groups')
        else: parent=T.path(root,['Other AOCs, region not yet set'],'eu')
        T.place(root,parent,e['name'],e['kind'],'eu-fr',e.get('also',()),eu_id=e['id'])
# Champagne's grand cru villages by subregion, after Chris's frame and Wine with Seth's cru list (secondary). The
# cahier des charges names the villages and their rank but not their subregion, so premier cru villages Chris didn't
# place wait in a "subregion not yet set" group.
CHAMPAGNE_GC_SUB={'Montagne de Reims':['Ambonnay','Beaumont-sur-Vesle','Bouzy','Louvois','Mailly-Champagne','Puisieulx','Sillery','Verzenay','Verzy'],
    'Côte des Blancs':['Avize','Chouilly','Cramant','Le Mesnil-sur-Oger','Oger','Oiry'],'Vallée de la Marne':['Ay','Tours-sur-Marne']}
def champagne(T):
    root='france/champagne'; sub={n:s for s,ns in CHAMPAGNE_GC_SUB.items() for n in ns}
    for e in load('fr-champagne-crus')['entries']:
        hit=T.find(root,e['name'])
        extra=dict(tiers=[e['kind']],commune=e['commune'],**({'village_code':e['village_code']} if e.get('village_code') else {}))
        also=[e['commune_name']] if norm(e['commune_name'])!=norm(e['name']) and not e.get('merged') else []
        if hit:
            v=T.n[hit]; v.update(extra); v.setdefault('official',[]); v['official']+=[] if 'cru village' in v['official'] else ['cru village']
            v.setdefault('sources',[]); v['sources']+=[] if 'fr-champagne-crus' in v['sources'] else ['fr-champagne-crus']
            if also: v.setdefault('also',[]); v['also']+=[a for a in also if a not in v['also']]
            continue
        parent=T.path(root,[sub[e['name']]],'fr-champagne-crus') if e['name'] in sub else T.path(root,['Villages, subregion not yet set'],'fr-champagne-crus')
        T.add(parent,e['name'],kind='cru village',source='fr-champagne-crus',also=also,official=['cru village'],sources=['fr-champagne-crus'],**extra)
def italy(T):
    root='italy'; g=load('it-groups'); idx={}
    for e in g['entries']: idx.setdefault(norm(e['name']),e['path'][0])
    REG={'Piemonte':'Piedmont','Toscana':'Tuscany','Lombardia':'Lombardy','Sicilia':'Sicily','Sardegna':'Sardinia','Sardinia':'Sardinia','Friuli-Venezia Giulia':'Friuli Venezia Giulia',
         'South Tyrol':'Alto Adige',"Valle d'Aosta/Vallée d'Aoste":"Valle d'Aosta"}
    for e in load('eu-it')['entries']:
        k=norm(e['name'])
        reg=idx.get(k) or next((v for n,v in idx.items() if n and (k.startswith(n+' ') or n.startswith(k+' '))),None)
        if reg and reg.startswith('Trentino'): reg='Alto Adige' if re.search(r'alto adige|sudtirol|südtirol',k) else 'Trentino'
        if e['kind']=='PGI' and not T.find(root,e['name'],e.get('also',())): parent=T.path(root,['IGT (indicazione geografica tipica)'],'eu')
        elif e['name'] in HAND['italy']: parent=T.path(root,[HAND['italy'][e['name']]],'claude')
        elif reg: parent=T.path(root,[REG.get(reg,reg)],'it-groups')
        else: parent=T.path(root,['Other DOCs, region not yet set'],'eu')
        T.place(root,parent,e['name'],e['kind'],'eu-it',e.get('also',()),eu_id=e['id'])
def spain(T):
    root='spain'; g=load('es-groups'); idx={norm(e['name']):e['path'][0] for e in g['entries']}
    for e in load('eu-es')['entries']:
        k=norm(e['name']); com=idx.get(k)
        if e['kind']=='PGI': parent=T.path(root,['Vino de la Tierra (IGP)'],'eu')
        elif com=='Canary Islands' or re.search(r'canari|tenerife|abona|orotava|ycoden|gran canaria|lanzarote|hierro|palma|gomera|guimar',k): parent=T.path(root,['Canary Islands'],'es-groups')
        else: parent=root
        hit=T.find(root,e['name'],e.get('also',()))
        if not hit and k.startswith('jerez'): hit=T.find(root,'Jerez')
        if hit: T.place(root,parent,T.n[hit]['name'],e['kind'],'eu-es',[e['name']],eu_id=e['id'])
        else: T.place(root,parent,e['name'],e['kind'],'eu-es',e.get('also',()),eu_id=e['id'])
def flat_eu(T,code,country,groups=None,pgi_label='PGIs',rename=None):
    root=T.path_root(country)
    gi=load('eu-'+code)['entries']; idx={}
    if groups:
        for e in load(groups)['entries']:
            for nm in [e['name']]: idx.setdefault(norm(nm),e['path'] or [e['name']])
    for e in gi:
        k=norm(e['name']); p=idx.get(k)
        if p is None and rename: p=idx.get(norm(next((a for a,b in rename.items() if b==e['name']),'')))
        if e['kind']=='PGI' and not p: parent=T.path(root,[pgi_label],'eu')
        elif p:
            p=[(rename or {}).get(x,x) for x in p]
            parent=T.path(root,p[:-1] if norm(p[-1])==k else p,'reference')
        else: parent=root
        T.place(root,parent,e['name'],e['kind'],'eu-'+code,e.get('also',()),eu_id=e['id'])
def usa(T):
    root='united-states'; avas=load('us-ava')['entries']; byname={a['name']:a for a in avas}
    ST={'CA':'California','OR':'Oregon','WA':'Washington','NY':'New York','AL':'Alabama','AZ':'Arizona','AR':'Arkansas','CO':'Colorado','CT':'Connecticut','DE':'Delaware','FL':'Florida','GA':'Georgia','HI':'Hawaii','ID':'Idaho','IL':'Illinois','IN':'Indiana','IA':'Iowa','KS':'Kansas','KY':'Kentucky','LA':'Louisiana','ME':'Maine','MD':'Maryland','MA':'Massachusetts','MI':'Michigan','MN':'Minnesota','MS':'Mississippi','MO':'Missouri','MT':'Montana','NE':'Nebraska','NV':'Nevada','NH':'New Hampshire','NJ':'New Jersey','NM':'New Mexico','NC':'North Carolina','ND':'North Dakota','OH':'Ohio','OK':'Oklahoma','PA':'Pennsylvania','RI':'Rhode Island','SC':'South Carolina','SD':'South Dakota','TN':'Tennessee','TX':'Texas','UT':'Utah','VT':'Vermont','VA':'Virginia','WV':'West Virginia','WI':'Wisconsin','WY':'Wyoming'}
    COUNTY={'Sonoma':'Sonoma County','Mendocino':'Mendocino County'}
    depth=lambda a:len([w for w in a['within'] if w in byname])
    for a in sorted(avas,key=depth):
        states=[ST.get(s,s) for s in a['states']]
        st=T.path(root,['Washington' if 'Washington' in states and 'Oregon' in states else states[0]],'us-ava',kind='state')
        hit=T.find(root,a['name'],a['also'])
        if hit: T.place(root,st,a['name'],'AVA','us-ava',a['also'],cfr=a['cfr']); continue
        ins=[T.find(root,w) for w in a['within'] if w in byname]; ins=[i for i in ins if i]
        parent=max(ins,key=lambda i:T.n[i]['depth']) if ins else st
        cs=[c for c in a['county'] if c]
        if (not ins or T.n[parent]['name']=='North Coast') and len(set(cs))==1 and cs[0] in COUNTY: parent=T.path(st,[COUNTY[cs[0]]],'us-ava',kind='county')
        T.place(root,parent,a['name'],'AVA','us-ava',a['also'],cfr=a['cfr'])
    for e in load('eu-us')['entries']: T.place(root,root,e['name'],e['kind'],'eu-us',(),eu_id=e['id'])
def nested(T,country,src,official=True):
    root=T.path_root(country)
    for e in load(src)['entries']:
        parent=T.path(root,e['path'],src) if e['path'] else root
        T.place(root,parent,e['name'],e['kind'],src,e.get('also',()),**({'note':e['note']} if e.get('note') else {}))
def path_root(T,country):
    i=slug(country)
    if i not in T.n: T.n[i]=dict(id=i,name=country,parent=None,depth=0,source='added')
    return i
Tree.path_root=path_root

def write_md(T,path):
    out=[]
    def walk(i,d):
        v=T.n[i]; label=v['name']+(f" ({', '.join(v['tiers'])})" if v.get('tiers') else '')
        out.append(('## '+label) if d==0 else '  '*(d-1)+'- '+label)
        for k in sorted(T.kids(i),key=lambda k:(T.n[k].get('source')!='chris',T.n[k]['name'])):
            walk(k,d+1)
        if d==0: out.append('')
    for r in [i for i,v in T.n.items() if v['parent'] is None]: walk(r,0)
    open(path,'w',encoding='utf-8').write('<!-- Generated by regions/build_tree.py from hierarchy.md and regions/sources/. Do not edit by hand. Chris\'s own entries come first under each place. -->\n\n'+'\n'.join(out)+'\n')

# ---------------------------------------------------------------- stable ids
def stable_ids(T):
    """Give every node an id that survives rebuilds and moves: country plus the place's own name, such as
    france/chassagne-montrachet. A second place of the same name in the country adds its parent, such as
    italy/barolo-in-barolo. regions/ids.json records each id with the path it last had; on rebuild a node keeps the id
    its path had, or, if it moved, the id of a place with the same name in the same country that no longer has a node.
    Ids never come back with a new meaning: a retired id stays in the registry."""
    path=os.path.join(ROOT,'regions','ids.json')
    reg=json.load(open(path,encoding='utf-8'))['ids'] if os.path.exists(path) else {}
    by_path={v['path']:k for k,v in reg.items() if not v.get('retired')}
    out={}; used=set()
    order=sorted(T.n,key=lambda i:(T.n[i]['depth'],i))
    for i in order:
        if i in by_path: out[i]=by_path[i]; used.add(by_path[i])
    for i in order:
        if i in out: continue
        v=T.n[i]; country=i.split('/')[0]
        moved=[k for k,r in reg.items() if k not in used and r['path'] not in T.n and k.split('/')[0]==country and norm(r['name'])==norm(v['name'])]
        if len(moved)==1: out[i]=moved[0]; used.add(moved[0]); continue
        base=country if v['parent'] is None else country+'/'+slug(v['name'])
        cand=base
        if cand in used or (cand in reg and cand not in used and reg[cand]['path'] in T.n):
            cand=base+'-in-'+slug(T.n[v['parent']]['name']) if v['parent'] else base
        k=2; root=cand
        while cand in used or cand in reg and cand not in out.values() and reg[cand]['path'] in T.n: cand=f'{root}-{k}'; k+=1
        out[i]=cand; used.add(cand)
    new={}
    for i,k in out.items(): new[k]=dict(name=T.n[i]['name'],path=i)
    for k,r in reg.items():
        if k not in new: new[k]=dict(r,retired=True)
    json.dump(dict(comment='Stable ids for regions/tree.json. Written by build_tree.py. Never reuse an id; to send an old id to a new place, add it to regions/redirects.json.',ids=dict(sorted(new.items()))),open(path,'w',encoding='utf-8'),indent=1,ensure_ascii=False)
    return out

if __name__=='__main__':
    T=Tree(parse(open(os.path.join(ROOT,'regions','hierarchy.md'),encoding='utf-8').read()))
    france(T); champagne(T); italy(T); spain(T); usa(T)
    flat_eu(T,'de','Germany',pgi_label='Landwein (PGI)')
    flat_eu(T,'at','Austria','at-groups',pgi_label='Landwein (PGI)',rename={'Lower Austria':'Niederösterreich','Styria':'Steiermark','Vienna':'Wien'})
    flat_eu(T,'pt','Portugal',pgi_label='Vinho Regional (PGI)')
    flat_eu(T,'hu','Hungary','hu-groups',pgi_label='PGIs')
    flat_eu(T,'gr','Greece','gr-groups',pgi_label='PGIs')
    for code,name in (('bg','Bulgaria'),('ro','Romania'),('hr','Croatia'),('si','Slovenia'),('cz','Czechia'),('sk','Slovakia'),('nl','Netherlands'),('be','Belgium'),('cy','Cyprus'),('dk','Denmark'),('mt','Malta'),('lu','Luxembourg'),('gb','United Kingdom'),('br','Brazil'),('cn','China')):
        flat_eu(T,code,name)
    for country,src in (('Australia','au'),('New Zealand','nz'),('Argentina','ar'),('Canada','ca'),('South Africa','za'),('Chile','cl'),('Switzerland','ch'),('Lebanon','lb')):
        nested(T,country,src)
    for f in sorted(os.listdir(SRC)):
        if f.startswith('w-'): nested(T,load(f[:-5])['source']['title'].split(': ')[-1],f[:-5])
    ID=stable_ids(T)
    out={}
    for i,v in T.n.items():
        w=dict(v); w['id']=ID[i]; w['path']=i; w['parent']=ID[v['parent']] if v['parent'] else None; w['children']=[]; out[ID[i]]=w
    for w in out.values():
        if w['parent']: out[w['parent']]['children'].append(w['id'])
    json.dump(dict(comment='Built by regions/build_tree.py from hierarchy.md and regions/sources/. Do not edit by hand. Keys are stable ids; path shows where the place sits today.',nodes=out),open(os.path.join(ROOT,'regions','tree.json'),'w',encoding='utf-8'),indent=1,ensure_ascii=False)
    write_md(T,os.path.join(ROOT,'regions','hierarchy-full.md'))
    # every official name must be a node
    miss=[]
    for f in sorted(os.listdir(SRC)):
        d=load(f[:-5])
        if d['source'].get('tier')!='official' and not f.startswith(('eu-','us-')): continue
        for e in d['entries']:
            keys={norm(x) for x in [e['name']]+e.get('also',[])}-{''}
            if not keys or not any(keys&T.names(i) for i in T.n): miss.append((f,e['name']))
    unset=[i for i in T.n if 'not yet set' in T.n[i]['name']]
    sys.path.insert(0,os.path.join(ROOT,'src')); import places
    P=places.Placer()
    CSV=sys.argv[1] if len(sys.argv)>1 else sorted(f for f in [os.path.join(ROOT,'cellar',x) for x in os.listdir(os.path.join(ROOT,'cellar'))] if f.endswith('.csv'))[-1]
    rows=list(csv.DictReader(open(CSV,encoding='utf-8'))); placed=[]
    for r in rows:
        node,tier,missed=P.place(r['Locale'],r['Wine'])
        placed.append(dict(wine=f"{r['Vintage'].replace('1001','NV')} {r['Wine']}",bottles=int(r['Quantity']),locale=r['Locale'],node=node,path=P.T[node]['path'] if node else None,tier=tier,not_in_tree=missed))
    json.dump(dict(missing_official=miss,unset_groups={i:T.kids(i) for i in unset},cellar=placed),open(os.path.join(ROOT,'build','region-coverage.json'),'w',encoding='utf-8'),indent=1,ensure_ascii=False)
    tot=sum(p['bottles'] for p in placed); ok=sum(p['bottles'] for p in placed if p['node'] and not p['not_in_tree'])
    print(f"{len(T.n)} nodes in {len([v for v in T.n.values() if v['parent'] is None])} countries. Official names missing from the tree: {len(miss)}.")
    for u in unset: print(f"  {T.n[u]['name']} under {T.n[u]['parent']}: {len(T.kids(u))}")
    print(f'{ok} of {tot} cellar bottles place fully.')
    for p in placed:
        if not p['node'] or p['not_in_tree']: print('  ',p['bottles'],p['wine'],'|',p['locale'],'->',p['node'],p['not_in_tree'])

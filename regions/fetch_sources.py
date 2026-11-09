#!/usr/bin/env python3
"""Download the official and reference lists of wine places and reduce each to a compact list in regions/sources/.
Raw downloads go to build/region-sources/ and are only parsed, never run. regions/build_tree.py merges the compact lists
into Chris's hierarchy. Rerun this to pick up new appellations; the date of each pull is recorded in the output.

Each regions/sources/<id>.json holds {"source": {...}, "entries": [{"path": [...group names...], "name": ..., "kind": ..., "also": [...]}]}.
`path` is where the source itself puts the entry. build_tree.py maps those group names onto nodes."""
import csv,datetime,html,io,json,os,re,subprocess,sys,urllib.parse,zipfile
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW=os.path.join(ROOT,'build','region-sources'); OUT=os.path.join(ROOT,'regions','sources')
os.makedirs(RAW,exist_ok=True); os.makedirs(OUT,exist_ok=True)
TODAY=datetime.date.today().isoformat(); UA='PourSheets/0.1 (wine reference research)'
def get(url,name,binary=False):
    p=os.path.join(RAW,name)
    if not os.path.exists(p):
        subprocess.run(['curl','-s','-L','-m','300','-A','Mozilla/5.0' if 'wikipedia' not in url else UA,url,'-o',p],check=True)
    return open(p,'rb').read() if binary else open(p,encoding='utf-8',errors='replace').read()
def wiki(lang,title,name):
    t=get(f'https://{lang}.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(title)}&prop=wikitext|revid&format=json&redirects=1',name)
    d=json.loads(t)['parse']; return d['wikitext']['*'],d.get('revid')
def save(id_,source,entries):
    json.dump(dict(source=source,entries=entries),open(os.path.join(OUT,id_+'.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=0)
    print(f'{id_}: {len(entries)} entries')
link=lambda s:[(m.group(2) or m.group(1)).strip() for m in re.finditer(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]',s)]
def clean(s): return re.sub(r'\s+',' ',re.sub(r"'''?|<[^>]+>|\{\{[^}]*\}\}",'',s)).strip(' ;.,')

# ---- EU register of protected wine names (official, every EU country)
def eambrosia():
    allr=[]
    for p in range(10):
        d=json.loads(get(f'https://webgate.ec.europa.eu/eambrosia-api/api/geographical-indications?page={p}&size=1000',f'eambrosia-{p}.json'))
        allr+=d['content']
        if d['last']: break
    w=[r for r in allr if r['productType']=='Wine' and not r['removedFlag'] and r['registration']['status']=='REGISTERED']
    by={}
    for r in w:
        names=[n for n in r['protectedNames']]
        tr=[t for t in (r.get('transcriptions') or []) if t]
        for c in r['countries']:
            by.setdefault(c,[]).append(dict(path=[],name=(tr[0] if tr and not re.search(r'[A-Za-z]',names[0]) else names[0]),also=[n for n in names[1:]+tr if n],kind=r['giType'],id=r['giIdentifier'],file=r['registration']['fileNumber']))
    for c,e in by.items():
        save('eu-'+c,dict(title='eAmbrosia, the EU geographical indications register: registered wine names',url='https://webgate.ec.europa.eu/eambrosia-api/api/geographical-indications',tier='official',pulled=TODAY),e)
# ---- US AVAs, with the AVAs each lies within (UC Davis AVA Project, from the TTB's 27 CFR part 9)
def avas():
    d=json.loads(get('https://raw.githubusercontent.com/UCDavisLibrary/ava/master/avas_aggregated_files/avas.geojson','avas.geojson'))
    e=[]
    for f in d['features']:
        p=f['properties']
        if p.get('removed'): continue
        e.append(dict(path=[],name=p['name'],kind='AVA',also=[p['aka']] if p.get('aka') else [],states=p['state'].split('|'),within=(p['within'] or '').split('|') if p.get('within') else [],county=(p['county'] or '').split('|'),cfr=p.get('cfr_index'),created=p.get('created')))
    save('us-ava',dict(title='UC Davis Library AVA Project, established American Viticultural Areas (27 CFR part 9)',url='https://github.com/UCDavisLibrary/ava',tier='official',pulled=TODAY),e)
# ---- France: where each AOC sits, from the French Wikipedia list of AOC wines (structure only; names come from eAmbrosia)
def france():
    t,rev=wiki('fr',"Vin français bénéficiant d'une AOC",'fr-aoc.json')
    e=[]; bassin=vign=sub=None
    for line in t.splitlines():
        if line.startswith('== '): bassin=clean(line.strip('= ')); vign=sub=None; continue
        if line.startswith('=== '): vign=clean(line.strip('= ')); sub=None; continue
        m=re.match(r'^(\*+)\s*(.*)',line)
        if not m or not bassin or bassin.startswith(('Principes','Notes','Voir')): continue
        lv,body=len(m.group(1)),m.group(2)
        if lv==1 and re.match(r"(le |la |et le )?\[\[(vignoble|vignobles)",body,re.I): sub=link(body)[0]; continue
        if lv==1 and not re.match(r"(le |la |et le |et la )?\[\[",body) and not re.match(r'[a-zà-ÿ]',body): continue
        names=link(body) or [clean(body.split('(')[0])]
        if not names or not names[0]: continue
        e.append(dict(path=[x for x in (bassin,vign,sub if lv>1 else None) if x],name=names[0],kind='AOC'))
    save('fr-groups',dict(title="Wikipédia, « Vin français bénéficiant d'une AOC » (classified by bassin and vignoble, after INAO)",url='https://fr.wikipedia.org/wiki/Vin_fran%C3%A7ais_b%C3%A9n%C3%A9ficiant_d%27une_AOC',revision=rev,tier='reference',pulled=TODAY),e)
# ---- Italy: DOC and DOCG wines by region
def italy():
    e=[]; revs=[]
    for title,kind,fn in (('List of Italian DOCG wines','DOCG','it-docg.json'),('List of Italian DOC wines','DOC','it-doc.json')):
        t,rev=wiki('en',title,fn); revs.append(rev); reg=None
        for line in t.splitlines():
            if re.match(r'^==',line): reg=(link(line) or [clean(line.strip('= '))])[0]; continue
            if line.startswith('*') and reg and reg not in ('References','See also','External links'):
                n=link(line)
                if n: e.append(dict(path=[reg],name=re.sub(r'\s+(DOCG|DOC)$','',n[0]),kind=kind))
            if line.startswith('|') and reg:   # DOCG list is a table
                n=link(line)
                if n and not re.search(r'province|Province',n[0]): e.append(dict(path=[reg],name=re.sub(r'\s+(DOCG|DOC)$','',n[0]),kind=kind))
    save('it-groups',dict(title='Wikipedia, List of Italian DOCG wines and List of Italian DOC wines (by region)',url='https://en.wikipedia.org/wiki/List_of_Italian_DOC_wines',revision=revs,tier='reference',pulled=TODAY),e)
# ---- Spain: DOPs and IGPs by autonomous community
def spain():
    t,rev=wiki('en','Spanish wine regions','es.json'); e=[]; com=None; col=0
    tab=t[t.find('{|'):t.find('|}',t.find('{|'))]
    for cell in re.split(r'\n\|-|\n\|',tab):
        if re.search(r"valign=top \| *'''",cell): com=(link(cell) or [clean(cell)])[0]; col=0; continue
        if 'valign=top' in cell:
            col+=1
            for n in link(cell): e.append(dict(path=[com],name=re.sub(r' \((wine|DO|DOCa|Vino de la Tierra)\)$','',n.replace('_',' ')),kind='DOP' if col==1 else 'IGP'))
    save('es-groups',dict(title='Wikipedia, Spanish wine regions (DOPs and IGPs by autonomous community)',url='https://en.wikipedia.org/wiki/Spanish_wine_regions',revision=rev,tier='reference',pulled=TODAY),e)
# ---- Austria, Hungary, Greece: regions and their appellations
def sections(lang,title,fn,id_,label,within,flat=False):
    """Headings inside the section named `within`. Level 3 headings are regions; level 4 headings and bullets sit
    under the nearest region above them. With flat=True every heading is a region and bullets are its sub-regions."""
    t,rev=wiki(lang,title,fn); e=[]; inside=False; top=sub=None
    for line in t.splitlines():
        m=re.match(r'^(=+)\s*(.*?)\s*=+\s*$',line)
        if m:
            lvl=len(m.group(1)); name=(link(m.group(2)) or [clean(m.group(2))])[0]
            if lvl==2: inside=clean(m.group(2)).startswith(within); top=sub=None; continue
            if not inside: continue
            if flat or lvl==3: top=name; sub=None; e.append(dict(path=[],name=top,kind='region'))
            else: sub=name; e.append(dict(path=[top],name=sub,kind='region'))
            continue
        if inside and top and line.startswith('*'):
            for n in link(line)[:1]:
                if n!=(sub or top): e.append(dict(path=[x for x in (top,sub) if x],name=n,kind='sub-region'))
    save(id_,dict(title=label,url=f'https://{lang}.wikipedia.org/wiki/'+title.replace(' ','_'),revision=rev,tier='reference',pulled=TODAY),e)
# ---- South Africa: Wine of Origin units, regions, districts and wards
def south_africa():
    t,rev=wiki('en','Wine regions of South Africa','za.json'); e=[]; cur=['','','','']
    tab=t[t.find('==Summary table=='):]; tab=tab[tab.find('{|'):tab.find('|}')]
    for row in tab.split('\n|-')[1:]:
        cells=[clean(re.sub(r'\[\[([^\]|]+)\|?([^\]]*)\]\]',lambda m:m.group(2) or m.group(1),c)) for c in row.strip().lstrip('|').split('||')]
        cells=(cells+['','','',''])[:4]
        for i,c in enumerate(cells):
            if c: cur[i]=c; cur[i+1:]=['']*(3-i)
        for i in range(4):
            if cells[i] and cells[i]!='Other': e.append(dict(path=[x for x in cur[:i] if x and x!='Other'],name=cells[i],kind=['geographical unit','region','district','ward'][i]))
    save('za',dict(title='Wikipedia, Wine regions of South Africa (summary of the Wine of Origin scheme)',url='https://en.wikipedia.org/wiki/Wine_regions_of_South_Africa',revision=rev,tier='secondary',note='SAWIS, the official source, failed to load (TLS error) on 2026-11-03.',pulled=TODAY),e)
# ---- Australia: zones, regions and subregions (Wine Australia register)
def australia():
    t=get('https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications','au.html')
    tb=re.findall(r'<table.*?</table>',t,flags=re.S)[0]
    rows=[[html.unescape(re.sub(r'<[^>]+>','',c)).replace('\xa0',' ').strip() for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>',r,flags=re.S)] for r in re.findall(r'<tr.*?</tr>',tb,flags=re.S)][1:]
    STATES=['South Australia','New South Wales','Western Australia','Queensland','Victoria','Tasmania','Northern Territory','Australian Capital Territory']
    e=[]; state=zone=region=None
    for r in rows:
        r=[re.sub(r'\d+$','',x).strip() for x in r]
        if len(r)==1:
            x=r[0]
            if x in STATES: state=x; zone=None; e.append(dict(path=[],name=x,kind='state')); continue
            if x in ('Australia',): continue
            if x=='South Eastern Australia': e.append(dict(path=[],name=x,kind='zone',note='Covers all of NSW, Vic. and Tas. and parts of Qld and SA.')); continue
            if x.startswith('Adelaide'): e.append(dict(path=[state],name='Adelaide',kind='super zone',note='Includes Mount Lofty Ranges, Fleurieu and Barossa.')); continue
            e.append(dict(path=[state],name=x,kind='zone')); continue
        z,rg,sr=(r+['','',''])[:3]
        if z: zone=z; e.append(dict(path=[state],name=z,kind='zone'))
        if rg: region=rg; e.append(dict(path=[state,zone] if zone else [state],name=rg,kind='region'))
        if sr: e.append(dict(path=[state,zone,region] if zone else [state,region],name=sr,kind='subregion'))
    save('au',dict(title='Wine Australia, Register of protected GIs: geographical indications',url='https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications',tier='official',pulled=TODAY),e)
# ---- New Zealand: registered wine GIs (IPONZ register export)
def new_zealand():
    z=zipfile.ZipFile(io.BytesIO(get('https://www.iponz.govt.nz/get-ip/geographical-indications/register/downloadExport','nz.xlsx',binary=True)))
    ns='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    import xml.etree.ElementTree as ET
    ss=[''.join(t.text or '' for t in si.iter(ns+'t')) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(ns+'si')]
    rows=[]
    for r in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).iter(ns+'row'):
        d={}
        for c in r.findall(ns+'c'):
            v=c.find(ns+'v'); d[re.match(r'[A-Z]+',c.get('r')).group(0)]=(ss[int(v.text)] if c.get('t')=='s' else v.text) if v is not None else ''
        rows.append(d)
    hi=next(i for i,r in enumerate(rows) if 'GI Name' in r.values()); H={k:v for k,v in rows[hi].items()}
    recs=[{H[k]:v for k,v in r.items() if k in H} for r in rows[hi+1:]]
    NI={'Northland','Auckland','Gisborne',"Hawke's Bay",'Wellington','Waikato','Bay of Plenty'}
    gis=[r for r in recs if r.get('Category')=='New Zealand' and r.get('Type')=='Wine' and r.get('Status')=='Registered']
    names={r['GI Name'].split(' / ')[0] for r in gis}
    e=[dict(path=[],name='North Island',kind='enduring GI'),dict(path=[],name='South Island',kind='enduring GI')]
    for r in gis:
        nm=r['GI Name'].split(' / '); reg=r.get('Region 1','').replace("’","'")
        isl='North Island' if reg in NI else 'South Island'
        parent=[isl]+([reg] if reg in names and reg!=nm[0] else [])
        e.append(dict(path=parent,name=nm[0],also=nm[1:],kind='GI'))
    save('nz',dict(title='IPONZ, New Zealand Geographical Indications Register (export)',url='https://www.iponz.govt.nz/get-ip/geographical-indications/register/',tier='official',pulled=TODAY),e)
# ---- Argentina: IGs and DOCs (INV)
def argentina():
    pdf=os.path.join(RAW,'ar.pdf'); get('https://www.argentina.gob.ar/sites/default/files/2022/04/i.g._y_d.o.c._de_la_republica_argentina.pdf','ar.pdf',binary=True)
    import pymupdf
    L=[l.strip() for l in '\n'.join(p.get_text() for p in pymupdf.open(pdf)).splitlines() if l.strip() and not re.fullmatch(r'\d+',l.strip())]
    types=[i for i,l in enumerate(L) if l in ('I.G.','D.O.C.')]; norm=lambda l:re.match(r'(Resol|RESOL|Ley |Disposici|Decreto)',l)
    raw=[]
    for k,i in enumerate(types):
        name=L[i-1]; j=i-2
        while j>0 and not norm(L[j]) and L[j] not in ('I.G.','D.O.C.') and (re.search(r'\b(de|del|o su|sinónimo|y)\s*$',L[j]) or L[j].endswith('–')): name=L[j]+' '+name; j-=1
        j=i+1; loc=[]
        while j<len(L) and not norm(L[j]) and (k+1>=len(types) or j<types[k+1]-1): loc.append(L[j]); j+=1
        raw.append((re.sub(r'\s+',' ',name),L[i],' '.join(loc)))
    PROV={'Mendoza','San Juan','La Rioja','Salta','Catamarca','Neuquén','Río Negro','Buenos Aires','Córdoba','Chubut','Jujuy','Tucumán','San Luis','Entre Ríos'}
    e=[]; uco={'San Carlos','Tunuyán','Tupungato'}
    base=lambda n:re.split(r' o su sinónimo | - | – ',n)[0].strip()
    igs={base(n) for n,_,_ in raw}
    for n,t,loc in raw:
        b=base(n); also=[x.strip() for x in re.split(r' o su sinónimo |, sinónimo ',n)[1:]]
        prov=next((p for p in PROV if loc.endswith(p)),None)
        dept=loc[:-len(prov)].strip(' ,') if prov else ''
        if b in ('Argentina',): continue
        if not prov: path=[]
        elif b==prov or b in (prov+' Argentina',): path=[prov]
        elif prov=='Mendoza' and b in uco: path=['Mendoza','Valle de Uco']
        elif dept in igs and dept!=b: path=[prov]+(['Valle de Uco'] if prov=='Mendoza' and dept in uco else [])+[dept]
        elif 'Valle de Uco' == b: path=['Mendoza']
        else: path=[prov]
        e.append(dict(path=path,name=b,also=also,kind='DOC' if t=='D.O.C.' else 'IG',location=loc))
    for p in sorted(PROV):
        if not any(x['name']==p for x in e): e.append(dict(path=[],name=p,kind='province'))
    save('ar',dict(title='Instituto Nacional de Vitivinicultura, Indicaciones geográficas y denominaciones de origen reconocidas y protegidas de la República Argentina (updated September 2025)',url='https://www.argentina.gob.ar/inv/proteccion-del-origen-ig-y-doc',tier='official',pulled=TODAY),e)
# ---- Canada: Ontario (VQA Ontario) and British Columbia (Wine Growers of BC)
def canada():
    e=[dict(path=[],name='Ontario',kind='province'),dict(path=['Ontario'],name='Niagara Peninsula',kind='appellation'),dict(path=['Ontario'],name='Lake Erie North Shore',kind='appellation'),
       dict(path=['Ontario','Lake Erie North Shore'],name='South Islands',kind='sub-appellation'),dict(path=['Ontario'],name='Prince Edward County',kind='appellation')]
    t=get('https://vqaontario.ca/ontario-appellations/niagara-peninsula/','on-niagara.html'); x=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S))))
    reg=x[x.find('Niagara Regional APPELLATIONS'):x.find('Niagara SUB APPELLATIONS')]; sub=x[x.find('Niagara SUB APPELLATIONS'):x.find(' Home ',x.find('Niagara SUB APPELLATIONS'))]
    for n in ('Niagara Escarpment','Niagara-on-the-Lake','West Niagara'):
        assert n in reg; e.append(dict(path=['Ontario','Niagara Peninsula'],name=n,kind='regional appellation'))
    for n in ('Beamsville Bench','Creek Shores','Four Mile Creek','Lincoln Lakeshore','Niagara Lakeshore','Niagara River','Short Hills Bench',"St. David's Bench",'Twenty Mile Bench','Vinemount Ridge'):
        assert n.replace("'","’").replace('. ','.') in sub or n in sub,n; e.append(dict(path=['Ontario','Niagara Peninsula'],name=n,kind='sub-appellation'))
    e.append(dict(path=[],name='British Columbia',kind='province'))
    for n in ('Vancouver Island','Gulf Islands','Fraser Valley','Similkameen Valley','Okanagan Valley','Kootenays','Lillooet','Shuswap','Thompson Valley'):
        e.append(dict(path=['British Columbia'],name=n,kind='GI'))
    for n in ('Lake Country','East Kelowna Slopes','South Kelowna Slopes','Summerland Valleys','Summerland Bench','Summerland Lakefront','Naramata Bench','Skaha Bench','Okanagan Falls','Golden Mile Bench','Golden Mile Slopes'):
        e.append(dict(path=['British Columbia','Okanagan Valley'],name=n,kind='sub-GI'))
    e.append(dict(path=['British Columbia'],name='Cowichan Valley',kind='sub-GI',note='Wine BC lists it among the sub-GIs without naming its parent GI.'))
    save('ca',dict(title='Ontario Wine Appellation Authority (VQA Ontario) appellation pages, and Wine Growers of British Columbia, BC wine regions',url='https://vqaontario.ca/ontario-appellations/ ; https://winebc.com/wine-regions/',tier='official for Ontario, industry for British Columbia',pulled=TODAY),e)
# ---- Chile, Switzerland, Lebanon (secondary: Wikipedia)
def small():
    cl=[('Atacama',['Copiapó Valley','Huasco Valley']),('Coquimbo',['Elqui Valley','Limarí Valley','Choapa Valley']),('Aconcagua',['Aconcagua Valley','Casablanca Valley','San Antonio Valley']),
        ('Central Valley',['Maipo Valley','Rapel Valley','Curicó Valley','Maule Valley']),('Southern Chile',['Itata Valley','Bío-Bío Valley','Malleco Valley']),('Austral',[])]
    sub={'Maipo Valley':['Alto Maipo','Central Maipo','Pacific Maipo'],'Rapel Valley':['Cachapoal Valley','Colchagua Valley'],'Curicó Valley':['Teno Valley','Lontué Valley']}
    e=[]
    for r,ch in cl:
        e.append(dict(path=[],name=r,kind='region'))
        for c in ch:
            e.append(dict(path=[r],name=c,kind='subregion'))
            for s in sub.get(c,[]): e.append(dict(path=[r,c],name=s,kind='zone'))
    save('cl',dict(title='Wikipedia, Chilean wine (wine regions, after the 2018 decree in Diario Oficial No. 42.065)',url='https://en.wikipedia.org/wiki/Chilean_wine',tier='secondary',pulled=TODAY),e)
    save('ch',dict(title='Wikipedia, Swiss wine (the six regions of Swiss Wine Promotion)',url='https://en.wikipedia.org/wiki/Swiss_wine',tier='secondary',pulled=TODAY),[dict(path=[],name=n,kind='region') for n in ('Valais','Vaud','Geneva','Three Lakes','German-speaking Switzerland','Ticino')])
    save('lb',dict(title='Wikipedia, Lebanese wine (wine-growing areas; Lebanon has no legal appellation list)',url='https://en.wikipedia.org/wiki/Lebanese_wine',tier='secondary',pulled=TODAY),[dict(path=[],name=n,kind='area') for n in ('Bekaa Valley','Batroun','Mount Lebanon','North Lebanon','Jezzine')])
# ---- other wine countries (secondary: Wikipedia's list of wine-producing regions)
WORLD=['Georgia','Israel','Uruguay','Mexico','Japan','Turkey','Moldova','Armenia','Serbia','North Macedonia','Morocco','Ukraine']
def world():
    t,rev=wiki('en','List of wine-producing regions','world.json'); sec=None; secs={}
    for line in t.splitlines():
        m=re.match(r'^===+\s*(.*?)\s*===+',line)
        if m: sec=clean(m.group(1)); secs.setdefault(sec,[]) if sec in WORLD else None; continue
        if line.startswith('==') : sec=None; continue
        if sec in WORLD and line.startswith('*'): secs[sec].append(line)
    for c,lines in secs.items():
        e=[]; stack=[]
        for line in lines:
            d=len(line)-len(line.lstrip('*')); n=link(line)
            if not n: continue
            nm=re.sub(r'\s*\((wine|wine region|region)\)$','',n[0]); stack=stack[:d-1]
            e.append(dict(path=list(stack),name=nm,kind='region')); stack.append(nm)
        if e: save('w-'+slug_(c),dict(title=f"Wikipedia, List of wine-producing regions: {c}",url='https://en.wikipedia.org/wiki/List_of_wine-producing_regions',revision=rev,tier='secondary',pulled=TODAY),e)
slug_=lambda s:re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
# ---- Champagne's grand cru and premier cru villages (official: the AOC Champagne cahier des charges, chapter I, II b and c)
CDC_CHAMPAGNE='https://info.agriculture.gouv.fr/gedei/site/bo-agri/document_administratif-3b36a01e-8edd-4742-ade7-fbd3251816c4/telechargement'
COG='https://www.insee.fr/fr/statistiques/fichier/7766585/v_commune_2024.csv'
def champagne_crus():
    """The two lists of villages, matched to INSEE commune codes. Several villages have merged into a larger commune
    since the list was written (Aÿ, Mareuil-sur-Ay and Bisseuil into Aÿ-Champagne, for example), so each entry keeps
    the village's own code and the code of the commune it now belongs to. The maps draw a merged village from its
    cadastral parcels, whose prefix is the village's old code."""
    import pymupdf
    get(CDC_CHAMPAGNE,'cdc-champagne-2022.pdf',binary=True)
    t=re.sub(r'\s+',' ',' '.join(p.get_text() for p in pymupdf.open(os.path.join(RAW,'cdc-champagne-2022.pdf'))))
    def grab(start,end):
        s=t[t.index(start)+len(start):]; s=s[:s.index(end)]
        return [x.strip(' .') for x in re.split(r', | et ',s.split(':',1)[1].replace('- ','-'))]
    gc=grab('“ grand cru “ et “ premier cru “ pour les vins','c) En vertu'); pc=grab('la mention “ premier cru “ pour les vins','III.')
    assert len(gc)==17 and len(pc)==42,(len(gc),len(pc))
    cog=list(csv.DictReader(io.StringIO(get(COG,'cog-2024.csv'))))
    key=lambda s:re.sub(r'[^a-z]','',unicodedata_ascii(s.replace('œ','oe')).lower().removeprefix('les').removeprefix('le'))
    cur={key(r['LIBELLE']):r for r in cog if r['TYPECOM']=='COM' and r['DEP']=='51'}
    old={key(r['LIBELLE']):r for r in cog if r['TYPECOM'] in ('COMD','COMA') and r['COMPARENT'].startswith('51')}
    byc={r['COM']:r for r in cog if r['TYPECOM']=='COM'}
    e=[]
    for tier,names in (('Grand Cru',gc),('Premier Cru',pc)):
        for n in names:
            m=re.match(r'(.*?) \((.*)\)$',n)   # "Coligny (Val-des-Marais)": the village, then the commune it belongs to
            if m:
                n=m.group(1); c=cur[key(m.group(2))]; e.append(dict(path=[],name=n,kind=tier,village_code=c['COM'],commune=c['COM'],commune_name=c['LIBELLE'],merged=True)); continue
            k=key(n); r=cur.get(k) or old.get(k) or next((v for kk,v in {**old,**cur}.items() if kk.startswith(k) or len(kk)>5 and k.startswith(kk) and len(k)-len(kk)<2),None)   # Vaudemanges is now spelled Vaudemange   # Tauxières is now Tauxières-Mutry
            if r is None: sys.exit(f'champagne_crus: no commune for {n}')
            if r['TYPECOM']=='COM': e.append(dict(path=[],name=n,kind=tier,commune=r['COM'],commune_name=r['LIBELLE']))
            else:
                parent=byc[r['COMPARENT']]; e.append(dict(path=[],name=n,kind=tier,village_code=r['COM'],commune=parent['COM'],commune_name=parent['LIBELLE'],merged=True))
    save('fr-champagne-crus',dict(title='Cahier des charges de l’AOC « Champagne », homologué par l’arrêté du 30 novembre 2022 (BO du MASA, 15 décembre 2022), chapitre I, II b (grand cru) et c (premier cru); commune codes from INSEE, Code officiel géographique 2024',
         url=CDC_CHAMPAGNE+' ; '+COG,tier='official',pulled=TODAY,note='The grand cru villages may use “grand cru” or “premier cru”. The text lists villages, not vineyards.'),e)
def unicodedata_ascii(s):
    import unicodedata; return unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode()
if __name__=='__main__':
    world()
    champagne_crus()
    for f in (eambrosia,avas,france,italy,spain,south_africa,australia,new_zealand,argentina,canada,small):
        f()
    sections('en','Austrian wine','at.json','at-groups','Wikipedia, Austrian wine (wine regions)','Wine regions')
    sections('en','Hungarian wine','hu.json','hu-groups','Wikipedia, Hungarian wine (wine regions and sub-regions)','Wine regions',flat=True)
    sections('en','Greek wine','gr.json','gr-groups','Wikipedia, Greek wine (wine regions)','Wine regions',flat=True)

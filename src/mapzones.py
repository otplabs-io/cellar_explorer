#!/usr/bin/env python3
"""Map engine for the zone precision tier: Italy, where each denomination (DOCG, DOC, IGT) is a delimited zone.
Usage: python src/mapzones.py wines/<id>/wine.json
Writes map.draft.svg, map.draft.png and map.stats.json next to the wine file. Copy the draft to map.svg once the
labels are approved. Regional settings come from the wine's region profile ("map" block). The wine gives "map_zone"
(the zone's slug in Orazio Campoli's Italian Wine Map), and optionally "map_cru" (an MGA, contrada or sub-zone by
name), "map_estate" (name, lon/lat and the source of the pin) and "map_estate_note" (lines for the key).

Zone shapes come from Orazio Campoli's Italian Wine Map data, used with his permission for personal, non-commercial
use. Each zone file names its own original source (Regione Piemonte, Regione Toscana, Regione del Veneto, the EU PDO
dataset), and the region profile's credit line repeats it. Commune outlines are ISTAT's, via openpolis (CC BY).

Three linked levels, the same layout as the other engines (design-system/maps.md):
  1 the region, its zones shaded by level (DOCG, DOC), the wine's zone in coral, and a locator of Italy
  2 one of the region's areas (the Langhe, the Valpolicella), its zones labelled, the wine's zone in coral
  3 the wine's zone with its sub-zones and crus, the zones around it and commune borders"""
import collections,json,os,re,subprocess,sys,unicodedata,warnings
warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from shapely.geometry import shape,box,Point
from shapely.ops import transform,unary_union
from pyproj import Transformer
import profiles,records
from mapkit import *
WINE=os.path.abspath(sys.argv[1]); OUT=os.path.dirname(WINE)
cfg=records.load_wine(WINE); prof=profiles.for_wine(cfg); M=prof['map']; OV=cfg.get('overrides',{})
if cfg.get('map_profile'): M=profiles.for_node(cfg['map_profile'])['map']   # a wine labelled with a broad zone, mapped where it grows
assert M['engine']=='zones',f"this wine's profile uses the {M['engine']} engine"
if M.get('zone_store')!='eu' and not M.get('region_slug'):   # an IGT filed under Italy's IGT list: drawn with the profile of the region its zone belongs to
    _r=next(a['region'] for a in json.load(open(os.path.join(CA,'oc-maps','_national.json'),encoding='utf-8'))['appellations'] if a['slug']==cfg['map_zone'])
    _p=next(n for n in profiles.tree() if os.path.exists(os.path.join(profiles.DIR,n+'.json')) and json.load(open(os.path.join(profiles.DIR,n+'.json'),encoding='utf-8')).get('map',{}).get('region_slug')==_r)
    M=profiles.for_node(_p)['map']
TF=Transformer.from_crs(4326,M['projection'],always_xy=True).transform
proj=lambda g:transform(TF,g)
def norm(s): return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
EU=M.get('zone_store')=='eu'   # outside Italy: the store src/eumaps.py builds from the EU PDO boundaries
def oc(path):
    """One of Orazio Campoli's map files, cached under data/cache/oc-maps/, or the EU store's file of the same name."""
    if EU:
        p=os.path.join(CA,'eu-maps',path)
        if not os.path.exists(p): sys.exit(f"{p} is missing. Run src/eumaps.py with this wine's country profile node (spain, germany ...)")
        return json.load(open(p,encoding='utf-8'))
    p=os.path.join(CA,'oc-maps',path)
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p),exist_ok=True)
        subprocess.run(['curl','-s','-f','-m','120','-o',p,f"{M['oc_base']}{path}?v={M['oc_ver']}"],check=True)
    return json.load(open(p,encoding='utf-8'))
def geo(f):
    g=proj(shape(f['geometry'])); return g if g.geom_type=='Point' else g.buffer(0)
RS=M['region_slug']
NAT={a['slug']:a for a in sorted(oc('_national.json')['appellations'],key=lambda a:a['region']==RS)}   # a slug two stores share: this profile's store wins
ZONES={f['properties']['slug']:dict(f['properties'],geom=geo(f)) for f in oc(f'{RS}/_zones.json')['features']}
REG=unary_union([geo(f) for f in oc(f'{RS}/_region.json')['features'] if f['properties'].get('kind')=='border'])
PLACES={f['properties']['name']:proj(shape(f['geometry'])) for f in oc(f'{RS}/_places.json')['features']}
C={}
if EU:
    for f in oc(f'{RS}/_communes.json')['features']: C[f['properties']['com_istat_code']]=dict(nom=f['properties']['name'],geom=geo(f))
for r in M.get('istat_regions',[]):   # commune outlines, one openpolis file per region
    p=fetch(f"{M['communes_url']}/limits_R_{r}_municipalities.geojson",f'it-comuni-R{r:02d}.json')
    for f in json.load(open(p,encoding='utf-8'))['features']:
        C[f['properties']['com_istat_code']]=dict(nom=f['properties']['name'],geom=geo(f))
SLUG=cfg['map_zone']; Z=NAT[SLUG]; ZR=Z['region']
ZF=oc(f'{ZR}/{SLUG}.json'); TG=geo(ZF)   # the wine's zone at full detail
ZP=ZF['properties']; SHORT=lambda s:M.get('short_names',{}).get(s,re.sub(r'\s*\((DOCG|DOC|IGT|IGP)\)$','',NAT[s]['name']) if s in NAT else s)
CRUS=oc(f'{ZR}/{SLUG}-crus.json')['features'] if Z.get('crus') else []
CRU=cfg.get('map_cru'); CRUL=CRU if isinstance(CRU,list) else [CRU] if CRU else []   # one cru, or several for a blend of crus
def cru_match(f,n): return norm(f['properties'].get('name',''))==norm(n) or norm(n) in map(norm,f['properties'].get('crus') or [])   # a contrada without published lines matches its group
CRUF=[]
for n in CRUL:
    hit=[f for f in CRUS if cru_match(f,n)]; assert hit,f'map_cru {n!r} is not among the crus of {SLUG}'; CRUF.append((n,hit[0]))
CRU=', '.join(CRUL) if CRUL else None
est=cfg.get('map_estate')   # a pin only with a source
EP=Point(*TF(*est['lonlat'])) if est else None
BROAD=set(M.get('broad',[]))
AREA=next((a for a in M.get('areas',[]) if a['name']==cfg.get('map_area')),None) or next((a for a in M.get('areas',[]) if SLUG in a['zones']),None)   # a wine can name its area
W,(AW,AH),BX,(BW,BH),CY,CH_=ML['width'],ML['region'],ML['subregion_x'],ML['subregion'],ML['village_y'],ML['village_h']
TIERFILL={t:{'gold':GOLD,'goldl':GOLDL}[c] for t,c in M.get('tier_fill',{'DOCG':'gold','DOC':'goldl'}).items()}
AUTO_AREA=AREA is None
if AUTO_AREA: SHORT=lambda s:M.get('short_names',{}).get(s,re.sub(r'\s*\((DOCG|DOC|IGT|IGP)\)$','',NAT[s]['name']).split(' / ')[0] if s in NAT else s)   # a name with others after ' / ' shows the first
if AUTO_AREA:   # a zone no area of the profile holds: panel 2 is the zone and the nearest zones around it
    _near=sorted([s for s,z in ZONES.items() if s!=SLUG and s not in BROAD and z['tier'] in TIERFILL and z['geom'].distance(TG)<max(15000,.5*(TG.area**.5))
                  and z['geom'].intersection(TG).area<.6*TG.area and TG.intersection(z['geom']).area<.6*z['geom'].area],key=lambda s:ZONES[s]['geom'].distance(TG))[:M.get('auto_area_zones',7)]
    AREA=dict(name='auto',title=f'Around {SHORT(SLUG)}',subtitle='The zones near it',zones=[SLUG]+_near,towns=[])
def dot(x,y): return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{num(MM["target_dot_r"])}" fill="{CORAL}" stroke="{WHITE}" stroke-width="{num(MS["target_dot_ring"])}"></circle>'
def place(n):
    if n in PLACES: return PLACES[n]
    k=next((k for k,c in C.items() if norm(c['nom'])==norm(n)),None)
    return C[k]['geom'].representative_point() if k else None
# ------ panel 1: the region
FA=fit(REG.bounds,AW,AH,34,2,6)
a_=[f'<rect width="{AW}" height="{AH}" fill="{PAPER}"></rect>',P(FA.path(REG,.5),LAND)]
for s,z in sorted(ZONES.items(),key=lambda kv:-kv[1]['geom'].area):
    if s in BROAD or s==SLUG or z['tier'] not in TIERFILL: continue
    a_.append(P(FA.path(z['geom'],.3),TIERFILL[z['tier']],WHITE,MS['commune_edge']))
a_.append(P(FA.path(TG,.3),CORAL,WHITE,MS['commune_edge']))
a_.append(P(FA.path(REG,.5),'none',EDGE,MS['department'],f'stroke-dasharray="{MS["department_dash"]}"'))
k1=[({'gold':GOLD,'goldl':GOLDL}[c],n) for c,n in M.get('tier_key',[['gold','DOCG zones'],['goldl','DOC zones']])]; kx,ky=AW-112,AH-12-len(k1)*MM['legend_row']
taken=[box(0,0,250,40),box(kx-2,ky,AW,AH),box(0,AH-64,ML['locator'][0]+8,AH)]   # panel 1's title, tier key and locator, and the labels below as they go down
for n in M.get('panel1_towns',[]):
    q=place(n)
    if q:
        sd=M.get('panel1_town_side',{}).get(n,'start'); a_.append(town(FA,q,n,LAND,sd)); _x,_y=FA.xy(q.x,q.y); taken.append(label_box(_x+5 if sd=='start' else _x-5,_y+3.5,n,'town',sd))
for ar in M.get('areas',[]):
    us=[ZONES[s]['geom'] for s in ar['zones'] if s in ZONES]
    if not us: continue
    q=unary_union(us).representative_point(); x,y=FA.xy(q.x,q.y); lx,ly,an={**M.get('panel1_labels',{}),**OV.get('panel1',{})}.get(ar['name'],(x-40,y,'end'))
    a_.append(lead(x,y,lx,ly,ar.get('label',ar['name']),an,'subregion_label',bg=PAPER)); taken.append(label_box(lx+(3 if an=='start' else -3),ly+3.5,ar.get('label',ar['name']),'subregion_label',an))
EP1=EP or TG.representative_point()
if not EP and not FA.box().contains(EP1) and not TG.intersection(REG).is_empty: EP1=TG.intersection(REG).representative_point()   # a zone that runs past the region (Delle Venezie): its dot on the part inside
px,py=FA.xy(EP1.x,EP1.y); a_.append(dot(px,py))
tw=OV.get('this_wine')
if not tw:   # the profile's spot or the usual one, unless it lands on another label: then the first clear spot around the dot
    d0=M.get('this_wine',[min(px+31,236),py+9]); d0=(d0[0],d0[1],d0[2] if len(d0)>2 else 'start')
    tw=pick(taken,[d0,(px+31,py+9,'start'),(px-31,py+9,'end'),(px+31,py-14,'start'),(px-31,py-14,'end'),(px+40,py+30,'start'),(px-40,py+30,'end'),(px+40,py-34,'start'),(px-40,py-34,'end')]+ring(px,py,(45,65,90)),'This wine','this_wine',AW,AH)
a_.append(lead(px,py,tw[0],tw[1],'This wine',tw[2] if len(tw)>2 else 'start','this_wine',TCORAL,CORAL,bg=PAPER))
a_.append(title(6,6,1,*M['panel1'],PAPER))
italy=unary_union([geo(f) for f in oc(M.get('locator_file','_italy.json'))['features']]).buffer(3000).buffer(-3000)
FF=fit(italy.bounds,*ML['locator'],pad=2)
LX_,LY_=M.get('locator_xy',[6,AH-62]); a_.append(f'<g transform="translate({LX_},{LY_})">'+P(FF.path(italy,.3),LOC,WHITE,MS['commune_edge'])+P(FF.path(REG,.3),CORAL)+'</g>')
a_.append(''.join(swatch(kx,ky+14+i*MM['legend_row'],'sw',cl,n) for i,(cl,n) in enumerate(k1)))
# ------ panel 2: the area
P2=[s for s in AREA['zones'] if s in ZONES]
FB=fit(unary_union([ZONES[s]['geom'] for s in P2]+([TG] if SLUG not in BROAD else [])).bounds,BW,BH,30,6,10)   # a broad zone (Cava) is framed by its area, not its whole spread
vis=FB.box(); b=[f'<rect width="{BW}" height="{BH}" fill="{PAPER}"></rect>']
for k,c in C.items():
    if c['geom'].intersects(vis): b.append(P(FB.path(c['geom'],.3),LAND,MINOR,MS['commune_edge']))
b.append(P(FB.path(REG,.4),'none',EDGE,MS['department'],f'stroke-dasharray="{MS["department_dash"]}"'))
for s in sorted(P2,key=lambda s:-ZONES[s]['geom'].area):
    if s!=SLUG: b.append(P(FB.path(ZONES[s]['geom'],.3),TIERFILL.get(ZONES[s]['tier'],CFILL),WHITE,MS['commune_edge']))
b.append(P(FB.path(TG,.3),CORAL,WHITE,MS['commune_edge']))
sides=[]
for s in P2+([SLUG] if SLUG not in P2 else []):
    g=(TG if s==SLUG else ZONES[s]['geom']).intersection(vis)
    if g.is_empty: continue
    q=g.representative_point(); x,y=FB.xy(q.x,q.y); sides.append((s,x,y))
sides.sort(key=lambda r:r[2]); last=30
taken2=[box(0,0,330,40),box(BW-110,BH-30,BW,BH)]   # the title, and the scale bar with the north arrow
if AUTO_AREA:   # a neighbour's name stays off the wine's own zone, and off the edges of panel 3's box and its badge
    from shapely.geometry import Polygon,LineString
    _tp=TG.intersection(vis).simplify(2/FB.k)
    for _g in getattr(_tp,'geoms',[_tp]):
        if _g.geom_type=='Polygon' and not _g.is_empty: taken2.append(Polygon([FB.xy(*q) for q in _g.exterior.coords]).buffer(0))
    _mc={norm(n) for n in cfg.get('map_communes',[])}; _foc=[c['geom'] for c in C.values() if norm(c['nom']) in _mc and c['geom'].intersects(TG.buffer(2000))] if cfg.get('map_fit')=='communes' else []
    _fc=fit((unary_union(_foc).buffer(cfg.get('map_fit_pad',2500)) if _foc else TG.buffer(600)).bounds,W,CH_,34,8,6)   # the same frame panel 3 takes below
    (_x0,_y0),(_x1,_y1)=FB.xy(_fc.x0,_fc.y1),FB.xy(_fc.x1,_fc.y0)
    taken2.append(LineString([(_x0,_y0),(_x1,_y0),(_x1,_y1),(_x0,_y1),(_x0,_y0)]).buffer(1.5)); taken2.append(Point(min(_x1,BW-MM['badge_r']-2),max(_y0,MM['badge_r']+2)).buffer(MM['badge_r']+3))
for s,x,y in sorted(sides,key=lambda r:r[0]!=SLUG) if AUTO_AREA else []:
    hot=s==SLUG; lab=SHORT(s); st='village_target' if hot else 'village'; sd='end' if x>BW/2 else 'start'; o='start' if sd=='end' else 'end'
    c_=[(x+(30 if a=='start' else -30),y+dy,a) for dy in (0,-16,16,-30,30) for a in (sd,o)]+ring(x,y,(30,50,80))
    if s in {**M.get('panel2_labels',{}),**OV.get('panel2',{})}: c_=[tuple({**M.get('panel2_labels',{}),**OV.get('panel2',{})}[s])]
    sp=pick(taken2,c_,lab,st,BW,BH,keep=hot)
    if sp: b.append(lead(x,y,*sp[:2],lab,sp[2],st,TCORAL if hot else INK,CORAL if hot else INK,bg=PAPER))
for s,x,y in [] if AUTO_AREA else sides:
    ly=max(y,last+15); last=ly; hot=s==SLUG; lab=SHORT(s)
    lx,ly,an={**M.get('panel2_labels',{}),**OV.get('panel2',{})}.get(s,(max(x-60,len(lab)*6+8),ly,'end'))
    _b=label_box(lx-3 if an=='end' else lx+3,ly+3.5,lab,'village_target' if hot else 'village',an).bounds
    if _b[0]<2: lx+=2-_b[0]   # a long name would run off the left edge: slide it right
    if hot and s not in {**M.get('panel2_labels',{}),**OV.get('panel2',{})}:   # the wine's own name at its usual spot: it steps down past a town name drawn on it
        _tn=[]
        for n in AREA.get('towns',[]):
            q=place(n)
            if q and vis.contains(q): _x,_y=FB.xy(q.x,q.y); sd=M.get('panel2_town_side',{}).get(n,'start'); _tn.append(label_box(_x+5 if sd=='start' else _x-5,_y+3.5,n,'town',sd))
        for _ in range(4):
            if not any(label_box(lx-3 if an=='end' else lx+3,ly+3.5,lab,'village_target',an).buffer(-3).intersects(t) for t in _tn): break
            ly+=12
        last=max(last,ly)
    b.append(lead(x,y,lx,ly,lab,an,'village_target' if hot else 'village',TCORAL if hot else INK,CORAL if hot else INK,bg=PAPER))
for n in AREA.get('towns',[]):
    q=place(n)
    if q and vis.contains(q): b.append(town(FB,q,n,LAND,M.get('panel2_town_side',{}).get(n,'start')))
m,lab=nice_scale(FB,70); b.append(title(6,6,2,AREA.get('title',AREA['name']),AREA.get('subtitle',M.get('panel2_subtitle','Its DOCG and DOC zones')),PAPER)); b.append(scale(BW-104,BH-10,m,lab,FB)); b.append(north(BW-16,BH-22))
# ------ panel 3: the zone
MC_={norm(n) for n in cfg.get('map_communes',[])}
FOC=[c['geom'] for c in C.values() if norm(c['nom']) in MC_ and c['geom'].intersects(TG.buffer(2000))] if cfg.get('map_fit')=='communes' else []
FC=fit((unary_union(FOC).buffer(cfg.get('map_fit_pad',2500)) if FOC else TG.buffer(600)).bounds,W,CH_,34,8,6)   # a big zone can zoom to the communes its vines grow in
vis=FC.box(); near=[k for k,c in C.items() if c['geom'].intersects(vis)]
c=[f'<rect width="{W}" height="{CH_}" fill="{PAPER}"></rect>']
for k in near: c.append(P(FC.path(C[k]['geom'],.25),LAND))
NB=[s for s,z in ZONES.items() if s!=SLUG and s not in BROAD and z['tier'] in TIERFILL and z['geom'].intersects(vis)
    and z['geom'].intersection(TG).area<.6*TG.area]   # the zones around it, not the broad ones it sits inside
def same(a,b): return a.symmetric_difference(b).area<.02*min(a.area,b.area)
_nb=[]
for s in sorted(NB,key=lambda s:(ZONES[s]['tier']!='DOCG',s)):   # Soave Superiore and Recioto di Soave share one zone: keep one name
    if not any(same(ZONES[s]['geom'],ZONES[t]['geom']) for t in _nb): _nb.append(s)
NB=_nb
for s in sorted(NB,key=lambda s:-ZONES[s]['geom'].area): c.append(P(FC.path(ZONES[s]['geom'],.2),NEIGH,WHITE,MS['vineyard_edge']))
c.append(P(FC.path(TG,.2),GOLD,WHITE,MS['vineyard_edge']))
SUBS=[f for f in CRUS if f['properties'].get('kind')=='subzone' and not str(f['properties'].get('label','')).startswith('Village') and f.get('geometry')]
for f in SUBS: c.append(P(FC.path(geo(f),.2),GOLDL,WHITE,MS['vineyard_edge']))
POLY=[f for f in CRUS if f['properties'].get('kind') in (None,'cru','sheet') and f.get('geometry') and f['geometry']['type']!='Point']
MERGE=M.get('cru_merge_m',60)   # an MGA is many vineyard parcels; close the gaps between them so it reads as one place
def cru_geom(f): return geo(f).buffer(MERGE).buffer(-MERGE)
for f in POLY:
    sh=f['properties'].get('kind')=='sheet'
    c.append(P(FC.path(cru_geom(f),.3),'none',WHITE,MS['vineyard_edge'],f'stroke-dasharray="{MS["neighbor_dash"]}"' if sh else ''))
placed_cru=[]
for n,f in CRUF:
    if f['geometry']['type']!='Point':
        g=cru_geom(f); c.append(P(FC.path(g,.2),CORAL,WHITE,MS['vineyard_edge'])); b0=g.bounds; (x0,y1),(x1,y0)=FC.xy(b0[0],b0[1]),FC.xy(b0[2],b0[3]); placed_cru.append(box(x0-3,y0-3,x1+3,y1+3))
for k in near: c.append(P(FC.path(C[k]['geom'],.25),'none',EDGE,MS['neighbor_border'],f'stroke-dasharray="{MS["neighbor_dash"]}"'))
VC=[k for k in near if norm(C[k]['nom']) in MC_ and C[k]['geom'].intersects(TG.buffer(2000))]   # the communes its vines grow in, when the label's zone is broader
assert len(VC)==len(cfg.get('map_communes',[])),f"map_communes not all found near the zone: {cfg.get('map_communes')}"
for k in VC: c.append(P(FC.path(C[k]['geom'],.25),'none',CORAL,2.2))
note=cfg.get('map_estate_note',[])
leg=[('sw',GOLD,f'{SHORT(SLUG)} zone')]+[('sw',GOLDL,M.get('subzone_legend','Its sub-zones'))]*bool(SUBS)
leg+=[('sw',CORAL,cfg.get('map_cru_legend',CRU))]*any(f['geometry']['type']!='Point' for n,f in CRUF)
leg+=[('out',CORAL,cfg.get('map_communes_legend','Where its vines grow'))]*bool(VC)+[('line',WHITE,M.get('cru_legend','Its named vineyards'))]*bool(POLY)+[('sw',NEIGH,'Other zones')]*bool(NB)+[('line',EDGE,'Commune border')]
KW=232-15-10 if AUTO_AREA else 1e9   # only the zone's own key entry wraps, and only without a hand-set area: the others fit as they are
lh=len(leg)*MM['legend_row']+30+len(note)*14+(MM['legend_row'] if est else 0)+key_extra(leg[0][2],KW)
placed=[box(0,0,330,40),box(W-246,CH_-lh-20,W,CH_),box(0,CH_-36,190,CH_)]+placed_cru   # the title, the legend box, the scale and the wine's cru
def wbox(x,y,t,style,a):
    w=len(t)*MT[style]['size']*(.68 if t.isupper() else .58)+6; h=MT[style]['size']+4
    x0={'start':x,'middle':x-w/2,'end':x-w}[a]; return box(x0-2,y-h+3,x0+w+2,y+4)
def free(bx):
    if bx.bounds[2]>W-4 or bx.bounds[0]<2 or bx.bounds[1]<2 or bx.bounds[3]>CH_-2 or any(bx.intersects(o) for o in placed): return False
    placed.append(bx); return True
def pin(F,p,label,an='start',dx=8,dy=-7):
    x,y=F.xy(p.x,p.y); tx=x+dx if an=='start' else x-dx
    placed.append(box(x-8,y-8,x+8,y+8)); placed.append(wbox(tx,y+dy,label,'this_wine',an))
    return dot(x,y)+H(tx,y+dy,label,fill=TCORAL,a=an,bg=WHITE,sw=MS['halo_wide'],**ty('this_wine'))
pins=[]
if est: pins.append(pin(FC,EP,est['name'],OV.get('estate_anchor','start')))
NAMES=cfg.get('map_cru_names',{}); last=-99; LX=None
def _cy(f): q=geo(f).representative_point(); return FC.xy(q.x,q.y)
for n,f in sorted(CRUF,key=lambda nf:_cy(nf[1])[1]):   # the wine's crus: a pin for a named place, a label on its own patch for a vineyard
    lab=cfg.get('map_cru_label',NAMES.get(n,n)) if len(CRUF)==1 else NAMES.get(n,n)
    if f['geometry']['type']=='Point': pins.append(pin(FC,geo(f),lab,OV.get('cru_anchor','start')))
    else:
        x,y=_cy(f)
        if len(CRUF)>1:   # several crus: stack their labels in one column to the right, top to bottom
            LX=LX or max(_cy(g)[0] for _,g in CRUF)+70; ly=max(y-10,last+17); last=ly; dflt=(LX,ly,'start')
        else: dflt=(x+40,y-24,'start')
        lx,ly,an=OV.get('cru_labels',{}).get(n,OV.get('cru_label',dflt))
        placed.append(wbox(lx+3 if an=='start' else lx-3,ly+3.5,lab,'this_wine',an)); pins.append(lead(x,y,lx,ly,lab,an,'this_wine',TCORAL,CORAL,bg=WHITE))
def spots(g,n=7):
    """Places to try for a label on g: its representative point, then points inside it nearest that point."""
    q=g.representative_point(); out=[FC.xy(q.x,q.y)]; x0,y0,x1,y1=g.bounds; st=max(x1-x0,y1-y0)/n
    pts=[Point(x0+i*st,y0+j*st) for i in range(n+1) for j in range(n+1)]
    for p in sorted([p for p in pts if g.contains(p)],key=lambda p:p.distance(q)): out.append(FC.xy(p.x,p.y))
    return out
for s in [SLUG]+[s for s in NB if ZONES[s]['tier']=='DOCG']:   # zone names on their own land
    g=(TG if s==SLUG else ZONES[s]['geom']).intersection(vis)
    if g.is_empty: continue
    lab=SHORT(s).upper()
    for x,y in [OV['panel3'][s][:2]] if s in OV.get('panel3',{}) else spots(g):
        if free(wbox(x,y,lab,'parent','middle')): c.append(H(x,y,lab,fill=TCORAL if s==SLUG else INK,a='middle',bg=WHITE,sw=MS['halo_wide'],**ty('parent'))); break
for f in SUBS:
    q=geo(f).representative_point(); x,y=FC.xy(q.x,q.y); x,y=OV.get('subzones',{}).get(f['properties']['name'],(x,y))[:2]; lab=f['properties']['name'].upper()
    if free(wbox(x,y,lab,'neighbor','middle')): c.append(H(x,y,lab,fill=INK,a='middle',bg=GOLDL,sw=MS['halo_wide'],extra=f'letter-spacing="{num(MT["neighbor"]["tracking"])}"',**ty('neighbor')))
shown={SHORT(s).upper() for s in [SLUG]+NB}
for k in near if M.get('commune_labels',True) else []:   # commune names where they fit (none where the outlines name them in a script the fonts lack)
    g=C[k]['geom'].intersection(vis)
    if g.area*FC.k*FC.k<3000: continue
    q=g.representative_point(); x,y=FC.xy(q.x,q.y); x,y=OV.get('communes',{}).get(C[k]['nom'],(x,y+14))[:2]; n=C[k]['nom'].upper()
    if n in shown: continue
    if free(wbox(x,y,n,'neighbor','middle')): c.append(H(x,y,n,fill=NLAB,a='middle',bg=LAND,sw=MS['halo_wide'],extra=f'letter-spacing="{num(MT["neighbor"]["tracking"])}"',**ty('neighbor')))
c+=pins
c.append(title(6,6,3,cfg.get('map_title',SHORT(SLUG)),cfg.get('map_subtitle',M.get('panel3_subtitle','Its delimited zone')),LAND))
lx0=W-230; ly0=CH_-lh-8
c.append(f'<rect x="{lx0-10}" y="{ly0-6}" width="232" height="{lh}" fill="{PAPER}" stroke="{EDGE}" stroke-width="{num(MS["legend_swatch"])}"></rect>')
if est: c.append(dot(lx0+5,ly0+8)+T(lx0+15,ly0+12,cfg.get('map_estate_legend','The estate'),**ty('legend'))); ly0+=MM['legend_row']
for i,line in enumerate(note): c.append(T(lx0,ly0+12+i*14,line,fill=INK,a='start',**ty('key')))
ly0+=len(note)*14
_ex=0
for i,(kd,cl,n) in enumerate(leg):
    y=ly0+28+i*MM['legend_row']+_ex; e,dx_=key_entry(lx0,y,'line' if kd=='line' and cl==WHITE else kd,cl,n,KW if i==0 else 1e9); _ex+=dx_
    c.append(f'<path d="M{lx0},{y-3}h{MM["swatch"][0]}" stroke="{GOLD}" stroke-width="5"></path>'+e if kd=='line' and cl==WHITE else e)
m,lab=nice_scale(FC,90); c.append(scale(16,CH_-12,m,lab,FC)); c.append(north(16+m*FC.k+24,CH_-20))
clamp=lambda r,w,h:((max(r[0][0],1),max(r[0][1],1)),(min(r[1][0],w-1),min(r[1][1],h-1)))
ra=clamp((FA.xy(FB.x0,FB.y1),FA.xy(FB.x1,FB.y0)),AW,AH); rb=clamp((FB.xy(FC.x0,FC.y1),FB.xy(FC.x1,FC.y0)),BW,BH)
MAP=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{CY+CH_}" viewBox="0 0 {W} {CY+CH_}" role="img" aria-label="Three linked maps: {esc(M["panel1"][0])} shaded by zone level, {esc(AREA.get("title",AREA["name"]))} by zone, and the {esc(SHORT(SLUG))} zone{(" with "+esc(CRU)+" marked") if CRUF else ""}."><g>{"".join(a_)}</g>{link_rect(ra)}{badge(ra[1][0],ra[0][1],2)}<g transform="translate({BX},0)"><g>{"".join(b)}</g>{link_rect(rb)}{badge(rb[1][0],rb[0][1],3)}</g><g transform="translate(0,{CY})">{"".join(c)}</g></svg>'
ha=lambda g:round(g.area/1e4)
STATS=dict(zone=SLUG,zone_name=ZP.get('official_name'),tier=ZP.get('tier'),status=ZP.get('status'),zone_ha=ha(TG),zone_source=ZP.get('source'),zone_note=ZP.get('note'),
           communes=[(x['name'],x.get('share'),x.get('part')) for x in (ZP.get('communes') if isinstance(ZP.get('communes'),list) else [])],
           cru=[dict(name=n,**{k:v for k,v in f['properties'].items() if k in ('comuni','ha','parcels','km2','how','partial')}) for n,f in CRUF] or None,
           estate=dict(name=est['name'],commune=next((C[k]['nom'] for k in C if C[k]['geom'].contains(EP)),None),inside_zone=TG.buffer(150).contains(EP)) if est else None,
           area=AREA['name'],neighbors={SHORT(s):ha(ZONES[s]['geom']) for s in NB})
open(os.path.join(OUT,'map.stats.json'),'w',encoding='utf-8').write(json.dumps(STATS,ensure_ascii=False,indent=1))
preview(MAP,OUT,W,CY+CH_)
print(json.dumps(STATS,ensure_ascii=False)[:1500]); print('Wrote map.draft.svg, map.draft.png and map.stats.json in',OUT)

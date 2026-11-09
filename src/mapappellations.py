#!/usr/bin/env python3
"""Map engine for the appellation precision tier: regions where the wine names an appellation and an estate, such as
the Médoc. Usage: python src/mapappellations.py wines/<id>/wine.json
Writes map.draft.svg, map.draft.png and map.stats.json next to the wine file. Copy the draft to map.svg once the
labels are approved. Regional settings come from the wine's region profile ("map" block). The wine gives
"map_appellation" (the appellation's name as INAO spells it) and "map_estate" (name, lon/lat and the source of the pin).

Three linked levels, the same layout as the other engines (design-system/maps.md):
  1 the department's wine communes, shaded by area (Left Bank, Right Bank...) from each commune's main appellation
  2 the wine's area, communes shaded by their main appellation, the wine's appellation in coral
  3 the appellation's own vineyard land from INAO, its neighbours, commune borders and a pin for the estate
Levels 1 and 2 shade whole communes, which is approximate: an appellation's land doesn't follow commune borders
exactly. Level 3 draws the delimited land itself. The estate is a pin, never a vineyard outline."""
import collections,json,os,re,sys,unicodedata,warnings
warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from shapely.geometry import shape,box,Point
from shapely.ops import transform,unary_union
from pyproj import Transformer
import profiles,records
from mapkit import *
WINE=os.path.abspath(sys.argv[1]); OUT=os.path.dirname(WINE)
cfg=records.load_wine(WINE); prof=profiles.for_wine(cfg); M=prof['map']; OV=cfg.get('overrides',{})
if cfg.get('map_profile'): M=profiles.for_node(cfg['map_profile'])['map']   # a generic Bordeaux wine mapped where its estate grows
assert M['engine']=='appellations',f"this wine's profile uses the {M['engine']} engine"
TREE=profiles.tree()
ODW='https://raw.githubusercontent.com/24eme/opendatawine/9d65ed62f55097faf109bcd4c44805f596981bda/delimitation_aoc'
FG='https://raw.githubusercontent.com/gregoiredavid/france-geojson/5d34ee6d0140c29f785fdb047d9329f1aab58833'
TF=Transformer.from_crs(4326,M['projection'],always_xy=True).transform
proj=lambda g:transform(TF,g)
def load(url,name):
    p=fetch(url,name); return json.load(open(p,encoding='utf-8')) if p else None
def norm(s): return re.sub(r'[^a-z]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
DEPS=M.get('departments') or [M['department']]   # one department (the Gironde) or several (the Rhône valley)
C={}
for dep,dname in DEPS:
    C.update({f['properties']['code']:dict(nom=f['properties']['nom'],geom=proj(shape(f['geometry']).buffer(0))) for f in load(f'{FG}/departements/{dname}/communes-{dname}.geojson',f'c{dep}.json')['features']})
DEP=unary_union([c['geom'] for c in C.values()]).buffer(30).buffer(-30)
DEN={k:(load(f'{ODW}/{k[:2]}/{k}/delimitations.json',f'd{k}.json') or {}) for k in C}
COUNT=collections.Counter(n for d in DEN.values() for n in d)
GEN=set(M['generic'])
def best(k):
    """A commune's main appellation: the one named after it, else the most specific (fewest communes) it has."""
    cands=[n for n in DEN[k] if n not in GEN]
    if not cands: return M.get('fallback','Bordeaux') if DEN[k] else None
    cn=norm(C[k]['nom'])
    named=[n for n in cands if norm(n.split(' ou ')[0]) and cn.startswith(norm(n.split(' ou ')[0])[:8])]
    return (named or sorted(cands,key=lambda n:(COUNT[n],n)))[0]
BEST={k:best(k) for k in C}
ROOTN=M.get('region_root','france/bordeaux')   # the region whose children are panel 1's areas
def node_for(app):
    if app in M.get('aliases',{}): return M['aliases'][app]   # names the tree doesn't hold, such as the Côtes de Bordeaux sub-names
    want={norm(app)}|{norm(x) for x in app.split(' ou ')}
    for i,v in TREE.items():
        if v['path'].startswith(TREE[ROOTN]['path']) and ({norm(v['name'])}|{norm(a) for a in v.get('also',[])})&want: return i
    return None
def area_of(app):
    i=node_for(app) if app else None
    while i and TREE[i]['parent']!=ROOTN: i=TREE[i]['parent']
    return M['subregions'].get(i,M.get('subregion_default','Bordeaux and Bordeaux Supérieur')) if app else None
BYDEP=M.get('subregions_by_department')   # flat regions (the Loire) shade panel 1 by department instead of by the tree
AREA={k:(BYDEP.get(k[:2]) if b else None) if BYDEP else area_of(b) for k,b in BEST.items()}
CSUB=TOK['subregion']
def geom(code,app):
    f=DEN.get(code,{}).get(app)
    if not f: return None
    d=load(f'{ODW}/{code[:2]}/{code}/{f}',f'g{code}-{f}')
    if not d: return None
    g=unary_union([proj(shape(x['geometry']).buffer(0)) for x in d['features']]).intersection(C[code]['geom'].buffer(500))
    return None if g.is_empty else g
APP=cfg['map_appellation']; SHORT=lambda n:M.get('short_names',{}).get(n,n)
est=cfg.get('map_estate')   # a pin only with a source; without one the key says why
EP=Point(*TF(*est['lonlat'])) if est else None
W,(AW,AH),BX,(BW,BH),CY,CH_=ML['width'],ML['region'],ML['subregion_x'],ML['subregion'],ML['village_y'],ML['village_h']
def pin(F,p,label,an='start',bg=WHITE,dx=8,dy=-7):
    x,y=F.xy(p.x,p.y); tx=x+dx if an=='start' else x-dx
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{num(MM["target_dot_r"])}" fill="{CORAL}" stroke="{WHITE}" stroke-width="{num(MS["target_dot_ring"])}"></circle>'+H(tx,y+dy,label,fill=TCORAL,a=an,bg=bg,sw=MS['halo_wide'],**ty('this_wine'))
AUTO2=APP not in M.get('panel2_appellations',[]) or APP in M.get('panel2_auto',[])   # an appellation the profile's panel 2 wasn't laid out for: panel 2 is its own communes and the land around them
# ------ panel 1: the department
wine_c=[k for k in C if DEN[k] and AREA.get(k)]   # a commune outside the region's areas (Beaujolais in the Rhône department) stays blank
FA=fit(DEP.bounds,AW,AH,34,2,6)
a_=[f'<rect width="{AW}" height="{AH}" fill="{PAPER}"></rect>',P(FA.path(DEP,.5),LAND)]
for k in wine_c: a_.append(P(FA.path(C[k]['geom'],.3),CSUB[AREA[k]],WHITE,MS['commune_edge']))
a_.append(P(FA.path(DEP,.5),'none',EDGE,MS['department'],f'stroke-dasharray="{MS["department_dash"]}"'))
for code in M['panel1_towns']: a_.append(town(FA,C[code]['geom'].representative_point(),M['towns'][code],LAND,M.get('panel1_town_side',{}).get(code,'start')))
for name in (list(dict.fromkeys(BYDEP.values())) if BYDEP else list(M['subregions'].values())):
    us=[C[k]['geom'] for k in wine_c if AREA[k]==name]
    if not us: continue
    q=unary_union(us).representative_point(); x,y=FA.xy(q.x,q.y); lx,ly,an={**M.get('panel1_labels',{}),**OV.get('panel1',{})}.get(name,(x-40,y,'end'))
    a_.append(lead(x,y,lx,ly,name,an,'subregion_label',bg=PAPER))
EP1=EP or unary_union([g for g in (geom(k,APP) for k in C if APP in DEN[k]) if g is not None]).representative_point()
px,py=FA.xy(EP1.x,EP1.y)
a_.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{num(MM["target_dot_r"])}" fill="{CORAL}" stroke="{WHITE}" stroke-width="{num(MS["target_dot_ring"])}"></circle>')
tw=OV.get('this_wine',M.get('this_wine',[min(px+31,236),py+9]))
if 'this_wine' not in OV:   # the wine sets no spot: the first spot clear of the towns, area names, title and locator (on a hand-set layout, only when a town or area name sits on the usual spot)
    t1=[box(0,0,330,40),box(0,AH-66,ML['locator'][0]+10,AH)]
    for code in M['panel1_towns']:
        q=C[code]['geom'].representative_point(); x,y=FA.xy(q.x,q.y); sd=M.get('panel1_town_side',{}).get(code,'start')
        t1+=[label_box(x+5 if sd=='start' else x-5,y+3.5,M['towns'][code],'town',sd),Point(x,y).buffer(4)]
    for name in (list(dict.fromkeys(BYDEP.values())) if BYDEP else list(M['subregions'].values())):
        us=[C[k]['geom'] for k in wine_c if AREA[k]==name]
        if not us: continue
        q=unary_union(us).representative_point(); x,y=FA.xy(q.x,q.y); lx,ly,an={**M.get('panel1_labels',{}),**OV.get('panel1',{})}.get(name,(x-40,y,'end'))
        t1.append(label_box(lx+(3 if an=='start' else -3),ly+3.5,name,'subregion_label',an))
    _tb=label_box(tw[0]+(-3 if len(tw)>2 and tw[2]=='end' else 3),tw[1]+3.5,'This wine','this_wine',tw[2] if len(tw)>2 else 'start').buffer(-3)
    if AUTO2 or any(_tb.intersects(o) for o in t1[2:]): tw=list(pick(t1,[(tw[0],tw[1],tw[2] if len(tw)>2 else 'start')]+[(px+31,py+dy,'start') for dy in (9,-9,20,-20)]+[(px-31,py+dy,'end') for dy in (9,-9,20,-20)]+ring(px,py,(30,45,65)),'This wine','this_wine',AW,AH))
a_.append(lead(px,py,tw[0],tw[1],'This wine',tw[2] if len(tw)>2 else 'start','this_wine',TCORAL,CORAL,bg=PAPER))
a_.append(title(6,6,1,*M['panel1'],PAPER))
france=unary_union([proj(shape(f['geometry']).buffer(0)) for f in load(FG+'/departements.geojson','dep.json')['features']]).buffer(2000).buffer(-2000)
FF=fit(france.bounds,*ML['locator'],pad=2)
a_.append(f'<g transform="translate(6,{AH-62})">'+P(FF.path(france,.3),LOC,WHITE,MS['commune_edge'])+P(FF.path(DEP,.3),CORAL)+'</g>')
# ------ panel 2: the area
P2=set(M.get('panel2_appellations',[])); COMM=set(M.get('communal',[]))
area_c=[k for k in C if BEST[k] in P2]
TC=[k for k in C if APP in DEN[k]]
if AUTO2: SHORT=lambda n:M.get('short_names',{}).get(n,re.split(r', | ou ',n)[0])   # INAO lists other names after a comma or 'ou': show the first
if AUTO2:
    M=dict(M,panel2=[f'Around {SHORT(APP)}','Its communes, and the others by their main appellation'])
    FB=fit(unary_union([C[k]['geom'] for k in TC]).buffer(2500).bounds,BW,BH,30,6,10)
else: FB=fit(unary_union([C[k]['geom'] for k in area_c]).bounds,BW,BH,30,6,10)
for k,c in C.items():   # inside this panel, a commune with several appellations takes the one with the most land
    cands=[n for n in DEN[k] if n not in GEN]
    if len(cands)>1 and c['geom'].intersects(FB.box()):
        # broad appellations such as Haut-Médoc overlap the communal ones, so the most specific one with a real share wins
        areas={n:(geom(k,n).area if geom(k,n) is not None else 0) for n in cands}; top=max(areas.values()) or 1
        PREF=M.get('prefer',[])   # where two appellations share the same land (Saint-Emilion and its grand cru), the profile names the one to show
        BEST[k]=sorted([n for n in cands if areas[n]>=.25*top],key=lambda n:(n not in PREF,COUNT[n],n))[0]
if AUTO2:
    for k in TC: BEST[k]=APP   # the wine's appellation in coral wherever it has land
    P2={BEST[k] for k in C if BEST[k] and BEST[k] not in GEN and C[k]['geom'].intersects(FB.box())}|{APP}
area_c=[k for k in C if BEST[k] in P2]
def fill2(k):
    b=BEST[k]
    if b==APP: return CORAL
    if b in COMM: return GOLD
    if b in M.get('broad',['Haut-Médoc']): return GOLDL
    if b in P2: return CFILL
    return LAND
b=[f'<rect width="{BW}" height="{BH}" fill="{PAPER}"></rect>']
vis=FB.box()
for k,c in C.items():
    if c['geom'].intersects(vis): b.append(P(FB.path(c['geom'],.3),fill2(k),WHITE if k in area_c else MINOR,MS['commune_edge']))
sides=[]
for app in sorted(P2) if AUTO2 else M['panel2_appellations']:
    us=[C[k]['geom'] for k in area_c if BEST[k]==app]
    if not us: continue
    u=unary_union(us)
    if AUTO2: u=u.intersection(vis.buffer(-6/FB.k))   # the point the leader starts from stays inside the panel
    if u.is_empty: continue
    q=u.representative_point(); x,y=FB.xy(q.x,q.y); sides.append((app,x,y))
sides.sort(key=lambda r:r[2]); last=30
if AUTO2:   # each name in the first clear spot, off the wine's own communes and panel 3's box; a neighbour's is dropped when none is clear
    from shapely.geometry import Polygon,LineString
    taken2=[box(0,0,330,40),box(BW-110,BH-30,BW,BH)]
    _tp=unary_union([C[k]['geom'] for k in TC]).intersection(FB.box()).simplify(2/FB.k)
    for _g in getattr(_tp,'geoms',[_tp]):
        if _g.geom_type=='Polygon' and not _g.is_empty: taken2.append(Polygon([FB.xy(*q) for q in _g.exterior.coords]).buffer(0))
    _tg=unary_union([g for g in (geom(k,APP) for k in TC) if g is not None]); _fc=fit(buf_bounds(_tg,800),W,CH_,34,8,6)
    (_x0,_y0),(_x1,_y1)=FB.xy(_fc.x0,_fc.y1),FB.xy(_fc.x1,_fc.y0)
    taken2+=[LineString([(_x0,_y0),(_x1,_y0),(_x1,_y1),(_x0,_y1),(_x0,_y0)]).buffer(1.5),Point(min(_x1,BW-MM['badge_r']-2),max(_y0,MM['badge_r']+2)).buffer(MM['badge_r']+3)]
    for code,n in M['towns'].items():   # the town names drawn below
        if code in C and code not in M['panel1_towns'] and C[code]['geom'].intersects(vis) and code!='33314':
            q=C[code]['geom'].representative_point(); x,y=FB.xy(q.x,q.y); taken2+=[label_box(x+5,y+3.5,n,'town','start'),Point(x,y).buffer(4)]
    for app,x,y in sorted(sides,key=lambda r:r[0]!=APP):
        hot=app==APP; lab=SHORT(app); st='village_target' if hot else 'village'; sd='end' if x>BW/2 else 'start'; o='start' if sd=='end' else 'end'
        sp=pick(taken2,[(x+(30 if a=='start' else -30),y+dy,a) for dy in (0,-16,16,-30,30) for a in (sd,o)]+ring(x,y,(30,50,80)),lab,st,BW,BH,keep=hot)
        if sp: b.append(lead(x,y,sp[0],sp[1],lab,sp[2],st,TCORAL if hot else INK,CORAL if hot else INK,bg=PAPER))
for app,x,y in [] if AUTO2 else sides:
    ly=max(y,last+15); last=ly; hot=app==APP; lab=SHORT(app)
    lx,ly,an={**M.get('panel2_labels',{}),**OV.get('panel2',{})}.get(app,(max(x-60,len(lab)*6+8),ly,'end'))
    if hot and app not in OV.get('panel2',{}):   # the wine's own label is set larger than the spot laid out for it: it moves in until it fits the panel
        lx=fit_x(lx,lab,'village_target',an,BW)
    b.append(lead(x,y,lx,ly,lab,an,'village_target' if hot else 'village',TCORAL if hot else INK,CORAL if hot else INK,bg=PAPER))
def _inside(code,n):   # a town at the panel's edge whose name would run outside it is left out
    q=C[code]['geom'].representative_point(); x,y=FB.xy(q.x,q.y); _b=label_box(x+5,y+3.5,n,'town','start').bounds
    return _b[0]>=-2 and _b[2]<=BW+2 and _b[1]>=-2 and _b[3]<=BH+2 and not (AUTO2 and box(*_b).intersects(box(0,0,330,40)))   # nor under an automatic panel's title
for code,n in M['towns'].items():
    if code in C and code not in M['panel1_towns'] and C[code]['geom'].intersects(vis) and code!='33314' and _inside(code,n): b.append(town(FB,C[code]['geom'].representative_point(),n,LAND))
m,lab=nice_scale(FB,70); b.append(title(6,6,2,*M['panel2'],PAPER)); b.append(scale(BW-104,BH-10,m,lab,FB)); b.append(north(BW-16,BH-22))
# ------ panel 3: the appellation's land
tc=[k for k in C if APP in DEN[k]]
TG=unary_union([g for g in (geom(k,APP) for k in tc) if g is not None])
FC=fit(buf_bounds(TG,800),W,CH_,34,8,6)
vis=FC.box(); near=[k for k,c in C.items() if c['geom'].intersects(vis)]
LAYERS=collections.OrderedDict()
for k in near:
    for app in DEN[k]:
        if app in GEN: continue
        g=geom(k,app)
        if g is not None: LAYERS[app]=g if app not in LAYERS else LAYERS[app].union(g)
c=[f'<rect width="{W}" height="{CH_}" fill="{PAPER}"></rect>']
for k in near: c.append(P(FC.path(C[k]['geom'],.25),LAND))
order=sorted(LAYERS,key=lambda a:(a==APP,a in COMM))   # broad appellations first, the wine's last
def fill3(app): return GOLD if app==APP else GOLDL if app in COMM else NEIGH
for app in order: c.append(P(FC.path(LAYERS[app],.2),fill3(app),WHITE,MS['vineyard_edge']))
for k in near: c.append(P(FC.path(C[k]['geom'],.25),'none',EDGE,MS['neighbor_border'],f'stroke-dasharray="{MS["neighbor_dash"]}"'))
_rows=1+any(a in COMM and a!=APP for a in LAYERS)+any(a not in COMM and a!=APP for a in LAYERS)+1
KW=232-15-10 if AUTO2 else 1e9   # only the wine's own key entry wraps, and only without a hand-set layout: the others fit as they are
_lh=_rows*MM['legend_row']+30+(0 if est else len(cfg.get('map_estate_note',[])))*14+key_extra(f'{SHORT(APP)} vineyard land',KW)
placed=[box(0,0,330,40),box(W-246,CH_-_lh-20,W,CH_),box(0,CH_-36,190,CH_)]   # the title, the legend box as drawn below, and the scale and north arrow
def wbox(x,y,t,style,a):
    w=len(t)*MT[style]['size']*(.68 if t.isupper() else .58)+6; h=MT[style]['size']+4
    x0={'start':x,'middle':x-w/2,'end':x-w}[a]; return box(x0-2,y-h+3,x0+w+2,y+4)
def free(bx):
    if bx.bounds[2]>W-4 or bx.bounds[0]<2 or bx.bounds[1]<2 or bx.bounds[3]>CH_-2 or any(bx.intersects(o) for o in placed): return False
    placed.append(bx); return True
ean=OV.get('estate_anchor','start'); elab=est['name'] if est else ''
if est:
    ex,ey=FC.xy(EP.x,EP.y); placed.append(box(ex-8,ey-8,ex+8,ey+8)); placed.append(wbox(ex+8 if ean=='start' else ex-8,ey-7,elab,'this_wine',ean))
for app in [a for a in order if a in COMM or a==APP]:   # appellation names on their own land
    g=LAYERS[app].intersection(vis)
    if g.is_empty: continue
    q=g.representative_point(); x,y=FC.xy(q.x,q.y); x,y=OV.get('panel3',{}).get(app,(x,y))[:2]; lab=SHORT(app).upper()
    if free(wbox(x,y,lab,'parent','middle')): c.append(H(x,y,lab,fill=TCORAL if app==APP else INK,a='middle',bg=WHITE,sw=MS['halo_wide'],**ty('parent')))
shown={SHORT(a).upper() for a in LAYERS}
for k in near:   # commune names where they fit, unless an appellation of the same name is already labelled
    g=C[k]['geom'].intersection(vis)
    if g.area*FC.k*FC.k<3000: continue
    q=g.representative_point(); x,y=FC.xy(q.x,q.y); x,y=OV.get('communes',{}).get(C[k]['nom'],(x,y+14))[:2]; n=C[k]['nom'].upper()
    if any(n.startswith(a) for a in shown): continue
    if free(wbox(x,y,n,'neighbor','middle')): c.append(H(x,y,n,fill=NLAB,a='middle',bg=LAND,sw=MS['halo_wide'],extra=f'letter-spacing="{num(MT["neighbor"]["tracking"])}"',**ty('neighbor')))
if est: c.append(pin(FC,EP,elab,ean))
c.append(title(6,6,3,cfg.get('map_title',SHORT(APP)),cfg.get('map_subtitle','Its delimited vineyard land, and the château' if est else 'Its delimited vineyard land'),LAND))
leg=[('sw',GOLD,f'{SHORT(APP)} vineyard land')]+([('sw',GOLDL,'Neighboring communal appellations')] if any(a in COMM and a!=APP for a in LAYERS) else [])+([('sw',NEIGH,'Other appellations')] if any(a not in COMM and a!=APP for a in LAYERS) else [])+[('line',EDGE,'Commune border')]
note=cfg.get('map_estate_note',[]) if not est else []
lh=len(leg)*MM['legend_row']+30+len(note)*14+key_extra(leg[0][2],KW); lx0=W-230; ly0=CH_-lh-8
c.append(f'<rect x="{lx0-10}" y="{ly0-6}" width="232" height="{lh}" fill="{PAPER}" stroke="{EDGE}" stroke-width="{num(MS["legend_swatch"])}"></rect>')
if est: c.append(f'<circle cx="{lx0+5}" cy="{ly0+8}" r="{num(MM["target_dot_r"])}" fill="{CORAL}" stroke="{WHITE}" stroke-width="{num(MS["target_dot_ring"])}"></circle>'+T(lx0+15,ly0+12,'The château',**ty('legend')))
for i,line in enumerate(note): c.append(T(lx0,ly0+12+i*14,line,fill=INK,a='start',**ty('key')))
ly0+=len(note)*14
_ex=0
for i,(kd,cl,n) in enumerate(leg): e,dx_=key_entry(lx0,ly0+28+i*MM['legend_row']+_ex,kd,cl,n,KW if i==0 else 1e9); _ex+=dx_; c.append(e)
m,lab=nice_scale(FC,90); c.append(scale(16,CH_-12,m,lab,FC)); c.append(north(16+m*FC.k+24,CH_-20))
clamp=lambda r,w,h:((max(r[0][0],1),max(r[0][1],1)),(min(r[1][0],w-1),min(r[1][1],h-1)))   # a frame wider than the panel above shows only its part inside
ra=clamp((FA.xy(FB.x0,FB.y1),FA.xy(FB.x1,FB.y0)),AW,AH); rb=clamp((FB.xy(FC.x0,FC.y1),FB.xy(FC.x1,FC.y0)),BW,BH)
MAP=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{CY+CH_}" viewBox="0 0 {W} {CY+CH_}" role="img" aria-label="Three linked maps: {esc(M["panel1"][0])} shaded by area, {esc(M["panel2"][0])} by appellation, and the {esc(SHORT(APP))} appellation{(' with '+esc(elab)+' pinned') if est else ''}."><g>{"".join(a_)}</g>{link_rect(ra)}{badge(ra[1][0],ra[0][1],2)}<g transform="translate({BX},0)"><g>{"".join(b)}</g>{link_rect(rb)}{badge(rb[1][0],rb[0][1],3)}</g><g transform="translate(0,{CY})">{"".join(c)}</g></svg>'
ha=lambda g:round(g.area/1e4)
STATS=dict(appellation=APP,appellation_ha=ha(TG),appellation_communes=[C[k]['nom'] for k in tc],
           estate=dict(name=elab,commune=next((C[k]['nom'] for k in C if C[k]['geom'].contains(EP)),None),inside_appellation_land=TG.buffer(150).contains(EP),
                       km_to={SHORT(a):round(EP.distance(g)/1000,2) for a,g in LAYERS.items() if a in COMM and a!=APP}) if est else None,
           layers={a:ha(g) for a,g in LAYERS.items()},communes_by_area=collections.Counter(AREA[k] for k in wine_c))
open(os.path.join(OUT,'map.stats.json'),'w',encoding='utf-8').write(json.dumps(STATS,ensure_ascii=False,indent=1))
preview(MAP,OUT,W,CY+CH_)
print(json.dumps(STATS,ensure_ascii=False)); print('Wrote map.draft.svg, map.draft.png and map.stats.json in',OUT)

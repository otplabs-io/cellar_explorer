#!/usr/bin/env python3
"""Map engine for the village precision tier: regions that rank whole villages, such as Champagne.
Usage: python src/mapvillages.py wines/<id>/wine.json
Writes map.draft.svg, map.draft.png and map.stats.json next to the wine file. Copy the draft to map.svg once the
labels are approved. Everything regional comes from the wine's region profile (its "map" block); the wine supplies
"map_villages", the tree ids of the villages its source names, each with the grape it gives, and "map_villages_note".

Three linked levels, the same layout as the parcel maps (design-system/maps.md):
  1 the whole appellation, its villages tinted and the ranked ones in their rank's color, with a locator of France
  2 the heartland department, every village shaded by rank
  3 the wine's villages, numbered, with a key and legend in the right column
A village that has merged into a larger commune is drawn from its own cadastral parcels, so a merged commune can
show two ranks. The map shows villages, never vineyards: no vineyard parcels exist in the data, and the rank belongs
to the whole village."""
import json,os,sys,warnings
warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from shapely.geometry import shape,box
from shapely.ops import transform,unary_union
from pyproj import Transformer
import profiles,records
from mapkit import *
WINE=os.path.abspath(sys.argv[1]); OUT=os.path.dirname(WINE)
cfg=records.load_wine(WINE); prof=profiles.for_wine(cfg); M=prof['map']; OV=cfg.get('overrides',{})
assert M['engine']=='villages',f"this wine's profile uses the {M['engine']} engine"
TREE=profiles.tree()
ODW='https://raw.githubusercontent.com/24eme/opendatawine/9d65ed62f55097faf109bcd4c44805f596981bda/delimitation_aoc'
FG='https://raw.githubusercontent.com/gregoiredavid/france-geojson/5d34ee6d0140c29f785fdb047d9329f1aab58833'
TF=Transformer.from_crs(4326,M['projection'],always_xy=True).transform
proj=lambda g:transform(TF,g)
def load(url,name): return json.load(open(fetch(url,name),encoding='utf-8'))
# ------ communes, departments and the appellation area
C={}
for dep,s in M['departments'].items():
    for f in load(f'{FG}/departements/{s}/communes-{s}.geojson',f'c{dep}.json')['features']:
        C[f['properties']['code']]=dict(nom=f['properties']['nom'],dep=dep,geom=proj(shape(f['geometry']).buffer(0)))
DEPS={f['properties']['code']:proj(shape(f['geometry']).buffer(0)) for f in load(FG+'/departements.geojson','dep.json')['features']}
france=unary_union([g.buffer(2000) for g in DEPS.values()]).buffer(-2000)
a=M['area']; AREA=unary_union([proj(shape(f['geometry']).buffer(0)) for f in load(f"{ODW}/{a['commune'][:2]}/{a['commune']}/{a['file']}",f"area-{a['commune']}-{a['file']}")['features']])
AIRE={k for k,c in C.items() if c['geom'].intersection(AREA).area>c['geom'].area*.5}
# ------ villages: one per commune, except merged communes, which split into their former villages
CRUS=json.load(open(os.path.join(ROOT,'regions','sources',M['ranks']+'.json'),encoding='utf-8'))['entries']
NODE={}   # village code -> tree id
for i,v in TREE.items():
    if v.get('commune'): NODE[v.get('village_code') or v['commune']]=i
RANK={(e.get('village_code') or e['commune']):e['kind'] for e in CRUS}
MERGED={}
for e in CRUS:
    if e.get('merged'): MERGED.setdefault(e['commune'],set()).add(e['village_code'])
def split(code):
    """A merged commune's former villages, from its cadastral parcels. A parcel's prefix is its former village's code
    (000 for the village that kept the commune's code). Gaps between parcels (roads, rivers) go to the nearest village."""
    fs=load(f'{ODW}/{code[:2]}/{code}/cadastre-parcelles.json',f'cad-{code}.json')['features']; by={}
    for f in fs:
        p=f['id'][5:8]; vc=code if p=='000' else code[:2]+p
        by.setdefault(vc,[]).append(shape(f['geometry']).buffer(0))
    whole=C[code]['geom']; out={}; taken=None
    for vc,gs in sorted(by.items(),key=lambda kv:-len(kv[1])):
        g=proj(unary_union(gs)).buffer(40).buffer(-40).intersection(whole)
        if taken is not None: g=g.difference(taken)
        out[vc]=g; taken=g if taken is None else taken.union(g)
    gap=whole.difference(taken)
    for piece in getattr(gap,'geoms',[gap]):
        if piece.is_empty: continue
        best=max(out,key=lambda vc:out[vc].intersection(piece.buffer(60)).area); out[best]=out[best].union(piece)
    return {vc:g.buffer(.5).buffer(-.5) for vc,g in out.items()}
U=[]   # units: code, name, rank, geom, commune
for k,c in C.items():
    if k in MERGED:
        for vc,g in split(k).items():
            node=NODE.get(vc); U.append(dict(code=vc,name=TREE[node]['name'] if node else None,rank=RANK.get(vc),geom=g,commune=k,aire=k in AIRE))
    else:
        node=NODE.get(k); U.append(dict(code=k,name=TREE[node]['name'] if node and RANK.get(k) else c['nom'],rank=RANK.get(k),geom=c['geom'],commune=k,aire=k in AIRE))
BY={u['code']:u for u in U}
FILL={'Grand Cru':PLUM,'Premier Cru':GOLD}
def fill(u): return FILL.get(u['rank']) or (GOLDL if u['aire'] else LAND)
# ------ the wine's villages
TV=[]
for node,grape in cfg.get('map_villages',[]):   # none when no source names the wine's villages
    v=TREE[node]; code=v.get('village_code') or v['commune']; u=BY[code]; TV.append(dict(u,node=node,grape=grape,label=v['name']))
TG=unary_union([t['geom'] for t in TV]) if TV else unary_union([u['geom'] for u in U if u['rank']])
W,(AW,AH),BX,(BW,BH),CY,CH_=ML['width'],ML['region'],ML['subregion_x'],ML['subregion'],ML['village_y'],ML['village_h']
def paint(F,units,edge=WHITE,ew=MS['commune_edge']):
    vis=F.box(); out=[]
    for u in units:
        if u['geom'].intersects(vis): out.append(P(F.path(u['geom'],.3),fill(u),edge,ew))
    return out
# ------ panel 1: the appellation
FA=fit(AREA.bounds,AW,AH,34,2,6)
a_=[f'<rect width="{AW}" height="{AH}" fill="{PAPER}"></rect>',P(FA.path(unary_union([DEPS[d] for d in M['departments']]),.5),LAND)]
a_+=paint(FA,[u for u in U if u['aire']])
for d in M['departments']: a_.append(P(FA.path(DEPS[d],.5),'none',EDGE,MS['department'],f'stroke-dasharray="{MS["department_dash"]}"'))
for code in M['panel1_towns']: a_.append(town(FA,C[code]['geom'].representative_point(),M['towns'][code],LAND,M.get('panel1_town_side',{}).get(code,'start')))
def area_anchor(ref):
    us=[u for u in U if u['aire'] and u['commune'][:2]==ref] if ref.isdigit() else [u for u in U if NODE.get(u['code']) and TREE[NODE[u['code']]]['parent']==ref]
    return unary_union([u['geom'] for u in us]).representative_point()
for i,(name,ref) in enumerate(M['areas']):
    q=area_anchor(ref); x,y=FA.xy(q.x,q.y); lx,ly,an={**M.get('panel1_labels',{}),**OV.get('panel1',{})}.get(name,(x-46,y,'end'))
    a_.append(lead(x,y,lx,ly,name,an,'subregion_label',bg=PAPER))
px,py=FA.xy(TG.centroid.x,TG.centroid.y)
if TV: a_.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{num(MM["target_dot_r"])}" fill="{CORAL}" stroke="{WHITE}" stroke-width="{num(MS["target_dot_ring"])}"></circle>')
tw=OV.get('this_wine',M.get('this_wine',[min(px+31,236),py+9]))
if TV: a_.append(lead(px,py,tw[0],tw[1],'This wine','start','this_wine',TCORAL,CORAL,bg=PAPER))
a_.append(title(6,6,1,*M['panel1'],PAPER))
FF=fit(france.bounds,*ML['locator'],pad=2); a_.append(f'<g transform="translate(6,{AH-62})">'+P(FF.path(france,.3),LOC,WHITE,MS['commune_edge'])+P(FF.path(AREA,.3),CORAL)+'</g>')
# ------ panel 2: the heartland
hl=unary_union([u['geom'] for u in U if u['rank']]).buffer(M['panel2_margin_m'])   # every ranked village, with room around them
FB=fit(hl.bounds,BW,BH,30,6,10)
b=[f'<rect width="{BW}" height="{BH}" fill="{PAPER}"></rect>']
b+=paint(FB,U,MINOR,MS['commune_edge'])
if TV: b.append(P(FB.path(TG,.3),CORAL,INK,MS['target']))
b.append(P(FB.path(DEPS[M['heartland']],.5),'none',EDGE,MS['department'],f'stroke-dasharray="{MS["department_dash"]}"'))
for code,n in M['towns'].items():
    if code in C and C[code]['geom'].intersects(FB.box()): b.append(town(FB,C[code]['geom'].representative_point(),n,LAND))
m,lab=nice_scale(FB,70); b.append(title(6,6,2,*M['panel2'],PAPER)); b.append(scale(BW-104,BH-10,m,lab,FB)); b.append(north(BW-16,BH-22))
# ------ panel 3: the wine's villages
COLW=W-ML['inset_x']+10; av=W-COLW
FC=fit(TG.buffer(1500 if TV else 0).bounds,W,CH_,34,8,6,right=COLW)
c=[f'<rect width="{W}" height="{CH_}" fill="{LAND}"></rect>']
c+=paint(FC,U,WHITE,MS['vineyard_edge'])
vis=FC.box()
for u in U:
    if u['geom'].intersects(vis): c.append(P(FC.path(u['geom'],.25),'none',EDGE,MS['neighbor_border']*.8))
for t in TV: c.append(P(FC.path(t['geom'],.2),CORAL,INK,MS['target']))
col=box(FC.x0+av/FC.k,FC.y0,FC.x1,FC.y1)
placed=[box(0,0,330,40)]   # the panel title
def wbox(x,y,t,style,a):
    w=len(t)*MT[style]['size']*(.68 if t.isupper() else .58)+6; h=MT[style]['size']+4
    x0={'start':x,'middle':x-w/2,'end':x-w}[a]; return box(x0-2,y-h+3,x0+w+2,y+4)
def free(b):
    if b.bounds[2]>av-4 or b.bounds[0]<2 or any(b.intersects(o) for o in placed): return False
    placed.append(b); return True
tlabels=[]
for i,t in enumerate(TV,1):   # the wine's villages first: they always get their label
    q=t['geom'].representative_point(); x,y=FC.xy(q.x,q.y)
    lx,ly,an=OV.get('panel3',{}).get(t['label'],(x+11,y+4,'start'))
    placed.append(box(x-8,y-8,x+8,y+8)); placed.append(wbox(lx,ly,t['label'],'village_target',an)); tlabels.append((x,y,lx,ly,an,i,t['label']))
for u in U:   # other ranked villages: their name, where it fits
    if not u['rank'] or u['code'] in {t['code'] for t in TV}: continue
    g=u['geom'].intersection(vis).difference(col)
    if g.is_empty or g.area*FC.k*FC.k<1800: continue
    q=g.representative_point(); x,y=FC.xy(q.x,q.y); x,y=OV.get('panel3',{}).get(u['name'],(x,y))[:2]
    if not free(wbox(x,y,u['name'].upper(),'neighbor','middle')): continue
    c.append(H(x,y,u['name'].upper(),fill=NLAB,a='middle',bg=fill(u) if u['rank']!='Grand Cru' else WHITE,sw=MS['halo_wide'],extra=f'letter-spacing="{num(MT["neighbor"]["tracking"])}"',**ty('neighbor')))
for code,n in M['towns'].items():
    if code in C:
        q=C[code]['geom'].representative_point()
        if col.contains(q) or not vis.contains(q): continue
        x,y=FC.xy(q.x,q.y)
        for an in ('start','end'):
            if free(wbox(x+5 if an=='start' else x-5,y+3.5,n,'town',an)): c.append(town(FC,q,n,LAND,an)); break
for x,y,lx,ly,an,i,lab in tlabels: c.append(number(x,y,i)+H(lx,ly,lab,fill=TCORAL,a=an,bg=WHITE,sw=MS['halo_wide'],**ty('village_target')))
c.append(f'<rect x="{av}" y="0" width="{COLW}" height="{CH_}" fill="{PAPER}"></rect>')
c.append(title(6,6,3,cfg.get('map_title',f"{len(TV)} of its villages" if TV else 'The ranked villages'),M['panel3_subtitle'],LAND))
IX=ML['inset_x']; IW=ML['inset_w']; y=34
c.append(T(IX,y,cfg.get('map_key_title','The villages named'),fill=TCORAL,a='start',**ty('inset_title'))); y+=20
for i,t in enumerate(TV,1):
    c.append(number(IX+7,y-4,i)+T(IX+20,y,t['label'],**ty('key_total'))+T(IX+20,y+14,f"{t['rank'] or 'Unranked'} · {t['grape']}",fill=SOFT,a='start',**ty('key'))); y+=34
for line in cfg.get('map_villages_note',[]):
    c.append(T(IX,y,line,fill=INK,a='start',**ty('key'))); y+=14
y+=14
shown=[u for u in U if u['geom'].intersects(vis.difference(col)) and u['code'] not in {t['code'] for t in TV}]
has=lambda f:any(f(u) for u in shown)
leg=([('sw',CORAL,'Named for this wine')] if TV else [])+[x for x,ok in ((('sw',PLUM,'Grand Cru village'),has(lambda u:u['rank']=='Grand Cru')),(('sw',GOLD,'Premier Cru village'),has(lambda u:u['rank']=='Premier Cru')),
     (('sw',GOLDL,'Other Champagne village'),has(lambda u:not u['rank'] and u['aire'])),(('sw',LAND,'Outside the appellation'),has(lambda u:not u['aire']))) if ok]+[('line',EDGE,'Village border')]
for i,(k,cl,n) in enumerate(leg): c.append(swatch(IX,y+i*MM['legend_row'],k,cl,n))
m,lab=nice_scale(FC,90); c.append(scale(16,CH_-12,m,lab,FC)); c.append(north(16+m*FC.k+24,CH_-20))
ra=(FA.xy(FB.x0,FB.y1),FA.xy(FB.x1,FB.y0)); rb=(FB.xy(FC.x0,FC.y1),FB.xy(FC.x0+av/FC.k,FC.y0))
names=', '.join(t['label'] for t in TV)
MAP=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{CY+CH_}" viewBox="0 0 {W} {CY+CH_}" role="img" aria-label="Three linked maps: {esc(M["panel1"][0])} with its villages, {esc(M["panel2"][0])} with villages shaded by rank, and the villages named for this wine: {esc(names)}."><g>{"".join(a_)}</g>{link_rect(ra)}{badge(ra[1][0],ra[0][1],2)}<g transform="translate({BX},0)"><g>{"".join(b)}</g>{link_rect(rb)}{badge(rb[1][0],rb[0][1],3)}</g><g transform="translate(0,{CY})">{"".join(c)}</g></svg>'
ha=lambda g:round(g.area/1e4,1)
STATS=dict(villages={t['label']:dict(rank=t['rank'],grape=t['grape'],commune=C[t['commune']]['nom'],ha=ha(t['geom'])) for t in TV},
           distances_km={f"{p['label']} to {q['label']}":round(p['geom'].distance(q['geom'])/1000,1) for i,p in enumerate(TV) for q in TV[i+1:]},
           ranked_in_view=sorted(f"{u['name']} ({u['rank']})" for u in U if u['rank'] and u['geom'].intersects(vis.difference(col))),
           appellation_villages=len(AIRE),appellation_km2=round(AREA.area/1e6))
open(os.path.join(OUT,'map.stats.json'),'w',encoding='utf-8').write(json.dumps(STATS,ensure_ascii=False,indent=1))
preview(MAP,OUT,W,CY+CH_)
print(json.dumps(STATS,ensure_ascii=False)); print('Wrote map.draft.svg, map.draft.png and map.stats.json in',OUT)

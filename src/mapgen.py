#!/usr/bin/env python3
# Map generator for NEW wines. Usage: python src/mapgen.py wines/<id>/wine.json
# Writes map.draft.svg and map.stats.json next to the wine file. Copy the draft to map.svg once the labels are approved.
import json,os,re,subprocess,sys,warnings
from pathlib import Path
warnings.filterwarnings('ignore')
from shapely.geometry import shape,box
from shapely.ops import transform,unary_union
from pyproj import Transformer
WINE=os.path.abspath(sys.argv[1]); ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.path.dirname(WINE); CA=os.path.join(ROOT,'data','cache','');os.makedirs(CA,exist_ok=True)
cfg=json.load(open(WINE))
ODW='https://raw.githubusercontent.com/24eme/opendatawine/9d65ed62f55097faf109bcd4c44805f596981bda/delimitation_aoc'
FG='https://raw.githubusercontent.com/gregoiredavid/france-geojson/5d34ee6d0140c29f785fdb047d9329f1aab58833'
REG="21010 21013 21017 21037 21050 21054 21058 21070 21077 21086 21093 21099 21109 21110 21133 21149 21150 21161 21162 21166 21169 21173 21182 21186 21192 21194 21195 21196 21200 21219 21223 21231 21241 21254 21265 21267 21289 21295 21297 21302 21309 21343 21368 21373 21378 21384 21390 21393 21397 21401 21407 21409 21412 21419 21428 21435 21442 21444 21450 21460 21461 21464 21465 21480 21485 21488 21492 21499 21506 21512 21523 21527 21541 21569 21582 21590 21597 21606 21617 21628 21653 21688 21693 21698 21700 21711 21712 21714 21716 71005 71007 71016 71019 71031 71032 71034 71035 71036 71037 71039 71042 71051 71052 71057 71058 71066 71067 71069 71070 71072 71073 71074 71078 71080 71084 71085 71087 71094 71099 71100 71105 71108 71109 71122 71124 71126 71130 71135 71146 71147 71149 71150 71151 71156 71159 71164 71169 71171 71174 71182 71183 71188 71193 71195 71201 71202 71210 71214 71221 71226 71235 71236 71241 71245 71247 71248 71249 71250 71258 71264 71267 71270 71272 71274 71284 71292 71294 71299 71302 71305 71308 71324 71338 71343 71345 71350 71353 71360 71369 71371 71374 71377 71378 71383 71392 71400 71403 71404 71416 71417 71425 71430 71431 71442 71447 71448 71455 71459 71460 71461 71464 71468 71480 71485 71487 71494 71495 71496 71498 71501 71503 71507 71512 71513 71515 71518 71525 71526 71543 71550 71563 71567 71572 71574 71582 71583 71584 89003 89021 89023 89024 89034 89038 89039 89045 89068 89084 89095 89098 89104 89108 89112 89118 89123 89130 89137 89149 89153 89155 89168 89175 89202 89206 89211 89212 89226 89227 89256 89262 89270 89303 89315 89319 89337 89341 89364 89393 89409 89418 89423 89426 89430 89438 89441 89446 89447 89477 89479 89482".split()
TOK=json.load(open(os.path.join(ROOT,'design-system','tokens.json'))); MC,MT,MS,MM,ML=TOK['map'],TOK['map_type'],TOK['map_stroke'],TOK['map_mark'],TOK['map_layout']
INK,CORAL,TCORAL,LAND,TEAL,PLUM,GOLD,GOLDL,EDGE,PAPER=(MC[k] for k in ('ink','target','target_text','land','parent_outline','grand_cru','premier_cru','village','border','paper'))
WHITE,SOFT,MINOR,CFILL,TFILL,NEIGH,TPAPER,NLAB,LOC=(MC[k] for k in ('white','soft_text','minor_border','commune_fill','target_commune_fill','neighbor_vineyard','target_commune_paper','neighbor_label','locator_land'))
CSUB=TOK['subregion']
VILLAGES={'Côte de Beaune':['Ladoix-Serrigny','Aloxe-Corton','Pernand-Vergelesses','Savigny-lès-Beaune','Chorey-les-Beaune','Beaune','Pommard','Volnay','Monthelie','Auxey-Duresses','Saint-Romain','Meursault','Puligny-Montrachet','Chassagne-Montrachet','Saint-Aubin','Santenay','Remigny','Cheilly-lès-Maranges','Dezize-lès-Maranges','Sampigny-lès-Maranges'],
'Côte de Nuits':['Marsannay-la-Côte','Couchey','Fixin','Brochon','Gevrey-Chambertin','Morey-Saint-Denis','Chambolle-Musigny','Vougeot','Flagey-Echezeaux','Vosne-Romanée','Nuits-Saint-Georges','Premeaux-Prissey','Comblanchien','Corgoloin'],
'Côte Chalonnaise':['Bouzeron','Rully','Mercurey','Saint-Martin-sous-Montaigu','Givry','Dracy-le-Fort','Jambles','Montagny-lès-Buxy','Buxy','Saint-Vallerin'],
'Mâconnais':['Fuissé','Solutré-Pouilly','Vergisson','Chaintré','Saint-Vérand','Davayé','Vinzelles','Loché','Viré','Clessé','Prissé','Lugny'],
'Chablis':['Chablis','Beine','Chichée','Courgis','Fleys','Fontenay-près-Chablis','La Chapelle-Vaupelteigne','Lignorelles','Maligny','Poilly-sur-Serein','Préhy','Villy','Viviers']}
GC=set('Chambertin|Chambertin-Clos de Bèze|Chapelle-Chambertin|Charmes-Chambertin|Mazoyères-Chambertin|Griotte-Chambertin|Latricières-Chambertin|Mazis-Chambertin|Ruchottes-Chambertin|Clos de la Roche|Clos Saint-Denis|Clos de Tart|Clos des Lambrays|Bonnes-Mares|Musigny|Clos de Vougeot|Clos Vougeot|Échezeaux|Grands Échezeaux|La Grande Rue|La Romanée|La Tâche|Richebourg|Romanée-Conti|Romanée-Saint-Vivant|Montrachet|Chevalier-Montrachet|Bâtard-Montrachet|Bienvenues-Bâtard-Montrachet|Criots-Bâtard-Montrachet|Charlemagne'.split('|'))
is_gc=lambda n:n in GC or n.startswith('Corton') or 'grand cru' in n
is_pc=lambda n:'premier cru' in n
is_reg=lambda n:n.startswith(('Bourgogne','Crémant','Coteaux Bourguignons','Côte de Beaune','Côte de Nuits','Petit Chablis'))
TF=Transformer.from_crs(4326,2154,always_xy=True).transform; TI=Transformer.from_crs(2154,4326,always_xy=True).transform
proj=lambda g:transform(TF,g); ll=TF
def fetch(url,name):
    p=CA+name
    if not os.path.exists(p): subprocess.run(['curl','-s','-f','-m','90','-o',p,url])
    return p if os.path.exists(p) else None
C={}
for dep,s in (('21','21-cote-d-or'),('71','71-saone-et-loire'),('89','89-yonne')):
    for f in json.load(open(fetch(f'{FG}/departements/{s}/communes-{s}.geojson',f'c{dep}.json')))['features']:
        C[f['properties']['code']]=dict(nom=f['properties']['nom'],dep=dep,geom=proj(shape(f['geometry']).buffer(0)))
inv={}
for k,c in C.items(): inv.setdefault(c['nom'],k)
deps={f['properties']['code']:proj(shape(f['geometry']).buffer(0)) for f in json.load(open(fetch(FG+'/departements.geojson','dep.json')))['features']}
france=unary_union([g.buffer(2000) for g in deps.values()]).buffer(-2000); tri=unary_union([deps[d] for d in ('21','71','89')])
def denoms(code):
    p=fetch(f'{ODW}/{code[:2]}/{code}/delimitations.json',f'd{code}.json')
    return json.load(open(p)) if p else {}
def dgeom(code,name):
    f=denoms(code).get(name)
    if not f: return None
    p=fetch(f'{ODW}/{code[:2]}/{code}/{f}',f'g{code}-{f}')
    if not p: return None
    # some source files carry stray non-AOC shapes (e.g. "Var"), so clip every denomination to its commune
    g=unary_union([proj(shape(x['geometry']).buffer(0)) for x in json.load(open(p))['features']]).intersection(C[code]['geom'].buffer(500))
    return None if g.is_empty else g
def U(gs):
    gs=[g for g in gs if g is not None]; return unary_union(gs) if gs else None
def land(code):
    g=U([dgeom(code,n) for n in denoms(code) if not is_reg(n) and not is_pc(n)])
    return g if g is not None else dgeom(code,'Bourgogne')
def broad(code):
    g=dgeom(code,'Crémant de Bourgogne')
    return g if g is not None else dgeom(code,'Bourgogne')
def sub(code):
    c=C[code]; lon,lat=TI(c['geom'].centroid.x,c['geom'].centroid.y)
    if c['dep']=='89': return 'Chablis'
    if c['dep']=='21':
        if lat>47.55: return 'Châtillonnais'
        return 'Côte de Nuits' if lat>47.098 or c['nom'] in('Corgoloin','Comblanchien') else 'Côte de Beaune'
    if c['nom'] in('Cheilly-lès-Maranges','Dezize-lès-Maranges','Sampigny-lès-Maranges','Remigny',"Paris-l'Hôpital",'Chagny'): return 'Côte de Beaune'
    return 'Côte Chalonnaise' if lat>46.60 else 'Mâconnais'
HF=f'font-family="{TOK["font"]["display"]["family"]}, sans-serif"'; BF=f"font-family=\"'{TOK['font']['body']['family']}', sans-serif\""
def num(v):
    """A number as the map writes it: 0.5 as .5, 2.0 as 2."""
    if isinstance(v,str): return v
    s=f'{v:g}'; return s.replace('0.','.',1) if s.startswith(('0.','-0.')) else s
def ty(name):
    t=MT[name]; return dict(size=t['size'],w=t['weight'],ff=HF if t.get('family')=='display' else BF)
def T(x,y,s,size=11,w=400,fill=INK,a='start',ff=BF,extra=''):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{a}" {ff} {extra}>{s.replace("&","&amp;")}</text>'
def H(x,y,s,size=11,w=600,fill=INK,a='middle',ff=BF,bg=WHITE,sw=MS['halo'],extra=''):
    return T(x,y,s,size,w,bg,a,ff,f'stroke="{bg}" stroke-width="{sw}" stroke-linejoin="round" {extra}')+T(x,y,s,size,w,fill,a,ff,extra)
def P(d,fill='none',stroke='none',sw=0,extra=''): return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{num(sw)}" {extra}></path>'
class Frame:
    def __init__(s,bb,W,H_):
        s.x0,s.y0,s.x1,s.y1=bb; s.k=W/(s.x1-s.x0); s.W=W; s.H=H_
    def xy(s,x,y): return (x-s.x0)*s.k,(s.y1-y)*s.k
    def path(s,g,tol=.4):
        if g is None or g.is_empty: return ''
        g=g.intersection(box(s.x0,s.y0,s.x1,s.y1)).simplify(tol/s.k,preserve_topology=True); out=[]
        def w(g):
            if g.geom_type=='Polygon':
                if g.area*s.k*s.k<.3: return
                for r in [g.exterior]+list(g.interiors): out.append('M'+' '.join('%.1f,%.1f'%s.xy(*c) for c in r.coords)+'Z')
            elif hasattr(g,'geoms'):
                for x in g.geoms: w(x)
        w(g); return ''.join(out)
def fit(bb,w,h,top=0,bottom=0,pad=8,dx=0):
    k=min((w-2*pad)/(bb[2]-bb[0]),(h-top-bottom-2*pad)/(bb[3]-bb[1])); cx,cy=(bb[0]+bb[2])/2,(bb[1]+bb[3])/2
    y1=cy+(h/2+(top-bottom)/2)/k; return Frame((cx-w/2/k+dx/k,y1-h/k,cx+w/2/k+dx/k,y1),w,h)
def title(x,y,n,t,s,bg):
    r=MM['panel_number_r']; hw=MS['halo_wide']
    return f'<circle cx="{x+r}" cy="{y+r}" r="{r}" fill="{INK}"></circle>'+T(x+r,y+15.5,str(n),fill=WHITE,a='middle',**ty('panel_number'))+H(x+28,y+11.5,t,fill=INK,a='start',bg=bg,sw=hw,**ty('panel_title'))+H(x+28,y+24.5,s,fill=SOFT,a='start',bg=bg,sw=hw,**ty('panel_subtitle'))
def lead(x0,y0,x1,y1,t,a='start',style='village',fill=INK,col=INK,dy=3.5,bg=LAND):
    return f'<path d="M{x0:.0f},{y0:.0f}L{x1:.0f},{y1:.0f}" stroke="{col}" stroke-width="{num(MS["leader"])}" fill="none"></path><circle cx="{x0:.0f}" cy="{y0:.0f}" r="{num(MM["leader_dot_r"])}" fill="{col}"></circle>'+H(x1+(3 if a=='start' else -3),y1+dy,t,fill=fill,a=a,bg=bg,**ty(style))
def scale(x,y,m,lab,F):
    w=m*F.k; return f'<path d="M{x},{y-4}V{y}H{x+w:.1f}V{y-4}" fill="none" stroke="{INK}" stroke-width="{num(MS['scale_bar'])}"></path>'+T(x+w/2,y-6,lab,fill=INK,a='middle',**ty('scale'))
def north(x,y): return f'<path d="M{x},{y-13}L{x+5},{y}L{x},{y-3}L{x-5},{y}Z" fill="{INK}"></path>'+T(x,y+11,'N',fill=INK,a='middle',**ty('north'))
def badge(x,y,n): return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{MM["badge_r"]}" fill="{CORAL}" stroke="{WHITE}" stroke-width="{num(MS["badge_ring"])}"></circle>'+T(x,y+3.6,str(n),fill=WHITE,a='middle',**ty('badge'))
OV=cfg.get('overrides',{})
# ------ target
tc=cfg.get('commune_codes') or [inv[n] for n in cfg['communes']]; TN=cfg['target']; APP=cfg['appellation']   # codes when two communes share a name (Givry)
for _n,_k in zip(cfg['communes'],tc): inv[_n]=_k   # later name lookups use the same commune
TG=U([dgeom(c,TN) for c in tc]); assert TG is not None,'target denomination not found: '+TN+' / options: '+', '.join(denoms(tc[0]))
CH=U([C[c]['geom'] for c in tc]); SUB=sub(tc[0])
nm=lambda n:n.replace(APP+' premier cru ','').replace(APP+' grand cru ','')
short=cfg.get('short') or nm(TN)
VIL=U([dgeom(c,n) for c in tc for n in denoms(c) if not is_reg(n) and not is_pc(n) and not is_gc(n)])
PC=U([dgeom(c,n) for c in tc for n in denoms(c) if n==APP+' premier cru'])
allc={n:U([dgeom(c,n) for c in tc]) for c in tc for n in denoms(c) if is_pc(n) and n not in(TN,APP+' premier cru')}
VILLAGE=TN==APP   # a village wine: its land is the village-level vineyards, without the premier and grand crus inside the name
if VILLAGE:
    hi=U([PC]+[dgeom(c,n) for c in tc for n in denoms(c) if is_gc(n)])
    if hi is not None: TG=TG.difference(hi).buffer(-.3).buffer(.3)
    allc_v=allc; allc={}
ha=lambda g:g.area/1e4
inside={n:g for n,g in allc.items() if g is not None and g.intersection(TG).area/g.area>.98}
parents={n:g for n,g in allc.items() if g is not None and TG.intersection(g).area/TG.area>.98 and g.area>TG.area*1.02}
inside={n:g for n,g in inside.items() if n not in parents}
PAR=min(parents.items(),key=lambda kv:kv[1].area) if parents and not OV.get('no_parent') else None   # no_parent: hide a premier cru that overlaps a Grand Cru target
parts={nm(n):g for n,g in inside.items()}
rest=TG.difference(U(list(inside.values()))).buffer(-.3).buffer(.3) if inside else None
if rest is not None and ha(rest)>.05: parts[short]=rest
parts=dict(sorted(parts.items(),key=lambda kv:(kv[0]!=short,-kv[1].area)))
# ------ commune borders, snapped to vineyard parcels
near=[k for k,c in C.items() if c['geom'].distance(CH)<30]
A={k:broad(k) for k in near}; A={k:v for k,v in A.items() if v is not None}
ref={}
for k in near:
    o=U([v for j,v in A.items() if j!=k]); g=C[k]['geom']
    if k in A: g=g.union(A[k])
    if o is not None: g=g.difference(o)
    ref[k]=g.buffer(.5).buffer(-.5)
RCH=U([ref[c] for c in tc])
W,(AW,AH),BX,(BW,BH),CY,CH_=ML['width'],ML['region'],ML['subregion_x'],ML['subregion'],ML['village_y'],ML['village_h']
# ------ panel 1
regc=[c for c in REG if c in C]
FA=fit(unary_union([C[c]['geom'] for c in regc]).bounds,AW,AH,34,2,6)
a=[f'<rect width="{AW}" height="{AH}" fill="{PAPER}"></rect>',P(FA.path(tri,.5),LAND)]
for c in regc: a.append(P(FA.path(C[c]['geom'],.3),CSUB[sub(c)],WHITE,MS['commune_edge']))
a.append(P(FA.path(tri,.5),'none',EDGE,MS['department'],f'stroke-dasharray="{MS["department_dash"]}"'))
def town(F,lon,lat,n):
    left=n in OV.get('town_left',[])   # a town whose label would sit under the panel-2 badge goes on the left of its dot
    x,y=F.xy(*ll(lon,lat)); return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{num(MM['town_r'])}" fill="{WHITE}" stroke="{INK}" stroke-width="{num(MS['town'])}"></circle>'+H(x-5 if left else x+5,y+3.5,n,fill=INK,a='end' if left else 'start',bg=LAND,**ty('town'))
for lon,lat,n in ((5.0415,47.322,'Dijon'),(4.84,47.026,'Beaune'),(4.8535,46.7806,'Chalon'),(4.8285,46.3069,'Mâcon')): a.append(town(FA,lon,lat,n))
for r in ((88,96,26,134,'Chablis','start'),(180,62,214,50,'Châtillonnais','start'),(218,165,152,159,'Côte de Nuits','end'),(197,200,132,196,'Côte de Beaune','end'),(196,240,132,236,'Côte Chalonnaise','end'),(196,288,146,288,'Mâconnais','end')):
    a.append(lead(*r[:4],r[4],r[5],'subregion_label'))
px,py=FA.xy(CH.centroid.x,CH.centroid.y)
a.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{num(MM['target_dot_r'])}" fill="{CORAL}" stroke="{WHITE}" stroke-width="{num(MS['target_dot_ring'])}"></circle>')
tw=OV.get('this_wine',[min(px+31,236),py+9]); a.append(lead(px,py,tw[0],tw[1],'This wine','start','this_wine',TCORAL,CORAL))
a.append(title(6,6,1,'Burgundy','Wine villages, shaded by subregion',PAPER))
FF=fit(france.bounds,*ML['locator'],pad=2); a.append(f'<g transform="translate(6,{AH-62})">'+P(FF.path(france,.3),LOC,WHITE,MS['commune_edge'])+P(FF.path(tri,.3),CORAL)+'</g>')
# ------ panel 2
vn=[n for n in VILLAGES.get(SUB,[]) if n in inv]
for n in cfg['communes']:
    if n not in vn: vn.append(n)
LN={n:land(inv[n]) for n in vn}
FB=fit(unary_union([g for g in LN.values() if g is not None]).bounds,BW,BH,26,6,14,18)
b=[f'<rect width="{BW}" height="{BH}" fill="{PAPER}"></rect>']
vis=box(FB.x0,FB.y0,FB.x1,FB.y1)
for c in C.values():
    if c['geom'].intersects(vis): b.append(P(FB.path(c['geom'],.3),LAND,MINOR,MS['commune_edge']))
for n in vn: b.append(P(FB.path(C[inv[n]]['geom'],.3),CFILL))
b.append(P(FB.path(CH,.2),TFILL))
for n,g in LN.items():
    if n not in cfg['communes']: b.append(P(FB.path(g,.3),GOLD))
b.append(P(FB.path(U([LN[n] for n in cfg['communes']]),.3),CORAL))
for n in vn:
    for d in denoms(inv[n]):
        if is_gc(d): b.append(P(FB.path(dgeom(inv[n],d),.3),PLUM))
for n in vn: b.append(P(FB.path(C[inv[n]]['geom'],.3),'none',EDGE,MS['village_border']))
b.append(P(FB.path(CH,.2),'none',INK,MS['target_village_border']))
pts=[(n,)+FB.xy(C[inv[n]]['geom'].representative_point().x,C[inv[n]]['geom'].representative_point().y) for n in vn]
ys=[p[2] for p in pts]; xs=[p[1] for p in pts]; my=sum(ys)/len(ys); mx=sum(xs)/len(xs)
sl=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/max(sum((y-my)**2 for y in ys),1)
sides={'start':[],'end':[]}
for n,x,y in pts: sides['start' if x>mx+sl*(y-my) else 'end'].append((n,x,y))
PRETTY={'Chorey-les-Beaune':'Chorey-lès-Beaune','Monthelie':'Monthélie','Flagey-Echezeaux':'Flagey-Échezeaux'}
for an,L in sides.items():
    L.sort(key=lambda r:r[2]); last=36
    for n,x,y in L:
        ly=max(y,last+15); last=ly; lab=PRETTY.get(n,n); hot=n in cfg['communes']; tw=len(lab)*(6.6 if hot else 5.6)
        lx=min(x+55,BW-tw-8) if an=='start' else max(x-55,tw+8); an2=an
        if n in OV.get('panel2',{}): lx,ly,an2=OV['panel2'][n]
        b.append(lead(x,y,lx,ly,lab,an2,'village_target' if hot else 'village',TCORAL if hot else INK,CORAL if hot else INK))
b.append(title(6,6,2,SUB,'Village borders and vineyard land',PAPER)); b.append(scale(BW-104,BH-10,5000,'5 km',FB)); b.append(north(BW-16,BH-22))
# ------ panel 3
IX,IY,IW=ML['inset_x'],ML['inset_y'],ML['inset_w']; COLW=W-IX+10; rb=RCH.bounds; av=W-COLW
kC=min((CH_-4)/((rb[3]-rb[1])+180),(av-60)/(rb[2]-rb[0]+300)); xx=rb[0]-(av/kC-(rb[2]-rb[0]))/2; y1=(rb[1]+rb[3])/2+CH_/2/kC
FC=Frame((xx,y1-CH_/kC,xx+W/kC,y1),W,CH_); vis=box(FC.x0,FC.y0,FC.x1,FC.y1)
c=[f'<rect width="{W}" height="{CH_}" fill="{LAND}"></rect>']
for k,v in A.items():
    if k not in tc: c.append(P(FC.path(v,.25),NEIGH))
c.append(P(FC.path(RCH,.2),TPAPER)); c.append(P(FC.path(VIL,.2),GOLDL,WHITE,MS['vineyard_edge'])); c.append(P(FC.path(PC,.2),GOLD,WHITE,MS['vineyard_edge']))
GCS={}
for k in near:
    for d in denoms(k):
        if is_gc(d):
            g=dgeom(k,d)
            if g is not None: GCS[d]=g if d not in GCS else GCS[d].union(g)
for d,g in GCS.items(): c.append(P(FC.path(g,.2),PLUM,WHITE,MS['grand_cru_edge']))
if PAR: c.append(P(FC.path(PAR[1],.2),'none',TEAL,MS['parent']))
c.append(P(FC.path(TG,.15),CORAL,INK,MS['target']))
for k,g in ref.items():
    if k not in tc and g.intersects(vis): c.append(P(FC.path(g,.25),'none',EDGE,MS['neighbor_border'],f'stroke-dasharray="{MS["neighbor_dash"]}"'))
c.append(P(FC.path(RCH,.2),'none',INK,MS['target_commune']))
col=box(FC.x0+av/kC,FC.y0,FC.x1,FC.y1-94/kC)
for k,g in ref.items():
    i=g.intersection(vis).difference(col)
    if k in tc or i.is_empty or i.area*kC*kC<2500: continue
    n=C[k]['nom'].upper(); q=i.representative_point(); x,y=FC.xy(q.x,q.y)
    if n in OV.get('neighbors',{}): x,y=OV['neighbors'][n]
    c.append(H(x,y,n,fill=NLAB,a='middle',bg=LAND,sw=MS['halo_wide'],extra=f'letter-spacing="{num(MT["neighbor"]["tracking"])}"',**ty('neighbor')))
if cfg.get('village_lonlat'):
    x,y=FC.xy(*ll(*cfg['village_lonlat'])); c.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{num(MM['village_marker_r'])}" fill="{WHITE}" stroke="{INK}" stroke-width="{num(MS['village_marker'])}"></circle>'+H(x+8,y-7,cfg.get('village_label',cfg['communes'][0].split('-')[0]+' village'),fill=INK,a='start',bg=TPAPER,**ty('village_marker')))
q=RCH.difference(U([VIL,PC])).representative_point(); x,y=FC.xy(q.x,q.y)
if 'commune_label' in OV: x,y=OV['commune_label']
for i,l in enumerate(cfg.get('commune_label_lines',[cfg['communes'][0]])): c.append(H(x,y+i*MT['commune']['line'],l.upper(),fill=INK,a='middle',bg=TPAPER,sw=MS['halo_wide'],extra=f'letter-spacing="{num(MT["commune"]["tracking"])}"',**ty('commune')))
c.append(f'<rect x="{av}" y="94" width="{COLW}" height="{CH_-94}" fill="{PAPER}"></rect>')
for l in cfg.get('map_labels',[]):
    g=GCS.get(l['denom']) or allc.get(l['denom']) or (allc_v.get(l['denom']) if VILLAGE else None); q=g.representative_point(); x,y=FC.xy(q.x,q.y); hot=l['denom'] in GCS
    c.append(lead(x,y,x+l.get('dx',40),y+l.get('dy',-14),l['text'],l.get('anchor','start'),'cru_label',PLUM if hot else INK,PLUM if hot else INK))
if PAR:
    q=PAR[1].difference(TG).representative_point(); x,y=FC.xy(q.x,q.y)
    if 'parent_label' in OV: x,y=OV['parent_label']
    c.append(H(x,y,nm(PAR[0]).upper(),fill=TEAL,a='middle',bg=WHITE,sw=MS['halo_wide'],**ty('parent')))
c.append(title(6,6,3,cfg['communes'][0],'Official vineyard boundaries',LAND))
rows=len(parts) if len(parts)>1 else 0; IH=ML['inset_h'] if rows<=6 else max(ML['inset_h_min'],ML['inset_h']-(rows-6)*ML['inset_row_cut'])
bq=[FC.xy(TG.bounds[0]-20,TG.bounds[3]+20),FC.xy(TG.bounds[2]+20,TG.bounds[1]-20)]
c.append(f'<rect x="{bq[0][0]:.1f}" y="{bq[0][1]:.1f}" width="{bq[1][0]-bq[0][0]:.1f}" height="{bq[1][1]-bq[0][1]:.1f}" fill="none" stroke="{CORAL}" stroke-width="{num(MS['zoom_link'])}"></rect><path d="M{bq[1][0]:.1f},{bq[1][1]:.1f}L{IX},{IY+IH}M{bq[1][0]:.1f},{bq[0][1]:.1f}L{IX},{IY}" stroke="{CORAL}" stroke-width="{num(MS['zoom_link'])}" fill="none"></path>')
FI=fit(TG.bounds,IW,IH,pad=10); ins=[f'<rect width="{IW}" height="{IH}" fill="{TPAPER}"></rect>',P(FI.path(PC,.2),GOLD,WHITE,MS['vineyard_edge'])]
TINTS=TOK['plot_tints']
if rows:
    for i,(n,g) in enumerate(parts.items()): ins.append(P(FI.path(g,.2),TINTS[i%len(TINTS)],WHITE,MS['plot_edge']))
    for i,(n,g) in enumerate(parts.items()):
        q=g.representative_point(); x,y=FI.xy(q.x,q.y); ins.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{num(MM['plot_number_r'])}" fill="{WHITE}" stroke="{INK}" stroke-width="{num(MS['plot_number_ring'])}"></circle>'+T(x,y+3.7,str(i+1),fill=INK,a='middle',**ty('plot_number')))
else: ins.append(P(FI.path(TG,.2),CORAL,WHITE,MS['plot_edge']))
if PAR: ins.append(P(FI.path(PAR[1],.2),'none',TEAL,MS['inset_parent']))
c.append(f'<g transform="translate({IX},{IY})">'+''.join(ins)+f'<rect width="{IW}" height="{IH}" fill="none" stroke="{CORAL}" stroke-width="{num(MS['inset_frame'])}"></rect></g>')
c.append(T(IX,IY-7,cfg.get('inset_title',f'Inside the {short} name' if rows else f'Zooming in on {short}'),fill=TCORAL,a='start',**ty('inset_title')))
ky=IY+IH+15
for i,(n,g) in enumerate(parts.items() if rows else []):
    yy=ky+i*MM['key_row']; c.append(T(IX+5,yy,str(i+1),fill=TCORAL,a='middle',**ty('key_number'))+T(IX+16,yy,n,**ty('key'))+T(IX+IW,yy,f'{ha(g):.1f} ha',fill=INK,a='end',**ty('key')))
yy=ky+rows*MM['key_row']+2
c.append(f'<path d="M{IX},{yy-11}H{IX+IW}" stroke="{INK}" stroke-width="{num(MS['key_rule'])}"></path>'+T(IX+16 if rows else IX,yy+1,'Total',**ty('key_total'))+T(IX+IW,yy+1,f'{ha(TG):.1f} ha',fill=INK,a='end',**ty('key_total')))
LY=yy+17
leg=[('sw',CORAL,short),('sw',PLUM,'Grand Cru'),('sw',GOLD,'Premier Cru'),('sw',GOLDL,'Village'),('line',INK,'Village border')]+([('out',TEAL,nm(PAR[0]))] if PAR else [])
lr,lc=MM['legend_row'],MM['legend_col']; pos=[(IX,LY),(IX,LY+lr),(IX,LY+2*lr),(IX+lc,LY+2*lr),(IX+lc,LY+lr),(IX+lc,LY)]; sw_,sh_=MM['swatch']
for (t,cl,n),(x,y) in zip(leg,pos):
    if t=='sw': c.append(f'<rect x="{x}" y="{y-8}" width="{sw_}" height="{sh_}" fill="{cl}" stroke="{EDGE}" stroke-width="{num(MS['legend_swatch'])}"></rect>')
    if t=='out': c.append(f'<rect x="{x+.5}" y="{y-7.5}" width="{sw_-1}" height="{sh_-1}" fill="none" stroke="{cl}" stroke-width="{num(MS['legend_outline'])}"></rect>')
    if t=='line': c.append(f'<path d="M{x},{y-3}h{sw_}" stroke="{cl}" stroke-width="{num(MS['legend_line'])}"></path>')
    c.append(T(x+15,y,n,**ty('legend')))
c.append(scale(16,CH_-12,1000,'1 km',FC)); c.append(north(16+1000*FC.k+24,CH_-20))
ra=(FA.xy(FB.x0,FB.y1),FA.xy(FB.x1,FB.y0)); rb_=(FB.xy(FC.x0,FC.y1),FB.xy(FC.x0+av/kC,FC.y0))
rect=lambda r:f'<rect x="{r[0][0]:.1f}" y="{r[0][1]:.1f}" width="{r[1][0]-r[0][0]:.1f}" height="{r[1][1]-r[0][1]:.1f}" fill="none" stroke="{CORAL}" stroke-width="{num(MS['level_link'])}"></rect>'
MAP=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{CY+CH_}" viewBox="0 0 {W} {CY+CH_}" role="img" aria-label="Three linked maps locating {short}: Burgundy with its wine villages, the {SUB} with village borders, and {cfg["communes"][0]} with its vineyards."><g>{"".join(a)}</g>{rect(ra)}{badge(ra[1][0],ra[0][1],2)}<g transform="translate({BX},0)"><g>{"".join(b)}</g>{rect(rb_)}{badge(rb_[1][0],rb_[0][1],3)}</g><g transform="translate(0,{CY})">{"".join(c)}</g></svg>'
STATS={'target_ha':round(ha(TG),2),'parent':PAR and [nm(PAR[0]),round(ha(PAR[1]),1)],'plots':{k:round(ha(v),2) for k,v in parts.items()},'dist_m':{C[k]['nom']:round(TG.distance(g)) for k,g in ref.items() if k not in tc},'grand_crus_near':sorted(GCS),'climats':sorted(nm(n) for n in (allc_v if VILLAGE else allc))}
print(json.dumps(STATS,ensure_ascii=False))
open(os.path.join(OUT,'map.stats.json'),'w').write(json.dumps(STATS,ensure_ascii=False,indent=1))
open(os.path.join(OUT,'map.draft.svg'),'w').write(MAP)
from playwright.sync_api import sync_playwright
FD=Path(ROOT,'design-system','fonts').as_uri()+'/'
CSS=''.join(f"@font-face{{font-family:'Nunito Sans';font-weight:{w};src:url(\"{FD}nunito-sans-latin-{w}-normal.woff2\")}}" for w in (400,600,700,800))+''.join(f"@font-face{{font-family:Poppins;font-weight:{w};src:url(\"{FD}poppins-latin-{w}-normal.woff2\")}}" for w in (600,700,800))
pv=os.path.join(OUT,'map.draft.html'); open(pv,'w').write(f'<!doctype html><meta charset="utf-8"><style>{CSS}body{{margin:0}}</style>{MAP}')
with sync_playwright() as p:
    br=p.chromium.launch(); pg=br.new_page(viewport={'width':736,'height':752},device_scale_factor=2); pg.goto(Path(pv).as_uri()); pg.wait_for_timeout(500); pg.screenshot(path=os.path.join(OUT,'map.draft.png')); br.close()
print('Wrote map.draft.svg, map.draft.png and map.stats.json in',OUT)

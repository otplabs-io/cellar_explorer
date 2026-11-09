#!/usr/bin/env python3
"""Map engine for the AVA precision tier: American Viticultural Areas nested inside each other, such as Napa.
Usage: python src/mapavas.py wines/<id>/wine.json
Writes map.draft.svg, map.draft.png and map.stats.json next to the wine file. Copy the draft to map.svg once the
labels are approved. Regional settings come from the wine's region profile ("map" block). The wine gives "map_ava"
(the AVA's name as the TTB spells it) and, optionally, "map_estate" (a pin with its source) or "map_estate_note"
(lines of text for the key when no source places the estate).

Three linked levels, the same layout as the other engines (design-system/maps.md):
  1 the outer AVA (North Coast) over its counties, with the region AVA (Napa Valley) inside it
  2 the region AVA with every AVA nested in it, the wine's in coral
  3 the wine's AVA and its neighbours, the county line, and the estate pin or note
AVA boundaries come from the UC Davis Library AVA project, digitized from the TTB's legal descriptions."""
import json,os,sys,warnings
warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from shapely.geometry import shape,box,Point
from shapely.ops import transform,unary_union
from pyproj import Transformer
import profiles,records
from mapkit import *
WINE=os.path.abspath(sys.argv[1]); OUT=os.path.dirname(WINE)
cfg=records.load_wine(WINE); prof=profiles.for_wine(cfg); M=prof['map']; OV=cfg.get('overrides',{})
assert M['engine']=='avas',f"this wine's profile uses the {M['engine']} engine"
TF=Transformer.from_crs(4326,M['projection'],always_xy=True).transform
proj=lambda g:transform(TF,g)
def load(url,name): return json.load(open(fetch(url,name),encoding='utf-8'))
AV={f['properties']['name']:dict(p=f['properties'],geom=proj(shape(f['geometry']).buffer(0))) for f in load(M['avas_url'],'avas.geojson')['features'] if not f['properties'].get('removed')}
if 'state_fips' not in M:   # a state with no profile of its own: its code from the tree, then any other state the AVA crosses
    _st={v[1]:k for k,v in M['states'].items()}; _node=next(i for i in profiles.chain(cfg['region']['node']) if profiles.tree()[i]['parent']=='united-states')
    _own=_st[profiles.tree()[_node]['name']]; _more=[x.strip() for x in (AV.get(cfg.get('map_ava'),{}).get('p',{}).get('state') or '').split('|')]
    _more=[_st.get(x,x) for x in _more if x]
    if _more and _own not in _more: _own=_more[0]   # an AVA filed under a wider AVA in another state (Kanawha River Valley under Ohio River Valley)
    _all=[_own]+[x for x in dict.fromkeys(_more) if x in M['states'] and x!=_own]
    M=dict(M,state_fips=[M['states'][x][0] for x in _all] if len(_all)>1 else M['states'][_own][0],state_name=M['states'][_own][1],state_names={M['states'][x][0]:M['states'][x][1] for x in _all})
FIPS=M['state_fips'] if isinstance(M['state_fips'],list) else [M['state_fips']]
CO={f['properties']['NAME']+('' if len(FIPS)==1 else f" ({M['state_names'][f['properties']['STATE']]})"):proj(shape(f['geometry']).buffer(0)) for f in load(M['counties_url'],'us-counties.json')['features'] if f['properties']['STATE'] in FIPS}
MAIN=[n for n in CO if len(FIPS)==1 or n.endswith(f"({M['state_names'][FIPS[0]]})")]   # the first state is the wine's own
STATE=unary_union([CO[n] for n in MAIN]).buffer(300).buffer(-300)
CTY=cfg.get('map_county')   # a wine from a whole county with no AVA of its own, such as Sonoma County
APP=CTY+' County' if CTY else cfg['map_ava']
def kids(n):   # the AVAs directly inside n: inside it and not inside another AVA that is inside it
    inside=[k for k in (AV[n]['p']['contains'] or '').split('|') if k in AV]
    return [k for k in inside if not any(o!=k and o in inside and o in (AV[k]['p']['within'] or '').split('|') for o in inside)]
def parents(n):
    if n==APP and CTY: return sorted([k for k,v in AV.items() if v['geom'].buffer(200).contains(CO[CTY].buffer(-2000))],key=lambda k:AV[k]['geom'].area)
    return sorted([k for k in (AV[n]['p']['within'] or '').split('|') if k in AV],key=lambda k:AV[k]['geom'].area)
AUTO=bool(M.get('auto_chain') or cfg.get('map_whole') or CTY)
if AUTO:   # the wine's AVA, the smallest AVA it sits in, the next one up, else the state
    up=parents(APP); OUTER=cfg.get('map_outer',up[1] if len(up)>1 else 'state' if up else 'west'); REG=cfg.get('map_region',up[0] if up else 'state')
else: OUTER,REG=cfg.get('map_outer',M['outer']),cfg.get('map_region',M['region'])
WHOLE=bool(CTY) or (AUTO and bool(kids(APP)))   # a wine from a whole AVA with smaller AVAs inside it, such as Napa Valley
INNER=[n for n in cfg.get('map_inner_avas',M.get('panel2_avas',[])) if n in AV] if CTY else kids(APP) if WHOLE else []
SNAME=M.get('state_name','the state')
MP={} if (cfg.get('map_whole') or CTY) else M   # a step-up map ignores the profile's hand-placed layout, which is for its usual level
WEST={}
if OUTER=='west':   # an AVA with no AVA around it: panel 1 shows the western states, with this one in gold
    allc=load(M['counties_url'],'us-counties.json')['features']
    WS=M.get('west_states')
    if not WS:   # outside the West Coast profiles: the wine's state and the states that border it
        _sg=lambda fp:unary_union([proj(shape(f['geometry']).buffer(0)) for f in allc if f['properties']['STATE']==fp]).buffer(300).buffer(-300)
        _own=_sg(FIPS[0]).buffer(2000); WS={FIPS[0]:SNAME}
        for fp,nm in M['states'].values():
            if fp!=FIPS[0] and any(f['properties']['STATE']==fp for f in allc) and _sg(fp).intersects(_own): WS[fp]=nm
    for fp,nm in WS.items(): WEST[nm]=unary_union([proj(shape(f['geometry']).buffer(0)) for f in allc if f['properties']['STATE']==fp]).buffer(300).buffer(-300)
TG=CO[CTY] if CTY else AV[APP]['geom']; OG=STATE if OUTER=='state' else unary_union(list(WEST.values())) if OUTER=='west' else AV[OUTER]['geom']; ONAME=SNAME if OUTER=='state' else M.get('west_name','The West Coast' if M.get('west_states') else f'{SNAME} and its neighbors') if OUTER=='west' else OUTER
RC=cfg.get('map_region_counties',None if AUTO else M.get('region_county'))
if RC:   # a county (or counties) with no AVA of its own (Sonoma): its outline, and a chosen set of AVAs that do not overlap
    RG=unary_union([CO[n] for n in ([RC] if isinstance(RC,str) else RC)]); SUBS=[n for n in cfg.get('map_panel2_avas',M.get('panel2_avas',[])) if n in AV]
elif REG=='state':
    RG=STATE; REG=SNAME; SUBS=[n for n,v in AV.items() if v['geom'].intersection(STATE).area>.5*v['geom'].area and not any(k in AV and AV[k]['geom'].intersection(STATE).area>.5*AV[k]['geom'].area for k in (v['p']['within'] or '').split('|'))]
    SUBS=sorted(SUBS,key=lambda n:-AV[n]['geom'].area)[:12]+([APP] if APP not in sorted(SUBS,key=lambda n:-AV[n]['geom'].area)[:12] else [])   # the state's big regions, and this wine's
else:
    RG=AV[REG]['geom']; SUBS=kids(REG) if AUTO else [n for n in (AV[REG]['p']['contains'] or '').split('|') if n in AV]
if CTY and APP not in SUBS: SUBS=SUBS+[APP]   # the county itself, drawn in coral in panel 2
SUBS=[n for n in SUBS if n in AV or n==APP]
G=lambda n:TG if n==APP else AV[n]['geom']
W,(AW,AH),BX,(BW,BH),CY,CH_=ML['width'],ML['region'],ML['subregion_x'],ML['subregion'],ML['village_y'],ML['village_h']
placed=[]
def wbox(x,y,t,style,a):
    w=len(t)*MT[style]['size']*(.68 if t.isupper() else .58)+6; h=MT[style]['size']+4
    x0={'start':x,'middle':x-w/2,'end':x-w}[a]; return box(x0-2,y-h+3,x0+w+2,y+4)
def free(bx,wmax,hmax=None):
    if bx.bounds[2]>wmax-4 or bx.bounds[0]<2 or (hmax and (bx.bounds[1]<2 or bx.bounds[3]>hmax-2)) or any(bx.intersects(o) for o in placed): return False
    placed.append(bx); return True
# ------ panel 1: the outer AVA over its counties
FA=fit(OG.bounds,AW,AH,34,2,6)
a_=[f'<rect width="{AW}" height="{AH}" fill="{PAPER}"></rect>']
P1=WEST or CO   # the shapes panel 1 is drawn on: states in west mode, else counties
for n,g in P1.items():
    if g.intersects(FA.box()): a_.append(P(FA.path(g,.4),LAND,MINOR,MS['commune_edge']))
a_.append(P(FA.path(OG,.4),CFILL,EDGE,MS['village_border'])); a_.append(P(FA.path(STATE if WEST else RG,.4),GOLD,WHITE,MS['commune_edge']))
placed=[box(0,0,250,40)]
from shapely.geometry import LineString
def link_edges(F,G,x1=None):   # the coral box a panel draws for the next one, and its badge: labels placed by default keep off them
    (a,b_),(c_,d)=F.xy(G.x0,G.y1),F.xy(x1 if x1 is not None else G.x1,G.y0)
    return [LineString([(a,b_),(c_,b_),(c_,d),(a,d),(a,b_)]).buffer(1.5),Point(c_,b_).buffer(MM['badge_r']+3)]
_FC=fit(TG.buffer(M.get('panel3_margin_m',1500)).bounds,W,CH_,34,8,6,right=250); _FB=fit(RG.bounds,BW,BH,30,6,10)
OB1=link_edges(FA,_FB); OB2=link_edges(_FB,_FC,_FC.x0+(W-250)/_FC.k)
def pk(obst,cands,lab,st,w,h):   # pick, with the link box as an obstacle that stays out of the placed list
    L=placed+obst; r=pick(L,cands,lab,st,w,h); placed.append(L[-1]); return r
q=TG.centroid; px,py=FA.xy(q.x,q.y); RL=SNAME if WEST else REG
_q=(STATE if WEST else RG).representative_point(); _x,_y=FA.xy(_q.x,_q.y)
_rl=OV.get('panel1_region_label',MP.get('panel1_region_label'))
_tw=OV.get('this_wine',MP.get('this_wine'))
if AUTO:   # reserve the region's own label, and the wine's, before county names take the space: the first clear spot
    _lx,_ly,_an=_rl or pk(OB1,[(_x+40,_y+30,'start'),(_x-40,_y+30,'end'),(_x+40,_y-30,'start'),(_x-40,_y-30,'end'),(_x+50,_y,'start'),(_x-50,_y,'end')]+ring(_x,_y),RL,'subregion_label',AW,AH)
    if _rl: placed.append(wbox(_lx+(3 if _an=='start' else -3),_ly+3.5,RL,'subregion_label',_an))
    if not _tw:
        _d=[px-40,py-20,'end'] if px>100 else [px+30,py-22,'start']
        _tw=list(pk(OB1,[tuple(_d),(px+30,py-22,'start'),(px-40,py-20,'end'),(px+30,py+26,'start'),(px-40,py+26,'end'),(px+50,py+4,'start'),(px-50,py+4,'end')]+ring(px,py),'This wine','this_wine',AW,AH))
for n,g in P1.items():
    if WEST and n==SNAME: continue
    i=g.intersection(FA.box())
    if i.is_empty or i.area*FA.k*FA.k<1500: continue
    q=i.representative_point(); x,y=FA.xy(q.x,q.y); lab=n.upper()
    if free(wbox(x,y,lab,'neighbor','middle'),AW,AH): a_.append(H(x,y,lab,fill=NLAB,a='middle',bg=LAND,sw=MS['halo_wide'],extra=f'letter-spacing="{num(MT["neighbor"]["tracking"])}"',**ty('neighbor')))
lx,ly,an=(_lx,_ly,_an) if AUTO else (_rl or [_x+40,_y+30,'start'])
if not AUTO and not _tw:   # a hand-set layout that sets no spot for this wine: the usual spot, unless a county name or the region's label sits on it
    _rb=wbox(lx+(3 if an=='start' else -3),ly+3.5,RL,'subregion_label',an); _d=[px-40,py-20,'end'] if px>100 else [px+30,py-22,'start']
    if any(wbox(_d[0]+(3 if _d[2]=='start' else -3),_d[1]+3.5,'This wine','this_wine',_d[2]).buffer(-3).intersects(o) for o in placed[1:]+[_rb]):
        _tw=list(pk(OB1+[_rb],[(px+30,py-22,'start'),(px-40,py-20,'end'),(px+30,py+26,'start'),(px-40,py+26,'end'),(px+50,py+4,'start'),(px-50,py+4,'end')]+ring(px,py),'This wine','this_wine',AW,AH))
a_.append(lead(_x,_y,lx,ly,RL,an,'subregion_label',bg=PAPER))
a_.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{num(MM["target_dot_r"])}" fill="{CORAL}" stroke="{WHITE}" stroke-width="{num(MS["target_dot_ring"])}"></circle>')
tw=_tw or ([px-40,py-20,'end'] if px>100 else [px+30,py-22,'start']); a_.append(lead(px,py,tw[0],tw[1],'This wine',tw[2] if len(tw)>2 else 'start','this_wine',TCORAL,CORAL,bg=PAPER))
a_.append(title(6,6,1,*cfg.get('map_panel1',MP.get('panel1',[ONAME,f'With {REG} inside it'])),PAPER))
if OUTER not in ('state','west'):
    FF=fit(STATE.bounds,*ML['locator'],pad=2); a_.append(f'<g transform="translate(6,{AH-62})">'+P(FF.path(STATE,.3),LOC,WHITE,MS['commune_edge'])+P(FF.path(OG,.3),CORAL)+'</g>')
# ------ panel 2: the region AVA and every AVA inside it
FB=fit(RG.bounds,BW,BH,30,6,10)
b=[f'<rect width="{BW}" height="{BH}" fill="{PAPER}"></rect>']
for n,g in CO.items():
    if g.intersects(FB.box()): b.append(P(FB.path(g,.3),LAND,MINOR,MS['commune_edge']))
b.append(P(FB.path(RG,.3),GOLDL,EDGE,MS['village_border']))
for n in SUBS: b.append(P(FB.path(G(n),.3),CORAL if n==APP else GOLD,WHITE,MS['commune_edge']))
b.append(P(FB.path(TG,.3),'none',INK,MS['target']))
placed=[box(0,0,330,40),box(BW-110,BH-30,BW,BH)]   # the title, and the scale bar with the north arrow
for n in sorted(SUBS,key=lambda n:(n!=APP,-G(n).area)):
    q=G(n).representative_point(); x,y=FB.xy(q.x,q.y); hot=n==APP; lab=M.get('short_names',{}).get(n,n)
    side='end' if x<BW/2 else 'start'; _set={**MP.get('panel2_labels',{}),**OV.get('panel2',{})}; lx,ly,an=_set.get(n,(x-28 if side=='end' else x+28,y,side))
    if hot and n not in _set:   # the wine's own label: the first clear spot, starting where it always went
        _o='start' if side=='end' else 'end'; _dx=lambda a_:x+28 if a_=='start' else x-28
        lx,ly,an=pk(OB2,[(lx,ly,an),(_dx(_o),y,_o),(_dx(side),y+22,side),(_dx(_o),y+22,_o),(_dx(side),y-22,side),(_dx(_o),y-22,_o)]+ring(x,y,(30,50,80,110)),lab,'village_target',BW,BH); hot_placed=True
    else:
        hot_placed=False
        if hot and n not in OV.get('panel2',{}):   # the profile's spot was laid out for the name as a neighbour: set larger as the wine's own, it moves in if it would run off the panel
            lx=fit_x(lx,lab,'village_target',an,BW)
    if hot_placed: b.append(lead(x,y,lx,ly,lab,an,'village_target',TCORAL,CORAL,bg=PAPER))
    elif hot or (not any(wbox(lx+(3 if an=='start' else -3),ly+3.5,lab,'village',an).intersects(o) for o in OB2) and free(wbox(lx+(3 if an=='start' else -3),ly+3.5,lab,'village_target' if hot else 'village',an),BW)):
        if hot: placed.append(wbox(lx+(3 if an=='start' else -3),ly+3.5,lab,'village_target',an))
        b.append(lead(x,y,lx,ly,lab,an,'village_target' if hot else 'village',TCORAL if hot else INK,CORAL if hot else INK,bg=PAPER))
m,lab=nice_scale(FB,70); b.append(title(6,6,2,*cfg.get('map_panel2',MP.get('panel2',[REG,'The AVAs inside it'])),PAPER)); b.append(scale(BW-104,BH-10,m,lab,FB)); b.append(north(BW-16,BH-22))
# ------ panel 3: the wine's AVA and its neighbours
FC=fit(TG.buffer(M.get('panel3_margin_m',1500)).bounds,W,CH_,34,8,6,right=250)
vis=FC.box()
c=[f'<rect width="{W}" height="{CH_}" fill="{PAPER}"></rect>']
for n,g in CO.items():
    if g.intersects(vis): c.append(P(FC.path(g,.25),LAND))
c.append(P(FC.path(RG,.25),GOLDL))
nb=[n for n in SUBS if n!=APP and AV[n]['geom'].intersects(vis)]
for n in nb: c.append(P(FC.path(AV[n]['geom'],.2),GOLD,WHITE,MS['vineyard_edge']))
c.append(P(FC.path(TG,.15),CORAL,INK,MS['target']))
for n in INNER: c.append(P(FC.path(AV[n]['geom'],.15),GOLD,WHITE,MS['vineyard_edge']))   # the smaller AVAs inside a whole-region wine's AVA
for n,g in CO.items():
    if g.intersects(vis): c.append(P(FC.path(g.boundary,.25),'none',EDGE,MS['neighbor_border'],f'stroke-dasharray="{MS["neighbor_dash"]}"'))
placed=[box(0,0,330,40),box(W-250,0,W,CH_)]
_sw=nice_scale(FC,90)[0]*FC.k; placed+=[box(16,CH_-24,16+_sw,CH_-8),box(16+_sw+19,CH_-15,16+_sw+29,CH_-6)]   # names keep off the scale's text and the north arrow's N, drawn last
q=(TG.difference(unary_union([AV[n]['geom'] for n in INNER])) if INNER else TG).representative_point(); x,y=FC.xy(q.x,q.y); x,y=OV.get('panel3',{}).get(APP,(x,y))[:2]
_hw=wbox(0,0,APP.upper(),'parent','middle').bounds[2]; x=min(max(x,_hw+4),W-250-_hw-6)   # a long name stays inside the map, left of the key
c.append(H(x,y,APP.upper(),fill=INK,a='middle',bg=WHITE,sw=MS['halo_wide'],**ty('parent'))); placed.append(wbox(x,y,APP.upper(),'parent','middle'))
for n in INNER+sorted(nb,key=lambda n:-AV[n]['geom'].intersection(vis).area):
    g=AV[n]['geom'].intersection(vis).intersection(box(FC.x0,FC.y0,FC.x0+(W-250)/FC.k,FC.y1))
    if g.is_empty: continue
    q=g.representative_point(); x,y=FC.xy(q.x,q.y); x,y=OV.get('panel3',{}).get(n,(x,y))[:2]; lab=M.get('short_names',{}).get(n,n).upper()
    if free(wbox(x,y,lab,'neighbor','middle'),W-250,CH_): c.append(H(x,y,lab,fill=NLAB,a='middle',bg=GOLD,sw=MS['halo_wide'],extra=f'letter-spacing="{num(MT["neighbor"]["tracking"])}"',**ty('neighbor')))
for n,g in CO.items():
    i=g.intersection(vis).difference(RG)
    if not TG.within(RG.buffer(50)): i=i.difference(TG)   # a target that pokes outside its region keeps its own colour clear of county names
    if i.is_empty or i.area*FC.k*FC.k<4000: continue
    q=i.representative_point(); x,y=FC.xy(q.x,q.y); lab=(n+' County').upper()
    if free(wbox(x,y,lab,'neighbor','middle'),W-250,CH_): c.append(H(x,y,lab,fill=NLAB,a='middle',bg=LAND,sw=MS['halo_wide'],extra=f'letter-spacing="{num(MT["neighbor"]["tracking"])}"',**ty('neighbor')))
est=cfg.get('map_estate')
if est:
    p=Point(*TF(*est['lonlat'])); ex,ey=FC.xy(p.x,p.y)
    c.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{num(MM["target_dot_r"])}" fill="{CORAL}" stroke="{WHITE}" stroke-width="{num(MS["target_dot_ring"])}"></circle>'+H(ex+8,ey-7,est['name'],fill=TCORAL,a='start',bg=WHITE,sw=MS['halo_wide'],**ty('this_wine')))
c.append(f'<rect x="{W-250}" y="0" width="250" height="{CH_}" fill="{PAPER}"></rect>')
c.append(title(6,6,3,cfg.get('map_title',APP),cfg.get('map_subtitle','Its boundary and the AVAs inside it' if WHOLE else f'Its boundary and the AVAs around it'),LAND))
IX=W-232; y=34
if cfg.get('map_key_title'): c.append(T(IX,y,cfg['map_key_title'],fill=TCORAL,a='start',**ty('inset_title'))); y+=20
for line in cfg.get('map_estate_note',[]): c.append(T(IX,y,line,fill=INK,a='start',**ty('key'))); y+=15
y+=14
leg=[('sw',CORAL,APP),('sw',GOLD,f'Other AVAs in {REG}'),('sw',GOLDL,f'{REG}, outside those'),('sw',LAND,f'Outside {REG}'),('line',EDGE,'County line')]
if WHOLE: leg=[('sw',CORAL,APP),('sw',GOLD,'Smaller AVAs, in it and around it'),('sw',GOLDL,f'{REG}, outside those'),('sw',LAND,f'Outside {REG}'),('line',EDGE,'County line')]
if est:
    c.append(f'<circle cx="{IX+5}" cy="{y-4}" r="{num(MM["target_dot_r"])}" fill="{CORAL}" stroke="{WHITE}" stroke-width="{num(MS["target_dot_ring"])}"></circle>'+T(IX+15,y,cfg.get('map_estate_label','The winery'),**ty('legend'))); y+=MM['legend_row']
for i,(kd,cl,n) in enumerate(leg):
    if wbox(0,0,n,'legend','start').bounds[2]>W-IX-15-8 and ' ' in n:   # a name too long for the key goes on two lines
        ws=n.split(' '); k=max(range(1,len(ws)),key=lambda j:-abs(len(' '.join(ws[:j]))-len(' '.join(ws[j:]))))
        c.append(swatch(IX,y+i*MM['legend_row'],kd,cl,' '.join(ws[:k]))+T(IX+15,y+i*MM['legend_row']+MT['legend']['size']+2,' '.join(ws[k:]),**ty('legend'))); y+=MT['legend']['size']+2
    else: c.append(swatch(IX,y+i*MM['legend_row'],kd,cl,n))
m,lab=nice_scale(FC,90); c.append(scale(16,CH_-12,m,lab,FC)); c.append(north(16+m*FC.k+24,CH_-20))
BR=MM['badge_r']+2   # the badge sits on the box's top-right corner, so that corner stays a badge's width inside the panel
clamp=lambda r,w,h:((max(r[0][0],1),max(r[0][1],BR)),(min(r[1][0],w-BR),min(r[1][1],h-1)))
ra=clamp((FA.xy(FB.x0,FB.y1),FA.xy(FB.x1,FB.y0)),AW,AH); rb=clamp((FB.xy(FC.x0,FC.y1),FB.xy(FC.x0+(W-250)/FC.k,FC.y0)),BW,BH)
MAP=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{CY+CH_}" viewBox="0 0 {W} {CY+CH_}" role="img" aria-label="Three linked maps: {esc(ONAME if OUTER=='state' else 'the '+OUTER+' AVA')} over its counties, the {esc(REG)} AVA with the AVAs inside it, and the {esc(APP)} AVA with its neighbors."><g>{"".join(a_)}</g>{link_rect(ra)}{badge(ra[1][0],ra[0][1],2)}<g transform="translate({BX},0)"><g>{"".join(b)}</g>{link_rect(rb)}{badge(rb[1][0],rb[0][1],3)}</g><g transform="translate(0,{CY})">{"".join(c)}</g></svg>'
acres=lambda g:round(g.area/4046.86)
PA=AV.get(APP,{}).get('p',{})
STATS=dict(ava=APP,ava_acres=acres(TG),established=PA.get('created'),cfr=PA.get('cfr_index'),within=PA.get('within'),
           neighbors={n:round(TG.distance(AV[n]['geom'])) for n in SUBS if n!=APP and TG.distance(AV[n]['geom'])<500},region_avas=len(SUBS))
open(os.path.join(OUT,'map.stats.json'),'w',encoding='utf-8').write(json.dumps(STATS,ensure_ascii=False,indent=1))
preview(MAP,OUT,W,CY+CH_)
print(json.dumps(STATS,ensure_ascii=False)); print('Wrote map.draft.svg, map.draft.png and map.stats.json in',OUT)

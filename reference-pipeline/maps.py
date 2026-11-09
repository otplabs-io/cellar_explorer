import sys,os; HERE=globals().get('HERE') or os.path.dirname(os.path.abspath(sys.argv[0])); sys.path.insert(0,HERE)
from geo import *
from shapely.geometry import LineString, box
from shapely.affinity import translate
INK='#1F2D3A'; CORAL='#D9482B'; LAND='#F4EFE3'; TEAL='#1F6F73'
CSUB={'Chablis':'#8DBBD0','Côte de Nuits':'#C58BA5','Côte de Beaune':'#E9B44C','Côte Chalonnaise':'#A5C286','Mâconnais':'#EEA679','Châtillonnais':'#BDB7A6'}
C=loadcommunes(); inv={}
for code,c in C.items(): inv.setdefault(c['nom'],code)
HF="font-family=\"Poppins, sans-serif\""
BF="font-family=\"'Nunito Sans', sans-serif\""
def T_(x,y,s,size=11,w=400,fill=INK,anchor='start',ff=BF,extra=''):
    s=s.replace('&','&amp;')
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{anchor}" {ff} {extra}>{s}</text>'
def halo(x,y,s,size=11,w=600,fill=INK,anchor='middle',ff=BF,stroke='#fff',sw=2.6,extra=''):
    return T_(x,y,s,size,w,stroke,anchor,ff,f'stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" {extra}')+T_(x,y,s,size,w,fill,anchor,ff,extra)
def P(d,fill='none',stroke='none',sw=0,extra=''):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}></path>'
def ll(lon,lat): return T(lon,lat)

# ---------- subregion assignment
regcodes=json.load(open(G+'regcodes_in_build_order.json'))
for n in ('Chablis','Beine','Chichée','Courgis','Fleys','Fontenay-près-Chablis','Fyé','La Chapelle-Vaupelteigne','Lignorelles','Ligny-le-Châtel','Maligny','Milly','Poilly-sur-Serein','Préhy','Saint-Cyr-les-Colons','Viviers','Villy','Poinchy','Chemilly-sur-Serein','Collan','Béru','Fontenay-près-Chablis','Varennes','Rameau','Rameau'):
    if n in inv and inv[n] not in regcodes and C[inv[n]]['dep']=='89': regcodes.append(inv[n])
NUITS_EXTRA={'Corgoloin','Comblanchien'}
BEAUNE71={'Cheilly-lès-Maranges','Dezize-lès-Maranges','Sampigny-lès-Maranges','Remigny','Paris-l\'Hôpital','Chagny'}
def sub(code):
    c=C[code]; x,y=c['geom'].centroid.x,c['geom'].centroid.y
    from pyproj import Transformer
    lon,lat=Transformer.from_crs(2154,4326,always_xy=True).transform(x,y)
    if c['dep']=='89': return 'Chablis'
    if c['dep']=='21':
        if lat>47.55: return 'Châtillonnais'
        if lat>47.098 or c['nom'] in NUITS_EXTRA: return 'Côte de Nuits'
        return 'Côte de Beaune'
    if c['nom'] in BEAUNE71: return 'Côte de Beaune'
    return 'Côte Chalonnaise' if lat>46.60 else 'Mâconnais'

deps={}
for f in json.load(open(G+'dep.geojson'))['features']:
    deps[f['properties']['code']]=proj(shape(f['geometry']).buffer(0))
france=unary_union([g.buffer(2000) for g in deps.values()]).buffer(-2000)
tri=unary_union([deps['21'],deps['71'],deps['89']])
CH=C[inv['Chassagne-Montrachet']]['geom']

# ---------- refined Panel C communes (cadastre-accurate where AOC parcels exist)
ids=['Chassagne-Montrachet','Puligny-Montrachet','Saint-Aubin','Santenay','Remigny']
A={n:loadgeo(G+f'cr/{inv[n]}.geojson') for n in ids}
ref={}
for n in ids:
    others=unary_union([A[m] for m in ids if m!=n])
    ref[n]=C[inv[n]]['geom'].union(A[n]).difference(others)
# remove AOC overflow from non-AOC neighbours too
near=[k for k,c in C.items() if c['geom'].intersects(box(*CH.buffer(3500).bounds))]
allA=unary_union(list(A.values()))
for k in near:
    n=C[k]['nom']
    if n not in ref: ref[n]=C[k]['geom'].difference(allA)
ref={k:v.buffer(0.5).buffer(-0.5) for k,v in ref.items()}
RCH=ref['Chassagne-Montrachet']

D=lambda f: loadgeo(G+f'odw/21150/{f}.geojson')
L={l.split('\t')[1].strip().replace('Chassagne-Montrachet premier cru ',''):l.split('\t')[0][:-8] for l in open(G+'odw/list.txt')}
BOU=D(L['La Boudriotte']); MOR=D(L['Morgeot']); PC=D(L['Chassagne-Montrachet premier cru']); VIL=D(L['Chassagne-Montrachet'])
BAT=D(L['Bâtard-Montrachet']); MON=D(L['Montrachet']); CRI=D(L['Criots-Bâtard-Montrachet'])
print('stats: Boudriotte->Santenay',round(BOU.distance(ref['Santenay'])),'Saint-Aubin',round(BOU.distance(ref['Saint-Aubin'])),'Puligny',round(BOU.distance(ref['Puligny-Montrachet'])),'Remigny',round(BOU.distance(ref['Remigny'])))
print('frac',BOU.area/PC.area,BOU.area/1e4,MOR.area/1e4, PC.area/1e4, VIL.area/1e4)
vx,vy=ll(4.7292,46.9378); print('Village to Boudriotte centroid m',round(Point(vx,vy).distance(BOU.centroid)), 'to nearest edge', round(Point(vx,vy).distance(BOU)))
parts={n:D(L[n]) for n in ('Les Fairendes','Les Petites Fairendes','Les Chaumes','Champs Jendreau','La Roquemaure')}
parts['La Boudriotte']=BOU.difference(unary_union(list(parts.values()))).buffer(-0.3).buffer(0.3)
print({k:round(v.area/1e4,2) for k,v in parts.items()})
T_cdb=json.load(open(G+'terroir/terroir-cote-de-beaune.geojson'))
apps={};gc={}
for f in T_cdb['features']:
    p=f['properties']; g=proj(shape(f['geometry']).buffer(0))
    if p['kind']=='appellation': apps[p['name']]=g
    if p['kind']=='grand_cru': gc[p['name']]=g

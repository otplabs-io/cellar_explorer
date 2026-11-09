import json,glob,os,warnings
warnings.filterwarnings('ignore')
from shapely.geometry import shape, Point, box, mapping
from shapely.ops import transform, unary_union
from shapely import set_precision
from pyproj import Transformer
G=os.path.join(os.path.dirname(os.path.abspath(__file__)),'data','')
T=Transformer.from_crs(4326,2154,always_xy=True).transform
def proj(g): return transform(T,g)
def loadcommunes():
    out={}
    for dep in ('21','71','89'):
        for f in json.load(open(G+f'c{dep}.geojson'))['features']:
            out[f['properties']['code']]=dict(nom=f['properties']['nom'],dep=dep,geom=proj(shape(f['geometry']).buffer(0)))
    return out
def loadgeo(fn):
    d=json.load(open(fn))
    return unary_union([proj(shape(f['geometry']).buffer(0)) for f in d['features']])
class Frame:
    def __init__(s,bb,W,H=None,pad=0):
        s.x0,s.y0,s.x1,s.y1=bb
        s.k=W/(s.x1-s.x0); s.W=W; s.H=H or (s.y1-s.y0)*s.k
    def xy(s,x,y): return (x-s.x0)*s.k,(s.y1-y)*s.k
    def clipbox(s): return box(s.x0,s.y0,s.x1,s.y1)
    def path(s,g,tol=0.4,clip=True):
        if g.is_empty: return ''
        if clip: g=g.intersection(s.clipbox())
        g=g.simplify(tol/s.k,preserve_topology=True)
        polys=[]
        def walk(g):
            if g.geom_type in('Polygon',): polys.append(g)
            elif g.geom_type in('MultiPolygon','GeometryCollection'):
                for x in g.geoms: walk(x)
        walk(g)
        o=[]
        for p in polys:
            if p.area*s.k*s.k<0.3: continue
            for r in [p.exterior]+list(p.interiors):
                pts=[s.xy(*c) for c in r.coords]
                o.append('M'+' '.join(f'{a:.1f},{b:.1f}' for a,b in pts)+'Z')
        return ''.join(o)
    def line(s,g,tol=0.4):
        g=g.intersection(s.clipbox()).simplify(tol/s.k)
        o=[]
        def w(g):
            if g.geom_type=='LineString':
                o.append('M'+' '.join(f'{a:.1f},{b:.1f}' for a,b in (s.xy(*c) for c in g.coords)))
            elif hasattr(g,'geoms'):
                for x in g.geoms: w(x)
        w(g); return ''.join(o)

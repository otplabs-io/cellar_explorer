"""Shared drawing pieces for the map engines: frames, text with halos, leaders, scale bars, badges and titles.
Every value comes from the map tokens in design-system/tokens.json. src/mapgen.py (the Burgundy parcel engine) keeps its
own copies of these, because its La Boudriotte draft is proven byte-identical; new engines import them from here."""
import json,os,subprocess
from shapely.geometry import box
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOK=json.load(open(os.path.join(ROOT,'design-system','tokens.json'),encoding='utf-8'))
MC,MT,MS,MM,ML=TOK['map'],TOK['map_type'],TOK['map_stroke'],TOK['map_mark'],TOK['map_layout']
INK,CORAL,TCORAL,LAND,TEAL,PLUM,GOLD,GOLDL,EDGE,PAPER=(MC[k] for k in ('ink','target','target_text','land','parent_outline','grand_cru','premier_cru','village','border','paper'))
WHITE,SOFT,MINOR,CFILL,TFILL,NEIGH,TPAPER,NLAB,LOC=(MC[k] for k in ('white','soft_text','minor_border','commune_fill','target_commune_fill','neighbor_vineyard','target_commune_paper','neighbor_label','locator_land'))
HF=f'font-family="{TOK["font"]["display"]["family"]}, sans-serif"'; BF=f"font-family=\"'{TOK['font']['body']['family']}', sans-serif\""
CA=os.path.join(ROOT,'data','cache','')
def fetch(url,name):
    os.makedirs(CA,exist_ok=True); p=CA+name
    if os.path.exists(p+'.missing'): return None   # a 404 we already met: INAO has no file for most communes
    if not os.path.exists(p):
        r=subprocess.run(['curl','-s','-f','-m','300','-o',p,'-w','%{http_code}',url],capture_output=True,text=True)
        if r.stdout.strip()=='404': open(p+'.missing','w').close()
    return p if os.path.exists(p) else None
def num(v):
    """A number as the map writes it: 0.5 as .5, 2.0 as 2."""
    if isinstance(v,str): return v
    s=f'{v:g}'; return s.replace('0.','.',1) if s.startswith(('0.','-0.')) else s
def esc(s): return s.replace('&','&amp;')
def ty(name):
    t=MT[name]; return dict(size=t['size'],w=t['weight'],ff=HF if t.get('family')=='display' else BF)
def T(x,y,s,size=11,w=400,fill=INK,a='start',ff=BF,extra=''):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{a}" {ff} {extra}>{esc(s)}</text>'
def H(x,y,s,size=11,w=600,fill=INK,a='middle',ff=BF,bg=WHITE,sw=MS['halo'],extra=''):
    """Halo text: a copy stroked in the ground color under the filled copy. Never paint-order."""
    return T(x,y,s,size,w,bg,a,ff,f'stroke="{bg}" stroke-width="{sw}" stroke-linejoin="round" {extra}')+T(x,y,s,size,w,fill,a,ff,extra)
def P(d,fill='none',stroke='none',sw=0,extra=''): return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{num(sw)}" {extra}></path>' if d else ''
class Frame:
    def __init__(s,bb,W,H_):
        s.x0,s.y0,s.x1,s.y1=bb; s.k=W/(s.x1-s.x0); s.W=W; s.H=H_
    def xy(s,x,y): return (x-s.x0)*s.k,(s.y1-y)*s.k
    def box(s): return box(s.x0,s.y0,s.x1,s.y1)
    def path(s,g,tol=.4):
        if g is None or g.is_empty: return ''
        g=g.intersection(s.box()).simplify(tol/s.k,preserve_topology=True); out=[]
        def w(g):
            if g.geom_type=='Polygon':
                if g.area*s.k*s.k<.3: return
                for r in [g.exterior]+list(g.interiors): out.append('M'+' '.join('%.1f,%.1f'%s.xy(*c) for c in r.coords)+'Z')
            elif hasattr(g,'geoms'):
                for x in g.geoms: w(x)
        w(g); return ''.join(out)
def fit(bb,w,h,top=0,bottom=0,pad=8,dx=0,left=0,right=0):
    """A frame w by h that shows bb whole inside the margins, centered in what the margins leave."""
    k=min((w-left-right-2*pad)/(bb[2]-bb[0]),(h-top-bottom-2*pad)/(bb[3]-bb[1])); cx,cy=(bb[0]+bb[2])/2,(bb[1]+bb[3])/2
    x0=cx-(left+(w-left-right)/2)/k+dx/k; y1=cy+(top+(h-top-bottom)/2)/k
    return Frame((x0,y1-h/k,x0+w/k,y1),w,h)
def title(x,y,n,t,s,bg):
    r=MM['panel_number_r']; hw=MS['halo_wide']
    return f'<circle cx="{x+r}" cy="{y+r}" r="{r}" fill="{INK}"></circle>'+T(x+r,y+15.5,str(n),fill=WHITE,a='middle',**ty('panel_number'))+H(x+28,y+11.5,t,fill=INK,a='start',bg=bg,sw=hw,**ty('panel_title'))+H(x+28,y+24.5,s,fill=SOFT,a='start',bg=bg,sw=hw,**ty('panel_subtitle'))
def lead(x0,y0,x1,y1,t,a='start',style='village',fill=INK,col=INK,dy=3.5,bg=LAND):
    return f'<path d="M{x0:.0f},{y0:.0f}L{x1:.0f},{y1:.0f}" stroke="{col}" stroke-width="{num(MS["leader"])}" fill="none"></path><circle cx="{x0:.0f}" cy="{y0:.0f}" r="{num(MM["leader_dot_r"])}" fill="{col}"></circle>'+H(x1+(3 if a=='start' else -3),y1+dy,t,fill=fill,a=a,bg=bg,**ty(style))
def scale(x,y,m,lab,F):
    w=m*F.k; return f'<path d="M{x},{y-4}V{y}H{x+w:.1f}V{y-4}" fill="none" stroke="{INK}" stroke-width="{num(MS["scale_bar"])}"></path>'+T(x+w/2,y-6,lab,fill=INK,a='middle',**ty('scale'))
def nice_scale(F,width_px):
    """The roundest distance whose bar is at most width_px long."""
    for m in (50000,20000,10000,5000,2000,1000,500,200,100):
        if m*F.k<=width_px: return m,(f'{m//1000} km' if m>=1000 else f'{m} m')
    return 100,'100 m'
def north(x,y): return f'<path d="M{x},{y-13}L{x+5},{y}L{x},{y-3}L{x-5},{y}Z" fill="{INK}"></path>'+T(x,y+11,'N',fill=INK,a='middle',**ty('north'))
def badge(x,y,n): return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{MM["badge_r"]}" fill="{CORAL}" stroke="{WHITE}" stroke-width="{num(MS["badge_ring"])}"></circle>'+T(x,y+3.6,str(n),fill=WHITE,a='middle',**ty('badge'))
def number(x,y,n): return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{num(MM["plot_number_r"])}" fill="{WHITE}" stroke="{INK}" stroke-width="{num(MS["plot_number_ring"])}"></circle>'+T(x,y+3.7,str(n),fill=INK,a='middle',**ty('plot_number'))
def town(F,pt,n,bg=LAND,a='start'):
    x,y=F.xy(pt.x,pt.y); tx=x+5 if a=='start' else x-5
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{num(MM["town_r"])}" fill="{WHITE}" stroke="{INK}" stroke-width="{num(MS["town"])}"></circle>'+H(tx,y+3.5,n,fill=INK,a=a,bg=bg,**ty('town'))
def link_rect(r): return f'<rect x="{r[0][0]:.1f}" y="{r[0][1]:.1f}" width="{r[1][0]-r[0][0]:.1f}" height="{r[1][1]-r[0][1]:.1f}" fill="none" stroke="{CORAL}" stroke-width="{num(MS["level_link"])}"></rect>'
def swatch(x,y,kind,col,label):
    sw_,sh_=MM['swatch']; out=''
    if kind=='sw': out=f'<rect x="{x}" y="{y-8}" width="{sw_}" height="{sh_}" fill="{col}" stroke="{EDGE}" stroke-width="{num(MS["legend_swatch"])}"></rect>'
    if kind=='out': out=f'<rect x="{x+.5}" y="{y-7.5}" width="{sw_-1}" height="{sh_-1}" fill="none" stroke="{col}" stroke-width="{num(MS["legend_outline"])}"></rect>'
    if kind=='line': out=f'<path d="M{x},{y-3}h{sw_}" stroke="{col}" stroke-width="{num(MS["legend_line"])}"></path>'
    return out+T(x+15,y,label,**ty('legend'))
def preview(svg,out_dir,w,h):
    """Write map.draft.svg and render map.draft.png with the sheet's fonts."""
    from pathlib import Path
    from playwright.sync_api import sync_playwright
    open(os.path.join(out_dir,'map.draft.svg'),'w',encoding='utf-8').write(svg)
    FD=Path(ROOT,'design-system','fonts').as_uri()+'/'
    CSS=''.join(f"@font-face{{font-family:'Nunito Sans';font-weight:{w_};src:url(\"{FD}nunito-sans-latin-{w_}-normal.woff2\")}}" for w_ in (400,600,700,800))+''.join(f"@font-face{{font-family:Poppins;font-weight:{w_};src:url(\"{FD}poppins-latin-{w_}-normal.woff2\")}}" for w_ in (600,700,800))
    pv=os.path.join(out_dir,'map.draft.html'); open(pv,'w',encoding='utf-8').write(f'<!doctype html><meta charset="utf-8"><style>{CSS}body{{margin:0}}</style>{svg}')
    if os.environ.get('MAP_NO_PNG'): return   # src/mapproof.py: the SVG and its page are enough for the label check
    with sync_playwright() as p:
        br=p.chromium.launch(); pg=br.new_page(viewport={'width':w,'height':h},device_scale_factor=2); pg.goto(Path(pv).as_uri()); pg.wait_for_timeout(500); pg.screenshot(path=os.path.join(out_dir,'map.draft.png')); br.close()
def label_box(x,y,t,style,a):
    """The box a label takes, estimated from its type style: the same estimate the engines' own wbox uses."""
    w=len(t)*MT[style]['size']*(.68 if t.isupper() else .58)+6; h=MT[style]['size']+4
    x0={'start':x,'middle':x-w/2,'end':x-w}[a]; return box(x0-2,y-h+3,x0+w+2,y+4)
def fit_x(lx,t,style,a,w,dx=3):
    """A label's x moved in just enough that its text stays inside a w-wide panel. The text is taken as .54 em a
    character, close to Nunito Sans as drawn (label_box's .58 plus padding runs wider, to keep labels apart)."""
    tw=len(t)*MT[style]['size']*.54; x0={'start':lx+dx,'middle':lx-tw/2,'end':lx-dx-tw}[a]
    return lx+(5-x0 if x0<0 else (w-5)-(x0+tw) if x0+tw>w else 0)   # once it clips, it moves 5px clear: the guess can be a few px short
def pick(placed,cands,lab,style,w,h,dx=3,dy=3.5,keep=True):
    """A leader label's spot: the first of cands, (x, y, anchor), whose text stays inside a w by h panel and clear of
    the boxes in placed. Its box joins placed. With no clear spot it keeps the first that stays inside the panel, so the
    label check reports the overlap, or with keep=False returns None, for a label that can be left out."""
    def fits(b):   # inside the panel, with a tenth of the width spare, since the box is an estimate of the real text
        m=(b[2]-b[0])*.1; return b[0]-m>=2 and b[2]+m<=w-4 and b[1]>=2 and b[3]<=h-2
    for lx,ly,an in cands:
        bx=label_box(lx+(dx if an=='start' else -dx),ly+dy,lab,style,an)
        if fits(bx.bounds) and not any(bx.intersects(o) for o in placed):
            placed.append(bx); return lx,ly,an
    if not keep: return None
    inside=[c for c in cands if fits(label_box(c[0]+(dx if c[2]=='start' else -dx),c[1]+dy,lab,style,c[2]).bounds)]
    lx,ly,an=(inside or cands)[0]; placed.append(label_box(lx+(dx if an=='start' else -dx),ly+dy,lab,style,an)); return lx,ly,an
def buf_bounds(g,d):
    """g.buffer(d).bounds without buffering all of g: only its outermost polygons can set the bounds, and each is buffered
    on its own the way GEOS buffers it inside g. An appellation's land is many thousands of parcels, and buffering all of
    them took most of a draw's time and gigabytes of memory. MAP_CHECK_BOUNDS=1 also buffers all of g and checks they agree."""
    ps=list(getattr(g,'geoms',[g])); x0,y0,x1,y1=g.bounds
    edge=[p for p in ps if p.bounds[0]<=x0+d or p.bounds[1]<=y0+d or p.bounds[2]>=x1-d or p.bounds[3]>=y1-d]
    bs=[p.buffer(d).bounds for p in edge]; out=(min(b[0] for b in bs),min(b[1] for b in bs),max(b[2] for b in bs),max(b[3] for b in bs))
    if os.environ.get('MAP_CHECK_BOUNDS'): assert out==g.buffer(d).bounds,(out,g.buffer(d).bounds)
    return out
def ring(x,y,rs=(30,50,80)):
    """Spots for a leader label around a point, nearest first: right and left, then above and below, then the diagonals."""
    out=[]
    for r in rs:
        for dx,dy in ((1,0),(-1,0),(0,-1),(0,1),(1,-1),(-1,-1),(1,1),(-1,1)):
            out.append((x+dx*r,y+dy*r*.7,'start' if dx>0 else 'end' if dx<0 else 'middle'))
    return out
def key_lines(label,maxw):
    """A key entry as one line, or two when it is wider than maxw: split at the space that best balances them."""
    if label_box(0,0,label,'legend','start').bounds[2]<=maxw or ' ' not in label: return [label]
    ws=label.split(' '); k=min(range(1,len(ws)),key=lambda j:abs(len(' '.join(ws[:j]))-len(' '.join(ws[j:]))))
    return [' '.join(ws[:k]),' '.join(ws[k:])]
def key_entry(x,y,kind,col,label,maxw):
    """swatch(), with a long label wrapped onto a second line below the first. Returns the SVG and the extra height."""
    ls=key_lines(label,maxw); dy=MT['legend']['size']+2
    return swatch(x,y,kind,col,ls[0])+''.join(T(x+15,y+dy*i,l,**ty('legend')) for i,l in enumerate(ls[1:],1)),dy*(len(ls)-1) or 0   # 0, not 0.0, so one-line keys print as before
def key_extra(label,maxw):
    """The extra height key_entry() adds for label: 0 when it stays on one line."""
    return (len(key_lines(label,maxw))-1)*(MT['legend']['size']+2) or 0

#!/usr/bin/env python3
"""Pre-press check for every icon in design-system/icons/. Exit 1 if any icon fails.
Fails: artwork outside the safe area, a detail line that runs past the shape it sits on,
self-closed or forbidden markup. Warns: thin strokes, too many colors.
Each icon is rasterized at 8x in Chromium. A stroke-only element drawn on top of filled shapes, and mostly
inside them, is a detail line, so any part of it outside those shapes (allowing 1 px of antialiasing) is a leak.
Strokes drawn first, such as stems under a fruit, and strokes mostly outside the fills are structure.
Approved icons are reported as HELD, not failing, because changing them changes an approved sheet."""
import json,os,re,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D=os.path.join(ROOT,'design-system','icons')
SAFE=(5,59)       # hard limit in viewBox units. The drawing guide asks for about 6 to 58.
K=8               # raster scale
EL=re.compile(r'<(path|circle|ellipse|rect)\b([^>]*)>\s*</\1>')
def attrs(s): return dict(re.findall(r'([\w-]+)="([^"]*)"',s))
icons={}
for fam in sorted(os.listdir(D)):
    if not os.path.isdir(os.path.join(D,fam)): continue
    for f in sorted(os.listdir(os.path.join(D,fam))):
        if f.endswith('.svg'): icons[f'{fam}/{f[:-4]}']=open(os.path.join(D,fam,f)).read()
only=sys.argv[1:]
if only: icons={k:v for k,v in icons.items() if k.split('/')[1] in only or k in only}
jobs={}; static={}
for k,s in icons.items():
    issues=[]; warns=[]
    if re.search(r'/\s*>',s): issues.append('self-closed element')
    if re.search(r'<(linearGradient|radialGradient|filter|clipPath|mask|text|image)\b',s): issues.append('forbidden element')
    els=[(m.group(0),m.group(1),attrs(m.group(2))) for m in EL.finditer(s)]
    fills=[e for e in els if e[2].get('fill','black')!='none']
    strokes=[(i,e) for i,e in enumerate(els) if e[2].get('fill')=='none' and float(e[2].get('stroke-width','0') or 0)>0]
    cols={e[2].get('fill') for e in fills}|{e[2].get('stroke') for e in els if e[2].get('stroke')}
    cols.discard(None); cols.discard('none')
    if len(cols)>6: warns.append(f'{len(cols)} colors')
    thin=sorted({float(e[2]['stroke-width']) for e in els if e[2].get('stroke') and float(e[2].get('stroke-width',0))<1.2})
    if thin: warns.append(f'strokes under 1.2: {thin}')
    wrap=lambda body:f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{64*K}" height="{64*K}">{body}</svg>'
    under=lambda i:wrap(''.join(e[0] for e in els[:i] if e[2].get('fill','black')!='none'))
    jobs[k]={'full':wrap(re.sub(r'^<svg[^>]*>|</svg>\s*$','',s.strip())),'strokes':[(i,wrap(e[0]),under(i)) for i,e in strokes]}
    static[k]=(issues,warns)
JS="""async (jobs)=>{const K=%d,N=64*K;const c=document.createElement('canvas');c.width=c.height=N;const x=c.getContext('2d',{willReadFrequently:true});
const mask=async s=>{const im=new Image();im.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(s);await im.decode();x.clearRect(0,0,N,N);x.drawImage(im,0,0);const d=x.getImageData(0,0,N,N).data;const m=new Uint8Array(N*N);for(let i=0;i<N*N;i++)m[i]=d[i*4+3]>32?1:0;return m};
const dil=m=>{const o=new Uint8Array(N*N);for(let y=0;y<N;y++)for(let X=0;X<N;X++){if(!m[y*N+X])continue;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const yy=y+dy,xx=X+dx;if(yy>=0&&yy<N&&xx>=0&&xx<N)o[yy*N+xx]=1}}return o};
const out={};for(const [k,j] of Object.entries(jobs)){const A=await mask(j.full);let x0=N,y0=N,x1=-1,y1=-1;for(let y=0;y<N;y++)for(let X=0;X<N;X++)if(A[y*N+X]){if(X<x0)x0=X;if(X>x1)x1=X;if(y<y0)y0=y;if(y>y1)y1=y}
const leaks=[];for(const [i,s,u] of j.strokes){const S=await mask(s);const F=dil(await mask(u));let n=0,inn=0,ox0=N,oy0=N,ox1=-1,oy1=-1;for(let p=0;p<N*N;p++){if(!S[p])continue;n++;if(F[p])inn++;else{const X=p%%N,y=(p/N)|0;if(X<ox0)ox0=X;if(X>ox1)ox1=X;if(y<oy0)oy0=y;if(y>oy1)oy1=y}}
if(n&&inn/n>=0.5&&n-inn>8)leaks.push({element:i,outside_px:n-inn,at:[+(ox0/K).toFixed(1),+(oy0/K).toFixed(1),+(ox1/K).toFixed(1),+(oy1/K).toFixed(1)]})}
out[k]={bbox:x1<0?null:[+(x0/K).toFixed(2),+(y0/K).toFixed(2),+((x1+1)/K).toFixed(2),+((y1+1)/K).toFixed(2)],leaks}}return out}""" % K
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); pg.set_content('<!doctype html><body></body>'); res=pg.evaluate(JS,jobs); b.close()
approved={i['id'] for i in json.load(open(os.path.join(ROOT,'design-system','icons.json')))['icons'] if i.get('status')=='approved'}
report={}; bad=0; held=0
for k in icons:
    issues,warns=static[k]; r=res[k]; bb=r['bbox']
    if bb and (bb[0]<SAFE[0] or bb[1]<SAFE[0] or bb[2]>SAFE[1] or bb[3]>SAFE[1]): issues.append(f'outside the safe area: artwork spans {bb}')
    for l in r['leaks']: issues.append(f'detail line {l["element"]} runs {l["outside_px"]} px past its shape, around {l["at"]}')
    hold=bool(issues) and k.split('/')[1] in approved
    if issues and not hold: bad+=1
    held+=hold
    report[k]={'bbox':bb,'issues':issues,'warnings':warns,'held':hold}
for k,v in report.items():
    if v['issues'] or v['warnings']: print(('HELD ' if v['held'] else 'FAIL ' if v['issues'] else 'warn ')+k, '; '.join(v['issues']+v['warnings']))
print(f'{len(icons)} icons checked, {bad} failing, {held} approved icons held for Chris')
os.makedirs(os.path.join(ROOT,'build'),exist_ok=True); json.dump(report,open(os.path.join(ROOT,'build','icon-check.json'),'w'),indent=1)
sys.exit(1 if bad else 0)

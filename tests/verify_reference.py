#!/usr/bin/env python3
"""Acceptance test: rebuild La Boudriotte and compare it to an approved PDF, pixel by pixel.
macOS: the baseline in reference/mac-baseline/. Linux: reference/linux-baseline/ if it exists, else the
master in reference/. Against a platform baseline, the difference from the master is reported but does not fail. Exit 0 only on zero differing pixels
at 300 dpi on both pages, with text, fonts and page size matching the master."""
import glob,hashlib,json,os,platform,subprocess,sys
import numpy as np, pymupdf
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER=os.path.join(ROOT,'reference','La-Boudriotte-2019-Print.pdf')
PLAT='mac-baseline' if sys.platform=='darwin' else 'linux-baseline'; MACDIR=os.path.join(ROOT,'reference',PLAT)
OUT=os.path.join(ROOT,'build','la-boudriotte-2019'); NEW=os.path.join(OUT,'sheet.pdf'); MAP=os.path.join(ROOT,'wines','la-boudriotte-2019','map.svg')
MAC=os.path.exists(os.path.join(MACDIR,'manifest.json'))  # a platform baseline exists
r=subprocess.run([sys.executable,os.path.join(ROOT,'src','render.py'),os.path.join(ROOT,'wines','la-boudriotte-2019','wine.json')]);
if r.returncode: sys.exit('Render reported issues. See build/la-boudriotte-2019/report.json')
for f in glob.glob(os.path.join(OUT,'diff-*.png')): os.remove(f)
fnt=lambda d:sorted({f[3].split('+')[-1] for p in d for f in p.get_fonts() if f[3]})
def compare(ref,new,tag):
    """Pixel counts per page, plus failures for page count, size, text and fonts."""
    a,b=pymupdf.open(ref),pymupdf.open(new); fail=[]; res=[]
    if len(a)!=len(b): fail.append(f'page count {len(a)} vs {len(b)}')
    if fnt(a)!=fnt(b): fail.append(f'fonts differ: {fnt(a)} vs {fnt(b)}')
    for i,(p,q) in enumerate(zip(a,b),1):
        if p.rect!=q.rect: fail.append(f'page {i} size {p.rect} vs {q.rect}')
        if p.get_text()!=q.get_text(): fail.append(f'page {i} text differs')
        px=p.get_pixmap(dpi=300,alpha=False); x=np.frombuffer(px.samples,dtype=np.uint8); y=np.frombuffer(q.get_pixmap(dpi=300,alpha=False).samples,dtype=np.uint8)
        if x.shape!=y.shape: fail.append(f'page {i} raster size differs'); continue
        d=(x!=y).reshape(px.h,px.w,3).any(axis=2); n=int(d.sum()); res.append(n)
        if n:
            fail.append(f'page {i}: {n} of {d.size} pixels differ, in x {np.where(d.any(0))[0][[0,-1]].tolist()}, y {np.where(d.any(1))[0][[0,-1]].tolist()}')
            pymupdf.Pixmap(pymupdf.csGRAY,px.w,px.h,(~d*255).astype(np.uint8).tobytes(),False).save(os.path.join(OUT,f'diff-{tag}page-{i}.png'))
    return res,fail
def streams(p):
    """Hashes of every PDF stream: drawing commands, fonts and images. MuPDF rasterizes a color
    one step off (say #3F5B45 vs #3F5B46) to the same pixels, and this catches it."""
    d=pymupdf.open(p); out=[]
    for x in range(1,d.xref_length()):
        try: s=d.xref_stream(x)
        except Exception: s=None
        if s: out.append(hashlib.sha256(s).hexdigest())
    return out
out={}; fail=[]
if hashlib.sha256(open(MAP,'rb').read()).hexdigest()!=json.load(open(os.path.join(ROOT,'reference','manifest.json')))['map_svg_sha256']: fail.append('locked map.svg changed')
mres,mfail=compare(MASTER,NEW,'master-' if MAC else '')
if MAC:
    man=json.load(open(os.path.join(MACDIR,'manifest.json')))
    res,bfail=compare(os.path.join(MACDIR,man['pdf']),NEW,'')
    fail+=bfail+[f for f in mfail if 'pixels differ' not in f]
    if streams(os.path.join(MACDIR,man['pdf']))!=streams(NEW): fail.append('PDF drawing commands differ from the platform baseline, even if the pixels match')
    out['checked_against']=f'reference/{PLAT}/'+man['pdf']
    out['differing_pixels_per_page_at_300dpi']=res
    out['vs_master_differing_pixels']=mres; out['vs_master_accepted']=man['differing_pixels_vs_master_at_300dpi']
    env=(platform.mac_ver()[0],platform.machine()); want=man['built_with']
    if sys.platform=='darwin' and (not want['os'].startswith('macOS '+env[0]+' ') or env[1]!=want['arch']): out['note']=f'This Mac is macOS {env[0]} {env[1]}. The baseline was made on {want["os"]} {want["arch"]}, so a font rasterizer change can show up as differing pixels.'
else:
    out['checked_against']='reference/La-Boudriotte-2019-Print.pdf'; out['differing_pixels_per_page_at_300dpi']=mres; fail+=mfail
out['failures']=fail
print(json.dumps(out,indent=1))
sys.exit(1 if fail else 0)

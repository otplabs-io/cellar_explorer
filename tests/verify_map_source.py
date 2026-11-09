#!/usr/bin/env python3
"""Rebuild the locked La Boudriotte map from the vendored raw data and require a byte-identical SVG.
Linux only: this depends on the exact Shapely, GEOS, pyproj and PROJ builds in requirements.txt,
and the Mac wheels round differently. The rebuild goes to reference-pipeline/output/ and never
touches wines/la-boudriotte-2019/map.svg, which stays the locked map the sheet uses."""
import filecmp,os,subprocess,sys
if not sys.platform.startswith('linux'):
    print(f'verify-map skipped: it is a Linux-only check and this is {sys.platform}. The sheet uses the locked wines/la-boudriotte-2019/map.svg, which make verify checks by hash.'); sys.exit(0)
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P=os.path.join(ROOT,'reference-pipeline')
r=subprocess.run([sys.executable,os.path.join(P,'compose.py')],cwd=P,capture_output=True,text=True)
if r.returncode: print(r.stdout[-1500:],r.stderr[-1500:]); sys.exit(1)
same=filecmp.cmp(os.path.join(P,'output','map.svg'),os.path.join(ROOT,'wines','la-boudriotte-2019','map.svg'),shallow=False)
print('map.svg byte-identical to the rebuild:',same); sys.exit(0 if same else 1)

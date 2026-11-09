"""Region profiles: what a sheet shows differently by region, as data. A wine's profile is regions/profiles/default.json,
then every profile on the way down the region tree to the wine's node, each overriding the one above. A profile file
sits at regions/profiles/<stable id>.json and states only what differs from its parent. Lists and strings replace;
objects merge."""
import json,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR=os.path.join(ROOT,'regions','profiles')
_TREE=None
def tree():
    global _TREE
    if _TREE is None: _TREE=json.load(open(os.path.join(ROOT,'regions','tree.json'),encoding='utf-8'))['nodes']
    return _TREE
def merge(a,b):
    out=dict(a)
    for k,v in b.items():
        if k.startswith('$'): continue
        out[k]=merge(out[k],v) if isinstance(v,dict) and isinstance(out.get(k),dict) else v
    return out
def chain(node):
    T=tree(); out=[]
    while node: out.append(node); node=T[node]['parent']
    return list(reversed(out))
def for_node(node):
    p=json.load(open(os.path.join(DIR,'default.json'),encoding='utf-8')); used=['default']
    for i in chain(node) if node else []:
        f=os.path.join(DIR,i+'.json')
        if os.path.exists(f): p=merge(p,json.load(open(f,encoding='utf-8'))); used.append(i)
    p['$used']=used; return p
def for_wine(cfg):
    return for_node((cfg.get('region') or {}).get('node'))

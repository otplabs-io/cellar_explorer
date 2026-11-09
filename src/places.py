"""Place a wine on the region tree from a CellarTracker locale, such as
"France, Burgundy, Côte de Beaune, Chassagne-Montrachet 1er Cru". Returns the deepest stable id it can reach, the tier
the locale names (Premier Cru, Grand Cru) and any locale words the tree doesn't know. Reads regions/tree.json and
regions/aliases.json, so it works without rebuilding the tree."""
import json,os,re,unicodedata
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def norm(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    s=re.sub(r"['’`]",' ',s).replace('.','').replace('-',' ').replace('/',' ')
    s=re.sub(r'\b(aoc|aop|doc|docg|do|dop|igp|igt|pdo|pgi|ava|vqa)\b','',s)
    return re.sub(r'\s+',' ',s).strip()
TIER_WORDS=((' 1er cru','Premier Cru'),(' premier cru','Premier Cru'),(' grand cru','Grand Cru'))
KEEP_GC={'saint emilion grand cru','chablis grand cru','corton grand cru'}   # grand cru is part of these names
class Placer:
    def __init__(s,tree=None,aliases=None):
        s.T=json.load(open(tree or os.path.join(ROOT,'regions','tree.json'),encoding='utf-8'))['nodes']
        s.A=json.load(open(aliases or os.path.join(ROOT,'regions','aliases.json'),encoding='utf-8'))['aliases']
        s.N={}
        for i,v in s.T.items():
            ns={norm(v['name'])}|{norm(a) for a in v.get('also',[])}
            for part in re.split(r' & | \(|\)',v['name']):
                if part.strip(): ns.add(norm(part))
            ns.discard(''); s.N[i]=ns
    def sub(s,i):
        out=[]; q=[i]
        while q: x=q.pop(0); out.append(x); q+=s.T[x]['children']
        return out
    def up(s,i):
        while i: yield i; i=s.T[i]['parent']
    def place(s,locale,wine=''):
        tier=None; cur=None; missed=[]
        for raw in [norm(x) for x in locale.split(',')]:
            x=raw
            for t,label in TIER_WORDS:
                if x.endswith(t) and x not in KEEP_GC: x=x[:-len(t)]; tier=label
            if x=='corton grand cru': tier='Grand Cru'
            x=norm(s.A.get(x,x))
            if not x: continue
            if cur is None:
                found=next((i for i,v in s.T.items() if v['parent'] is None and norm(v['name'])==x),None)
            else:
                found=next((i for i in s.sub(cur)[1:] if x in s.N[i]),None)
                if not found:   # the locale sometimes skips a level the tree has, or names one it doesn't
                    country=list(s.up(cur))[-1]; above=set(s.up(cur))
                    found=next((i for i in s.sub(country) if x in s.N[i] and i not in above),None)
            if found: cur=found
            elif cur and any(x in s.N[a] for a in s.up(cur)): pass
            else: missed.append(raw)
        if cur and s.T[cur]['path'].startswith('france/champagne'):   # Champagne villages are named in the wine, not the locale
            for i in s.sub('france/champagne'):
                if s.T[i]['path'].count('/')==3 and re.search(r'\b'+re.escape(norm(s.T[i]['name']))+r'\b',norm(wine)): cur=i   # whole words: Aÿ is not in Chardonnay
        return cur,tier,missed
    def path(s,i): return list(reversed(list(s.up(i))))

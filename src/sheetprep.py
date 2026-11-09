"""What a sheet needs before its blocks are drawn, shared by the PDF (render.py) and the phone view (mobile.py):
the region profile, the bottle shape, the blend bar, the AVA chain and the map credit."""
import json,os
import blocks as B
import profiles
ROOT=B.ROOT
def prepare(cfg):
    """Fill in cfg['content'] in place and return the wine's region profile."""
    c=cfg['content']
    prof=profiles.for_wine(cfg)
    if prof.get('bottle_shape') and 'bottle_shape' not in cfg and cfg.get('theme')!='sparkling': cfg['bottle_shape']=prof['bottle_shape']   # sparkling keeps its theme's champagne bottle
    gr=(cfg.get('identity') or {}).get('grapes',[])
    if prof.get('facts_blend') and len(gr)>1 and all(x.get('share') for x in gr) and abs(sum(x['share'] for x in gr)-100)<.5: c.setdefault('blend',[(x['name'],x['share']) for x in gr])
    sig=prof['story'].get('signature') or {}
    if sig.get('component')=='ava_nest' and c.get('level') and 'ava_chain' not in c:   # the AVAs that hold this one, outermost first
        AVA={e['name']:e for e in json.load(open(os.path.join(ROOT,'regions','sources','us-ava.json'),encoding='utf-8'))['entries']}
        names=[n for n in AVA[c['level']]['within'] if n in AVA]+[c['level']]
        names.sort(key=lambda n:len([x for x in AVA[n]['within'] if x in AVA]))
        chain=[]   # overlapping umbrellas (Sonoma Coast and Northern Sonoma both hold Russian River Valley) are not nested in each other: keep a true nest
        for n in names:
            if not chain or chain[-1] in AVA[n]['within']: chain.append(n)
        names=chain
        c['ava_chain']=[(n,(AVA[n].get('created') or '')[:4]) for n in names]
        sig.setdefault('short_names',prof['map'].get('short_names',{}))
    if '{estate_source}' in prof['map'].get('credit',''):   # the pin's source belongs to the wine, not the region
        prof['map']['credit']=prof['map']['credit'].replace('; estate location from {estate_source}','; estate location from '+cfg['map_estate']['credit'] if cfg.get('map_estate') else '')
    return prof

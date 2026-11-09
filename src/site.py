#!/usr/bin/env python3
"""Build the app into build/site/: the browse page, the phone sheets and the data they read.
Usage: python src/site.py [--geo] [--out DIR]   (DIR defaults to build/site; restock.py builds into a fresh folder)    then python src/serve.py to open it on the home network.
  index.html, assets/           the app (from app/), with app.css headed by the design tokens as CSS variables
  data/catalog.json             one slim entry per wine in the cellar, no prices
  geo/                          the map views (src/geoindex.py; rebuilt when the places with wine change, or with --geo)
  sheets/<id>/index.html        the phone sheet (src/mobile.py), next to sheet.pdf, sheet.web.html and map.svg
PDFs and maps are hard links to the files in build/<id>/ and wines/<id>/, so the site takes little extra space."""
import argparse,hashlib,json,os,re,shutil,sys
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
ROOT=os.path.dirname(HERE); SITE=os.path.join(ROOT,'build','site')
import catalog,geoindex,mobile
import blocks as B
TOK=json.load(open(os.path.join(ROOT,'design-system','tokens.json'),encoding='utf-8'))
ICONS={i['id']:i for i in json.load(open(os.path.join(ROOT,'design-system','icons.json'),encoding='utf-8'))['icons']}
STYLE_NAME={'red':'Red','white':'White','sparkling':'Sparkling','rosé':'Rosé','dessert':'Dessert','fortified':'Fortified','orange':'Orange'}
STYLE_THEME={'red':'red','white':'white','sparkling':'sparkling','rosé':'rose','dessert':'dessert','fortified':'fortified','orange':'white'}
def link(src,dst):
    if os.path.exists(dst): os.remove(dst)
    try: os.link(src,dst)
    except OSError: shutil.copy2(src,dst)
def css_vars():
    C,M=TOK['color'],TOK['map']; F=TOK['font']
    v={'ink':C['ink'],'soft':C['soft_text'],'coral':C['coral'],'coral-text':C['coral_text'],'gold':C['gold'],'gold-tint':C['gold_tint'],'gold-deep':'#C98F22',
       'sand':C['sand'],'teal':C['teal'],'paper':M['paper'],'edge-soft':C['page_edge'],'map-paper':M['paper'],'map-land':M['land'],'map-border':M['border'],
       'map-locator':M['locator_land'],'map-neighbor':M['neighbor_vineyard'],'map-village':M['village'],
       'display':f"{F['display']['family']}, sans-serif",'body':f"'{F['body']['family']}', sans-serif"}
    fonts=''.join(f"@font-face{{font-family:'Nunito Sans';font-weight:{w};font-display:swap;src:url(fonts/nunito-sans-latin-{w}-normal.woff2) format('woff2')}}" for w in (400,600,700,800))
    fonts+="@font-face{font-family:'Nunito Sans';font-style:italic;font-weight:400;font-display:swap;src:url(fonts/nunito-sans-latin-400-italic.woff2) format('woff2')}"
    fonts+=''.join(f"@font-face{{font-family:'Poppins';font-weight:{w};font-display:swap;src:url(fonts/poppins-latin-{w}-normal.woff2) format('woff2')}}" for w in (600,700,800))
    v.update({'hot':C['coral'],'panel':C['sand'],'rule':C['ink'],'dot-empty-border':C['dot_empty_border'],'map-premier':M['premier_cru'],'fill':'#EEF2F5','ground':'#E9EEF2','ocean':'#CFE3EE','ocean-hi':'#E4F0F6','land':'#F7F8F9','land-edge':'#C3CED6','map-target':M['target'],'map-target-fill':M['target_commune_fill']})
    types=''.join(f'.ts-{k}{{{B.ts(k)}}}' for k in TOK['type'] if not k.startswith('$'))   # every sheet type style as a class
    return fonts+':root{'+';'.join(f'--{k}:{x}' for k,x in v.items())+'}\n'+types+'\n'
def visuals():
    """The sheet's own pieces for the app: flavor and pairing icons, a bottle per wine style, theme accents, grape colors."""
    icons={k:B.ICONS[k] for k,v in ICONS.items() if v['family'] in ('flavor','pairing') and k in B.ICONS}
    bottles={st:B.bottle(B.Theme({'theme':th}),['','','']) for st,th in STYLE_THEME.items()}
    return dict(icons=icons,bottles=bottles,accent={st:TOK['themes'][th]['accent'] for st,th in STYLE_THEME.items()},
                grape={k:v for k,v in TOK['grape'].items() if not k.startswith('$')},window=TOK['layout']['drink_window'])
def slim(it,rec):
    r=it.get('region') or {}; names=r.get('names') or []
    where=', '.join(reversed(names[-2:])) if len(names)>1 else (names[0] if names else '')
    c=(rec or {}).get('content',{})
    th=it.get('theme') or STYLE_THEME.get(it.get('style'),'white')
    return dict(k=it['iwine'],id=it.get('record') if it.get('sheet') else None,name=it['name'],title=c.get('title') or it['name'],sub=c.get('subtitle'),
                producer=it['producer'],vintage=it.get('vintage'),style=it.get('style'),styleName=STYLE_NAME.get(it.get('style'),(it.get('style') or '').title()),
                accent=TOK['themes'][th]['accent'],grapes=it.get('grapes') or [],abv=it.get('alcohol'),country=r.get('country'),where=where,
                struct=it.get('structure'),aromas=[[a['id'],a['label']] for a in it.get('aromas',[])],pairs=[[p['id'],p['label']] for p in it.get('pairings',[])],
                win=[it['window']['start'],it['window']['end']] if it.get('window') and it['window'].get('start') else None,
                qty=it.get('quantity',0),sizes=it.get('sizes'),intro=it.get('intro'))
def main():
    global SITE
    ap=argparse.ArgumentParser(); ap.add_argument('--geo',action='store_true',help='rebuild the map views even if the places with wine have not changed')
    ap.add_argument('--out',help='build into this folder instead of build/site'); a=ap.parse_args()
    if a.out: SITE=os.path.abspath(a.out); geoindex.OUT=os.path.join(SITE,'geo')
    catalog.build() if hasattr(catalog,'build') else None
    cat=json.load(open(os.path.join(ROOT,'build','catalog.json'),encoding='utf-8'))
    os.makedirs(os.path.join(SITE,'data'),exist_ok=True); os.makedirs(os.path.join(SITE,'assets','fonts'),exist_ok=True)
    # the map views, only when the set of places changes: they take a few minutes
    key=hashlib.sha1(json.dumps(sorted({(i.get('region') or {}).get('node') or '' for i in cat['items']})).encode()+open(os.path.join(ROOT,'regions','geo-sources.json'),'rb').read()+open(os.path.join(HERE,'geoindex.py'),'rb').read()).hexdigest()
    kp=os.path.join(SITE,'geo','.key')
    if a.geo or not os.path.exists(kp) or open(kp).read()!=key:
        print('building the map views (a few minutes)...'); geoindex.main(); open(kp,'w').write(key)
    # the app
    shutil.copy2(os.path.join(ROOT,'app','app.js'),os.path.join(SITE,'assets','app.js'))
    shutil.copy2(os.path.join(ROOT,'app','icons','cellar-explorer-180.png'),os.path.join(SITE,'assets','cellar-explorer-180.png'))   # the Home screen icon
    url=mobile.ATLAS_URL; page=open(os.path.join(ROOT,'app','index.html'),encoding='utf-8').read()
    open(os.path.join(SITE,'index.html'),'w',encoding='utf-8').write(page.replace('{{ATLAS_URL}}',url) if url else re.sub(r' *<p class="app-sub.*?</p>\n','',page,count=1))   # the link to the Atlas, or none
    open(os.path.join(SITE,'assets','app.css'),'w',encoding='utf-8').write(css_vars()+open(os.path.join(ROOT,'app','app.css'),encoding='utf-8').read())
    for f in os.listdir(os.path.join(ROOT,'design-system','fonts')):
        if f.endswith('.woff2'): shutil.copy2(os.path.join(ROOT,'design-system','fonts',f),os.path.join(SITE,'assets','fonts',f))
    # the sheets
    items=[]; built=0; os.makedirs(os.path.join(SITE,'sheets'),exist_ok=True)
    for it in cat['items']:
        rid=it.get('record'); rec=None
        if rid and it.get('sheet'):
            wp=os.path.join(ROOT,'wines',rid,'wine.json'); rec=json.load(open(wp,encoding='utf-8'))
            d=os.path.join(SITE,'sheets',rid); os.makedirs(d,exist_ok=True)
            open(os.path.join(d,'index.html'),'w',encoding='utf-8').write(mobile.render(wp))
            for src,dst in ((os.path.join(ROOT,'build',rid,'sheet.pdf'),'sheet.pdf'),(os.path.join(ROOT,'build',rid,'sheet.web.html'),'sheet.web.html'),(os.path.join(ROOT,'wines',rid,rec.get('map_file','map.svg')),'map.svg')):
                if os.path.exists(src): link(src,os.path.join(d,dst))
            built+=1
        items.append(slim(it,rec))
    aroma_names={k:v['label'] for k,v in ICONS.items() if v['family']=='flavor'}; PS=json.load(open(os.path.join(ROOT,'design-system','pairing_sources.json'),encoding='utf-8')); pair_names={k:v['label'] for k,v in ICONS.items() if v['family']=='pairing'}
    pair_names.update({icon:PS['categories'][cat] for cat,icon in PS['icons'].items() if cat in PS['categories']})   # the pairing category's name, not one sheet's dish
    json.dump(visuals(),open(os.path.join(SITE,'data','visuals.json'),'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
    json.dump(dict(generated=cat['generated'],items=items,aromaNames=aroma_names,pairNames=pair_names,aromaGroup={k:v.get('group') for k,v in ICONS.items() if v['family']=='flavor'}),open(os.path.join(SITE,'data','catalog.json'),'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
    print(f'site: {len(items)} wines, {built} phone sheets, written to {os.path.relpath(SITE,ROOT)}/')
if __name__=='__main__': main()

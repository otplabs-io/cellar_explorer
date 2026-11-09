"""Sheet component library. Every function returns one block of markup.
Pixel-locked to reference/La-Boudriotte-2019-Print.pdf. Run `make verify` after any change.
All design values come from design-system/tokens.json. Components ask for roles, never hex."""
import json,os,re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOK=json.load(open(os.path.join(ROOT,'design-system','tokens.json')))
_c=TOK['color']; ROLE={k:_c[v] for k,v in TOK['role'].items() if not k.startswith('$')}
INK,SOFT,HOT,HOT_TEXT,ON_HOT,PAPER,PANEL,RULE=(ROLE[k] for k in ('text','text_soft','hot','hot_text','on_hot','paper','panel','rule'))
TY,L,ST,RAD=TOK['type'],TOK['layout'],TOK['stroke_px'],TOK['radius']
FAM={'display':TOK['font']['display']['family'],'body':TOK['font']['body']['family']}
PH=f"font-family: {FAM['display']}, sans-serif"; PB=f"font-family: '{FAM['body']}', sans-serif"
def n(v):
    """A number as the sheet writes it: 0.2 as .2, 15.0 as 15."""
    s=f'{v:g}'; return s.replace('0.','.',1) if s.startswith(('0.','-0.')) else s
def ts(name,**over):
    """CSS for a type style. Only what the style sets, so the rest inherits from the page."""
    t={**TY[name],**over}; s=[PH] if t.get('family')=='display' else []
    s.append(f"font-size: {n(t['size'])}px")
    if 'weight' in t: s.append(f"font-weight: {t['weight']}")
    if 'line' in t: s.append(f"line-height: {n(t['line'])}")
    if 'tracking' in t: s.append(f"letter-spacing: {n(t['tracking'])}px")
    return '; '.join(s)
def tsvg(name):
    t=TY[name]; ff=f'{FAM["display"]}, sans-serif' if t.get('family')=='display' else f"'{FAM['body']}', sans-serif"
    return f'font-family="{ff}" font-size="{n(t["size"])}" font-weight="{t["weight"]}"'
fr=lambda ws:' '.join(f'minmax(0, {n(w)}fr)' for w in ws)
ICON_DIR=os.path.join(ROOT,'design-system','icons')
def _load_icons():
    out={}
    for fam in os.listdir(ICON_DIR):
        d=os.path.join(ICON_DIR,fam)
        if not os.path.isdir(d): continue
        for f in os.listdir(d):
            if f.endswith('.svg'):
                s=open(os.path.join(d,f)).read()
                out[f[:-4]]=re.sub(r'^<svg[^>]*>|</svg>\s*$','',s.strip())
    return out
ICONS=_load_icons()
def icon(name,size,extra=None):
    inner=(extra or {}).get(name) or ICONS[name]
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{size}" height="{size}" style="flex: none" aria-hidden="true">{inner}</svg>'
DRAWN_WINE=TOK['themes']['white']['wine']  # serving icons draw their wine in this color
class Theme:
    """The wine's theme roles. cfg['theme'] picks a theme from tokens.json, and any role can be overridden in wine.json."""
    def __init__(s,cfg):
        s.name=cfg.get('theme','white'); d=TOK['themes'][s.name]; g=lambda k:cfg.get(k,d[k])
        s.accent,s.tint,s.disc,s.glass,s.highlight,s.wine=g('accent'),g('tint'),g('disc'),g('bottle'),g('bottle_highlight'),g('wine'); s.shape=g('bottle_shape'); s.capsule=cfg.get('capsule',d.get('capsule') or HOT)
        auto={k:ICONS[k].replace(DRAWN_WINE,s.wine) for k in ('decant','glass')} if s.wine!=DRAWN_WINE else {}
        s.icons={**auto,**cfg.get('icons',{})}
def section_head(t): return f'<h2 style="margin: 0 0 {L["section_head"]["gap_below"]}px; {ts("section_head")}; color: {INK}">{t}</h2>'
def taste_dots(th,k,label,value):
    g=L['taste_dots']
    d=''.join(f'<span style="display: block; width: {g["dot"]}px; height: {g["dot"]}px; border-radius: {RAD["circle"]}; background: {th.accent if i<k else ROLE["dot_empty"]}; border: {n(ST["dot"])}px solid {ROLE["dot_filled_border"] if i<k else ROLE["dot_empty_border"]}; box-sizing: border-box"></span>' for i in range(g['steps']))
    return f'<div style="display: grid; grid-template-columns: {g["label_col"]}px {g["dots_col"]}px minmax(0, 1fr); align-items: center; gap: {g["col_gap"]}px"><span style="{ts("dot_label")}">{label}</span><span style="display: flex; gap: {g["dot_gap"]}px">{d}</span><span style="{ts("dot_value")}; color: {SOFT}">{value}</span></div>'
def flavor(th,k,t):
    g=L['flavor']; return f'<div style="display: flex; flex-direction: column; align-items: center; gap: {g["gap"]}px; width: {g["cell"]}px">{icon(k,g["icon"],th.icons)}<span style="{ts("flavor_label")}; text-align: center">{t}</span></div>'
def pairing(th,k,t):
    g=L['pairing']; return f'<div style="display: flex; flex-direction: column; align-items: center; gap: {g["gap"]}px"><span style="display: flex; align-items: center; justify-content: center; width: {g["circle"]}px; height: {g["circle"]}px; border-radius: {RAD["circle"]}; background: {PANEL}">{icon(k,g["icon"],th.icons)}</span><span style="{ts("pairing_label")}; text-align: center">{t}</span></div>'
def fact(l,v,s): return f'<div style="display: flex; flex-direction: column; gap: {L["facts"]["item_gap"]}px"><span style="{ts("fact_label")}; color: {SOFT}">{l}</span><span style="{ts("fact_value")}">{v}</span><span style="{ts("fact_note")}; color: {SOFT}">{s}</span></div>'
# Bottle outlines share one label rectangle (44, 136, 82 by 76), so the shape changes and the layout doesn't.
BOTTLES={
 'burgundy':dict(name='Burgundy',glass='M72 8h26v56c0 22 28 30 28 64v104c0 6-4 10-10 10H54c-6 0-10-4-10-10V128c0-34 28-42 28-64z',capsule='M72 8h26v20H72z',highlight='M57 92c-8 8-12 18-12 34'),
 'bordeaux':dict(name='Bordeaux',glass='M73 8H97V74C97 86 126 88 126 104V232C126 238 122 242 116 242H54C48 242 44 238 44 232V104C44 88 73 86 73 74Z',capsule='M72 8h26v28H72z',highlight='M52 112V172'),
 'champagne':dict(name='Champagne',glass='M73 14H97V76C99 92 124 108 126 132V232C126 238 122 242 116 242H54C48 242 44 238 44 232V132C46 108 71 92 73 76Z',capsule='M71 10C71 6 74 4 78 4H92C96 4 99 6 99 10V18C99 21 97.5 22 97.5 23V64C97.5 68 98.5 71 100 74C94 76.5 76 76.5 70 74C71.5 71 72.5 68 72.5 64V23C72.5 22 71 21 71 18Z',highlight='M65 95C58 102 53 112 52 124',band='M72.5 58H97.5V63H72.5Z'),
}
def bottle(th,label):
    a,b,c=label; g=L['bottle']; sh=BOTTLES[th.shape]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170 250" width="{g['width']}" height="{g['height']}" role="img" aria-label="Illustration of a {sh['name']} bottle"><circle cx="85" cy="130" r="80" fill="{th.disc}"></circle><path d="{sh['glass']}" fill="{th.glass}"></path><path d="{sh['capsule']}" fill="{th.capsule}"></path>{f'<path d="{sh["band"]}" fill="{HOT}"></path>' if sh.get('band') and th.capsule!=HOT else ''}<path d="{sh['highlight']}" stroke="{th.highlight}" stroke-width="{n(ST['bottle_highlight'])}" fill="none" stroke-linecap="round"></path><rect x="44" y="136" width="82" height="76" fill="{ROLE['label_paper']}"></rect><text x="85" y="161" text-anchor="middle" {tsvg('bottle_name')} fill="{INK}">{a}</text><path d="M58 168h54" stroke="{HOT}" stroke-width="{n(ST['label_rule'])}"></path><text x="85" y="183" text-anchor="middle" {tsvg('bottle_appellation')} fill="{INK}">{b}</text><text x="85" y="202" text-anchor="middle" {tsvg('bottle_year')} fill="{INK}">{c}</text></svg>'''
def quality_ladder(level,tiers=('Grand Cru','Premier Cru','Village','Regional'),labels=None):
    g=L['quality_ladder']; ws=g['widths']
    if len(tiers)!=len(ws): ws=[round(g['min_width']+(ws[-1]-g['min_width'])*i/max(len(tiers)-1,1)) for i in range(len(tiers))]
    s=''.join(f'<div style="width: {w}px; height: {g["height"]}px; display: flex; align-items: center; justify-content: center; background: {HOT if t==level else PANEL}; color: {ON_HOT if t==level else INK}; {ts("ladder_step")}; white-space: nowrap">{lab}</div>' for t,lab,w in zip(tiers,labels or tiers,ws))
    return f'<div style="display: flex; flex-direction: column; align-items: center; gap: {g["gap"]}px">{s}</div>'
def dosage_scale(level,sig):
    """The label terms for sugar in sparkling wine, driest at the top, with this wine's term in hot. Terms come from the profile."""
    g=L['dosage_scale']
    s=''.join(f'<div style="width: {g["width"]}px; height: {g["height"]}px; box-sizing: border-box; padding: 0 {g["pad_x"]}px; display: flex; align-items: center; justify-content: space-between; background: {HOT if t==level else PANEL}; color: {ON_HOT if t==level else INK}; white-space: nowrap"><span style="{ts("ladder_step")}">{t}</span><span style="{ts("dosage_range")}">{r}</span></div>' for t,r in sig['terms'])
    return f'<div style="display: flex; flex-direction: column; align-items: center; gap: {g["gap"]}px">{s}</div>'
def ava_nest(level,sig,chain):
    """The wine's AVA inside the AVAs that hold it, outermost first, each with the year it was established.
    The wine's AVA is in hot. chain is [(name, year)], from the TTB data in regions/sources/us-ava.json."""
    g=L['ava_nest']; short=sig.get('short_names',{})
    def box_(i):
        nm,yr=chain[i]; hot=nm==level; bg=HOT if hot else (PANEL if i%2==0 else PAPER)
        head=f'<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 6px; min-height: {g["row"]}px"><span style="{ts("ladder_step")}">{short.get(nm,nm)}</span><span style="{ts("dosage_range")}">{yr}</span></div>'
        inner=box_(i+1) if i+1<len(chain) else ''
        return f'<div style="box-sizing: border-box; padding: {g["pad"]}px; background: {bg}; color: {ON_HOT if hot else INK}; display: flex; flex-direction: column; gap: {g["gap"]}px">{head}{inner}</div>'
    return f'<div style="width: {g["width"]}px; margin: 0 auto">{box_(0)}</div>'
SIGNATURES={'ava_nest':lambda c,sig:ava_nest(c['level'],sig,c['ava_chain']),'quality_ladder':lambda c,sig:quality_ladder(c.get('level'),sig['tiers'],sig.get('labels')),'dosage_scale':lambda c,sig:dosage_scale(c.get('level'),sig)}
def drink_window(th,first,last,now):
    yrs=list(range(first,last+1)); g=L['drink_window']
    cells=''.join(f'<span style="display: block; height: {g["bar"]}px; background: {HOT if y==now else th.accent}"></span>' for y in yrs)
    shown=set(yrs)
    if len(yrs)>g['max_ticks']:   # too many to label: this year first, then the ends, then every fifth year, never side by side
        shown=set()
        for y in [now,first,last]+[y for y in yrs if y%5==0]:
            if first<=y<=last and all(abs(y-x)>=max(3 if len(yrs)>16 else 2,round(len(yrs)/8)) for x in shown): shown.add(y)   # labels need more cells between them as the cells narrow
    ticks=''.join(f'<span style="{ts("window_tick_now" if y==now else "window_tick")}; color: {HOT_TEXT if y==now else SOFT}; text-align: center">{y if y in shown else ""}</span>' for y in yrs)
    return f'<div style="display: grid; grid-template-columns: repeat({len(yrs)}, minmax(0, 1fr)); gap: {g["gap"]}px">{cells}{ticks}</div>'
# ---- composed sections. data-block names are used by the overflow report.
def hero(th,c):
    g=L['hero']
    return f'''<section data-block="hero" style="display: grid; grid-template-columns: minmax(0, 1fr) {g['bottle_col']}px; column-gap: {g['col_gap']}px; background: {th.tint}; padding: {g['pad_y']}px {g['pad_x']}px; height: {g['height']}px; box-sizing: border-box">
<div style="display: flex; flex-direction: column; gap: {g['stack_gap']}px; justify-content: center">
<p style="margin: 0; {ts('eyebrow')}; color: {HOT_TEXT}">{c['eyebrow']}</p>
<h1 style="margin: 0; {ts('sheet_title',size=c.get('title_px',TY['sheet_title']['size']))}">{c['title']}</h1>
<p style="margin: {g['subtitle_gap']}px 0 0; {ts('subtitle')}">{c['subtitle']}</p>
<p style="margin: 0; {ts('producer')}">{c['producer']}</p>
{f'<p style="margin: {g["intro_gap"]}px 0 0; {ts("intro")}">{c["intro"]}</p>' if c.get('intro') else ''}
</div>
<div style="display: flex; align-items: center; justify-content: center">{bottle(th,c['bottle_label'])}</div>
</section>'''
GRAPE=TOK['grape']
def blend(parts):
    """The blend as a stacked bar with a key, spanning two fact columns. Only for sourced shares of this vintage."""
    g=L['blend']; fb=iter(GRAPE['fallback']); col={nm:GRAPE.get(nm) or next(fb) for nm,_ in parts}
    bar=''.join(f'<span style="display: block; width: {n(sh)}%; height: {g["bar"]}px; background: {col[nm]}"></span>' for nm,sh in parts)
    key=''.join(f'<span style="display: inline-flex; align-items: center; gap: 4px; {ts("fact_note")}; color: {SOFT}; white-space: nowrap"><span style="display: block; width: {g["swatch"]}px; height: {g["swatch"]}px; background: {col[nm]}"></span>{n(sh)}% {nm}</span>' for nm,sh in parts)
    return f'<div style="grid-column: span 2; display: flex; flex-direction: column; gap: {L["facts"]["item_gap"]}px"><span style="{ts("fact_label")}; color: {SOFT}">BLEND</span><div style="display: flex; gap: {g["gap"]}px; margin-top: {g["bar_gap"]}px">{bar}</div><div style="display: flex; flex-wrap: wrap; column-gap: {g["key_gap"]}px; margin-top: {g["bar_gap"]}px">{key}</div></div>'
def facts_row(c):
    g=L['facts']; lead_=blend(c['blend']) if c.get('blend') else ''
    return f'<section data-block="facts" style="display: grid; grid-template-columns: repeat({g["columns"]}, minmax(0, 1fr)); column-gap: {g["col_gap"]}px; padding: 0 {g["pad_x"]}px {g["pad_bottom"]}px; border-bottom: {n(ST["rule"])}px solid {RULE}">{lead_}{"".join(fact(*f) for f in c["facts"])}</section>'
def taste_row(th,c):
    g=L['taste']
    return f'''<section data-block="taste" style="display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); column-gap: {g['col_gap']}px">
<div style="display: flex; flex-direction: column">{section_head('Taste profile')}
<div style="display: flex; flex-direction: column; gap: {g['row_gap']}px">{''.join(taste_dots(th,*d) for d in c['taste'])}</div>
<p style="margin: {g['note_gap']}px 0 0; {ts('caption')}; color: {SOFT}">{c['taste_note']}</p></div>
<div style="display: flex; flex-direction: column">{section_head('What you may smell and taste')}
<div style="display: flex; justify-content: space-between">{''.join(flavor(th,*f) for f in c['flavors'])}</div>
{f'<p style="margin: {g["flavor_note_gap"]}px 0 0; {ts("body")}">{c["flavor_note"]}</p>' if c.get('flavor_note') else ''}</div>
</section>'''
def serve_row(th,c,prof):
    w=c.get('window'); g=L['serve']   # no window when no source gives one: the note says so and no bar is drawn
    cells=[x for x in prof['serve_cells'] if c.get(x[2])]   # a cell drops out when the wine has no text for it
    cell=lambda head,ic,txt:f'<div style="display: flex; flex-direction: column; gap: {g["stack_gap"]}px">{section_head(head)}<div style="display: flex; gap: {g["icon_gap"]}px; align-items: flex-start">{icon(ic,g["icon"],th.icons)}<p style="margin: 0; {ts("serve")}">{txt}</p></div></div>'
    return f'''<section data-block="serve" style="background: {PANEL}; padding: {g['pad_y']}px {g['pad_x']}px; display: grid; grid-template-columns: {fr(g['columns'][:1+len(cells)])}; column-gap: {g['col_gap']}px">
<div>{section_head('When to drink it')}{drink_window(th,w[0],w[1],w[2]) if w else ''}<p style="margin: {g['note_gap']}px 0 0; {ts('window_note')}">{c['window_note']}</p></div>
{chr(10).join(cell(h,ic,c[k]) for h,ic,k in cells)}
</section>'''
def pairing_row(th,c):
    g=L['pairing']
    return f'''<section data-block="pairings">{section_head('What to eat with it')}
<div style="display: grid; grid-template-columns: repeat({len(c['pairs'])}, minmax(0, 1fr)); column-gap: {g['col_gap']}px">{''.join(pairing(th,*p) for p in c['pairs'])}</div>
{f'<p style="margin: {g["note_gap"]}px 0 0; {ts("body")}; text-align: center">{c["pair_note"]}</p>' if c.get('pair_note') else ''}</section>'''
def story_row(c,prof):
    """The region's signature graphic (a quality ladder, a dosage scale), then the producer and the vintage.
    Without a signature, or without the wine's level, the row reflows to two columns."""
    g=L['story']; sig=prof['story'].get('signature'); lab=prof['story']['labels']
    sig=sig if sig and (c.get('level') or c.get('show_signature')) else None   # show_signature: the scale with no rung lit, when the wine's own rung isn't sourced
    left=f'''<div>{section_head(c.get('ladder_title',sig['title']))}{SIGNATURES[sig['component']](c,sig)}<p style="margin: {g['note_gap']}px 0 0; {ts('ladder_note')}; color: {SOFT}; text-align: center">{c['ladder_note']}</p></div>
''' if sig else ''
    return f'''<section data-block="story" style="display: grid; grid-template-columns: {str(g['ladder_col'])+'px ' if sig else ''}{fr(g['columns'])}; column-gap: {g['col_gap']}px; border-top: {n(ST['rule'])}px solid {RULE}; padding-top: {g['pad_top']}px; flex-grow: 1">
{left}<div>{section_head(c.get('family_title',lab['family']))}<p style="margin: 0; {ts('story')}">{c['family']}</p></div>
<div>{section_head(c.get('vintage_title',lab['vintage']))}<p style="margin: 0; {ts('story')}">{c['vintage']}</p></div>
</section>'''
def place_header(c,prof):
    sub=c.get('place_subtitle',prof['place']['subtitle'])
    return f'<header data-block="place-header" style="display: flex; align-items: baseline; justify-content: space-between; gap: {L["place_header"]["gap"]}px"><h1 style="margin: 0; {ts("page_title")}">{c.get("place_title",prof["place"]["title"])}</h1>'+(f'<p style="margin: 0; {ts("place_subtitle")}; color: {SOFT}">{sub}</p>' if sub else '')+'</header>'
def map_block(svg): return f'<div data-block="map" style="width: {L["map"]["width"]}px; height: {L["map"]["height"]}px">{svg}</div>'
def notes_row(c):
    cols=''.join(f'<div>{section_head(k)}<p style="margin: 0; {ts("notes")}">{v}</p></div>' for k,v in c['place'])
    return f'<section data-block="notes" style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); column-gap: {L["notes"]["col_gap"]}px">{cols}</section>'
def credits_footer(c,prof):
    mc=prof['map']['credit']
    return f'<footer data-block="credits" style="margin-top: auto; border-top: {n(ST["footer_rule"])}px solid {RULE}; padding-top: {L["credits"]["pad_top"]}px; {ts("footer")}; color: {SOFT}">{mc+" " if mc else ""}{c["credits"]}</footer>'
def page(gap,lh,children):
    P=TOK['page']
    return f'<div class="sheet-page" style="width: {P["width_px"]}px; height: {P["height_px"]}px; box-sizing: border-box; padding: {P["margin_px"]}px; display: flex; flex-direction: column; gap: {gap}px; background: {PAPER}; color: {INK}; {PB}; font-size: {n(TY["page_base"]["size"])}px; line-height: {n(lh)}">\n'+'\n'.join(children)+'\n</div>'

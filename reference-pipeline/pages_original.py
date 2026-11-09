# FROZEN RECORD of the script that made the delivered PDF. Not run by the build. Paths are from the original workspace.
B_='/tmp/claude-0/-home-claude/8b5e5abc-501d-54cd-8257-a48a145c8c87/scratchpad/build/'
import json,os
INK='#1F2D3A';CORAL='#D9482B';GOLD='#E9B44C';GOLDL='#F9EBC6';TEAL='#1F6F73';SOFT='#47525C';SAND='#F4EFE3';PLUM='#7C4F75'
H="font-family: Poppins, sans-serif"; BODY="font-family: 'Nunito Sans', sans-serif"
def svg(vb,inner,size,label=None):
    a=f'role="img" aria-label="{label}"' if label else 'aria-hidden="true"'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb} {vb}" width="{size}" height="{size}" style="flex: none" {a}>{inner}</svg>'
# flat icons, 64 viewbox
IC={}
IC['apple']='<path d="M32 22c-5-5-20-4-20 12 0 11 8 22 14 22 3 0 4-2 6-2s3 2 6 2c6 0 14-11 14-22 0-16-15-17-20-12z" fill="#F0C94D"></path><path d="M32 22c0-5 1-8 4-11" stroke="#6B4E2E" stroke-width="3" fill="none" stroke-linecap="round"></path><path d="M36 15c4-5 9-5 12-4-1 5-7 8-12 4z" fill="#7FA650"></path>'
IC['pear']='<path d="M32 16c-5 0-7 4-7 9 0 6-9 10-9 20 0 8 7 12 16 12s16-4 16-12c0-10-9-14-9-20 0-5-2-9-7-9z" fill="#BFCB5D"></path><path d="M32 16c0-3 1-6 3-8" stroke="#6B4E2E" stroke-width="3" fill="none" stroke-linecap="round"></path>'
IC['peach']='<circle cx="32" cy="36" r="21" fill="#F2A679"></circle><path d="M32 15c-7 8-7 34 0 42" stroke="#D97F52" stroke-width="2.5" fill="none"></path><path d="M33 15c4-6 10-7 15-5-2 6-9 9-15 5z" fill="#7FA650"></path>'
IC['lemon']='<path d="M7 34c0-3 4-4 6-8 4-8 11-12 19-12s15 4 19 12c2 4 6 5 6 8s-4 4-6 8c-4 8-11 12-19 12s-15-4-19-12c-2-4-6-5-6-8z" fill="#F5D63D"></path><path d="M21 24c3-3 7-5 11-5" stroke="#FFF3B0" stroke-width="3.5" fill="none" stroke-linecap="round"></path>'
IC['nut']='<path d="M32 10c12 6 20 16 20 27 0 11-9 18-20 18s-20-7-20-18c0-11 8-21 20-27z" fill="#B57F4A"></path><path d="M12 37c6-5 34-5 40 0 0 3-1 6-2 8-9-4-27-4-36 0-1-2-2-5-2-8z" fill="#8A5A2E"></path>'
IC['flint']='<path d="M9 44 19 19l17-9 19 16 2 18-15 11-22 1z" fill="#9AA5AD"></path><path d="m19 19 8 16 15 20M27 35l28-9M27 35 9 44" stroke="#6F7A82" stroke-width="2" fill="none"></path>'
IC['chicken']='<path d="M40 8c10 0 17 7 17 16 0 11-10 17-20 15l-9 9c1 4-1 8-5 8-2 0-3-1-4-3-2-1-3-2-3-4 0-4 4-6 8-5l9-9C31 25 29 8 40 8z" fill="#D49A5A"></path><path d="M38 15c5-2 11 1 12 6" stroke="#EFC48E" stroke-width="3" fill="none" stroke-linecap="round"></path>'
IC['scallop']='<path d="M32 54c-3 0-6-2-8-4H16C8 42 6 32 10 24c5-10 14-14 22-14s17 4 22 14c4 8 2 18-6 26h-8c-2 2-5 4-8 4z" fill="#F0B9A5"></path><path d="M32 50V12M26 50 17 16M38 50l9-34M21 49 10 27M43 49l11-22" stroke="#C97F68" stroke-width="2.4" fill="none"></path>'
IC['lobster']='<path d="M32 21c5 0 8 4 8 10v10c0 3-1 5-3 7l6 8H21l6-8c-2-2-3-4-3-7V31c0-6 3-10 8-10z" fill="#D9482B"></path><path d="M26 29 15 24M38 29l11-5M25 36H14M39 36h11M25 42l-9 3M39 42l9 3" stroke="#D9482B" stroke-width="2.6" stroke-linecap="round"></path><path d="M8 5c6 1 11 6 11 13 0 5-3 8-7 8-6 0-9-5-9-10 0-4 1-7 3-9l2 8z" fill="#D9482B"></path><path d="M56 5c-6 1-11 6-11 13 0 5 3 8 7 8 6 0 9-5 9-10 0-4-1-7-3-9l-2 8z" fill="#D9482B"></path><path d="M26 44h12M26 49h12" stroke="#fff" stroke-width="1.6" opacity=".7"></path>'
IC['cheese']='<path d="M6 36 46 14c7 3 12 11 12 22z" fill="#F7DC84"></path><path d="M6 36h52v16H6z" fill="#F0C94D"></path><circle cx="20" cy="44" r="3.4" fill="#D9A92E"></circle><circle cx="40" cy="45" r="2.6" fill="#D9A92E"></circle><circle cx="36" cy="28" r="3" fill="#E5BE52"></circle>'
IC['risotto']='<path d="M8 34h48c0 12-9 22-24 22S8 46 8 34z" fill="#7D8B93"></path><path d="M20 34c-1-7 5-13 12-13s13 6 12 13z" fill="#F3E6C2"></path><path d="M39 21c-6 0-10-3-10-8 0-4 5-7 10-7s10 3 10 7c0 5-4 8-10 8z" fill="#A9835B"></path><path d="M36 20h6l1 11h-8z" fill="#E7D7B6"></path>'
IC['thermo']='<path d="M26 12a6 6 0 0 1 12 0v26a12 12 0 1 1-12 0z" fill="#fff" stroke="#1F2D3A" stroke-width="3"></path><circle cx="32" cy="47" r="7" fill="#D9482B"></circle><path d="M32 26v20" stroke="#D9482B" stroke-width="5"></path>'
IC['decant']='<path d="M27 6h10v14c0 5 17 18 17 28 0 7-9 10-22 10S10 55 10 48c0-10 17-23 17-28z" fill="#fff" stroke="#1F2D3A" stroke-width="3"></path><path d="M15 44h34c2 6-4 11-17 11s-19-5-17-11z" fill="#E9B44C"></path>'
IC['glass']='<path d="M20 6h24c4 14 2 28-12 29C18 34 16 20 20 6z" fill="#fff" stroke="#1F2D3A" stroke-width="3"></path><path d="M19 20h26c-1 8-5 14-13 14s-12-6-13-14z" fill="#E9B44C"></path><path d="M32 35v19M22 56h20" stroke="#1F2D3A" stroke-width="3" stroke-linecap="round"></path>'
def h2(t,color=INK): return f'<h2 style="margin: 0 0 8px; {H}; font-size: 15px; font-weight: 700; line-height: 1.2; letter-spacing: .2px; color: {color}">{t}</h2>'
def dots(n,label,val):
    d=''.join(f'<span style="display: block; width: 18px; height: 18px; border-radius: 50%; background: {GOLD if i<n else "#fff"}; border: 1.5px solid {INK if i<n else "#8E8778"}; box-sizing: border-box"></span>' for i in range(5))
    return f'<div style="display: grid; grid-template-columns: 78px 118px minmax(0, 1fr); align-items: center; gap: 8px"><span style="font-size: 13.5px; font-weight: 800">{label}</span><span style="display: flex; gap: 4px">{d}</span><span style="font-size: 13px; color: {SOFT}">{val}</span></div>'
def flav(k,t):
    return f'<div style="display: flex; flex-direction: column; align-items: center; gap: 4px; width: 62px">{svg(64,IC[k],50)}<span style="font-size: 12.5px; font-weight: 700; text-align: center; line-height: 1.15">{t}</span></div>'
def pair(k,t):
    return f'<div style="display: flex; flex-direction: column; align-items: center; gap: 5px"><span style="display: flex; align-items: center; justify-content: center; width: 54px; height: 54px; border-radius: 50%; background: {SAND}">{svg(64,IC[k],38)}</span><span style="font-size: 13px; font-weight: 700; text-align: center; line-height: 1.15">{t}</span></div>'
def fact(l,v,s=''):
    return f'<div style="display: flex; flex-direction: column; gap: 1px"><span style="font-size: 11.5px; font-weight: 800; letter-spacing: .7px; color: {SOFT}">{l}</span><span style="{H}; font-size: 16px; font-weight: 700; line-height: 1.2">{v}</span><span style="font-size: 12px; color: {SOFT}; line-height: 1.2">{s}</span></div>'
BOTTLE=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170 250" width="136" height="200" role="img" aria-label="Illustration of a Burgundy bottle"><circle cx="85" cy="130" r="80" fill="{GOLD}"></circle><path d="M72 8h26v56c0 22 28 30 28 64v104c0 6-4 10-10 10H54c-6 0-10-4-10-10V128c0-34 28-42 28-64z" fill="#3F5B45"></path><path d="M72 8h26v20H72z" fill="{CORAL}"></path><path d="M57 92c-8 8-12 18-12 34" stroke="#7E9B82" stroke-width="4" fill="none" stroke-linecap="round"></path><rect x="44" y="136" width="82" height="76" fill="#FFFDF8"></rect><text x="85" y="161" text-anchor="middle" font-family="Poppins, sans-serif" font-size="9.5" font-weight="800" fill="{INK}">LA BOUDRIOTTE</text><path d="M58 168h54" stroke="{CORAL}" stroke-width="1.4"></path><text x="85" y="183" text-anchor="middle" font-family="'Nunito Sans', sans-serif" font-size="7.2" font-weight="700" fill="{INK}">Chassagne-Montrachet</text><text x="85" y="202" text-anchor="middle" font-family="Poppins, sans-serif" font-size="14" font-weight="800" fill="{INK}">2019</text></svg>'''
def pyramid():
    tiers=[('Grand Cru',76,False),('Premier Cru',104,True),('Village',132,False),('Regional',160,False)]
    s=''
    for t,w,on in tiers:
        s+=f'<div style="width: {w}px; height: 22px; display: flex; align-items: center; justify-content: center; background: {CORAL if on else SAND}; color: {"#fff" if on else INK}; font-size: 12px; font-weight: 800; white-space: nowrap">{t}</div>'
    return f'<div style="display: flex; flex-direction: column; align-items: center; gap: 2px">{s}</div>'
tl=''
yrs=list(range(2024,2033))
ticks=''.join(f'<span style="font-size: 12px; font-weight: {800 if y==2026 else 600}; color: {"#B93414" if y==2026 else SOFT}; text-align: center">{y}</span>' for y in yrs)
cells=''.join(f'<span style="display: block; height: 15px; background: {CORAL if y==2026 else GOLD}"></span>' for y in yrs)
timeline=f'<div style="display: grid; grid-template-columns: repeat(9, minmax(0, 1fr)); gap: 2px">{cells}{ticks}</div>'
FRONT=f'''<div style="width: 816px; height: 1056px; box-sizing: border-box; padding: 40px; display: flex; flex-direction: column; gap: 11px; background: #fff; color: {INK}; {BODY}; font-size: 14px; line-height: 1.42">
<section style="display: grid; grid-template-columns: minmax(0, 1fr) 140px; column-gap: 20px; background: {GOLDL}; padding: 10px 28px; height: 220px; box-sizing: border-box">
<div style="display: flex; flex-direction: column; gap: 6px; justify-content: center">
<p style="margin: 0; font-size: 12.5px; font-weight: 800; letter-spacing: 1.4px; color: #B93414">WHITE BURGUNDY</p>
<h1 style="margin: 0; {H}; font-size: 56px; font-weight: 800; line-height: 1.02; letter-spacing: -1.4px">La Boudriotte</h1>
<p style="margin: 2px 0 0; {H}; font-size: 18px; font-weight: 600; line-height: 1.25">Chassagne-Montrachet Premier Cru, 2019</p>
<p style="margin: 0; font-size: 15.5px; font-weight: 700">Domaine Gagnard-Delagrange</p>
<p style="margin: 5px 0 0; font-size: 14.5px; line-height: 1.38">A classic white Burgundy from a family domaine in the village. Expect ripe orchard fruit, a round, rich texture and a stony, nutty finish.</p>
</div>
<div style="display: flex; align-items: center; justify-content: center">{BOTTLE}</div>
</section>
<section style="display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); column-gap: 14px; padding: 0 2px 9px; border-bottom: 1.5px solid {INK}">
{fact('GRAPE','Chardonnay','100%')}{fact('REGION','Côte de Beaune','Burgundy, France')}{fact('ALCOHOL','13.8%','2019 vintage')}{fact('OAK','20% new','French barrels, 228 L')}{fact('MADE','9 barrels','About 3,000 bottles')}
</section>
<section style="display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); column-gap: 26px">
<div style="display: flex; flex-direction: column">{h2('Taste profile')}
<div style="display: flex; flex-direction: column; gap: 7px">{dots(1,'Sweetness','Dry')}{dots(4,'Body','Medium to full')}{dots(3,'Acidity','Moderate')}{dots(2,'Oak','Subtle, creamy')}</div>
<p style="margin: 8px 0 0; font-size: 12px; line-height: 1.3; color: {SOFT}">The typical style of this site in a warm vintage. A guide, not a measurement of this bottle.</p></div>
<div style="display: flex; flex-direction: column">{h2('What you may smell and taste')}
<div style="display: flex; justify-content: space-between">{flav('apple','Yellow apple')}{flav('pear','Pear')}{flav('peach','Peach')}{flav('lemon','Lemon peel')}{flav('nut','Hazelnut')}{flav('flint','Flint')}</div>
<p style="margin: 9px 0 0; font-size: 13.5px; line-height: 1.38">Barrel aging adds a little vanilla, toast and cream. One drinker on an older vintage: <em>“Minty, stony, and full of apple and pear fruit.”</em></p></div>
</section>
<section style="background: {SAND}; padding: 10px 16px; display: grid; grid-template-columns: minmax(0, 1.75fr) minmax(0, 1fr) minmax(0, 1fr); column-gap: 18px">
<div>{h2('When to drink it')}{timeline}<p style="margin: 7px 0 0; font-size: 13px; line-height: 1.35">In its window now and good into the early 2030s. A seeping cork or deep amber color can signal oxidation, a known white Burgundy risk.</p></div>
<div style="display: flex; flex-direction: column; gap: 3px">{h2('Serve')}<div style="display: flex; gap: 8px; align-items: flex-start">{svg(64,IC['thermo'],38)}<p style="margin: 0; font-size: 13.5px; line-height: 1.35"><strong>50 to 55°F.</strong> Cool, not icy.</p></div></div>
<div style="display: flex; flex-direction: column; gap: 3px">{h2('Decant')}<div style="display: flex; gap: 8px; align-items: flex-start">{svg(64,IC['decant'],38)}<p style="margin: 0; font-size: 13.5px; line-height: 1.35"><strong>20 to 30 minutes</strong> if it seems tight. Longer can dull its freshness.</p></div></div>
</section>
<section>{h2('What to eat with it')}
<div style="display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); column-gap: 8px">{pair('chicken','Roast chicken')}{pair('scallop','Seared scallops')}{pair('lobster','Lobster with butter')}{pair('cheese','Comté')}{pair('risotto','Creamy mushroom risotto')}</div>
<p style="margin: 6px 0 0; font-size: 13.5px; line-height: 1.38; text-align: center">The acidity keeps buttery dishes from feeling heavy. The weight stands up to roast chicken and nutty Comté.</p></section>
<section style="display: grid; grid-template-columns: 164px minmax(0, 1.25fr) minmax(0, 1fr); column-gap: 22px; border-top: 1.5px solid {INK}; padding-top: 10px; flex-grow: 1">
<div>{h2('Burgundy’s ladder')}{pyramid()}<p style="margin: 6px 0 0; font-size: 12px; line-height: 1.25; color: {SOFT}; text-align: center">Second rung of four</p></div>
<div>{h2('The family')}<p style="margin: 0; font-size: 13.5px; line-height: 1.4">The domaine dates to 1959, when Jacques Gagnard married Marie-Josèphe Delagrange. Most of the vines later passed to their daughters, Laurence and Claudine, of Fontaine-Gagnard and Blain-Gagnard. Grandson Marc-Antonin Blain makes the small remaining core in a traditional style.</p></div>
<div>{h2('The vintage')}<p style="margin: 0; font-size: 13.5px; line-height: 1.4">2019 was warm and dry. Spring frost and poor flowering cut the crop, and what survived came in ripe and concentrated. Whites turned out rich, with good balance and freshness.</p></div>
</section>
</div>'''
MAP=open(B_+'map.svg').read()
BACK=f'''<div style="width: 816px; height: 1056px; box-sizing: border-box; padding: 40px; display: flex; flex-direction: column; gap: 10px; background: #fff; color: {INK}; {BODY}; font-size: 14px; line-height: 1.4">
<header style="display: flex; align-items: baseline; justify-content: space-between; gap: 16px"><h1 style="margin: 0; {H}; font-size: 30px; font-weight: 800; letter-spacing: -.5px; line-height: 1.1">Where it grows</h1><p style="margin: 0; font-size: 14px; font-weight: 700; color: {SOFT}">From all of Burgundy down to one vineyard</p></header>
<div style="width: 736px; height: 752px">{MAP}</div>
<section style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); column-gap: 20px">
<div>{h2('The spot')}<p style="margin: 0; font-size: 13px; line-height: 1.36">About a kilometer south of the village, close to where Chassagne meets Santenay and Remigny. The slope is gentle, faces east to southeast, and sits near 240 meters.</p></div>
<div>{h2('The soil')}<p style="margin: 0; font-size: 13px; line-height: 1.36">Clay-rich with stony limestone. The clay gives whites more weight and a rounder shape than the leaner, flintier sites in the village. Pinot Noir grows here too.</p></div>
<div>{h2('The name')}<p style="margin: 0; font-size: 13px; line-height: 1.36">Six plots can use the La Boudriotte name, and all six sit inside Morgeot. This wine comes from old vines in three sections of the vineyard, which the map does not separate.</p></div>
</section>
<footer style="margin-top: auto; border-top: 1px solid {INK}; padding-top: 5px; font-size: 10.5px; line-height: 1.28; color: {SOFT}">Maps: INAO vineyard delimitations (Licence Ouverte) via OpenDataWine; commune outlines from france-geojson, drawn to the vineyard parcels where they exist and simplified elsewhere. For orientation, not a legal boundary. Text: Bottle Brief; Winebow (US importer); Inside Burgundy; Decanter; Becky Wasserman &amp; Co.; Delectable (drinker quote). Serving temperature is general guidance.</footer>
</div>'''
HEADF='<link rel="preconnect" href="https://fonts.googleapis.com"></link>'
GF='https://fonts.googleapis.com/css2?family=Nunito+Sans:ital,wght@0,400;0,600;0,700;0,800;1,400&amp;family=Poppins:wght@600;700;800&amp;display=swap'
def dc(title,root):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="stylesheet" href="{GF}">
<style>
body{{margin:0}}
</style>
</helmet>
{root}
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":816,"height":1056}}}}'>
class Component extends DCLogic {{
renderVals() {{ return {{}}; }}
}}
</script>
</body>
</html>
'''
os.makedirs(B_+'canvas/project',exist_ok=True)
open(B_+'canvas/project/Main.dc.html','w').write(dc('La Boudriotte: the wine',FRONT))
open(B_+'canvas/project/Where-It-Grows.dc.html','w').write(dc('La Boudriotte: where it grows',BACK))
FONT=''.join(f"@font-face{{font-family:'Nunito Sans';font-weight:{w};src:url(node_modules/@fontsource/nunito-sans/files/nunito-sans-latin-{w}-normal.woff2)}}" for w in (400,600,700,800))
FONT+="@font-face{font-family:'Nunito Sans';font-style:italic;font-weight:400;src:url(node_modules/@fontsource/nunito-sans/files/nunito-sans-latin-400-italic.woff2)}"
FONT+=''.join(f"@font-face{{font-family:'Poppins';font-weight:{w};src:url(node_modules/@fontsource/poppins/files/poppins-latin-{w}-normal.woff2)}}" for w in (600,700,800))
open(B_+'proof.html','w').write(f'<!doctype html><html><head><meta charset="utf-8"><title>La Boudriotte</title><style>{FONT}@page{{size:8.5in 11in;margin:0}}html,body{{margin:0;padding:0}}.pg{{width:816px;height:1056px;overflow:hidden;break-after:page}}</style></head><body><div class="pg">{FRONT}</div><div class="pg">{BACK}</div></body></html>')

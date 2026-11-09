import sys,os
HERE=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE,'maps.py')).read())
B_=os.path.join(HERE,'output','')
os.makedirs(B_,exist_ok=True)
W=736; AW,AH=292,330; BX,BW,BH=304,432,330; CY,CH_=340,412
PLUM='#7C4F75'; GOLD='#E9B44C'; GOLDL='#F4DDA6'; EDGE='#6F675A'
def title(x,y,n,t,sub=None,bg='#fff'):
    s=f'<circle cx="{x+11}" cy="{y+11}" r="11" fill="{INK}"></circle>'+T_(x+11,y+15.5,str(n),12,700,'#fff','middle',HF)
    s+=halo(x+28,y+11.5,t,14,700,INK,'start',HF,bg,3)
    if sub: s+=halo(x+28,y+24.5,sub,10.5,600,'#47525C','start',BF,bg,3)
    return s
def scalebar(x,y,meters,lab,F):
    w=meters*F.k
    return f'<path d="M{x},{y-4}V{y}H{x+w:.1f}V{y-4}" fill="none" stroke="{INK}" stroke-width="1.2"></path>'+T_(x+w/2,y-6,lab,9.5,700,INK,'middle')
def north(x,y):
    return f'<path d="M{x},{y-13}L{x+5},{y}L{x},{y-3}L{x-5},{y}Z" fill="{INK}"></path>'+T_(x,y+11,'N',10,700,INK,'middle',HF)
def town(F,lon,lat,n,dx=5,dy=3.5,anchor='start',size=10,w=600):
    p=F.xy(*ll(lon,lat))
    return f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="2.4" fill="#fff" stroke="{INK}" stroke-width="1.1"></circle>'+halo(p[0]+dx,p[1]+dy,n,size,w,INK,anchor)
def fitframe(bb,w,h,top=0,bottom=0,pad=8):
    fw,fh=bb[2]-bb[0],bb[3]-bb[1]
    k=min((w-2*pad)/fw,(h-top-bottom-2*pad)/fh); cx,cy=(bb[0]+bb[2])/2,(bb[1]+bb[3])/2
    y1=cy+(h/2+(top-bottom)/2)/k; y0=y1-h/k
    return Frame((cx-w/2/k,y0,cx+w/2/k,y1),w,h)
def lead(x0,y0,x1,y1,txt,anchor='start',w=600,size=10.5,fill=INK,col=None,dy=3.5,bg='#fff'):
    col=col or INK
    return f'<path d="M{x0},{y0}L{x1},{y1}" stroke="{col}" stroke-width=".7" fill="none"></path><circle cx="{x0}" cy="{y0}" r="1.5" fill="{col}"></circle>'+halo(x1+(3 if anchor=="start" else -3),y1+dy,txt,size,w,fill,anchor,BF,bg)
def badge(x,y,n):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{CORAL}" stroke="#fff" stroke-width="1.2"></circle>'+T_(x,y+3.6,str(n),10,700,'#fff','middle',HF)
# ---- PANEL 1
regc=[c for c in dict.fromkeys(regcodes) if c in C]
bx=unary_union([C[c]['geom'] for c in regc]).bounds
FA=fitframe(bx,AW,AH,top=34,bottom=2,pad=6)
a=[f'<rect width="{AW}" height="{AH}" fill="#FCFAF5"></rect>',P(FA.path(tri,.5),LAND)]
for c in regc: a.append(P(FA.path(C[c]['geom'],.3),CSUB[sub(c)],'#fff','.5'))
a.append(P(FA.path(tri,.5),'none',EDGE,'.9','stroke-dasharray="3 2.5"'))
px,py=FA.xy(CH.centroid.x,CH.centroid.y)
for lon,lat,n,dx,dy,an in ((5.0415,47.3220,'Dijon',5,3.5,'start'),(4.8400,47.0260,'Beaune',5,3.5,'start'),(4.8535,46.7806,'Chalon',5,3.5,'start'),(4.8285,46.3069,'Mâcon',5,3.5,'start')):
    a.append(town(FA,lon,lat,n,dx,dy,an))
for x0,y0,x1,y1,t,an in ((88,96,26,134,'Chablis','start'),(180,62,214,50,'Châtillonnais','start'),(218,165,152,159,'Côte de Nuits','end'),(197,200,132,196,'Côte de Beaune','end'),(196,240,132,236,'Côte Chalonnaise','end'),(196,288,146,288,'Mâconnais','end')):
    if an=='middle':
        a.append(f'<path d="M{x0},{y0}L{x1},{y1}" stroke="{INK}" stroke-width=".7"></path>'+halo(x1,y1-3,t,10.5,700,INK,'middle',BF,LAND))
    else: a.append(lead(x0,y0,x1,y1,t,an,700,10.5,INK,INK,3.5,LAND))
a.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.6" fill="{CORAL}" stroke="#fff" stroke-width="1.4"></circle>')
a.append(lead(round(px),round(py),236,221,'This wine','start',800,11,'#B93414',CORAL,3.5,LAND))
a.append(title(6,6,1,'Burgundy','Wine villages, shaded by subregion','#FCFAF5'))
FF=fitframe(france.bounds,56,58,pad=2)
a.append(f'<g transform="translate(6,{AH-62})">'+P(FF.path(france,.3),'#D8CDB4','#fff','.5')+P(FF.path(tri,.3),CORAL)+'</g>')
# ---- PANEL 2
cb=['Ladoix-Serrigny','Aloxe-Corton','Pernand-Vergelesses','Savigny-lès-Beaune','Chorey-les-Beaune','Beaune','Pommard','Volnay','Monthelie','Auxey-Duresses','Saint-Romain','Meursault','Puligny-Montrachet','Chassagne-Montrachet','Saint-Aubin','Santenay','Remigny','Cheilly-lès-Maranges','Dezize-lès-Maranges','Sampigny-lès-Maranges']
cbc=[n for n in cb if n in inv]
bb=unary_union(list(apps.values())).bounds
FB=fitframe(bb,BW,BH,top=26,bottom=6,pad=14)
FB=Frame((FB.x0+18/FB.k,FB.y0,FB.x1+18/FB.k,FB.y1),BW,BH)
b=[f'<rect width="{BW}" height="{BH}" fill="#FCFAF5"></rect>']
vis=FB.clipbox()
for k_,c in C.items():
    if c['geom'].intersects(vis): b.append(P(FB.path(c['geom'],.3),LAND,'#CFC7B5','.5'))
for n in cbc: b.append(P(FB.path(C[inv[n]]['geom'],.3),'#F8E9C8'))
b.append(P(FB.path(CH,.2),'#F7C9B7'))
for n,g in apps.items():
    if n!='Chassagne-Montrachet': b.append(P(FB.path(g,.3),GOLD))
b.append(P(FB.path(VIL,.3),CORAL))
for n,g in gc.items(): b.append(P(FB.path(g,.3),PLUM))
for n in cbc: b.append(P(FB.path(C[inv[n]]['geom'],.3),'none',EDGE,'.8'))
b.append(P(FB.path(CH,.2),'none',INK,'1.5'))
PB=[('Aloxe-Corton','Aloxe-Corton',324,46,'start'),('Pernand-Vergelesses','Pernand-Vergelesses',270,24,'start'),('Savigny-lès-Beaune','Savigny-lès-Beaune',162,52,'end'),
('Chorey-lès-Beaune','Chorey-les-Beaune',324,106,'start'),('Beaune','Beaune',306,136,'start'),('Pommard','Pommard',292,160,'start'),('Volnay','Volnay',282,184,'start'),('Monthélie','Monthelie',128,114,'end'),
('Saint-Romain','Saint-Romain',82,148,'end'),('Auxey-Duresses','Auxey-Duresses',90,186,'end'),('Meursault','Meursault',274,209,'start'),('Puligny-Montrachet','Puligny-Montrachet',254,235,'start'),('Saint-Aubin','Saint-Aubin',74,224,'end'),
('Santenay','Santenay',64,258,'end'),('Remigny','Remigny',218,306,'start'),('Maranges','Sampigny-lès-Maranges',56,300,'end')]
for n,cn,x1,y1,an in PB:
    g=C[inv[cn]]['geom']; p_=g.representative_point() if cn in ('Meursault','Santenay','Remigny') else g.centroid; x0_,y0_=FB.xy(p_.x,p_.y)
    b.append(lead(round(x0_),round(y0_),x1,y1,n,an,600,10.5,INK,INK,3.5,LAND))
g=C[inv['Ladoix-Serrigny']]['geom']; lx_,ly_=FB.xy(g.centroid.x,g.centroid.y); b.append(halo(lx_+4,ly_+6,'Ladoix-Serrigny',10.5,600,INK,'middle',BF,'#F8E9C8'))
x0_,y0_=FB.xy(CH.centroid.x,CH.centroid.y); b.append(lead(round(x0_),round(y0_),234,272,'Chassagne-Montrachet','start',800,12.5,'#B93414',CORAL,4,LAND))
b.append(title(6,6,2,'Côte de Beaune','Village borders and vineyard land','#FCFAF5'))
b.append(scalebar(BW-104,BH-10,5000,'5 km',FB)); b.append(north(BW-16,BH-22))
# ---- PANEL 3
rb=RCH.bounds
kC=(CH_-4)/((rb[3]-rb[1])+180)
x0=rb[0]-560; y1=rb[3]+90
FC=Frame((x0,y1-CH_/kC,x0+W/kC,y1),W,CH_)
c=[f'<rect width="{W}" height="{CH_}" fill="{LAND}"></rect>']
for n,g in ref.items():
    if g.intersects(FC.clipbox()): c.append(P(FC.path(g,.25),LAND))
for n in ('Puligny-Montrachet','Saint-Aubin','Santenay','Remigny'): c.append(P(FC.path(A[n],.25),'#E5DCC6'))
c.append(P(FC.path(RCH,.2),'#FFFDF8'))
c.append(P(FC.path(VIL,.2),GOLDL,'#fff','.5')); c.append(P(FC.path(PC,.2),GOLD,'#fff','.5'))
for n in ('Montrachet','Bâtard-Montrachet','Criots-Bâtard-Montrachet','Chevalier-Montrachet','Bienvenues-Bâtard-Montrachet'): c.append(P(FC.path(gc[n],.2),PLUM,'#fff','.4'))
c.append(P(FC.path(MOR,.2),'none',TEAL,'1.7'))
c.append(P(FC.path(BOU,.15),CORAL,INK,'.9'))
for n,g in ref.items():
    if n!='Chassagne-Montrachet' and g.intersects(FC.clipbox()): c.append(P(FC.path(g,.25),'none',EDGE,'1','stroke-dasharray="5 3"'))
c.append(P(FC.path(RCH,.2),'none',INK,'2'))
vx_,vy_=FC.xy(*ll(4.7292,46.9378))
c.append(f'<circle cx="{vx_:.1f}" cy="{vy_:.1f}" r="4.4" fill="#fff" stroke="{INK}" stroke-width="1.7"></circle>')
for n,x,y in (('SAINT-AUBIN',56,120),('SANTENAY',54,322),('REMIGNY',302,404),('CORPEAU',466,345),('CHAGNY',430,392)):
    c.append(halo(x,y,n,10,700,'#5A5347','middle',HF,LAND,3,'letter-spacing=".6"'))
c.append(halo(170,204,'CHASSAGNE-',13,800,INK,'middle',HF,'#FFFDF8',3,'letter-spacing=".5"')+halo(170,221,'MONTRACHET',13,800,INK,'middle',HF,'#FFFDF8',3,'letter-spacing=".5"'))
c.append(halo(vx_+8,vy_-7,'Chassagne village',11,800,INK,'start',BF,'#FFFDF8'))
IX,IY,IW,IH=514,118,212,146
c.append(f'<rect x="{IX-10}" y="94" width="{W-IX+10}" height="{CH_-94}" fill="#FCFAF5"></rect>')
c.append(lead(383,28,352,12,'Le Montrachet','end',700,10.5,PLUM,PLUM,3.5,LAND))
c.append(lead(407,48,448,44,'Bâtard-Montrachet','start',700,10.5,PLUM,PLUM,3.5,LAND))
c.append(lead(383,78,430,86,'Criots-Bâtard','start',700,10.5,PLUM,PLUM,3.5,LAND))
c.append(halo(620,34,'PULIGNY-MONTRACHET',10,700,'#5A5347','middle',HF,LAND,3,'letter-spacing=".6"'))
c.append(halo(236,340,'MORGEOT',11.5,800,TEAL,'middle',HF,'#fff',3))
c.append(title(6,6,3,'Chassagne-Montrachet','Official vineyard boundaries',LAND))
FI=fitframe(BOU.bounds,IW,IH,pad=10)
i=[f'<rect width="{IW}" height="{IH}" fill="#FFFDF8"></rect>',P(FI.path(MOR,.2),GOLD)]
order=[('La Boudriotte',1),('Les Fairendes',2),('Les Chaumes',3),('Champs Jendreau',4),('Les Petites Fairendes',5),('La Roquemaure',6)]
tints=['#D9482B','#EC8166','#F2A18B','#B93A1F','#F6BBA9','#A82F18']
for (n,k_),t in zip(order,tints): i.append(P(FI.path(parts[n],.2),t,'#fff','1'))
for (n,k_) in order:
    pt=parts[n].representative_point(); x_,y_=FI.xy(pt.x,pt.y)
    i.append(f'<circle cx="{x_:.1f}" cy="{y_:.1f}" r="7.2" fill="#fff" stroke="{INK}" stroke-width=".9"></circle>'+T_(x_,y_+3.7,str(k_),10,800,INK,'middle',HF))
i.append(P(FI.path(MOR,.2),'none',TEAL,'1.6'))
inset=f'<g transform="translate({IX},{IY})">'+''.join(i)+f'<rect width="{IW}" height="{IH}" fill="none" stroke="{CORAL}" stroke-width="1.6"></rect></g>'
bq=[FC.xy(BOU.bounds[0]-20,BOU.bounds[3]+20),FC.xy(BOU.bounds[2]+20,BOU.bounds[1]-20)]
c.append(f'<rect x="{bq[0][0]:.1f}" y="{bq[0][1]:.1f}" width="{bq[1][0]-bq[0][0]:.1f}" height="{bq[1][1]-bq[0][1]:.1f}" fill="none" stroke="{CORAL}" stroke-width="1"></rect>')
c.append(f'<path d="M{bq[1][0]:.1f},{bq[1][1]:.1f}L{IX},{IY+IH}M{bq[1][0]:.1f},{bq[0][1]:.1f}L{IX},{IY}" stroke="{CORAL}" stroke-width="1" fill="none"></path>')
c.append(inset)
c.append(T_(IX,IY-7,'Inside the La Boudriotte name',12,800,'#B93414','start',HF))
ky=IY+IH+15
keyrows=[(1,'La Boudriotte','2.2'),(2,'Les Fairendes','7.1'),(3,'Les Chaumes','2.7'),(4,'Champs Jendreau','2.1'),(5,'Les Petites Fairendes','0.8'),(6,'La Roquemaure','0.6')]
for r,(k_,n,h) in enumerate(keyrows):
    yy=ky+r*14
    c.append(T_(IX+5,yy,str(k_),10.5,800,'#B93414','middle',HF)+T_(IX+16,yy,n,11,600)+T_(IX+IW,yy,h+' ha',11,600,INK,'end'))
yy=ky+6*14+2
c.append(f'<path d="M{IX},{yy-11}H{IX+IW}" stroke="{INK}" stroke-width=".8"></path>'+T_(IX+16,yy+1,'Total',11,800)+T_(IX+IW,yy+1,'15.6 ha',11,800,INK,'end'))
LY=yy+17
leg2=[('sw',CORAL,'La Boudriotte'),('sw',PLUM,'Grand Cru'),('sw',GOLD,'Premier Cru'),('sw',GOLDL,'Village'),('line',INK,'Village border'),('out',TEAL,'Morgeot')]
pos=[(IX,LY),(IX,LY+14),(IX,LY+28),(IX+106,LY+28),(IX+106,LY+14),(IX+106,LY)]
for (t,col,n),(x_,y_) in zip(leg2,pos):
    if t=='sw': c.append(f'<rect x="{x_}" y="{y_-8}" width="11" height="9" fill="{col}" stroke="{EDGE}" stroke-width=".4"></rect>')
    if t=='out': c.append(f'<rect x="{x_+.5}" y="{y_-7.5}" width="10" height="8" fill="none" stroke="{col}" stroke-width="1.6"></rect>')
    if t=='line': c.append(f'<path d="M{x_},{y_-3}h11" stroke="{col}" stroke-width="2"></path>')
    c.append(T_(x_+15,y_,n,10.5,600))
c.append(scalebar(16,CH_-12,1000,'1 km',FC)); c.append(north(170,CH_-20))
print('LY end',LY+28,'of',CH_)
# --- assemble
rectA=(FA.xy(FB.x0,FB.y1),FA.xy(FB.x1,FB.y0))
rectB=(FB.xy(FC.x0,FC.y1),FB.xy(FC.x1,FC.y0))
svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{CY+CH_}" viewBox="0 0 {W} {CY+CH_}" role="img" aria-label="Three linked maps locating La Boudriotte: Burgundy with its wine villages, the Côte de Beaune with village borders, and Chassagne-Montrachet with its vineyards.">'
svg+=f'<g>{"".join(a)}</g>'
svg+=f'<rect x="{rectA[0][0]:.1f}" y="{rectA[0][1]:.1f}" width="{rectA[1][0]-rectA[0][0]:.1f}" height="{rectA[1][1]-rectA[0][1]:.1f}" fill="none" stroke="{CORAL}" stroke-width="1.3"></rect>'+badge(rectA[1][0],rectA[0][1],2)
svg+=f'<g transform="translate({BX},0)"><g>{"".join(b)}</g><rect x="{rectB[0][0]:.1f}" y="{rectB[0][1]:.1f}" width="{rectB[1][0]-rectB[0][0]:.1f}" height="{rectB[1][1]-rectB[0][1]:.1f}" fill="none" stroke="{CORAL}" stroke-width="1.3"></rect>'+badge(rectB[1][0],rectB[0][1],3)+'</g>'
svg+=f'<g transform="translate(0,{CY})"><g>{"".join(c)}</g></g>'
svg+='</svg>'
open(B_+'map.svg','w').write(svg)
print('svg kb',len(svg)/1024,'rectB',rectB)

inv_=lambda F,x,y:(F.x0+x/F.k,F.y1-y/F.k)
for nm,xy in (('Montrachet',(383,28)),('Bâtard-Montrachet',(407,48)),('Criots-Bâtard-Montrachet',(383,78))):
    print(nm,'leader dot inside:',gc[nm].contains(Point(*inv_(FC,*xy))))
print('village in commune',RCH.contains(Point(*ll(4.7292,46.9378))))
print('Morgeot contains BOU',MOR.buffer(1).contains(BOU))

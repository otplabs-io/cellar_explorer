/* Cellar Explorer. The home page is a set of choices drawn the way the pour sheets draw them: a globe for the origin,
   bottles for the type, the drinking window, the taste dots, the flavor and pairing icons, grape swatches and
   vintages. Every choice counts the wines it would leave and is greyed out when it would leave none. The dock shows
   how many wines match and opens them on their own page (#/wines) at any point.
   Data: data/catalog.json and data/visuals.json (src/site.py), geo/world.json, geo/index.json and geo/views/*.json
   (src/geoindex.py). The choices live in the URL, so the back button and shared links keep them. */
(()=>{
'use strict';
const $=s=>document.querySelector(s), esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fold=s=>String(s??'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();
const YEAR=new Date().getFullYear(), NS='http://www.w3.org/2000/svg';
let CAT,GEO,VIS,WORLD,VIEWS={},Y0=YEAR,Y1=YEAR+20;
const S={page:'home',f:{},q:'',sort:'place'};
const SCALES=[['sw','Sweetness','sweetness'],['bo','Body','body'],['ac','Acidity','acidity'],['ta','Tannin','tannin'],['oa','Oak','oak']];
const MULTI=['style','grape','pair','vint','ain','aout',...SCALES.map(s=>s[0])];
const pl=(n,w)=>`${n} ${w}${n===1?'':'s'}`;
// ---------- state and the URL
function readHash(){
  const [path,qs]=location.hash.replace(/^#\/?/,'').split('?'); S.page=path==='wines'?'wines':'home';
  const u=new URLSearchParams(qs||''); S.f={};
  for(const k of MULTI){const v=u.get(k); if(v) S.f[k]=v.split('|');}
  if(u.get('p')) S.f.p=u.get('p'); if(u.get('po')&&u.get('po')===S.f.p) S.f.po=u.get('po'); if(/^\d{4}$/.test(u.get('yr')||'')) S.f.yr=u.get('yr');
  S.q=u.get('q')||''; S.sort=u.get('sort')||'place';
}
function qs(f=S.f){
  const u=new URLSearchParams();
  for(const [k,v] of Object.entries(f)) if(v&&(!Array.isArray(v)||v.length)) u.set(k,Array.isArray(v)?v.join('|'):v);
  if(S.q) u.set('q',S.q); if(S.sort!=='place') u.set('sort',S.sort);
  const s=u.toString(); return s?'?'+s:'';
}
const link=(page,f)=>'#/'+(page==='wines'?'wines':'')+qs(f);
function set(fn){fn(S.f); if(S.f.po&&S.f.po!==S.f.p) delete S.f.po; for(const k in S.f) if(S.f[k]==null||(Array.isArray(S.f[k])&&!S.f[k].length)) delete S.f[k]; history.replaceState(null,'',link(S.page)); render();}
function toggle(k,v){set(f=>{const a=f[k]||(f[k]=[]); const i=a.indexOf(v); i>-1?a.splice(i,1):a.push(v);});}
// ---------- matching
const place=()=>S.f.p||'world';
const isOwn=(w,id)=>w.place.includes(id)&&!w.place.some(x=>{const g=GEO.places[x]; return g&&g.parent===id&&g.source;});   // goes no deeper than id, or only to a part of it with no shape
function matches(w,skip){
  const f=S.f, on=k=>k!==skip&&f[k]&&f[k].length;
  if(skip!=='p'&&f.p&&!w.place.includes(f.p)) return false;
  if(skip!=='p'&&f.po&&!isOwn(w,f.po)) return false;   // this place only, none of its subregions
  if(on('style')&&!f.style.includes(w.style)) return false;
  if(on('grape')&&!w.grapes.some(g=>f.grape.includes(g))) return false;
  if(on('pair')&&!w.pairs.some(p=>f.pair.includes(p[0]))) return false;
  if(on('vint')&&!f.vint.includes(String(w.vintage||'NV'))) return false;
  if(on('ain')&&!f.ain.every(a=>w.aromas.some(x=>x[0]===a))) return false;
  if(on('aout')&&w.aromas.some(x=>f.aout.includes(x[0]))) return false;
  if(skip!=='yr'&&f.yr){const y=+f.yr; if(!(w.win&&w.win[0]<=y&&w.win[1]>=y)) return false;}   // in its drinking window that year
  for(const [k,,field] of SCALES) if(on(k)&&!(w.struct&&f[k].includes(String(w.struct[field])))) return false;
  if(S.q&&!w.text.includes(fold(S.q))) return false;
  return true;
}
const base=skip=>CAT.items.filter(w=>matches(w,skip));
function tally(list,keys){const m=new Map(); for(const w of list) for(const k of new Set(keys(w))) m.set(k,(m.get(k)||0)+1); return m;}
function winState(w){if(!w.win) return null; const [a,b]=w.win; return a>YEAR?'later':b<=YEAR+1?'soon':'ready';}
const winLabel=y=>+y===YEAR?'Ready now':`Ready in ${y}`;

// ---------- the map: an orthographic globe that flies from the world down to the village
const RAD=Math.PI/180, TAU=2*Math.PI;
async function view(id){
  if(!VIEWS[id]){const r=await fetch('geo/views/'+id.replace(/\//g,'__')+'.json'); if(!r.ok) return null; const v=await r.json();
    for(const it of v.items) if(it.p) it.g=prep(it.p); if(v.ctx) for(const c of v.ctx) c.g=prep(c.p); if(v.others) for(const o of v.others) o.g=prep(o.p); v.og=prep(v.outline); VIEWS[id]=v;}
  return VIEWS[id];
}
function viewFor(p){let id=p; while(id&&id!=='world'&&!(GEO.places[id]&&GEO.places[id].view)) id=GEO.places[id]?.parent; return id||'world';}
function el(tag,attrs,parent){const e=document.createElementNS(NS,tag); for(const k in attrs) e.setAttribute(k,attrs[k]); if(parent) parent.appendChild(e); return e;}
function tier(n,max){return n===0?0:max<=2?2:n>=max*.6?3:n>=max*.25?2:1;}
// shapes arrive as polygons of rings of [lon,lat,...]; keep each vertex's trig and a cap around each polygon for culling
function prep(P){
  return P.map(rings=>{let X=0,Y=0,Z=0;
    const rs=rings.map(r=>{const n=r.length/2, lam=new Float64Array(n), cp=new Float64Array(n), sp=new Float64Array(n);
      for(let i=0;i<n;i++){const l=r[2*i]*RAD,p=r[2*i+1]*RAD; lam[i]=l; cp[i]=Math.cos(p); sp[i]=Math.sin(p); X+=cp[i]*Math.cos(l); Y+=cp[i]*Math.sin(l); Z+=sp[i];}
      return {n,lam,cp,sp};});
    const L=Math.hypot(X,Y,Z)||1; X/=L;Y/=L;Z/=L; let m=1;
    for(const r of rs) for(let i=0;i<r.n;i++){const d=r.cp[i]*Math.cos(r.lam[i])*X+r.cp[i]*Math.sin(r.lam[i])*Y+r.sp[i]*Z; if(d<m) m=d;}
    return {rs,c:[X,Y,Z],rad:Math.acos(Math.max(-1,Math.min(1,m)))};});
}
function camOf(lon,lat,R){const l0=lon*RAD,p0=lat*RAD; return {lon,lat,R,l0,c0:Math.cos(p0),s0:Math.sin(p0),v:[Math.cos(p0)*Math.cos(l0),Math.cos(p0)*Math.sin(l0),Math.sin(p0)]};}
function pt(cam,lon,lat){const d=lon*RAD-cam.l0,p=lat*RAD,cp=Math.cos(p),sp=Math.sin(p),cd=Math.cos(d);
  return [cp*Math.sin(d),cam.c0*sp-cam.s0*cp*cd,cam.s0*sp+cam.c0*cp*cd];}
function unpt(cam,x,y){const r=Math.hypot(x,y); if(r>1) return null; const c=Math.asin(r), sc=Math.sin(c), cc=Math.cos(c);
  return [(cam.l0+Math.atan2(x*sc,r*cc*cam.c0-y*sc*cam.s0))/RAD,Math.asin(cc*cam.s0+(r?y*sc*cam.c0/r:0))/RAD];}
function projRing(r,cam){const out=new Array(r.n);
  for(let i=0;i<r.n;i++){const d=r.lam[i]-cam.l0,cd=Math.cos(d),cp=r.cp[i],sp=r.sp[i]; out[i]=[cp*Math.sin(d),cam.c0*sp-cam.s0*cp*cd,cam.s0*sp+cam.c0*cp*cd];}
  return out;}
function cross(a,b){const t=a[2]/(a[2]-b[2]),x=a[0]+t*(b[0]-a[0]),y=a[1]+t*(b[1]-a[1]),L=Math.hypot(x,y)||1; return [x/L,y/L,0];}
// cut a polygon at the horizon and close it along the globe's edge (outer rings run counterclockwise)
function clip(rings){
  const out=[],segs=[];
  for(const r of rings){const n=r.length; let vis=0; for(const p of r) if(p[2]>=0) vis++;
    if(vis===n){out.push(r); continue;} if(!vis) continue;
    let s=0; while(!(r[s][2]>=0&&r[(s-1+n)%n][2]<0)) s++;
    let cur=[cross(r[(s-1+n)%n],r[s])];
    for(let k=0;k<n;k++){const a=r[(s+k)%n],b=r[(s+k+1)%n];
      if(a[2]>=0){cur.push(a); if(b[2]<0){cur.push(cross(a,b)); segs.push(cur); cur=null;}}
      else if(b[2]>=0) cur=[cross(a,b)];}}
  const A=p=>Math.atan2(p[1],p[0]), sg=segs.map(p=>({p,a0:A(p[0]),a1:A(p[p.length-1]),used:false}));
  for(const s0 of sg){if(s0.used) continue; const ring=[]; let s=s0;
    for(let g=0;g<400;g++){s.used=true; for(const q of s.p) ring.push(q);
      let best=null,bd=9; for(const t of sg) if(!t.used||t===s0){let d=(t.a0-s.a1)%TAU; if(d<0) d+=TAU; if(d<bd){bd=d;best=t;}}
      const st=Math.ceil(bd/.06); for(let k=1;k<st;k++){const a=s.a1+bd*k/st; ring.push([Math.cos(a),Math.sin(a)]);}
      if(!best||best===s0) break; s=best;}
    out.push(ring);}
  return out;
}
const M={};   // the map: its svg, size, camera, layers and the view it shows
const r1=v=>Math.round(v*10)/10;
function polyD(poly,cam){
  const dot=poly.c[0]*cam.v[0]+poly.c[1]*cam.v[1]+poly.c[2]*cam.v[2], dist=Math.acos(Math.max(-1,Math.min(1,dot)));
  if(dist-poly.rad>M.va||Math.sin(Math.min(poly.rad,1.5))*cam.R<.35) return '';   // off the screen, behind the globe, or under a pixel
  let rings=poly.rs.map(r=>projRing(r,cam)); if(dist+poly.rad>Math.PI/2-1e-4) rings=clip(rings);
  const cx=M.W/2,cy=M.H/2,R=cam.R; let d='';
  for(const r of rings) if(r.length>2){d+='M'; for(let i=0;i<r.length;i++) d+=(i?'L':'')+r1(cx+R*r[i][0])+','+r1(cy-R*r[i][1]); d+='Z';}
  return d;
}
function gratD(cam){
  const cx=M.W/2,cy=M.H/2,R=cam.R; let d='';
  const line=pts=>{let on=false; for(const [lo,la] of pts){const p=pt(cam,lo,la); if(p[2]<0){on=false; continue;} d+=(on?'L':'M')+r1(cx+R*p[0])+','+r1(cy-R*p[1]); on=true;}};
  for(let lo=-180;lo<180;lo+=15){const a=[]; for(let la=-80;la<=80;la+=4) a.push([lo,la]); line(a);}
  for(let la=-75;la<=75;la+=15){const a=[]; for(let lo=-180;lo<=180;lo+=4) a.push([lo,la]); line(a);}
  return d;
}
function home(v){   // the world view faces the point that brings every country with wine closest to the middle, and fits them all
  if(v.home) return v.home; const P=[], rs=[];
  for(const it of v.items) if(it.g) for(const poly of it.g) for(const r of poly.rs){rs.push(r); for(let i=0;i<r.n;i+=3) P.push([r.cp[i]*Math.cos(r.lam[i]),r.cp[i]*Math.sin(r.lam[i]),r.sp[i]]);}
  const far=(lo,la)=>{const c=camOf(lo,la,1).v; let m=1; for(const q of P){const d=c[0]*q[0]+c[1]*q[1]+c[2]*q[2]; if(d<m) m=d;} return m;};   // the cosine to the farthest point
  let best=[v.center[0],v.center[1]], bm=-2;
  for(const [st,w] of [[4,90],[1,5]]){const [l0,a0]=best; for(let lo=l0-w;lo<=l0+w;lo+=st) for(let la=Math.max(-60,a0-w);la<=Math.min(70,a0+w);la+=st){const m=far(lo,la); if(m>bm){bm=m; best=[lo,la];}}}
  const cam=camOf(best[0],best[1],1); let ex=.2,ey=.2;
  for(const r of rs) for(const q of projRing(r,cam)) if(q[2]>0){ex=Math.max(ex,Math.abs(q[0])); ey=Math.max(ey,Math.abs(q[1]));}
  return v.home={lon:best[0],lat:best[1],ex,ey};
}
function camFor(v){
  if(v.id==='world'){const h=home(v); return camOf(h.lon,h.lat,Math.min(M.W/2/h.ex,M.H/2/h.ey)*.94);}
  return camOf(v.center[0],v.center[1],Math.min(M.W/2/v.half[0],M.H/2/v.half[1])*.9);}
function draw(){
  const cam=M.cam, hd=Math.hypot(M.W,M.H)/2; M.va=hd>=cam.R?Math.PI/2:Math.asin(hd/cam.R)+.01;
  M.ocean.setAttribute('r',r1(cam.R)); M.rim.setAttribute('r',r1(cam.R));
  M.grat.setAttribute('d',cam.R<Math.min(M.W,M.H)*2.5?gratD(cam):'');
  for(const f of M.feats) if(f.on()) f.el.setAttribute('d',f.g.map(p=>polyD(p,cam)).join(''));
}
function needWorld(cam,v){   // does this view's own land cover the screen, or does the coarse world have to show through
  if(!v.box) return true;
  for(const [X,Y] of [[0,0],[M.W,0],[0,M.H],[M.W,M.H],[M.W/2,0],[M.W/2,M.H],[0,M.H/2],[M.W,M.H/2]]){
    const q=unpt(cam,(X-M.W/2)/cam.R,(M.H/2-Y)/cam.R); if(!q) continue;
    let lo=q[0]; while(lo<v.box[0]-180) lo+=360; while(lo>v.box[0]+180) lo-=360;
    if(lo<v.box[0]||lo>v.box[2]||q[1]<v.box[1]||q[1]>v.box[3]) return true;}
  return false;
}
let C={};   // the counts the map is showing
function addFeat(g,cls,geo,extra){const e=el('path',Object.assign({class:cls},extra||{}),g); const f={el:e,g:geo,on:()=>g.isConnected&&g.style.display!=='none'}; M.feats.push(f); return f;}
function buildView(v,par){   // a view's layers: the land near it, its outline, its neighbours with wine, its places
  const g=el('g',{class:'vw'}); M.layers.insertBefore(g,null);
  if(v.ctx){const c=el('g',{class:'ctxg'},g); for(const x of v.ctx) addFeat(c,'land',x.g);}
  const sg=el('g',{},g);   // neighbours first: some contain this place (North Coast holds Napa)
  if(par) for(const it of par.items) if(it.g&&it.id!==v.id){const f=addFeat(sg,'rg sib',it.g,{'data-id':it.id}); f.it=it; f.sib=true;}
  if(v.og.length&&v.id!=='world'){   // the place itself, for the wines that go no deeper than it
    const f=addFeat(g,'rg own n0',v.og,{'data-own':v.id}); f.it={id:v.id,name:v.name,own:true,l:par?.items.find(i=>i.id===v.id)?.l||v.center}; v.ownIt=f.it;}
  if(v.og.length) addFeat(g,'outline',v.og);
  const ig=el('g',{},g);
  for(const it of v.items) if(it.g){const f=addFeat(ig,'rg',it.g,{'data-id':it.id}); f.it=it;}
  if(v.others){const og=el('g',{class:'others'},g); for(const o of v.others) addFeat(og,'other',o.g);}   // the places inside it with no wine yet: thin outlines over the rest
  g.view=v; return g;
}
function dropView(g){M.feats=M.feats.filter(f=>!g.contains(f.el)); g.remove();}
const cnt=it=>it.own?M.own:(C[it.id]||0);
function restyle(){
  const v=M.view; if(!v) return;
  M.own=v.ownIt?(M.inP||[]).filter(w=>isOwn(w,v.id)).length:0;
  const all=[...v.items,...(M.par?M.par.items:[])], max=Math.max(1,M.own,...all.map(i=>C[i.id]||0));
  for(const f of M.feats) if(f.it){const n=cnt(f.it); if(f.it.own&&f.it!==v.ownIt) continue;
    f.el.setAttribute('class',`rg${f.sib?' sib':''}${f.it.own?' own':''} n${tier(n,max)}${(f.it.own?S.f.po===f.it.id:M.leaf===f.it.id)?' sel':''}`);
    f.el.replaceChildren(); el('title',{},f.el).textContent=f.it.own?`${f.it.name}: ${pl(n,'wine')} with no smaller area`:`${f.it.name}: ${pl(n,'wine')}`;}
}
function labels(){
  const g=M.lab; g.replaceChildren(); const v=M.view, cam=M.cam; if(!v) return;
  const cx=M.W/2,cy=M.H/2,R=cam.R, max=Math.max(1,M.own||0,...v.items.map(i=>C[i.id]||0)), placed=[], fs=13;
  const scr=([lo,la])=>{const p=pt(cam,lo,la); return p[2]<0?null:[cx+R*p[0],cy-R*p[1]];};
  const free=b=>!(b[0]<2||b[2]>M.W-2||b[1]<2||b[3]>M.H-2||placed.some(o=>b[0]<o[2]-2&&o[0]<b[2]-2&&b[1]<o[3]-2&&o[1]<b[3]-2));
  const live=v.items.filter(i=>i.g&&(C[i.id]||M.leaf===i.id)).sort((a,b)=>cnt(b)-cnt(a));
  for(const it of v.items) it.s=null; if(v.ownIt) v.ownIt.s=null;
  for(const it of live){   // too small to tap at this size: add a dot
    const f=M.feats.find(f=>f.it===it&&!f.sib), bb=f&&f.el.getBBox(); const s=scr(it.l); if(!s) continue; it.s=s; it.dot=!bb||Math.max(bb.width,bb.height)<16; it.bb=bb;
    if(it.dot){const c=el('circle',{cx:r1(s[0]),cy:r1(s[1]),r:7,class:`dot-m n${tier(cnt(it),max)}${M.leaf===it.id?' sel':''}`,[it.own?'data-own':'data-id']:it.id},g); el('title',{},c).textContent=`${it.name}: ${pl(cnt(it),'wine')}`; placed.push([s[0]-6,s[1]-6,s[0]+6,s[1]+6]);}}
  const o=v.ownIt, of=o&&M.own&&M.feats.find(f=>f.it===o), ob=of&&of.el.getBBox();   // the place itself: spaced capitals along its edge, where the places inside it do not crowd
  if(ob&&ob.width){const fz=11, h=fz*1.2, w=(o.name.length+String(M.own).length+1)*fz*.8+4;
    const X0=Math.max(4,ob.x), X1=Math.min(M.W-4,ob.x+ob.width), Y0=Math.max(4,ob.y), Y1=Math.min(M.H-4,ob.y+ob.height), mx=(X0+X1)/2, my=(Y0+Y1)/2;
    for(const [X,Y,a] of [[mx,Y0-6,'middle'],[mx,Y1+h+2,'middle'],[mx,Y0+h+2,'middle'],[mx,Y1-6,'middle'],[X1+6,my+4,'start'],[X0-6,my+4,'end'],[X0+4,Y0+h+2,'start'],[X1-4,Y0+h+2,'end'],[X0+4,Y1-6,'start'],[X1-4,Y1-6,'end']]){
      const x0=a==='middle'?X-w/2:a==='end'?X-w:X, bx=[x0,Y-h,x0+w,Y+h*.25]; if(!free(bx)) continue; placed.push(bx);
      const tx=el('text',{x:r1(X),y:r1(Y),class:'rl','text-anchor':a,'data-own':v.id},g); tx.textContent=o.name.toUpperCase(); el('tspan',{class:'cnt',dx:5},tx).textContent=M.own;
      el('title',{},tx).textContent=`${o.name}: ${pl(M.own,'wine')} with no smaller area`; break;}}
  for(const it of live){if(!it.s) continue; const t=it.name+'  '+(cnt(it)), w=t.length*fs*.56, h=fs*1.2, [x,y]=it.s, b=it.bb;
    const tries=it.dot?[[x+10,y+4,'start'],[x-10,y+4,'end'],[x,y-11,'middle'],[x,y+h+8,'middle']]
      :[[x,y+fs*.35,'middle'],[x,y-8,'middle'],[x,y+h+4,'middle'],[x+12,y+fs*.35,'start'],[x-12,y+fs*.35,'end'],[x+8,y-8,'start'],[x-8,y-8,'end'],[x+8,y+h+4,'start'],[x-8,y+h+4,'end'],[x+20,y-14,'start'],[x+20,y+h+10,'start'],[x-20,y-14,'end'],[x-20,y+h+10,'end']];
    if(it===live[0]) tries.push([x,y+fs*.35,'middle','force']);   // the busiest place always gets its name
    for(const [X,Y,a,force] of tries){const x0=a==='middle'?X-w/2:a==='end'?X-w:X, bx=[x0,Y-h,x0+w,Y+h*.25]; if(!force&&!free(bx)) continue;
      placed.push(bx); const tx=el('text',{x:r1(X),y:r1(Y),'font-size':fs,'text-anchor':a,[it.own?'data-own':'data-id']:it.id},g); tx.textContent=it.name; const s=el('tspan',{class:'cnt',dx:4},tx); s.textContent=cnt(it); break;}}
  if(v.id!=='world'){   // the countries around, for bearings
    const here=v.id.split('/')[0], own=GEO.places[here]?.name;
    for(const c of WORLD.countries){if(c.n===own) continue; const s=scr(c.l); if(!s) continue; const t=c.n.toUpperCase(), w=t.length*10*.62, bx=[s[0]-w/2,s[1]-10,s[0]+w/2,s[1]+3];
      if(!free(bx)) continue; placed.push(bx); el('text',{x:r1(s[0]),y:r1(s[1]),class:'cl','text-anchor':'middle'},g).textContent=t;}}
  for(const o of v.others||[]){const s=o.l&&scr(o.l); if(!s) continue; const w=o.n.length*11*.5, bx=[s[0]-w/2,s[1]-9,s[0]+w/2,s[1]+3];   // their names, small, where there is room
    if(!free(bx)) continue; placed.push(bx); el('text',{x:r1(s[0]),y:r1(s[1]),class:'ol','text-anchor':'middle'},g).textContent=o.n;}
}
const ease=k=>k<.5?4*k*k*k:1-Math.pow(-2*k+2,3)/2;
function setWorld(o){M.world.style.opacity=o; M.world.style.display=o>0?'':'none';}
async function fly(v,par){
  const g=buildView(v,par), old=[...M.layers.children].filter(x=>x!==g), a=M.cam, b=camFor(v);
  M.view=v; M.par=par; restyle(); M.lab.replaceChildren();
  const wa=+M.world.style.opacity||0, wb=needWorld(b,v)?1:0; setWorld(Math.max(wa,.001));
  let dl=b.lon-a.lon; dl=((dl+540)%360)-180;
  const zr=Math.abs(Math.log(b.R/a.R)), ms=Math.min(1900,900+zr*160);
  M.busy=true; g.style.opacity=0;
  await new Promise(res=>{const t0=performance.now(); const step=t=>{const k=Math.min(1,(t-t0)/ms), e=ease(k);
    M.cam=camOf(a.lon+dl*e,a.lat+(b.lat-a.lat)*e,Math.exp(Math.log(a.R)+(Math.log(b.R)-Math.log(a.R))*e));
    const fi=Math.min(1,Math.max(0,(e-.15)/.6)); g.style.opacity=fi; for(const o of old) o.style.opacity=1-fi; setWorld(Math.max(.001,wa+(wb-wa)*e));
    draw(); k<1?requestAnimationFrame(step):res();}; requestAnimationFrame(step);});
  for(const o of old) dropView(o); M.cam=b; setWorld(wb); g.style.opacity=1; M.busy=false; draw();
}
async function intro(b){   // on load the globe comes in from far away, turning on its axis, and settles facing home
  const a=camOf(b.lon+300,b.lat-20,b.R*.05), ms=3600, out=k=>1-Math.pow(1-k,3);
  M.busy=true; M.svg.style.opacity=0;
  await new Promise(res=>{const t0=performance.now(); const step=t=>{const k=Math.min(1,(t-t0)/ms), z=ease(Math.min(1,k*1.15)), sp=out(k);
    M.cam=camOf(a.lon+(b.lon-a.lon)*sp,a.lat+(b.lat-a.lat)*sp,Math.exp(Math.log(a.R)+(Math.log(b.R)-Math.log(a.R))*z));
    M.svg.style.opacity=Math.min(1,k*5); draw(); k<1?requestAnimationFrame(step):res();}; requestAnimationFrame(step);});
  M.cam=b; M.svg.style.opacity=''; M.busy=false; draw();
}
function mapSize(){const w=M.box.clientWidth||360, h=Math.round(Math.max(320,Math.min(w*.95,innerHeight*.62))); M.W=w; M.H=h;
  M.svg.setAttribute('viewBox',`0 0 ${w} ${h}`); M.svg.setAttribute('height',h); M.ocean.setAttribute('cx',w/2); M.ocean.setAttribute('cy',h/2); M.rim.setAttribute('cx',w/2); M.rim.setAttribute('cy',h/2);}
function mapInit(){
  M.box=$('#map'); M.feats=[];
  M.svg=el('svg',{role:'img','aria-label':'Map of where the wines come from'});
  const defs=el('defs',{},M.svg), gr=el('radialGradient',{id:'sea',cx:'42%',cy:'38%',r:'62%'},defs);
  el('stop',{offset:'0','stop-color':'var(--ocean-hi)'},gr); el('stop',{offset:'1','stop-color':'var(--ocean)'},gr);
  M.ocean=el('circle',{class:'ocean',fill:'url(#sea)'},M.svg); M.grat=el('path',{class:'grat'},M.svg);
  M.world=el('g',{class:'world'},M.svg); for(const c of WORLD.countries){c.g=prep(c.p); addFeat(M.world,'land',c.g);}
  M.layers=el('g',{},M.svg); M.rim=el('circle',{class:'rim'},M.svg); M.lab=el('g',{class:'lab'},M.svg);
  M.box.replaceChildren(M.svg); mapSize();
  const out=document.createElement('button'); out.type='button'; out.className='zout ts-place_subtitle'; out.onclick=zoomOut; out.hidden=true; M.box.appendChild(out); M.out=out;
  // taps on places
  M.svg.addEventListener('click',e=>{if(M.dragged||M.busy) return; const t=e.target.closest('[data-id]');
    if(t){const id=t.dataset.id; const it=[...M.view.items,...(M.par?M.par.items:[])].find(i=>i.id===id); if(it) pick(it); return;}
    const b=M.svg.getBoundingClientRect(), x=(e.clientX-b.left)*M.W/b.width, y=(e.clientY-b.top)*M.H/b.height;   // a near miss: the closest place within a fingertip
    let best=null,bd=24; for(const it of M.view.items) if(it.s&&C[it.id]){const d=Math.hypot(it.s[0]-x,it.s[1]-y); if(d<bd){bd=d;best=it;}} if(best){pick(best); return;}
    const o=e.target.closest('[data-own]'); if(o){const id=o.dataset.own; set(f=>{f.p=id; f.po=f.po===id?null:id;});}});   // the place itself: its wines that go no deeper
  M.svg.addEventListener('dblclick',e=>{if(!e.target.closest('[data-id]')) zoomOut();});
  // drag to turn the globe; pinch, or ctrl and scroll, to zoom in and out around the fingers
  const P=new Map(); let g0=null, wt;
  const loc=(x,y)=>{const b=M.svg.getBoundingClientRect(); return [(x-b.left)*M.W/b.width,(y-b.top)*M.H/b.height];};
  const geoAt=(cam,s)=>unpt(cam,(s[0]-M.W/2)/cam.R,(M.H/2-s[1])/cam.R);
  const mid=()=>{const v=[...P.values()], x=v.reduce((t,p)=>t+p[0],0)/v.length, y=v.reduce((t,p)=>t+p[1],0)/v.length;
    return [loc(x,y),v.length>1?Math.hypot(v[0][0]-v[1][0],v[0][1]-v[1][1]):0];};
  const begin=()=>{const [s,d]=mid(); g0={cam:M.cam,s,d,geo:geoAt(M.cam,s),flat:P.size===1&&M.view.id==='world'&&!zoomed()};};   // the whole globe at its start size only turns, so the page still scrolls over it
  M.svg.addEventListener('pointerdown',e=>{if(M.busy) return; P.set(e.pointerId,[e.clientX,e.clientY]); if(P.size===1) M.dragged=false; begin();});
  M.svg.addEventListener('pointermove',e=>{if(!P.has(e.pointerId)||M.busy||!g0) return; P.set(e.pointerId,[e.clientX,e.clientY]);
    let [s,d]=mid();
    if(P.size===1){if(!M.dragged&&Math.hypot(s[0]-g0.s[0],s[1]-g0.s[1])<6) return; if(g0.flat&&e.pointerType==='touch') s=[s[0],g0.s[1]];}
    if(!M.dragged){M.dragged=true; M.lab.replaceChildren(); try{M.svg.setPointerCapture(e.pointerId);}catch(_){}}
    look(g0.geo,s,P.size>1&&g0.d?clampR(g0.cam.R*d/g0.d):g0.cam.R,g0.cam);});
  const up=e=>{if(!P.delete(e.pointerId)) return; if(P.size) begin(); else {g0=null; if(M.dragged) settle();}};
  M.svg.addEventListener('pointerup',up); M.svg.addEventListener('pointercancel',up);
  M.svg.addEventListener('wheel',e=>{if(!e.ctrlKey) return; e.preventDefault(); if(M.busy) return;   // a trackpad pinch arrives as ctrl and scroll
    const s=loc(e.clientX,e.clientY); M.lab.replaceChildren(); look(geoAt(M.cam,s),s,clampR(M.cam.R*Math.exp(-Math.max(-50,Math.min(50,e.deltaY))*.01)),M.cam);
    clearTimeout(wt); wt=setTimeout(settle,250);},{passive:false});
  // keep the browser from zooming the page when two fingers are on the map (iOS)
  M.svg.addEventListener('touchmove',e=>{if(e.touches.length>1) e.preventDefault();},{passive:false});
  for(const t of ['gesturestart','gesturechange']) M.svg.addEventListener(t,e=>e.preventDefault());
}
const baseR=()=>camFor(M.view).R, zoomed=()=>M.cam.R>baseR()*1.03;
function clampR(R){const b=baseR(), w=M.view.id==='world'; return Math.min(b*(w?14:8),Math.max(b*(w?.8:.5),R));}
function look(geo,s,R,cam0){   // the camera at size R that keeps the point geo under the screen point s
  let c=geo&&unpt(camOf(geo[0],geo[1],R),(M.W/2-s[0])/R,(s[1]-M.H/2)/R); if(!c) c=[cam0.lon,cam0.lat];
  M.cam=camOf(c[0],Math.max(-80,Math.min(80,c[1])),R); if(M.view.id!=='world') setWorld(needWorld(M.cam,M.view)?1:0); draw();
}
function touchMode(){M.svg.style.touchAction=M.view.id==='world'&&!zoomed()?'pan-y':'none';}   // below the world, a finger moves the map every way
async function settle(){   // after a gesture: zoomed in on one place goes a level down, pinched well out goes a level up, smaller than the start springs back
  if(M.busy||!M.view) return; const v=M.view, b=camFor(v);
  if(v.id!=='world'&&M.cam.R<b.R*.75){zoomOut(); return;}
  if(M.cam.R>b.R*1.03&&await deeper()) return;
  if(M.busy||M.view!==v) return;
  if(M.cam.R<b.R) glide(v.id==='world'?camOf(M.cam.lon,Math.max(-60,Math.min(70,M.cam.lat)),b.R):b); else {labels(); touchMode();}
}
async function deeper(){   // the place whose extent fills most of the screen, nearest the middle, if it clearly leads, has its own map and the zoom is most of the way to it
  const hd=Math.hypot(M.W,M.H)/2, sc=[];
  for(const f of M.feats) if(f.it&&!f.sib&&!f.it.own&&C[f.it.id]&&f.on()&&f.el.getAttribute('d')){const bb=f.el.getBBox();
    const x0=Math.max(0,bb.x), x1=Math.min(M.W,bb.x+bb.width), y0=Math.max(0,bb.y), y1=Math.min(M.H,bb.y+bb.height); if(x1<=x0||y1<=y0) continue;
    const a=(x1-x0)*(y1-y0)/(M.W*M.H), d=Math.hypot((x0+x1)/2-M.W/2,(y0+y1)/2-M.H/2)/hd; sc.push([f.it,a,a*(1-d*.8)]);}
  sc.sort((p,q)=>q[2]-p[2]); const [best,area,score]=sc[0]||[];
  if(!best||area<.2||(sc[1]&&sc[1][2]*1.3>score)||viewFor(best.id)!==best.id) return false;
  const cv=await view(best.id); if(!cv||M.cam.R<camFor(cv).R*.6) return false;
  set(f=>{f.p=best.id;}); return true;
}
async function glide(b,ms=500){
  const a=M.cam; let dl=b.lon-a.lon; dl=((dl+540)%360)-180; M.busy=true; M.lab.replaceChildren();
  await new Promise(res=>{const t0=performance.now(); const step=t=>{const k=Math.min(1,(t-t0)/ms), e=ease(k);
    M.cam=camOf(a.lon+dl*e,a.lat+(b.lat-a.lat)*e,Math.exp(Math.log(a.R)+(Math.log(b.R)-Math.log(a.R))*e)); if(M.view.id!=='world') setWorld(needWorld(M.cam,M.view)?1:0);
    draw(); k<1?requestAnimationFrame(step):res();}; requestAnimationFrame(step);});
  M.cam=b; M.busy=false; draw(); labels(); touchMode();
}
function zoomOut(){if(M.busy||!M.view) return; const v=M.view; if(v.id==='world'){if(zoomed()) glide(camFor(v)); else if(S.f.p) set(f=>{f.p=null;}); return;} set(f=>{f.p=v.parent==='world'?null:v.parent;});}
let want=null;
async function mapShow(){
  want=place(); if(M.going) return; M.going=true;
  try{
    while(true){const p=want, v=await view(viewFor(p))||await view('world'), par=v.parent?await view(v.parent):null;
      M.leaf=p!==v.id&&p!=='world'?p:null;
      if(!M.view){const b=camFor(v); buildView(v,par); M.view=v; M.par=par; setWorld(needWorld(b,v)?1:0); restyle();
        if(v.id==='world'&&!matchMedia('(prefers-reduced-motion: reduce)').matches) await intro(b); else {M.cam=b; draw();}}
      else if(M.view.id!==v.id) await fly(v,par);
      if(want===p) break;}
    restyle(); labels();
    const v=M.view; M.out.hidden=v.id==='world'; M.out.textContent='‹ '+(v.parent==='world'?'The world':GEO.places[v.parent]?.name||'Back');
    touchMode();
  } finally {M.going=false;}
}
async function pick(it){
  if(M.busy||!C[it.id]) return;
  if(S.f.p===it.id){set(f=>{f.p=M.view.id==='world'?null:M.view.id;}); return;}   // tap the chosen place again to widen back out
  set(f=>{f.p=it.id;});
}
function renderOrigin(){
  const f=S.f, p=place(), vid=viewFor(p), inP=base('p'); C={}; M.inP=inP;
  for(const id in GEO.places) C[id]=0; for(const w of inP) for(const id of w.place) C[id]=(C[id]||0)+1;
  const chain=[]; let id=vid; while(id&&id!=='world'){chain.unshift(id); id=GEO.places[id]?.parent;}
  const leaf=p!==vid&&p!=='world'?p:null;
  const crumbs=[['world','The world'],...chain.map(i=>[i,GEO.places[i].name]),...(leaf?[[leaf,GEO.places[leaf]?.name]]:[])];
  $('#crumbs').innerHTML=crumbs.map(([i,n],k)=>k===crumbs.length-1?`<b>${esc(n)}</b>`:`<a href="${link('home',{...f,p:i==='world'?undefined:i})}">${esc(n)}</a>`).join(' › ');
  const kids=Object.entries(GEO.places).filter(([i,x])=>x.parent===vid).map(([i,x])=>[i,x.name]);
  const st=kids.filter(([i])=>C[i]||p===i).sort((a,b)=>C[b[0]]-C[a[0]]||a[1].localeCompare(b[1])).map(([i,n])=>[i,n,C[i],p===i]);
  let top='';   // the place itself first: all its wines, then the ones that go no deeper when some do
  if(vid!=='world'){const tot=C[vid]||0, own=inP.filter(w=>isOwn(w,vid)).length, nm=esc(GEO.places[vid].name);
    top=`<button type="button" class="step ts-ladder_step whole" data-whole aria-pressed="${p===vid&&!f.po}">${nm}<b>${tot}</b></button>`
      +(own&&own<tot?`<button type="button" class="step ts-ladder_step" data-only aria-pressed="${f.po===vid}">${nm} only<b>${own}</b></button>`:'');}
  $('#places').innerHTML=steps('place',st).replace('<div class="steps">','<div class="steps">'+top);
  const wb=$('#places [data-whole]'), ob=$('#places [data-only]');
  if(wb) wb.onclick=()=>set(f=>{f.p=vid; f.po=null;}); if(ob) ob.onclick=()=>set(f=>{f.p=vid; f.po=f.po===vid?null:vid;});
  $('#places').querySelectorAll('[data-k]').forEach(b=>b.onclick=()=>{const id=b.dataset.v; if(S.f.p===id) set(f=>{f.p=vid==='world'?null:vid;}); else if(C[id]) set(f=>{f.p=id;});});
  $('#mapNote').textContent=vid==='world'?'Tap a country or pinch to zoom in. Drag to turn the globe.':'Tap a place to go in. Drag to move. Pinch to zoom in or out.';
  mapShow();
}
// ---------- the home page: the choices
const sec=(cls,head,note,body)=>`<section class="row ${cls||''}"><div class="head"><h2 class="ts-section_head">${head}</h2>${note?`<span class="ts-caption">${note}</span>`:''}</div>${body}</section>`;
const svgIcon=id=>`<svg viewBox="0 0 64 64" aria-hidden="true">${VIS.icons[id]||''}</svg>`;
function iconCells(k,items,circle){
  return items.map(([v,label,n,state])=>{const on=state==='in', no=state==='out';
    const art=circle?`<span class="circ">${svgIcon(v)}</span>`:svgIcon(v);
    return `<button type="button" class="ic${no?' no':''}" data-k="${k}" data-v="${esc(v)}" aria-pressed="${on}"${!n&&!on&&!no?' disabled':''} title="${esc(label)}: ${pl(n,'wine')}">${art}<span class="lab ${circle?'ts-pairing_label':'ts-flavor_label'}">${esc(label)}</span><span class="n ts-caption">${n}</span></button>`;}).join('');
}
function steps(k,items,swatch){
  return '<div class="steps">'+items.map(([v,label,n,on])=>`<button type="button" class="step ts-ladder_step" data-k="${k}" data-v="${esc(v)}" aria-pressed="${!!on}"${!n&&!on?' disabled':''}>${swatch?`<span class="sw" style="background:${swatch(v)}"></span>`:''}${esc(label)}<b>${n}</b></button>`).join('')+'</div>';
}
const shown={};   // groups opened with "Show all"
function moreLink(k,all,top){return all>top&&!shown[k]?`<button type="button" class="link ts-caption more" data-more="${k}">Show all ${all}</button>`:'';}
function live(list){const keep=list.filter(x=>x[2]||x[3]); return [keep,list.length-keep.length];}   // a long list keeps only the choices that still match
const gone=n=>n?`<p class="note ts-caption">${n} more with no matches</p>`:'';
function windowRow(){   // one year: the wines that are in their drinking window then
  const by=base('yr'), n=Y1-Y0+1, yc=new Array(n).fill(0); for(const w of by) if(w.win) for(let y=Math.max(Y0,w.win[0]);y<=Math.min(Y1,w.win[1]);y++) yc[y-Y0]++;
  const mx=Math.max(1,...yc), y=S.f.yr?+S.f.yr:null, ticks=[Y0,...Array.from({length:n},(_,i)=>Y0+i).filter(t=>t%20===0&&t-Y0>(Y1-Y0)*.1&&Y1-t>(Y1-Y0)*.1),Y1];
  return sec('','Drinking window',`<span id="winLab">${y?winLabel(y):'Any year'}</span>`,
`<div class="wnd${y?'':' off'}"><div class="hist">${yc.map((c,i)=>`<i style="height:${c?Math.max(8,Math.round(c/mx*100)):0}%" class="${Y0+i===y?'in':''}${Y0+i===YEAR?' now':''}" title="${Y0+i}: ${pl(c,'wine')} ready"></i>`).join('')}</div>
<div class="range"><input id="wy" type="range" min="${Y0}" max="${Y1}" value="${y||YEAR}" aria-label="Year to open the bottle"></div>
<div class="ticks ts-window_tick">${ticks.map(t=>`<span style="left:${(t-Y0)/(Y1-Y0)*100}%">${t}</span>`).join('')}<span class="now ts-window_tick_now" style="left:${(YEAR-Y0)/(Y1-Y0)*100}%">NOW</span></div></div>
<p class="note ts-caption">Pick the year you want to open a bottle. You'll see the wines that are ready then. <button type="button" class="link" id="readyNow">Ready now</button>${y?' · <button type="button" class="link" id="anyYear">Any year</button>':''}</p>`);
}
function wireWindow(){
  const wy=$('#wy'), bars=[...document.querySelectorAll('.hist i')];
  const show=()=>{const y=+wy.value; $('#winLab').textContent=winLabel(y); $('.wnd').classList.remove('off'); bars.forEach((x,i)=>x.classList.toggle('in',Y0+i===y)); return y;};
  wy.oninput=show; wy.onchange=()=>{const y=show(); set(f=>{f.yr=String(y);});};
  $('#readyNow').onclick=()=>set(f=>{f.yr=String(YEAR);});
  const any=$('#anyYear'); if(any) any.onclick=()=>set(f=>{f.yr=null;});
}
function renderChoices(){
  const f=S.f; let html='';
  // type
  const bs=tally(base('style'),w=>[w.style]); const styles=[...new Set(CAT.items.map(w=>w.style))].sort((a,b)=>(bs.get(b)||0)-(bs.get(a)||0));
  html+=sec('','Type','',`<div class="icons">${styles.map(s=>{const n=bs.get(s)||0,on=(f.style||[]).includes(s); return `<button type="button" class="ic bottle" data-k="style" data-v="${s}" aria-pressed="${on}"${!n&&!on?' disabled':''}>${VIS.bottles[s]}<span class="lab ts-flavor_label">${esc(CAT.items.find(w=>w.style===s).styleName)}</span><span class="n ts-caption">${n}</span></button>`;}).join('')}</div>`);
  html+=windowRow();
  // taste profile
  html+=sec('','Taste profile','1 is low, 5 is high',`<div class="dots">${SCALES.map(([k,name,field])=>{const b=tally(base(k),w=>w.struct&&w.struct[field]?[String(w.struct[field])]:[]); const sel=f[k]||[];
    return `<div class="drow"><span class="ts-dot_label">${name}</span><span class="d">${[1,2,3,4,5].map(i=>{const n=b.get(String(i))||0,on=sel.includes(String(i)); return `<button type="button" class="dot" data-k="${k}" data-v="${i}" aria-pressed="${on}" title="${name} ${i}: ${pl(n,'wine')}"${!n&&!on?' disabled':''}></button>`;}).join('')}</span><span class="v ts-dot_value">${sel.length?[...sel].sort().join(', '):'Any'}</span></div>`;}).join('')}</div>`);
  // aromas: tap once to want it, twice to leave it out
  const all=base(null), ta=tally(all,w=>w.aromas.map(a=>a[0])); const ain=f.ain||[], aout=f.aout||[];
  const ar=[...new Set(CAT.items.flatMap(w=>w.aromas.map(a=>a[0])))].map(a=>[a,CAT.aromaNames[a]||a,ain.includes(a)?all.length:(ta.get(a)||0),ain.includes(a)?'in':aout.includes(a)?'out':null])
    .sort((a,b)=>(!!b[3]-!!a[3])||b[2]-a[2]||a[1].localeCompare(b[1]));
  const [arL,arG]=live(ar); html+=sec('','Aromas and flavors','Tap once to look for it, twice to leave it out',`<div class="icons">${iconCells('aroma',shown.ain?arL:arL.slice(0,24))}</div>${moreLink('ain',arL.length,24)}${gone(arG)}`);
  // pairings
  const tp=tally(base('pair'),w=>w.pairs.map(p=>p[0])); const pr=[...new Set(CAT.items.flatMap(w=>w.pairs.map(p=>p[0])))].map(x=>[x,CAT.pairNames[x]||x,tp.get(x)||0,(f.pair||[]).includes(x)?'in':null]).sort((a,b)=>(!!b[3]-!!a[3])||b[2]-a[2]);
  const [prL,prG]=live(pr); html+=sec('','Suggested pairings','',`<div class="icons">${iconCells('pair',shown.pair?prL:prL.slice(0,16),true)}</div>${moreLink('pair',prL.length,16)}${gone(prG)}`);
  // grape, with the blend bar's colors
  const tg=tally(base('grape'),w=>w.grapes); const gr=[...new Set(CAT.items.flatMap(w=>w.grapes))].map(g=>[g,g,tg.get(g)||0,(f.grape||[]).includes(g)]).sort((a,b)=>(b[3]-a[3])||b[2]-a[2]||a[1].localeCompare(b[1]));
  const [grL,grG]=live(gr); html+=sec('','Grape','',steps('grape',shown.grape?grL:grL.slice(0,18),g=>GCOL[g])+moreLink('grape',grL.length,18)+gone(grG));
  // vintage
  const tv=tally(base('vint'),w=>[String(w.vintage||'NV')]); const vs=[...new Set(CAT.items.map(w=>String(w.vintage||'NV')))].sort().map(x=>[x,x,tv.get(x)||0,(f.vint||[]).includes(x)]);
  html+=sec('','Vintage','',steps('vint',vs));
  const box=$('#choices'); box.innerHTML=html;
  box.querySelectorAll('[data-k]').forEach(b=>{const k=b.dataset.k,x=b.dataset.v;
    b.onclick=k==='aroma'?()=>set(f=>{const ain=f.ain||(f.ain=[]),aout=f.aout||(f.aout=[]);
      if(ain.includes(x)){ain.splice(ain.indexOf(x),1); aout.push(x);} else if(aout.includes(x)) aout.splice(aout.indexOf(x),1); else ain.push(x);}):()=>toggle(k,x);});
  box.querySelectorAll('[data-more]').forEach(b=>b.onclick=()=>{shown[b.dataset.more]=true; renderChoices();});
  wireWindow();
}
const GCOL={};
// ---------- the results page
function chosenSteps(){
  const f=S.f, out=[];
  if(f.p) out.push(['p',null,(GEO.places[f.p]?.name||'')+(f.po?' only':'')]);
  for(const s of f.style||[]) out.push(['style',s,CAT.items.find(w=>w.style===s)?.styleName||s]);
  if(f.yr) out.push(['yr',null,winLabel(f.yr)]);
  for(const [k,name] of SCALES) if(f[k]) out.push([k,null,`${name} ${[...f[k]].sort().join(', ')}`]);
  for(const a of f.ain||[]) out.push(['ain',a,CAT.aromaNames[a]||a]);
  for(const a of f.aout||[]) out.push(['aout',a,'No '+(CAT.aromaNames[a]||a).toLowerCase()]);
  for(const x of f.pair||[]) out.push(['pair',x,'With '+(CAT.pairNames[x]||x).toLowerCase()]);
  for(const g of f.grape||[]) out.push(['grape',g,g]);
  for(const x of f.vint||[]) out.push(['vint',x,x]);
  if(S.q) out.push(['q',null,`“${S.q}”`]);
  return out;
}
function wineRow(w){
  const st=winState(w), when=st==='ready'?`<span class="ready">Ready</span>, drink by ${w.win[1]}`:st==='later'?`Best from ${w.win[0]}`:st==='soon'?`<span class="soon">Drink soon</span>`:'';
  const inner=`<span class="b">${VIS.bottles[w.style]||''}</span><span><span class="t ts-fact_value">${esc(w.title)}</span><span class="s ts-body">${esc((w.sub||w.where).replace(/,\s*(\d{4}|NV)$/,''))}</span><span class="p ts-dot_label">${esc(w.producer)}</span><span class="m ts-caption">${[when,esc(w.where)].filter(Boolean).join(' · ')}</span></span>
<span class="y"><span class="ts-fact_value">${w.vintage||'NV'}</span><small class="ts-caption">${pl(w.qty,'bottle')}</small></span>`;
  return w.id?`<a class="wine" href="sheets/${w.id}/">${inner}</a>`:`<div class="wine" title="No pour sheet yet">${inner}</div>`;
}
function renderResults(){
  const list=base(null), bottles=list.reduce((s,w)=>s+w.qty,0);
  const sorters={vintage:(a,b)=>(a.vintage||9999)-(b.vintage||9999),'vintage-desc':(a,b)=>(b.vintage||0)-(a.vintage||0),name:(a,b)=>a.title.localeCompare(b.title),
    ready:(a,b)=>((winState(a)==='ready'?0:1)-(winState(b)==='ready'?0:1))||((a.win?a.win[1]:9999)-(b.win?b.win[1]:9999))};
  const groupOf=w=>w.place.filter(i=>GEO.places[i]).slice(0,2).map(i=>GEO.places[i].name).join(' · ')||w.country||'Elsewhere';
  const ch=chosenSteps();
  let html=`<nav class="res-nav"><a class="res-back ts-place_subtitle" href="${link('home')}">‹ Back to the map and your choices</a></nav><section class="row res-head"><h2 class="ts-page_title">${pl(list.length,'wine')}</h2><p class="ts-place_subtitle" style="color:var(--soft)">${pl(bottles,'bottle')}${ch.length?' that match your choices':' in the cellar'}</p>
${ch.length?`<div class="chosen">${ch.map(([k,v,l],i)=>`<button type="button" class="step ts-ladder_step" aria-pressed="true" data-i="${i}" title="Remove this choice">${esc(l)} ✕</button>`).join('')}</div>`:''}
<div class="res-tools"><span></span><select id="sort" aria-label="Sort" class="ts-body"><option value="place">By place</option><option value="vintage">Oldest first</option><option value="vintage-desc">Youngest first</option><option value="ready">Ready to drink</option><option value="name">By name</option></select></div></section>`;
  if(!list.length) html+='<p class="empty ts-body">Nothing matches. Remove a choice above.</p>';
  else if(S.sort==='place'){
    const g=new Map(); for(const w of [...list].sort((a,b)=>a.where.localeCompare(b.where)||a.title.localeCompare(b.title))){const k=groupOf(w); if(!g.has(k)) g.set(k,[]); g.get(k).push(w);}
    html+=[...g].sort((a,b)=>a[0].localeCompare(b[0])).map(([k,ws])=>`<h3 class="group ts-eyebrow">${esc(k.toUpperCase())}</h3>`+ws.map(wineRow).join('')).join('');
  } else html+=[...list].sort(sorters[S.sort]).map(wineRow).join('');
  const r=$('#results'); r.innerHTML=html; $('#sort').value=S.sort;
  $('#sort').onchange=e=>{S.sort=e.target.value; history.replaceState(null,'',link('wines')); render();};
  r.querySelectorAll('.chosen .step').forEach(b=>b.onclick=()=>{const [k,v]=ch[+b.dataset.i]; if(k==='q'){S.q=''; $('#q').value='';} set(f=>{if(v==null) delete f[k]; else f[k]=f[k].filter(x=>x!==v);});});
}
// ---------- search, with suggestions as you type
let SUG=[];
function buildSuggestions(){
  const add=(kind,label,n,act,sub)=>SUG.push({kind,label,n,act,sub,key:fold(label)});
  for(const [id,x] of Object.entries(GEO.places)){const n=CAT.items.filter(w=>w.place.includes(id)).length; if(n) add('Place',x.name,n,()=>set(f=>{f.p=id;}),x.parent!=='world'?GEO.places[x.parent]?.name:'');}
  const cnt=(arr)=>{const m=new Map(); for(const k of arr) m.set(k,(m.get(k)||0)+1); return m;};
  for(const [g,n] of cnt(CAT.items.flatMap(w=>w.grapes))) add('Grape',g,n,()=>set(f=>{f.grape=[...new Set([...(f.grape||[]),g])];}));
  for(const [p,n] of cnt(CAT.items.map(w=>w.producer))) add('Producer',p,n,()=>{S.q=p; $('#q').value=p; history.replaceState(null,'',link(S.page)); render();});
  for(const [s,n] of cnt(CAT.items.map(w=>w.style))) add('Type',CAT.items.find(w=>w.style===s).styleName,n,()=>set(f=>{f.style=[...new Set([...(f.style||[]),s])];}));
  for(const [a,n] of cnt(CAT.items.flatMap(w=>[...new Set(w.aromas.map(x=>x[0]))]))) add('Aroma',CAT.aromaNames[a]||a,n,()=>set(f=>{f.ain=[...new Set([...(f.ain||[]),a])]; if(f.aout) f.aout=f.aout.filter(x=>x!==a);}));
  for(const [x,n] of cnt(CAT.items.flatMap(w=>[...new Set(w.pairs.map(p=>p[0]))]))) add('Pairing',CAT.pairNames[x]||x,n,()=>set(f=>{f.pair=[...new Set([...(f.pair||[]),x])];}));
  for(const w of CAT.items) if(w.id) add('Wine',`${w.title} ${w.vintage||'NV'}`,0,()=>{location.href=`sheets/${w.id}/`;},w.producer);
}
const KIND_ORDER=['Place','Grape','Producer','Type','Aroma','Pairing','Wine'];
function suggest(q){
  const k=fold(q.trim()); if(k.length<2) return [];
  const score=s=>s.key.startsWith(k)?0:s.key.split(/[\s'’\-]+/).some(t=>t.startsWith(k))?1:s.key.includes(k)?2:9;
  return SUG.map(s=>[score(s),s]).filter(x=>x[0]<9).sort((a,b)=>a[0]-b[0]||KIND_ORDER.indexOf(a[1].kind)-KIND_ORDER.indexOf(b[1].kind)||b[1].n-a[1].n||a[1].label.localeCompare(b[1].label)).slice(0,8).map(x=>x[1]);
}
function hi(label,q){const f=fold(label), i=f.indexOf(fold(q.trim())); if(i<0) return esc(label); const n=q.trim().length; return esc(label.slice(0,i))+'<b>'+esc(label.slice(i,i+n))+'</b>'+esc(label.slice(i+n));}
function wireSearch(){
  const q=$('#q'), box=$('#sugg'); let list=[],act=-1;
  const close=()=>{box.hidden=true; act=-1; q.setAttribute('aria-expanded','false');};
  const paint=()=>{box.innerHTML=list.map((s,i)=>`<li role="option" id="sg${i}" aria-selected="${i===act}" data-i="${i}"><span class="sl ts-body">${hi(s.label,q.value)}${s.sub?`<small class="ts-caption"> ${esc(s.sub)}</small>`:''}</span><span class="sk ts-caption">${s.kind}${s.n?' · '+s.n:''}</span></li>`).join('');
    box.hidden=!list.length; q.setAttribute('aria-expanded',String(!!list.length)); if(act>-1) q.setAttribute('aria-activedescendant','sg'+act); else q.removeAttribute('aria-activedescendant');};
  const choose=s=>{close(); if(s.kind!=='Producer'){q.value=''; S.q='';} q.blur(); s.act();};
  q.addEventListener('input',()=>{list=suggest(q.value); act=-1; paint(); if(!q.value.trim()&&S.q){S.q=''; history.replaceState(null,'',link(S.page)); render();}});   // the text only filters on Enter
  q.addEventListener('keydown',e=>{
    if(e.key==='ArrowDown'&&list.length){e.preventDefault(); act=(act+1)%list.length; paint();}
    else if(e.key==='ArrowUp'&&list.length){e.preventDefault(); act=(act-1+list.length)%list.length; paint();}
    else if(e.key==='Enter'){e.preventDefault(); if(act>-1) choose(list[act]); else {close(); S.q=q.value.trim(); history.replaceState(null,'',link(S.page)); render(); q.blur();}}
    else if(e.key==='Escape') close();});
  box.addEventListener('pointerdown',e=>{const li=e.target.closest('li'); if(li){e.preventDefault(); choose(list[+li.dataset.i]);}});
  q.addEventListener('blur',()=>setTimeout(close,120));
  q.addEventListener('focus',()=>{if(q.value.trim().length>1){list=suggest(q.value); paint();}});
}
// ---------- the dock and routing
function dock(){
  const list=base(null), bottles=list.reduce((s,w)=>s+w.qty,0), any=Object.keys(S.f).length||S.q;
  $('#nMatch').textContent=pl(list.length,'wine'); $('#nSub').textContent=`${pl(bottles,'bottle')}${any?' match':' in the cellar'}`;
  const show=$('#show'); show.href=link(S.page==='wines'?'home':'wines'); show.textContent=S.page==='wines'?'‹ Back to the map':'Show the wines';
  show.setAttribute('aria-disabled',S.page==='home'&&!list.length); $('#clear').hidden=!any;
}
async function render(){
  $('#home').hidden=S.page!=='home'; $('#results').hidden=S.page!=='wines';
  if(S.page==='home'){renderOrigin(); renderChoices();} else renderResults();
  dock();
}
async function route(){const was=S.page; readHash(); $('#q').value=S.q; await render(); if(was!==S.page) window.scrollTo(0,0);}
async function main(){
  [CAT,GEO,VIS,WORLD]=await Promise.all(['data/catalog.json','geo/index.json','data/visuals.json','geo/world.json'].map(u=>fetch(u).then(r=>r.json())));
  for(const w of CAT.items){w.place=GEO.wine_place[w.k]||[]; w.text=fold([w.title,w.name,w.producer,w.where,w.sub,w.grapes.join(' '),w.aromas.map(a=>a[1]).join(' '),w.vintage].join(' '));}
  const ws=CAT.items.filter(w=>w.win); if(ws.length){Y0=Math.min(...ws.map(w=>w.win[0])); Y1=Math.max(...ws.map(w=>w.win[1]));}
  let fb=0; for(const g of [...new Set(CAT.items.flatMap(w=>w.grapes))]) GCOL[g]=VIS.grape[g]||VIS.grape.fallback[fb++%VIS.grape.fallback.length];
  buildSuggestions(); mapInit(); wireSearch();
  window.addEventListener('hashchange',route);
  $('#clear').onclick=()=>{S.f={}; S.q=''; $('#q').value=''; history.replaceState(null,'',link(S.page)); render();};
  let rt,lw=innerWidth; window.addEventListener('resize',()=>{clearTimeout(rt); rt=setTimeout(()=>{if(innerWidth===lw&&M.W) return; lw=innerWidth; mapSize(); if(M.view&&!M.busy){M.cam=camFor(M.view); draw(); labels();}},200);});
  route();
}
main();
})();

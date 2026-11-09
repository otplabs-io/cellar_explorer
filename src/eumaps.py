#!/usr/bin/env python3
"""Build a zone store for the zones engine (src/mapzones.py) from the EU PDO boundaries, for countries outside Italy.
Usage: python src/eumaps.py <profile node>     e.g. spain, spain/canary-islands, germany
Writes data/cache/eu-maps/<store>/ in the same layout as Orazio Campoli's Italian files, so mapzones.py draws both:
  _national.json   every PDO in the store: slug, name, tier, region
  _zones.json      the PDO shapes, one feature each
  _region.json     the border of panel 1 (NUTS 2 regions), kind "border"
  _places.json     empty: towns are found among the communes
  _communes.json   commune outlines (LAU) around the region
  _locator.json    the countries around it, for the locator
  <slug>.json      one PDO at full detail, with its communes from the PDO table

Sources (all cached under data/cache/):
  eu-pdo/   Candiago et al. 2022, the EU wine PDO boundaries (figshare collection 5877659), CC0. Each PDO is the union of
            the communes in its rules, so a zone is drawn by whole commune: part of each commune may be outside it.
  gisco/    Eurostat GISCO LAU 2021, NUTS 2021 and countries 2020, 1:1 million. Non-commercial use, credited
            "© EuroGeographics for the administrative boundaries".
The profile's "map" block gives "eu": {"country", "nuts", "tiers", "default_tier", "locator_bbox"} and "region_slug"."""
import csv,json,os,re,sqlite3,struct,sys,unicodedata
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from shapely import wkb
from shapely.geometry import shape,mapping,box
from shapely.ops import transform,unary_union
from pyproj import Transformer
import profiles
ROOT=os.path.dirname(HERE); CA=os.path.join(ROOT,'data','cache')
def slug(s): return re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip('-')
def gpkg_geom(b):
    """A GeoPackage geometry blob: 'GP', version, flags, srs id, an envelope sized by the flags, then WKB."""
    flags=b[3]; env={0:0,1:32,2:48,3:48,4:64}[(flags>>1)&7]
    return wkb.loads(bytes(b[8+env:]))
def write(p,obj):
    os.makedirs(os.path.dirname(p),exist_ok=True); json.dump(obj,open(p,'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
def fc(feats): return {'type':'FeatureCollection','features':feats}
def feat(g,**props): return {'type':'Feature','properties':props,'geometry':mapping(g)}
def rnd(g,n=5):
    return shape(json.loads(json.dumps(mapping(g)),parse_float=lambda x:round(float(x),n)))
def unit_zone(z,cs,RS,src,note):
    """A zone with no published boundary, drawn as the union of admin units (communes, departments, municipalities)."""
    want={u.lower() for u in z['units']}; hit=[c for c in cs if c['properties']['name'].lower() in want]
    assert len(hit)==len(want),f"{z['name']}: units not found: {want-{c['properties']['name'].lower() for c in hit}}"
    g=unary_union([shape(c['geometry']) for c in hit]).buffer(0); s=z.get('slug',slug(z['name']))
    p=dict(slug=s,name=z['name'],official_name=z['name'],tier=z.get('tier','Region'),source=src,note=z.get('note',note),communes=[{'name':c['properties']['name']} for c in hit])
    return s,g,p
def latin():
    """The Latin name eAmbrosia registers for each PDO, by dossier number (the PDO dataset's PDOid)."""
    import glob
    out={}
    for f in glob.glob(os.path.join(ROOT,'regions','sources','eu-*.json')):
        for e in json.load(open(f,encoding='utf-8'))['entries']:
            if e.get('file'): out[e['file']]=e['name']
    return out
def main(node):
    M=profiles.for_node(node)['map']; RS=M['region_slug']; OUT=os.path.join(CA,'eu-maps')
    zones=[];nat=[]
    def add(s,g,p):
        zones.append(feat(g,**{k:p[k] for k in ('slug','name','tier')})); nat.append(dict(slug=s,name=p['name'],tier=p['tier'],region=RS,crus=False,**({'pdo_id':p['pdo_id']} if p.get('pdo_id') else {})))
        write(os.path.join(OUT,RS,f'{s}.json'),feat(g,**p))
    if 'admin' in M:   # outside the EU: geoBoundaries outlines, and zones built from admin units
        A=M['admin']; GB=os.path.join(CA,'geoboundaries')
        bf=json.load(open(os.path.join(GB,A['border']['file']),encoding='utf-8'))['features']
        reg=unary_union([shape(f['geometry']) for f in bf if not A['border'].get('names') or f['properties']['shapeName'] in A['border']['names']]).buffer(0)
        assert not reg.is_empty
        near=box(*reg.bounds).buffer(.3); cs=[]
        for f in json.load(open(os.path.join(GB,A['communes']['file']),encoding='utf-8'))['features']:
            g=shape(f['geometry'])
            if g.intersects(near): cs.append(feat(rnd(g.buffer(0)),com_istat_code=f['properties'].get('shapeID'),name=f['properties']['shapeName']))
        inside=[c for c in cs if shape(c['geometry']).representative_point().within(reg.buffer(.01))]
        for z in A['zones']: add(*unit_zone(z,inside,RS,A['source'],A['note']))
        bbox=A['locator_bbox']
    else:
        E=M['eu']; bbox=E['locator_bbox']
        to4326=Transformer.from_crs(3035,4326,always_xy=True).transform
        # panel 1's border: the NUTS 2 regions the profile names
        nuts=json.load(open(os.path.join(CA,'gisco','NUTS_RG_01M_2021_4326_LEVL_2.geojson'),encoding='utf-8'))['features']
        NU={f['properties']['NUTS_ID']:shape(f['geometry']) for f in nuts}
        nl=E['nuts'] if E['nuts']!='all' else [n for n in NU if n.startswith({'GR':'EL'}.get(E['country'],E['country'])) and box(*E['locator_bbox']).contains(NU[n].representative_point())]   # 'all': the country's regions inside the locator box
        reg=unary_union([NU[n] for n in nl]).buffer(0)
        # the PDOs of the country that touch the region
        T={r['PDOid']:r for r in csv.DictReader(open(os.path.join(CA,'eu-pdo','PDO_EU_id.csv'),encoding='utf-8-sig'))}
        db=sqlite3.connect(os.path.join(CA,'eu-pdo','EU_PDO.gpkg'))
        for pid,blob in db.execute('select PDOid,Shape from EU_PDO'):
            if E['country'] not in pid.split('-')[1].split('+'): continue   # its own PDOs, and those it shares (PDO-BE+NL-02172)
            g=gpkg_geom(blob).buffer(0).simplify(25)   # metres, in EPSG:3035
            g=transform(to4326,g)
            if not g.intersects(reg): continue
            r=T[pid]; name=r['PDOnam'].split(' / ')[0].strip(); name=E.get('names',{}).get(name,name)   # 'names' gives Latin names for Greek PDOs
            if re.search(r'[\u0370-\u03ff\u0400-\u04ff]',name): name=latin().get(pid,name)   # else the register's own Latin name (Bulgaria, Cyprus)
            s=E.get('slugs',{}).get(name,slug(name)) or slug(pid)
            tier=E.get('tiers',{}).get(name,E.get('default_tier','PDO'))
            add(s,g,dict(slug=s,name=name,official_name=r['PDOnam'],tier=tier,pdo_id=pid,registration=r['Registration'],
                   source='EU wine PDO boundaries, Candiago et al. 2022 (CC0), from the communes in the PDO rules',
                   note='Shaded by commune: part of each commune may be outside the zone.',
                   communes=[{'name':n} for n in r['Municip_nam'].split('/') if n and n!='na']))
        for z in E.get('extra_zones',[]):   # a PGI, which the PDO dataset leaves out, drawn from NUTS regions
            g=unary_union([NU[n] for n in z['nuts']]).buffer(0); s=z.get('slug',slug(z['name']))
            add(s,g,dict(slug=s,name=z['name'],official_name=z['name'],tier=z.get('tier','PGI'),source='Eurostat GISCO NUTS 2021 regions',note=z['note'],communes=[]))
        # commune outlines around the region
        near=box(*reg.bounds).buffer(.3); cs=[]
        if E.get('communes_gb'):   # Greece: GISCO's LAU are small communities in Greek script, so use geoBoundaries' municipalities
            for f in json.load(open(os.path.join(CA,'geoboundaries',E['communes_gb']),encoding='utf-8'))['features']:
                g=shape(f['geometry'])
                if g.intersects(near): cs.append(feat(rnd(g.buffer(0)),com_istat_code=f['properties'].get('shapeID'),name=f['properties']['shapeName']))
        for f in [] if E.get('communes_gb') else json.load(open(os.path.join(CA,'gisco','LAU_RG_01M_2021_4326.geojson'),encoding='utf-8'))['features']:
            if f['properties']['CNTR_CODE']!=E['country'] or not f.get('geometry'): continue
            g=shape(f['geometry'])
            if not g.intersects(near): continue
            n=re.sub(r',\s*(Stadt|Landeshauptstadt|Kreisstadt|Stadt der.*|Hansestadt|Universitätsstadt|Statutarstadt)$','',f['properties']['LAU_NAME']).strip()
            n=re.sub(r"^(.*), (El|La|Los|Las|Els|Les|O|A|Os|As)$",r"\2 \1",n)   # Spain and Portugal list 'Rosario, El': print 'El Rosario'
            n=re.sub(r"^(.*), (L')$",r"\2\1",n)
            cs.append(feat(rnd(g.simplify(.0002)),com_istat_code=f['properties']['GISCO_ID'],name=n))
    write(os.path.join(OUT,RS,'_zones.json'),fc(zones))
    write(os.path.join(OUT,RS,'_region.json'),fc([feat(rnd(reg),kind='border')]))
    write(os.path.join(OUT,RS,'_places.json'),fc([]))
    write(os.path.join(OUT,RS,'_communes.json'),fc(cs))
    # the locator: countries in a box around the region, merged
    bb=box(*bbox)
    cn=[shape(f['geometry']).intersection(bb) for f in json.load(open(os.path.join(CA,'gisco','CNTR_RG_01M_2020_4326.geojson'),encoding='utf-8'))['features']]
    write(os.path.join(OUT,RS,'_locator.json'),fc([feat(rnd(unary_union([g for g in cn if not g.is_empty]).simplify(.02)))]))
    # the national list, merged across stores so a wine in one store can find its zone by slug
    np_=os.path.join(OUT,'_national.json'); old=json.load(open(np_,encoding='utf-8'))['appellations'] if os.path.exists(np_) else []
    keep=[a for a in old if a['region']!=RS]; write(np_,{'appellations':keep+nat})
    print(f'{RS}: {len(zones)} zones, {len(cs)} communes, written to data/cache/eu-maps/{RS}/')
if __name__=='__main__': main(sys.argv[1])

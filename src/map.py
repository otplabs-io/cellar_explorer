#!/usr/bin/env python3
"""Draw a wine's draft map with the engine its region profile names. Usage: python src/map.py wines/<id>/wine.json
  parcels   src/mapgen.py      vineyard parcels (Burgundy)
  villages  src/mapvillages.py whole villages ranked by the appellation (Champagne)
  appellations src/mapappellations.py appellation land with an estate pin (Bordeaux)
  avas      src/mapavas.py     nested American Viticultural Areas (Napa)
  zones     src/mapzones.py    delimited denomination zones with their crus (Italy)"""
import os,runpy,sys
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import profiles,records
ENGINES={'parcels':'mapgen.py','villages':'mapvillages.py','appellations':'mapappellations.py','avas':'mapavas.py','zones':'mapzones.py'}
eng=profiles.for_wine(records.load_wine(sys.argv[1]))['map'].get('engine')
if eng not in ENGINES: sys.exit(f'No map engine for this region yet (profile engine: {eng}). See design-system/maps.md.')
sys.argv=[ENGINES[eng]]+sys.argv[1:]; runpy.run_path(os.path.join(HERE,ENGINES[eng]),run_name='__main__')

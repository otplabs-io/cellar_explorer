PY ?= .venv/bin/python
WINE ?= wines/la-boudriotte-2019/wine.json
.PHONY: setup verify verify-map map sheet gallery layout check-icons pairings regions check-wines import catalog queue app serve restock-check publish rollback test-app service atlas
setup:
	python3.13 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/playwright install chromium
verify:
	$(PY) tests/verify_reference.py
verify-map:
	$(PY) tests/verify_map_source.py
map:
	$(PY) src/map.py $(WINE)
sheet:
	$(PY) src/render.py $(WINE) $(if $(YEAR),--year $(YEAR))
gallery:
	$(PY) design-system/build_gallery.py
layout:
	$(PY) tests/extract_layout.py
check-icons:
	$(PY) design-system/check_icons.py
pairings:
	$(PY) design-system/derive_pairings.py

regions:
	$(PY) regions/build_tree.py
	$(PY) regions/render_tree_page.py
check-wines:
	$(PY) regions/check_wines.py
import:
	$(PY) src/inventory.py import $(CSV)
	$(PY) src/catalog.py
catalog:
	$(PY) src/catalog.py
queue:
	$(PY) src/work.py status
	$(PY) src/work.py list --ready --limit 20
# Try the app with the example wines. Writes a local inventory, so run it only before you add your own.
EXAMPLES = la-boudriotte-2019 krug-grande-cuvee-172 ridge-estate-cabernet-2021 guido-porro-gianetto-2018 lopez-de-heredia-bosconia-2008
demo:
	$(PY) src/inventory.py import examples/cellar-export.csv
	for w in $(EXAMPLES); do $(PY) src/render.py wines/$$w/wine.json || exit 1; done
	$(PY) src/catalog.py
	$(PY) src/site.py
app:
	$(PY) src/site.py
serve:
	$(PY) src/serve.py
restock-check:
	$(PY) src/restock.py check $(CSV)
publish:
	$(PY) src/restock.py publish
rollback:
	$(PY) src/restock.py rollback
test-app:
	$(PY) tests/app_smoke.py $(or $(URL),http://localhost:8800/)

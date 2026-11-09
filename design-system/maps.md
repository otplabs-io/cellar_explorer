# Map kit

The rules for every "Where it grows" map. The La Boudriotte map in `wines/la-boudriotte-2019/map.svg` is the approved example and is locked. `src/mapgen.py` draws drafts for new wines with these rules, and reads every color, type size, stroke and panel size from `tokens.json` (`map`, `subregion`, `plot_tints`, `map_type`, `map_stroke`, `map_mark`, `map_layout`).

## Layout

The map is one 736 by 752 SVG with three linked levels.

| Level | Origin | Size | Shows |
|---|---|---|---|
| 1 Region | 0, 0 | 292 by 330 | The whole region's wine communes, shaded by subregion. Department lines dashed. Country locator, 56 by 58, at lower left |
| 2 Subregion | 304, 0 | 432 by 330 | Every commune. Wine communes tinted, vineyard land gold, the target village coral, Grand Cru plum |
| 3 Village | 0, 340 | 736 by 412 | Village, Premier Cru and Grand Cru land. The target in coral, its parent cru outlined in teal |
| Plot inset | 514, 458 | 212 by 146 | The target's plots, numbered, with a key of hectares and a total. Shrinks by 14 px a row past six plots, to 90 at least |

- **Linked levels.** A coral rectangle on each level shows the area of the next, with a numbered badge. Each panel title has a matching ink number.
- **Plot inset.** Add it when a vineyard name covers more than one plot. With one plot, the inset zooms in on the target instead.
- **Legend.** Lives under the inset key, in two columns.

## Projection

Use an equal-area or conformal national projection. France uses Lambert-93 (EPSG:2154). Name the projection for each new country here before drawing.

## Color roles

All in `tokens.json` under `map`.

| Role | Token | Value |
|---|---|---|
| Target vineyard | `target` fill with an `ink` outline | `#D9482B` |
| Parent cru | `parent_outline`, outline only | `#1F6F73` |
| Grand Cru | `grand_cru` | `#7C4F75` |
| Premier Cru | `premier_cru` | `#E9B44C` |
| Village land | `village` | `#F4DDA6` |
| Neighbor vineyards | `neighbor_vineyard` | `#E5DCC6` |
| Target village | `target_commune_paper` fill, heavy `ink` border | `#FFFDF8` |
| Other villages | `border`, dashed | `#6F675A` |
| Land, paper | `land`, `paper` | `#F4EFE3`, `#FCFAF5` |
| Plots inside the target | `plot_tints`, in order | 8 coral steps |

**Region color** comes from a fixed subregion palette (`subregion`). A new region gets its own palette in the same lightness range as Burgundy's six. Check it next to the target coral, which must stay the hottest thing on the map.

## Labels

- **Halo:** Doubled text. A copy stroked in the ground color sits under the filled copy. Never `paint-order`, which some renderers drop.
- **Halo width:** 2.6 for most labels, 3 for panel titles, commune names, neighbors and the parent cru.
- **Leaders:** 0.7 px with a 1.5 px dot at the feature.
- **Size floor:** 9.5 px. Only the scale bar label is that small.
- **Never:** clipped, overlapping, or crossing the target.
- **Target text** uses `target_text`, the darker coral, for contrast.
- **Tuning:** `mapgen.py` places labels on its own, then `overrides` in `wine.json` fixes the ones that collide. Look at `map.draft.png` every time.
- **Parcel overrides** (`mapgen.py`): `this_wine` [x, y]; `panel2` {village: [x, y, anchor]}; `neighbors` {NAME: [x, y]}, with [-500, -500] hiding a label clipped at the frame; `commune_label` [x, y]; `parent_label` [x, y]; `no_parent` true; `town_left` [town names]. Wine-level keys: `inset_title`, `map_labels`.
- **Village wines:** when `target` equals `appellation`, the coral is the village-level land only, and the inset lists no climats.

## Always include

- A scale bar on levels 2 and 3, and a north arrow.
- A country locator on level 1.
- A legend with only the classes present.
- The map sources in the credits footer, with the orientation-only line.

**Known gap:** `mapgen.py` always draws the Grand Cru and Premier Cru legend entries, even on a map without them. Fix it when the first such wine comes up.

## Precision tiers

From `docs/REGIONS.md`. The map must not imply more than the tier supports.

| Tier | Example | Target drawn as |
|---|---|---|
| Parcel | Burgundy named climats | The vineyard polygon and its plots |
| Appellation | Pauillac, Pomerol | Appellation area, with a pin for the estate |
| Village | Champagne | Whole villages shaded by rank, the wine's villages numbered |
| AVA | Napa sub-AVAs | AVA polygon, nested |
| Zone | Barolo, Brunello | The denomination's delimited zone, with its sub-zones and named vineyards |
| Region | Anything without data | A pin on a regional map |

An estate pin needs its own source for each producer. The parcel and village tiers are built.

## Engines

`make map WINE=...` runs `src/map.py`, which picks the engine the wine's region profile names in `map.engine`.

| Engine | File | Tier | Used by |
|---|---|---|---|
| `parcels` | `src/mapgen.py` | Parcel | Burgundy |
| `villages` | `src/mapvillages.py` | Village | Champagne |
| `appellations` | `src/mapappellations.py` | Appellation, with an estate pin | Bordeaux, the Rhône, the Loire, Provence, Languedoc-Roussillon, the Jura |
| `avas` | `src/mapavas.py` | AVA | Every US AVA |
| `zones` | `src/mapzones.py` | Zone, with crus | Italy, and the EU PDOs elsewhere (France where no other engine draws) |

New engines draw with `src/mapkit.py`. `mapgen.py` keeps its own copies of the same helpers, because its La Boudriotte draft was proven byte-identical.

### The appellation engine

For wines that name an appellation and an estate. Level 1 shades the department's wine communes by area (Left Bank, Right Bank...), from each commune's main appellation. Level 2 shades the wine's area by appellation: inside the panel, a commune takes the most specific appellation that holds at least a quarter as much land as its largest, because broad names such as Haut-Médoc overlap the communal ones. Both say in their subtitle that they shade whole communes. Level 3 draws INAO's delimited land for the wine's appellation and its neighbours, commune borders, and a pin for the estate, whose source goes in the producer's `sources.md`. The wine gives `map_appellation` and `map_estate`. The profile maps the Côtes de Bordeaux sub-names, which the tree doesn't hold, to tree nodes in `aliases`.

### The AVA engine

For nested American Viticultural Areas. Level 1 is the outer AVA (North Coast) over its counties, with the region AVA (Napa Valley) inside it. Level 2 is the region AVA with every AVA in it, the wine's in coral. Level 3 is the wine's AVA with its neighbours and the county line, and a right column with the key and legend. California Albers (EPSG:3310). An estate gets a pin only with a source; otherwise the wine's `map_estate_note` says where the source puts it and why there's no pin. Cain Five 2017 has no pin: neither OpenStreetMap nor the Census geocoder knows the winery.

### The zone engine

For Italy, where each DOCG, DOC and IGT is a delimited zone. The shapes come from Orazio Campoli's Italian Wine Map, which Chris may use for personal, non-commercial sheets (his permission, 2026-11-05). Each zone file names its original source (Regione Piemonte, Regione Toscana, Regione del Veneto, the EU PDO dataset), and the region profile's credit line repeats it. Commune outlines are ISTAT's via openpolis. The files are cached under `data/cache/oc-maps/`.

- **Level 1:** the region, with its zones shaded by level (DOCG gold, DOC light gold) and the wine's zone in coral. Region-wide zones such as Piemonte DOC or Langhe DOC would cover everything, so the profile lists them in `broad` and they aren't drawn. Area labels come from the profile's `areas`. A locator shows Italy.
- **Level 2:** the wine's area (the Langhe and Roero), with the area's zones labelled and the wine's in coral.
- **Level 3:** the wine's zone in gold, with its sub-zones (Valpolicella Classico) in light gold and its named vineyards (Barolo's MGAs, Etna's contrade) outlined in white. An MGA is many vineyard parcels, so the engine closes the gaps between them (`cru_merge_m`, 60 m) to draw one outline. The wine's cru, given in `map_cru`, is coral; a cru that is only a named place (Montosoli) is a pin. Contrade whose lines aren't published are dashed.

The wine gives `map_zone` (the slug in Orazio's data, such as `barolo-docg`), and optionally `map_cru`, `map_estate` and `map_estate_note`. An approximate zone (Etna, drawn from its altitude bands; Aglianico del Vulture, by commune) says so in `map_estate_note`. A wine labelled with a zone that covers a whole region (Toscana IGT, Sicilia DOC) is mapped at the zone where its vines grow, with `map_subtitle` and `map_estate_note` saying so. `map_area` picks the panel 2 area by name when the zone isn't in one.

### The zone engine outside Italy

Every EU country outside Italy uses the same engine on a store (France only where no other engine draws) that `src/eumaps.py` builds from the EU wine PDO boundaries (Candiago et al. 2022, CC0). Run `python src/eumaps.py <country profile>` once per store (Madeira and the Azores have their own, from their island profiles); it writes `data/cache/eu-maps/<region_slug>/` in Orazio's layout, so the panels draw the same way. A profile sets `zone_store: "eu"` and an `eu` block: the country code, the NUTS 2 regions for panel 1's border (or `"all"`: the country's regions inside the locator box), a locator box, and the level of each PDO by name (`tiers`, with `default_tier`). Commune outlines are Eurostat GISCO's LAU 2021 (parishes in Portugal), and region borders are NUTS 2021, credited "© EuroGeographics for the administrative boundaries", non-commercial use only.

- **Every EU zone is a whole-commune shape.** The PDO polygon is the union of the communes in its rules, so part of each commune may be outside the zone. Panel 3's subtitle says "drawn by commune".
- **Levels.** Spain shades DOCa (Rioja, Priorat) and DO. Single-estate Vinos de Pago are one commune each, so they get tier `Pago` and aren't drawn. Germany's small single-vineyard PDOs (the Uhlen sites, Monzinger Niederberg, Würzburger Stein-Berg, Bürgstadter Berg) get tier `Lage` and aren't drawn. Germany, Austria, Hungary and Portugal shade their regions in one color.
- **Zooming in.** A region as long as the Mosel would make panel 3 unreadable, so a wine can set `map_fit: "communes"` (with `map_fit_pad` in metres) to frame the communes in `map_communes` instead of the whole zone.
- **Broad zones.** Cava covers parts of several regions, so the Spain profile lists it in `broad`. Panel 2 then frames the wine's area, not the zone's whole spread.
- **No sub-zones or named vineyards.** The EU data has neither, so a Mosel Einzellage or a Rioja zone is shown by outlining its commune in coral.

### Zones built from admin units

Where no wine-zone data exists (Lebanon, Mendoza, the Western Cape), a profile's `admin` block names a geoBoundaries border file, a communes file, and each zone as a list of admin units (`units`). `src/eumaps.py` unions them into a zone, so the zones engine draws it like any other. The note and credit say how each is drawn: Lebanon by district, Mendoza by department, Wine of Origin districts by municipality. In the EU store, `extra_zones` adds a PGI from NUTS regions (Attiki). `names` gives Latin names for Greek PDOs, and `communes_gb` swaps GISCO's Greek-script communities for geoBoundaries municipalities.

### The village engine

For regions that rank whole villages. Everything regional is in the profile's `map` block: departments, the appellation area file, the rank list, towns, area labels and panel titles. The wine gives `map_villages` (tree ids, each with the grape it gives), `map_title`, `map_key_title` and `map_villages_note`.

- **Level 1:** the appellation's villages in the village tint, ranked villages in plum and gold, department lines dashed, area labels anchored on the villages the tree places in each area, and a coral dot for the wine.
- **Level 2:** every ranked village with room around it, and the wine's villages in coral.
- **Level 3:** the wine's villages, numbered, with village names where they fit. A label that would collide is dropped. The right column holds the key (rank and grape per village) and a legend of only the classes in view.
- **Merged villages.** Some ranked villages now belong to a larger commune: Aÿ, Mareuil-sur-Ay and Bisseuil to Aÿ-Champagne, Louvois and Tauxières to Val de Livre, Oger, Vertus and Voipreux to Blancs-Coteaux, and Coligny to Val-des-Marais. The engine draws each one from its cadastral parcels, whose prefix is the old village code from INSEE, and gives the gaps between parcels to the nearest village.
- **No vineyards.** Champagne's parcel delimitation isn't in the INAO open data, so the map shows villages only. Its legend and title say so.
- The appellation area is commune-based and covers 619 villages.

### Places with no hand-set layout (2026-11-06)

Covers now run country-wide (see the project notes), so most places an engine draws have no layout tuned for them. The engines fall back to rules, and `src/mapproof.py` proves every covered place draws with labels clear (`maplint`).

- **Zone engine, panel 2.** A zone in none of the profile's `areas` gets its own area: the zone and the nearest zones of a shaded tier within 15 km (up to `auto_area_zones`, 7), titled "Around <zone>". Zones that hold most of it, or that it holds, are left out, as broad ones are. Each name takes the first clear spot around its point, off the wine's zone and off panel 3's box and badge; a neighbour with no clear spot is left out.
- **Appellation engine, panel 2.** An appellation the profile's `panel2_appellations` doesn't list is drawn the same way: its own communes in coral, framed with 2.5 km around them, the other communes by their main appellation. It shows the first of the names INAO lists ("Côtes de Bourg, Bourg et Bourgeais" prints as Côtes de Bourg).
- **AVA engine.** A state with no profile takes its FIPS code from the tree and the `states` table in `united-states.json`, and any other state its AVA crosses from the AVA's record. An AVA with no AVA around it is drawn over its state and the states that border it. The default spots for "This wine", the region name and the wine's own AVA name try the usual place first, then the first clear spot around their point.
- **Appellation engine, panel 1 and the key.** Without a hand-set spot, "This wine" takes the first spot clear of the towns, area names, title and locator. Town names in panel 2 count as taken too. A profile can list an appellation in `panel2_auto` to give it this layout even though `panel2_appellations` names it, where the hand-set one crowds its name (Coteaux d'Aix-en-Provence, Les Baux de Provence, Côtes du Roussillon Villages).
- **Any engine.** In these layouts the wine's own key entry wraps onto two lines when it is too long. The fixed entries never wrap, and no entry wraps in a hand-set layout, so existing maps redraw as before. Labels placed by default keep off the coral box of the next panel and its badge.
- **Big appellations.** Panel 3's frame takes its bounds from the outermost parcels only (`buf_bounds` in `src/mapkit.py`), since buffering every parcel of the Côtes du Rhône took 20 minutes and gigabytes. `MAP_CHECK_BOUNDS=1` buffers it all too and checks they agree; they did on all 52 existing appellation maps. `src/mapproof.py` stops a draw past 4 GB (`MAPPROOF_MAXGB`) or 40 minutes (`MAPPROOF_TIMEOUT`), since this Mac has 8 GB.
- **Commune labels in another script.** GISCO names Bulgarian and Cypriot communes in Cyrillic and Greek, which the sheet's fonts don't carry, so those profiles set `commune_labels: false`. Their zones take the Latin name the EU register gives.

## Print

- Strokes that must print are 0.7 px or more. The 0.4 and 0.5 px white edges between shapes are separators and may drop out on a home printer.
- No clip paths or filters.

## Locked maps

Once a draft is clean, copy `map.draft.svg` to `map.svg`. That file is the map from then on. Nothing regenerates it. `reference-pipeline/` rebuilds La Boudriotte's map only to prove the source data, on Linux, into its own `output/` folder.

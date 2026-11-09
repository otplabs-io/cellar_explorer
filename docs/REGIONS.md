# Regions plan

**One layout, one component library, no template per region.** Adding a region should take one small profile file and at most one new component. If a region needs its own layout, something is split wrong.

Chris's hierarchy of regions arrived on 2026-11-03. It's kept word for word in `regions/hierarchy.md` and is the frame of the tree. `regions/fetch_sources.py` pulls the official lists of wine places (the EU register, the US AVAs, and the registers of Australia, New Zealand, Argentina and Canada) and reference lists for the rest. `regions/build_tree.py` adds every registered place the frame doesn't name, under the right parent, and writes `regions/tree.json` (the inheritance tree) and `regions/hierarchy-full.md` (the same tree to read). Every officially registered name must be in the tree, and the build fails the check if one is missing. Sources and judgment calls are in `regions/sources.md`. Each node inherits from its parent and states only what differs.

## Placing a wine

Every `wines/<id>/wine.json` has a `region` block. `make check-wines` fails if any wine's place doesn't resolve.

```json
"region": {"node": "france/chassagne-montrachet", "tier": "Premier Cru", "vineyard": "La Boudriotte", "placed_by": "label"}
```

- **node:** the deepest place in the tree that the label supports. A country is fine when that's all the label says. Use the place the label names, not where the vines grow: Tignanello is Toscana IGT even though its vineyards sit in Chianti Classico.
- **tier:** the rank the label states within that place, such as Premier Cru. When the node lists its tiers, the tier must be one of them.
- **vineyard:** a name below the appellation, which the tree doesn't hold: a Burgundy climat, a lieu-dit, a German Einzellage, a Barolo MGA. Grand cru appellations such as Chambertin are nodes, so they go in `node`, not here.
- **grown_in:** optional. Where the vines grow, when a source says so and it differs from the label's place.
- **placed_by:** `label`, `source` (a cited source other than the label) or `judgment`. The check also notes a place that rests on a secondary source. A sheet's map and story must not claim more precision than this supports.

**Ids.** Each place's id is its country plus its own name, such as `france/chassagne-montrachet`; a second place of the same name adds its parent, such as `italy/barolo-in-barolo` for the commune inside the Barolo DOCG. `regions/ids.json` pins every id, so a place keeps its id when the tree is rebuilt or the place moves. When a place is renamed, merged or split, add the old id to `regions/redirects.json`. Never reuse a retired id.

**Places that span two parents,** such as Walla Walla Valley (Washington and Oregon) or Corton (three villages), have one parent in the tree by convention. Describe them from their own data, not their parent's.

## Layers

1. **Library:** tokens, icons, charts, map engine. No wine facts.
2. **Layout:** the front stays nearly the same for every wine. The back holds a map, a signature graphic and three notes.
3. **Profiles:** main story, quality ladder, map levels and vocabulary per node.
4. **Records:** region, producer, vintage and bottle, stored separately and reused.

Blocks must drop out cleanly. Pomerol has no official classification, so a sheet for it can't show a ladder.

## Starting point by region

| Region | Main story | Quality ladder | Signature graphic |
|---|---|---|---|
| Burgundy | Vineyard | Grand Cru to Regional | Plots inside the vineyard name |
| Médoc | Château | 1855 classification | Blend bar, first vs. second wine |
| Right Bank | Estate and soil | Saint-Émilion's own, none for Pomerol | Blend bar, soil cross-section |
| Champagne | Producer and style | Grower vs. house, vintage vs. non-vintage | Dosage scale, base and reserve years |
| Napa | Producer and sub-AVA | None | Nested AVAs, hillside vs. valley floor |
| Rhône | Blend, north vs. south | Regional to Cru | Blend bar |
| Rioja | Aging | Crianza to Gran Reserva | Barrel and bottle aging timeline |

This table was reasoned from wine knowledge, not checked against sources. Verify each ladder before building it.

## Region profiles

Built on 2026-11-04. A profile is a JSON file at `regions/profiles/<stable id>.json`. `src/profiles.py` gives a wine its profile: `default.json`, then every profile on the way down the tree to the wine's node, each overriding the one above. A profile states only what differs from its parent. Built so far: `default`, `france/burgundy`, `france/champagne`, `france/bordeaux` and `france/left-bank`. Bordeaux sets the château heading, the Bordeaux bottle, the blend bar and the appellation map; the Left Bank adds the 1855 ladder. Right Bank wines and second wines have no `level`, so their story row reflows. `united-states` sets the winery heading, and `united-states/napa-valley` adds the `ava_nest` signature (the wine's AVA inside the AVAs that hold it, with the year each was established), the Bordeaux bottle, the blend bar and the AVA map.

**Covers, from 2026-11-06.** A profile's `map.covers` says which places its engine can draw; a wine is ready for `/bottle` only inside it. Covers now sit as high as is true. A country, state or region has no map of its own, so its profile lists its children in `covers` (every EU country, the United States and its states, and each French or Italian region with its own engine): everything under it is ready, but a wine labelled only "Italy" or "California" is not. A place the data can't draw has its own small profile with `"covers": []` and a `$why`. `src/mapproof.py exclude` writes both kinds from the proof's results, and `docs/MAP_COVERAGE.md` lists what stays out. Layer 2, a region's ladder, signature and tuned map layout, is still built when its first wine arrives.

| Key | What it sets | Burgundy | Champagne |
|---|---|---|---|
| `story.signature` | The graphic at the left of the story row, or `null` to reflow to two columns | `quality_ladder` with Burgundy's four tiers | `dosage_scale` with the EU sugar terms |
| `story.labels` | Headings for the story columns | The family, The vintage | The house, The vintage |
| `place` | The back page title and subtitle | "From all of Burgundy down to one vineyard" | "From all of Champagne down to the villages in the bottle" |
| `serve_cells` | The cells after the drinking window: heading, icon, content key | Serve, Decant | Serve, The glass |
| `map` | The map engine, its precision tier, its data and the map credit line | `parcels` | `villages` |
| `bottle_shape`, `facts_blend` | The bottle drawn, and whether the facts row leads with a blend bar | (theme's) | (theme's) |

A wine's `content` can still override a label (`ladder_title`, `family_title`, `vintage_title`, `place_title`, `place_subtitle`), and a producer record can set `story_title`, for a grower in a region of houses. `make check-wines` checks the record against its profile: the wine's `level` must be one of the signature's tiers or terms, and a village map needs `map_villages`.

**Champagne, as built.** The rank belongs to the village, not the vineyard. The cahier des charges names 17 grand cru and 42 premier cru villages, and the tree now holds all 59 with their rank and INSEE commune code (`regions/sources/fr-champagne-crus.json`). A label's rank is a node's `tier` for a single-village wine, such as Bonnaire's Cramant Grand Cru. A house blend sits at `france/champagne` with no tier, and its sheet uses the dosage scale as its signature instead of a ladder.

## Map precision tiers

| Tier | Example | Target drawn as |
|---|---|---|
| Parcel | Burgundy named climats | The vineyard polygon and its plots |
| Appellation | Pauillac, Pomerol | Appellation area, with a pin for the estate |
| Village | Champagne | Whole villages shaded by rank, the wine's villages numbered. Built |
| AVA | Napa sub-AVAs | AVA polygon, nested |
| Region | Anything without data | A pin on a regional map |

Never imply more precision than the data has. Estate pins need their own source for each producer.

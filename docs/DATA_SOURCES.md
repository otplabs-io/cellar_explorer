# Data sources

| Data | Source | Pinned to | Licence as stated | Used for |
|---|---|---|---|---|
| AOC vineyard boundaries | INAO delimitations, through [24eme/opendatawine](https://github.com/24eme/opendatawine) | commit `9d65ed62f55097faf109bcd4c44805f596981bda` | INAO data: Licence Ouverte | All vineyard shapes |
| Commune and department outlines | [gregoiredavid/france-geojson](https://github.com/gregoiredavid/france-geojson) | commit `5d34ee6d0140c29f785fdb047d9329f1aab58833` in `mapgen.py`. The vendored reference copy came from `master` on 2026-11-02 | Check the repo's licence before any public use | Borders |
| Côte de Beaune village shapes in the locked map | [kyusik-yang/playground-terroir](https://github.com/kyusik-yang/playground-terroir), derived from INAO | commit `6b034fcb7f98a9f341e6aa7c1033a305a83eea67` | Check the repo's licence before any public use | Panel 2 of the locked map, and elevation and aspect cross-checks |
| Fonts | Poppins and Nunito Sans through @fontsource 5.2.5 | vendored | SIL Open Font License | All type |
| Champagne appellation area | INAO, through opendatawine: `delimitation_aoc/51/51030/00055.geojson` | the same commit as above | Licence Ouverte | Level 1 and the "Champagne village" class. Every commune folder holds the whole area, which follows commune borders |
| Champagne cadastral parcels | Etalab cadastre, through opendatawine: `delimitation_aoc/51/<commune>/cadastre-parcelles.json` | the same commit | Licence Ouverte | Splitting merged communes back into their ranked villages |
| Champagne village ranks | AOC Champagne cahier des charges, 2022, chapter I, II b and c | read 2026-11-04 | Official text | `regions/sources/fr-champagne-crus.json` |
| Commune codes, old and new | INSEE, Code officiel géographique 2024 (`v_commune_2024.csv`) | read 2026-11-04 | Licence Ouverte | Matching ranked villages to communes, and merged villages to their parcels |
| Estate pins | OpenStreetMap, read through Nominatim | read 2026-11-04 | ODbL | One pin per estate, its node id in the producer's `sources.md` |
| AVA boundaries | UC Davis Library AVA Project, `avas_aggregated_files/avas.geojson` | `master`, read 2026-11-03. Pin a commit before relying on it | Described as free to use | The AVA maps and the `ava_nest` dates |
| US county outlines | US Census cartographic boundaries, through Plotly's `datasets` repository (`geojson-counties-fips.json`) | `master`, read 2026-11-04 | Census data is public domain | AVA map backgrounds |
| EU wine PDO boundaries | Candiago et al. 2022, figshare collection 5877659: `EU_PDO.gpkg` and `PDO_EU_id.csv` | downloaded 2026-11-05 to `data/cache/eu-pdo/` | CC0 | Zone shapes for Spain, Germany, Portugal, Austria and Hungary, through `src/eumaps.py` |
| Commune, region and country outlines (EU) | Eurostat GISCO: LAU 2021, NUTS 2021 level 2, countries 2020, all 1:1 million | downloaded 2026-11-05 to `data/cache/gisco/` | Non-commercial use, credited "© EuroGeographics for the administrative boundaries" | EU map backgrounds, panel 1 borders and locators |
| Admin outlines outside the EU | geoBoundaries gbOpen, commit `9469f09`: Lebanon ADM1 and ADM2 (public domain), Argentina ADM1 and ADM2 (CC BY 2.5 and CC BY 3.0 IGO, from the Instituto Geográfico Nacional), South Africa ADM1 to ADM3 (CC BY 3.0 IGO, from the Municipal Demarcation Board), Greece ADM3 (CC0) | downloaded 2026-11-05 to `data/cache/geoboundaries/` | As listed | Zones built from districts, departments and municipalities, and Greek municipality outlines |
| Sugar terms for sparkling wine | Commission Delegated Regulation (EU) 2019/33, Annex III, Part A, on EUR-Lex | read 2026-11-04 | EU law | The dosage scale |

These sheets are personal and printed at home. Confirm the licence of each source before publishing them widely. INAO's own notice says its digital boundaries are informational and that the official plans are those filed in town halls or with INAO. The sheet's footer carries an orientation-only line.

## Coverage checked so far

- **France:** The opendatawine repo returned data for Pauillac, Saint-Émilion and Pomerol, Champagne, Châteauneuf-du-Pape, Alsace and Chinon. One Rhône department code came back empty and wasn't investigated, so don't assume Beaujolais coverage until tested.
- **Bordeaux detail:** Appellation level. There are no estate parcels.
- **Chablis:** The playground-terroir notes say INAO's file names only some premier cru climats.
- **US:** [UC Davis AVA project](https://datalab.ucdavis.edu/digitizing-american-viticultural-areas/), repository `UCDavisLibrary/ava`. Described as free to use. Not downloaded or tested yet.
- **Rest of Europe:** [A geospatial inventory of wine PDOs in Europe](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9276794/). The paper wouldn't open, so its coverage, detail and licence are unconfirmed.

## Gotchas already found

- Champagne has no vineyard parcels in the INAO open data: `00055.geojson` is the appellation's commune-based area, not its vineyards. Maps there work at the village tier.
- Eight ranked Champagne villages have merged into larger communes since the rank list was written. The cadastral parcel id holds the old village's code in characters 6 to 8 (`000` for the village that kept the commune's code). `data.gouv`'s geo API doesn't return former communes, so the engine rebuilds them from parcels.
- `france-geojson` spells some communes differently from the cahier des charges: Vaudemange (Vaudemanges), Ville-Dommange (Villedommange), Villeneuve-Renneville-Chevigny (Villeneuve-Renneville), Mesnil-sur-Oger (Le Mesnil-sur-Oger).

- Some opendatawine commune folders hold stray non-AOC shapes. Gevrey-Chambertin has one named "Var", located in Provence. `mapgen.py` clips every denomination to its commune for this reason.
- Commune outlines are simplified. Vineyard parcels can cross them slightly, so the code snaps borders to parcels where parcels exist.
- Commune names must match the source spelling: `Chorey-les-Beaune`, `Monthelie`, `Flagey-Echezeaux`.
- A climat can contain other climats. La Boudriotte's 15.6 ha contains five other named plots and sits inside Morgeot's 56.4 ha. `mapgen.py` detects this nesting.

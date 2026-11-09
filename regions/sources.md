# Region sources

`regions/fetch_sources.py` pulls these lists and `regions/build_tree.py` merges them into Chris's hierarchy. Chris's hierarchy is the frame and is never changed. Every name an official list registers must be in the tree; the build checks this and reports any that are missing.

Pulled on 2026-11-03. Rerun both scripts to pick up new appellations.

## Official lists

**EU register (eAmbrosia).** Every registered wine PDO and PGI in the EU, plus a few non-EU names registered there. One list per country:
 AT 30, BE 10, BG 54, BR 1, CN 4, CY 11, CZ 13, DE 46, DK 5, ES 149, FR 440, GB 6, GR 147, HR 18, HU 44, IT 522, LU 1, MT 3, NL 21, PT 44, RO 54, SI 17, SK 10, US 2.
 Source: https://webgate.ec.europa.eu/eambrosia-api/api/geographical-indications

- **ar** (125 entries): Instituto Nacional de Vitivinicultura, Indicaciones geográficas y denominaciones de origen reconocidas y protegidas de la República Argentina (updated September 2025). https://www.argentina.gob.ar/inv/proteccion-del-origen-ig-y-doc
- **au** (115 entries): Wine Australia, Register of protected GIs: geographical indications. https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications
- **ca** (40 entries): Ontario Wine Appellation Authority (VQA Ontario) appellation pages, and Wine Growers of British Columbia, BC wine regions. https://vqaontario.ca/ontario-appellations/ ; https://winebc.com/wine-regions/
- **nz** (21 entries): IPONZ, New Zealand Geographical Indications Register (export). https://www.iponz.govt.nz/get-ip/geographical-indications/register/
- **fr-champagne-crus** (59 entries, pulled 2026-11-04): the AOC Champagne cahier des charges, homologated by the arrêté of 30 November 2022 (BO du MASA, 15 December 2022), chapter I, II b (17 grand cru villages) and c (42 premier cru villages). Commune codes from INSEE, Code officiel géographique 2024, which also gives the old code of each village that has merged into a larger commune. https://info.agriculture.gouv.fr/gedei/site/bo-agri/document_administratif-3b36a01e-8edd-4742-ade7-fbd3251816c4/telechargement
- **us-ava** (276 entries): UC Davis Library AVA Project, established American Viticultural Areas (27 CFR part 9). https://github.com/UCDavisLibrary/ava

## Reference lists, used only to place official names under a region

- **at-groups**: Wikipedia, Austrian wine (wine regions). https://en.wikipedia.org/wiki/Austrian_wine
- **es-groups**: Wikipedia, Spanish wine regions (DOPs and IGPs by autonomous community). https://en.wikipedia.org/wiki/Spanish_wine_regions
- **fr-groups**: Wikipédia, « Vin français bénéficiant d'une AOC » (classified by bassin and vignoble, after INAO). https://fr.wikipedia.org/wiki/Vin_fran%C3%A7ais_b%C3%A9n%C3%A9ficiant_d%27une_AOC
- **gr-groups**: Wikipedia, Greek wine (wine regions). https://en.wikipedia.org/wiki/Greek_wine
- **hu-groups**: Wikipedia, Hungarian wine (wine regions and sub-regions). https://en.wikipedia.org/wiki/Hungarian_wine
- **it-groups**: Wikipedia, List of Italian DOCG wines and List of Italian DOC wines (by region). https://en.wikipedia.org/wiki/List_of_Italian_DOC_wines

## Secondary lists, used where no official list could be read

These are weaker. Check a place against an official source before a sheet relies on it.

- **ch** (6 entries): Wikipedia, Swiss wine (the six regions of Swiss Wine Promotion). https://en.wikipedia.org/wiki/Swiss_wine
- **cl** (28 entries): Wikipedia, Chilean wine (wine regions, after the 2018 decree in Diario Oficial No. 42.065). https://en.wikipedia.org/wiki/Chilean_wine
- **lb** (5 entries): Wikipedia, Lebanese wine (wine-growing areas; Lebanon has no legal appellation list). https://en.wikipedia.org/wiki/Lebanese_wine
- **w-armenia** (17 entries): Wikipedia, List of wine-producing regions: Armenia. https://en.wikipedia.org/wiki/List_of_wine-producing_regions
- **w-georgia** (5 entries): Wikipedia, List of wine-producing regions: Georgia. https://en.wikipedia.org/wiki/List_of_wine-producing_regions
- **w-israel** (10 entries): Wikipedia, List of wine-producing regions: Israel. https://en.wikipedia.org/wiki/List_of_wine-producing_regions
- **w-japan** (3 entries): Wikipedia, List of wine-producing regions: Japan. https://en.wikipedia.org/wiki/List_of_wine-producing_regions
- **w-mexico** (28 entries): Wikipedia, List of wine-producing regions: Mexico. https://en.wikipedia.org/wiki/List_of_wine-producing_regions
- **w-moldova** (5 entries): Wikipedia, List of wine-producing regions: Moldova. https://en.wikipedia.org/wiki/List_of_wine-producing_regions
- **w-morocco** (3 entries): Wikipedia, List of wine-producing regions: Morocco. https://en.wikipedia.org/wiki/List_of_wine-producing_regions
- **w-north-macedonia** (3 entries): Wikipedia, List of wine-producing regions: North Macedonia. https://en.wikipedia.org/wiki/List_of_wine-producing_regions
- **w-serbia** (8 entries): Wikipedia, List of wine-producing regions: Serbia. https://en.wikipedia.org/wiki/List_of_wine-producing_regions
- **w-turkey** (39 entries): Wikipedia, List of wine-producing regions: Turkey. https://en.wikipedia.org/wiki/List_of_wine-producing_regions
- **w-ukraine** (6 entries): Wikipedia, List of wine-producing regions: Ukraine. https://en.wikipedia.org/wiki/List_of_wine-producing_regions
- **w-uruguay** (7 entries): Wikipedia, List of wine-producing regions: Uruguay. https://en.wikipedia.org/wiki/List_of_wine-producing_regions
- **za** (98 entries): Wikipedia, Wine regions of South Africa (summary of the Wine of Origin scheme). https://en.wikipedia.org/wiki/Wine_regions_of_South_Africa SAWIS, the official source, failed to load (TLS error) on 2026-11-03.

## Judgment calls

- **Champagne's cru villages by subregion.** The cahier des charges ranks villages but doesn't place them in subregions. The 17 grand cru villages sit under Montagne de Reims, Côte des Blancs or Vallée de la Marne, following Chris's hierarchy and Wine with Seth's cru list (winewithseth.com/winewiki/champagne-cru-classifications, secondary). The premier cru villages Chris didn't place wait under "Villages, subregion not yet set" (40), because no source read places them all. A grand cru village may also label its wine premier cru, so its node lists only Grand Cru.
- **Corton, Corton-Charlemagne and Charlemagne** sit under Aloxe-Corton, as Chris agreed. Their vineyards also reach into Ladoix and Pernand-Vergelesses.
- **Côte d'Or grand crus** sit under the village the French list names just before them, such as Chambertin under Gevrey-Chambertin.
- **Hand placements.** 18 French AOCs and 44 Italian DOCs had no match in the reference lists, usually because the list spells them differently. I placed each by the region in its official name or area. They are in `HAND` in `build_tree.py`.
- **Official long names** for five places Chris already had stay as alternate names on his entries: Oak Knoll District of Napa Valley, North Fork of Long Island, The Hamptons, Long Island, Conegliano Valdobbiadene - Prosecco and Collio Goriziano.
- **Combined entries** in Chris's hierarchy, such as La Mancha & Valdepeñas, take each official appellation as a child.
- **Sonoma and Mendocino AVAs** sit under Chris's county entries rather than under the North Coast AVA. AVAs inside another AVA sit under it, as the TTB records it.
- **Washington and Oregon:** AVAs in both states, such as Walla Walla Valley and Columbia Valley, sit under Washington, as in Chris's hierarchy.
- **Not placed below the country** because no source gives their parent: Germany's smaller PDOs (Monzinger Niederberg, the three Uhlen sites, Würzburger Stein-Berg, Bürgstadter Berg), Austria's Rosalia, Ruster Ausbruch and Wiener Gemischter Satz, and British Columbia's Cowichan Valley.
- **Not included:** Burgundy and Bordeaux dénominations géographiques complémentaires (such as the Bourgogne Côtes d'Auxerre names) that aren't separate AOCs, and the vineyard names (climats, lieux-dits, Einzellagen) below appellation level. A sheet names those from the wine's own record.

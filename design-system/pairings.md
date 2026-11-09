# Pairing icons: what to draw

Proposed on 2026-11-03 from Chris's cellar export. Chris approved the list the same day. The 23 new drawings are in `design-system/icons/pairing/`, all approved on 2026-11-03, and steak, mushroom and dark chocolate reuse the approved flavor drawings. `build_review.py p1 p2 p3` renders them for review.

## How the list was made

1. `cellar/cellar-2026-11-03.csv` is the CellarTracker export: 259 bottles, 213 wines. It was converted to UTF-8 with no other changes.
2. `design-system/derive_pairings.py` sorts every wine into one of 29 styles by type, region and grape, such as Left Bank Bordeaux or White Burgundy. These styles exist only to pick icons. They are not region profiles.
3. `design-system/pairing_sources.json` holds each style's classic pairings, as the source names them, with a link. Each pairing maps to one icon category.
4. The script weights each pairing by the style's bottle count, split evenly across that style's pairings, and ranks the categories. Run `make pairings` to redo it after a new export.

A sheet still sources its own pairings in the wine's `sources.md`. This list only decides which icons need to exist.

## The list

31 categories. 5 already exist. Drawing the other 26 covers every pairing the sources name for this cellar. The top 24 reach 95%.

| Rank | Icon | Have it | Share | Running | Bottles reached | Styles that call for it |
|---|---|---|---|---|---|---|
| 1 | steak (steak and roast beef) | | 24.5% | 24.5% | 131 | NW Cabernet, Left Bank, Grenache blends, Tuscan, Brunello, Rioja, Right Bank, Rosé, Amarone |
| 2 | lamb | | 7.0% | 31.5% | 80 | NW Cabernet, Grenache blends, Zinfandel, Rioja, Amarone, Syrah |
| 3 | pasta | | 6.5% | 38.0% | 51 | Tuscan, Brunello, Rioja, Rosé, Barolo |
| 4 | pork (pork and veal) | | 6.2% | 44.1% | 82 | NW Cabernet, White Burgundy, Sweet white, Zinfandel, Riesling, Syrah, NW Chardonnay |
| 5 | mushroom | | 6.1% | 50.3% | 73 | Red Burgundy, White Burgundy, Brunello, Zinfandel, Amarone, NW Pinot |
| 6 | duck | | 5.9% | 56.1% | 71 | Red Burgundy, Grenache blends, Brunello, Champagne, NW Pinot, Riesling |
| 7 | salmon | | 3.9% | 60.0% | 35 | Red Burgundy, Zinfandel, NW Pinot |
| 8 | blue-cheese | | 3.6% | 63.6% | 32 | Grenache blends, Sweet white, Fortified |
| 9 | fried (fried food and chips) | | 3.6% | 67.3% | 18 | Champagne, Other sparkling |
| 10 | cheese (hard cheese) | yes | 3.2% | 70.5% | 58 | Grenache blends, Brunello, Champagne, Zinfandel, Barolo |
| 11 | spicy (spicy Asian and Indian) | | 3.1% | 73.6% | 42 | Grenache blends, Sweet white, Riesling, Syrah, Chenin, Sauvignon |
| 12 | chicken (roast chicken and turkey) | yes | 2.9% | 76.6% | 45 | White Burgundy, Zinfandel, Right Bank, Chenin, Sauvignon, NW Chardonnay |
| 13 | roast-vegetables | | 2.3% | 78.9% | 44 | White Burgundy, Zinfandel, Right Bank, Rosé |
| 14 | braise (braised beef) | | 2.3% | 81.2% | 38 | Grenache blends, Brunello, Right Bank |
| 15 | white-fish | | 2.1% | 83.3% | 31 | White Burgundy, Rosé, Sauvignon, NW Chardonnay |
| 16 | lobster (lobster and crab) | yes | 1.9% | 85.2% | 40 | White Burgundy, Champagne, Riesling, Sauvignon, NW Chardonnay |
| 17 | risotto | yes | 1.6% | 86.9% | 28 | White Burgundy, Barolo, Sauvignon |
| 18 | barbecue (ribs and pulled pork) | | 1.5% | 88.4% | 28 | Grenache blends, Zinfandel |
| 19 | oyster | | 1.4% | 89.8% | 34 | White Burgundy, Champagne, Sauvignon |
| 20 | sushi | | 1.4% | 91.1% | 34 | White Burgundy, Champagne, Sauvignon |
| 21 | soft-cheese (soft and washed-rind) | | 1.3% | 92.5% | 23 | Champagne, Sweet white |
| 22 | burger | | 1.3% | 93.8% | 19 | Zinfandel, Rioja |
| 23 | game (venison, wild boar) | | 1.0% | 94.7% | 22 | Brunello, Zinfandel |
| 24 | mussels (mussels and clams) | | 0.8% | 95.6% | 21 | White Burgundy, NW Chardonnay |
| 25 | shrimp | | 0.8% | 96.4% | 11 | Rosé, Riesling |
| 26 | nuts (salted nuts) | | 0.8% | 97.2% | 11 | Sweet white |
| 27 | scallop (scallops and shellfish) | yes | 0.7% | 97.8% | 19 | White Burgundy |
| 28 | chocolate (dark chocolate) | | 0.6% | 98.5% | 12 | Brunello |
| 29 | goat-cheese | | 0.6% | 99.1% | 10 | Rosé, Sauvignon |
| 30 | caviar | | 0.6% | 99.6% | 12 | Champagne |
| 31 | pizza | | 0.4% | 100.0% | 10 | Zinfandel |

## Against the planned list in DESIGN_SYSTEM.md

- **Kept:** steak, lamb, duck, pork, salmon, white-fish, oyster, shrimp, blue-cheese, goat-cheese, soft-cheese, mushroom (was mushroom-dish), roast-vegetables, pasta, pizza, chocolate.
- **Folded in:** fried-chicken becomes fried, which also covers tempura and chips. Sausage falls under pasta and pork, because no source names it on its own.
- **Dropped for now:** fruit-tart. Only Demi-Sec Champagne calls for it, and the cellar has none.
- **New from the sources:** braise, game, barbecue, burger, sushi, mussels, spicy, nuts, caviar.

## Weak spots

- **Bordeaux has no regional source yet.** Left Bank rests on Wine Folly's Cabernet page, which says only "grilled meats" and "peppery sauces". Right Bank uses Wine Folly's Merlot page. Decanter's Bordeaux pairing article returned only its title, and bordeaux.com's pairing pages give no appellation pairings in their text. This is 28 bottles.
- **Tier B sources carry four styles:** Banfi for Brunello, Millesima for Champagne, Matching Food & Wine for rosé and Laithwaites for Châteauneuf-du-Pape. Banfi is a Brunello producer and the other three are a retailer, a writer and a merchant. The rosé page is paywalled past two general sentences.
- **Borrowed rules:** Other sparkling uses Wine Folly's Champagne rule. Fortified uses Wine Folly's Port page, though the bottles are a Maury and a Ratafia.
- **21 bottles (8%) have no source:** Other white (7), Other red (6), White Rhône (3), White Rioja (3), Vin jaune (1) and Orange (1). Their sheets will need sources, and may need an icon outside this list.
- **The weighting favors short sources.** A style with a one-line source puts all its weight on one or two icons, so Cabernet's "grilled meats" lifts steak. Steak still reaches the most bottles, 131, by any measure.

## Drawing rules for pairing icons

Agreed in the review of 2026-11-03. Apply them to every new pairing icon.

1. **Show the food as it's served,** in the view that makes it easiest to recognize. Don't show the live animal or a symbol for it. Shellfish served whole, like lobster and oysters, count as served.
2. **When two dishes look alike, add one cue** attached to the food, never a separate symbol. Duck is shown as confit, a crisp leg with potatoes on a plate, so it reads apart from the roast chicken drumstick. Game gets juniper and rosemary. Pork is a ham on its side, led by its round pink cut face.
3. **Use a vessel only when the dish is served in one:** stew in a pot, curry in a bowl, nuts in a bowl, caviar in its tin, pasta and duck confit on a plate.
4. **One garnish at most,** and only when it helps tell the dish: basil on pasta, lemon with oysters, a chili with curry, potatoes with duck confit, steam over the ribs.
5. **Same size and weight.** The larger side of the artwork is 50 units on the 64 grid, centered. `build_review.py` shows each icon in its pairing circle at print size.
6. **Show up on sand.** White foods, like goat cheese and brie, get a darker sand edge so they show on the pairing circle. Every bone is cream `#F3EAD8` with a tan edge `#BFA57A`, because plain cream disappears on the circle.
7. **One drawing per food.** Steak, mushroom and dark chocolate use the approved flavor drawings.
8. **House style,** as for all icons: flat fills, no outlines, at most six colors and `make check-icons` clean.

**Approved pairing icons that break these rules,** which are left alone until Chris says otherwise:
- The chicken drumstick uses one color, where the new icons use a highlight and a shade.
- The risotto bowl is a side view with no rim, where the new bowls show their rim.
- The scallop and lobster are drawn in a single color.

On 2026-11-03 Chris supplied reference icons for lamb, ham, ribs and duck confit. The drawings follow those compositions in the house style. Nothing was traced.

**Added on 2026-11-03 at Chris's request:** a foie gras icon, for the sweet wines. No source we read names it, so it's not in `pairing_sources.json`. Source it in the wine's `sources.md` before a sheet uses it. First used on 2026-11-04 for Bollinger La Grande Année 2015, sourced to Bollinger's own pairing note.

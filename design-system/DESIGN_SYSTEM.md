# Directions: build the design system

Turn what the La Boudriotte sheet already does into a reusable system that can cover every wine in the cellar. The look is approved. This work extends it and must not redesign it.

A seed is already here: `tokens.json`, `fonts/`, 14 icons in `icons/`, `icons.json`, `gallery.png`, and the components in `src/blocks.py`.

**Hard gate:** `make verify` must stay at zero differing pixels through every step. Extract first, then extend. To change something visible on the reference sheet, ask Chris first.

## 1. What makes the look

- **Inspired by, never copied from.** The brief was "in the style of Wine Folly": flat, friendly, teaching-first infographics. Every drawing here is original. Never trace their art, use their name or logo, or reuse their exact charts.
- **Flat shapes.** Solid fills only. No gradients, shadows, photos, emoji or textures.
- **One hot color.** Coral means "this wine, here, now." It marks the vineyard, the current year and the quality tier. Don't use it for decoration.
- **Teaching order.** Each block answers one question a guest would ask: What is it? What will I taste? When and how do I drink it? What do I eat with it? Why is it special? Where is it from?
- **Plain words.** Section heads are questions or everyday phrases, such as "What to eat with it."
- **Print first.** White paper, tints instead of floods, nothing that depends on bleed. Grayscale is not a requirement. Chris decided on 2026-11-02 that color may carry meaning.
- **Honest graphics.** A chart never implies a measurement that doesn't exist. Taste dots carry a "guide" note. Maps never imply more precision than the data has.

## 2. Deliverables

```
design-system/
  tokens.json          every color, type size, space, stroke and radius
  fonts/               vendored, with licences
  icons/<family>/*.svg one file per icon
  icons.json           id, family, label, tasting words, stage, and regions used
  components.md        catalog: purpose, inputs, size, empty state, sample
  maps.md              map kit rules
  build_gallery.py     renders the review sheet below
  gallery.png          tokens, icons and components in one view
```

Optional at the end: also publish it as a Design System artifact on claude.ai, so new Design canvases and decks there can use the same tokens. Chris would need to ask for that in a claude.ai session.

## 3. Step by step

1. **Finish the tokens.** Move the remaining literals in `src/blocks.py` and `src/mapgen.py` into `tokens.json`: spacing, sizes, radii, line heights. `make verify` proves nothing moved.
2. **Name by role.** Components refer to roles (`accent`, `tint`, `target`), never to raw hex or to a particular wine.
3. **Build the color themes.** White is approved. The red accent in the seed (`#8E2F3C` on `#F3DFDD`) is an untested proposal. Propose sparkling, rosé, dessert and fortified themes too, and show them all to Chris on real sheets before locking any.
4. **Grow the icon set** using sections 4 and 5, in the priority order given there.
5. **Write the component catalog** using section 6.
6. **Add the planned components** in section 7 only when a real wine needs them.
7. **Write the map kit** using section 8.
8. **Render the gallery** and get Chris's approval.

## 4. Icon rules

Measure new work against the existing 14.

- **Grid:** 64 by 64 viewBox, with artwork inside about 6 to 58.
- **Style:** Flat fills, 2 to 4 colors, one simple highlight at most. Detail strokes are allowed only as internal marks, such as the ribs on the scallop. Serving tools use the ink outline style of `thermo` and `decant`.
- **Color:** Use the real-world color of the thing. Keep saturation in the same range as the seed set.
- **Sizes:** It must read at 50 px and 38 px on paper.
- **Avoid:** Text inside icons, emoji, gradients, and clip paths or filters.
- **Markup:** Close every element and don't self-close (`<path ...></path>`). This keeps them compatible with Design canvases.
- **Naming:** Lowercase English nouns with hyphens. No wine or region names.
- **Register every icon** in `icons.json` with its tasting words, so copy can resolve "citrus peel" to `lemon`.
- **Tell-alike pairs must be told apart at 38 px:** raspberry vs. blackberry, cherry vs. plum, lemon vs. lime, chalk vs. flint. Color may do the work, since grayscale is not a requirement. Prefer a different silhouette when it costs nothing. If two still look alike, flag them to Chris.

Review every batch on the gallery at both sizes before use.

## 5. Icon library to build

**Priority:** Draw what real wines need first. When the CellarTracker export arrives, count what's in the cellar and order the work by bottles. Until then, Burgundy, Bordeaux, Champagne, Napa, Rhône and Rioja come first, because they're the known focus of the cellar. Add an icon when a sheet calls for it. Don't draw all of these up front.

**Coverage (2026-11-02):** at Chris's request, the flavor library covers every descriptor in the aroma and flavour section of the WSET Level 4 Wine-Lexicon. `icons.json` records each icon's place in it under `lexicon`. The one exception is "simple", which describes a wine rather than an aroma. The drawings are original. Use the lexicon as a checklist, and don't print its name or logo on a sheet.

The groups below came first and remain a working structure for icons outside the lexicon.

### Smell and taste: primary

| Group | Icons |
|---|---|
| Floral | white-flowers, acacia, honeysuckle, elderflower, orange-blossom, rose, violet |
| Green and yellow fruit | apple (exists), green-apple, pear (exists), quince, gooseberry, grape |
| Citrus | lemon (exists), lime, grapefruit, orange, tangerine |
| Stone fruit | peach (exists), apricot, nectarine |
| Tropical | pineapple, mango, passion-fruit, lychee, banana, melon |
| Red fruit | red-cherry, raspberry, strawberry, cranberry, red-currant, red-plum, pomegranate |
| Black fruit | blackcurrant, blackberry, black-cherry, black-plum, blueberry |
| Herbal and green | mint, eucalyptus, thyme, bay-leaf, fennel, cut-grass, bell-pepper, tomato-leaf |
| Spice | black-pepper, white-pepper, licorice, anise |
| Mineral | flint (exists), chalk, wet-stone, slate, sea-salt, graphite |

### Smell and taste: secondary

| Group | Icons |
|---|---|
| Oak | vanilla, toast, cedar, clove, cinnamon, nutmeg, coconut, smoke, coffee, dark-chocolate |
| Malolactic | butter, cream |
| Lees and bottle age | brioche, biscuit, bread-dough, yeast |

Chris favors bready, autolytic Champagne, so draw brioche and its neighbors early and make them clearly different.

### Smell and taste: tertiary

| Group | Icons |
|---|---|
| Dried fruit | fig, prune, raisin, dried-apricot, marmalade |
| Nuts and sweet | hazelnut (exists), almond, walnut, honey, caramel, toffee, beeswax |
| Earth | mushroom, truffle, forest-floor, wet-leaves, earth |
| Savory | tobacco, leather, game, meat, petrol |

### Everything else

| Family | Icons |
|---|---|
| Pairing | chicken, scallop, lobster, cheese, risotto (all exist), steak, lamb, duck, pork, sausage, salmon, white-fish, oyster, shrimp, blue-cheese, goat-cheese, soft-cheese, mushroom-dish, roast-vegetables, pasta, pizza, fried-chicken, chocolate, fruit-tart |
| Serving | thermo, decant, glass (exist), chill, open-early, bottle-upright, burgundy-glass, bordeaux-glass, tulip-glass, flute |
| Bottle shapes | burgundy (exists in `blocks.bottle`), bordeaux, champagne, rhone, alsace-flute. Keep the same label area, so the shape changes and the layout doesn't |
| Winemaking | barrel, new-oak, steel-tank, concrete-egg, lees, whole-cluster, hand-harvest, old-vine, organic, riddling-rack, disgorgement |
| Soil | limestone, clay, gravel, sand, chalk, slate, granite, volcanic, marl |
| Climate and site | sun, frost, rain, hillside, valley-floor, river, ocean, elevation |

## 6. Component catalog: exists today

Document each with purpose, inputs, size, empty state and a gallery sample. All are in `src/blocks.py`.

| Component | Purpose | Inputs | If data is missing |
|---|---|---|---|
| `hero` | Name the wine | eyebrow, title, subtitle, producer, intro, bottle label | Required |
| `bottle` | Identify the bottle | label text, theme. Add a shape input | Required |
| `facts_row` | Five hard facts | label, value, note. 5 items | Replace a missing fact with another fact. Never leave a blank |
| `taste_dots` | Structure, 5 steps | filled count, label, word | Drop the row |
| `flavor` row | What you'll smell | icon, label. 6 items | Fewer items, spaced evenly |
| `drink_window` | When to drink | first, last, current year | Replace with a note if unknown |
| serving pair | Temperature, decant | short text | Drop decant when not advised |
| `pairing` row | What to eat | icon, label. 3 to 5 items | Fewer items, spaced evenly |
| `quality_ladder` | The region's rank system | tiers, active tier | Drop it and widen the story text. Pomerol needs this |
| `story_row` | Producer and vintage | ladder, family, vintage | Must reflow when the ladder drops |
| `map_block` | Where it's from | locked SVG | Fall back to the lowest precision tier |
| `notes_row` | Spot, soil, name | 3 heading and text pairs | 2 or 3 columns |
| `credits_footer` | Sources | text | Required |

**Taste scale rubric.** Use one fixed scale, so dots mean the same thing on every sheet. For body, acidity, tannin, alcohol and oak: 1 low, 2 medium-minus, 3 medium, 4 medium-plus, 5 high. For sweetness: 1 dry, 2 off-dry, 3 medium, 4 sweet, 5 very sweet. Show tannin on reds, and add mousse on sparkling. The reference sheet's dots fit this scale.

## 7. Components to add when needed

| Component | Needed for | What it shows |
|---|---|---|
| `blend_bar` | Bordeaux, Rhône, blends | Stacked bar of grapes with percentages. Only with sourced percentages for that vintage |
| `chateau_card` | Médoc, Right Bank | Estate facts and first vs. second wine |
| `classification_ladder` | Médoc, Saint-Émilion, Rioja | The ladder with region-specific tiers and optional growth counts |
| `soil_section` | Burgundy, Right Bank | Simple cross-section of the slope with soil icons. Only where a source supports it |
| `dosage_scale` | Champagne | Brut Nature to Doux, with this wine marked. Show the dosage only if sourced |
| `base_years` | Champagne | Base vintage, reserve wine and disgorgement date, when known |
| `aging_timeline` | Rioja, Champagne, Port | Time in barrel and bottle before release |
| `nested_ava` | Napa, Sonoma | Nested area diagram |
| `vintage_meter` | Any | A rating only with a named source. Otherwise words |

Rules for all new components: they fit the existing page grid, use existing tokens, have an empty state, and carry sourced data only. Prefer adapting a component before adding one. If a component serves only one wine, it doesn't belong in the library.

## 8. Map kit

Write `maps.md` to capture these rules. Colors are in `tokens.json`.

- **Three linked levels,** with a numbered badge and rectangle linking each to the next. Add a plot inset when a vineyard name contains multiple plots.
- **Equal-area or conformal national projection.** France uses Lambert-93.
- **Color roles:** Target coral with an ink outline. Parent cru teal outline. Grand Cru plum, Premier Cru gold, Village pale gold. Neighbors muted tan. The target village has a heavy ink border, and other villages get dashed borders.
- **Region-level color** comes from a fixed subregion palette. Add other regions' palettes with the same lightness range.
- **Labels:** Doubled text for the halo, not `paint-order`. Leaders are 0.7 px. Nothing clipped, overlapping, or crossing a target. Minimum 9.5 px.
- **Always include** a scale bar, north arrow and locator, plus a legend with only the classes present.
- **Precision tiers** are in `docs/REGIONS.md`. The sheet must not imply more than the tier supports.
- **Sources** go in the credits footer, every time.

## 9. Print rules

- US Letter, 816 by 1056 px at 96 px per inch. Keep 40 px clear on every edge.
- Body 13 to 14.5 px. Captions 12 px. Footer 10.5 px. Map labels 9.5 px minimum.
- Text contrast 4.5:1 or better. Use `coral_text`, never `coral`, for small text.
- Strokes that must print are at least 0.7 px on maps and 1 px elsewhere.

## 10. Done means

- [ ] `make verify` reports zero differing pixels.
- [ ] No raw color or type size remains outside `tokens.json`.
- [ ] Every icon is registered, and has been reviewed at both sizes.
- [ ] Every component has a catalog entry, an empty state and a gallery sample.
- [ ] A second wine in a different color theme renders with no new one-off code.
- [ ] Chris has approved the gallery.

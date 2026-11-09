# Component catalog

Every component on the La Boudriotte sheet, as built in `src/blocks.py`. Each one reads its values from `tokens.json` and asks for roles, never hex. Sizes are CSS px on the 816 by 1056 page. The gallery (`gallery.png`, built by `make gallery`) shows a sample of each under the same name.

**How to read "If data is missing".** The rule says what the sheet should do. The status says whether the code does it today. Only La Boudriotte has been built, so most empty states are rules waiting for the first wine that needs them. Build them then, and keep `make verify` at zero.

## Roles

Components use these names. The page roles live in `tokens.json` under `role`. The theme roles come from the wine's theme.

| Role | Means | White theme value |
|---|---|---|
| `text` | Ink for all text and rules | ink `#1F2D3A` |
| `text_soft` | Labels, notes, captions | soft_text `#47525C` |
| `hot` | This wine, here, now. Current year, active tier, capsule | coral `#D9482B` |
| `hot_text` | `hot` for small text. Passes 4.5:1 | coral_text `#B93414` |
| `on_hot` | Text on a `hot` fill | white |
| `panel` | Sand fill behind the serve block, pairing circles and ladder | sand `#F4EFE3` |
| `paper` | Page ground | white |
| `label_paper` | Bottle label | `#FFFDF8` |
| `accent` (theme) | Filled taste dots, drinking window | gold `#E9B44C` |
| `tint` (theme) | Hero band | `#F9EBC6` |
| `disc` (theme) | Circle behind the bottle | the accent, `#E9B44C` |
| `bottle` (theme) | Bottle glass | `#3F5B45` |
| `bottle_highlight` (theme) | The single highlight stroke on the glass | `#7E9B82` |
| `wine` (theme) | The wine in the decant and glass icons | `#E9B44C` |
| `capsule` (theme) | The foil | coral |

`hot` is never a theme color. It stays coral on every sheet.

Themes live in `tokens.json` under `themes`. A wine picks one with `"theme"` in `wine.json` (white if absent) and can override any role. All six themes are approved. A normal render with a proposed theme would fail. `render.py --theme <name> --out <folder>` proofs one, and `make gallery` proofs them all. The serving icons draw their wine in the white theme's gold, and a theme's `wine` role swaps that color in.

## Building blocks

### `section_head`
- **Purpose:** Head a block with a question or everyday phrase.
- **Inputs:** text.
- **Size:** Poppins 700, 15 px, 8 px below. Type style `section_head`.
- **If data is missing:** Never empty. The block it heads decides.

### `taste_dots`
- **Purpose:** One structure row on a fixed 5-step scale.
- **Inputs:** filled count (1 to 5), label, word. One row per list item in `content.taste`.
- **Size:** Columns 78, 118 and the rest, gap 8. Dots 18 px, gap 4, border 1.5 px. Filled dots use `accent` with a `text` border. Empty dots are `paper` with a `dot_empty_border` border.
- **Scale:** For body, acidity, tannin, alcohol and oak: 1 low, 2 medium-minus, 3 medium, 4 medium-plus, 5 high. For sweetness: 1 dry, 2 off-dry, 3 medium, 4 sweet, 5 very sweet. Show tannin on reds. Add mousse on sparkling.
- **Honesty:** The block always carries `taste_note`, which says the dots are a guide.
- **If data is missing:** Drop the row. **Built:** rows come from the list.

### `flavor`
- **Purpose:** One smell or taste note.
- **Inputs:** icon id, label.
- **Size:** 62 px cell, icon 50 px, gap 4. Label 12.5 px, 700, centered.
- **If data is missing:** See the flavor row.

### `pairing`
- **Purpose:** One food.
- **Inputs:** icon id, label.
- **Size:** 54 px `panel` circle with a 38 px icon, gap 5. Label 13 px, 700, centered.

### `fact`
- **Purpose:** One hard fact.
- **Inputs:** label (caps), value, note.
- **Size:** Label 11.5 px, 800, tracked 0.7. Value Poppins 700, 16 px. Note 12 px.

### `bottle`
- **Purpose:** Identify the bottle.
- **Inputs:** three label lines (name, appellation, year) and the theme.
- **Size:** 136 by 200. Disc in `disc`, glass in `bottle`, capsule in `capsule`, label rule in `hot`, label in `label_paper`.
- **Shape:** `burgundy` or `champagne`, from the theme's `bottle_shape` or `bottle_shape` in `wine.json`. Both keep the label rectangle where it is, so only the outline changes. Champagne takes its proportions from a Dom Pérignon bottle: a long neck, a long gradual shoulder and a foil down to the shoulder. Only the silhouette is borrowed, never the label. `bordeaux` has high, rounded shoulders, set by the Bordeaux profile. Rhône and Alsace flute are not built.
- **Capsule:** the theme's `capsule` role, coral unless the theme sets it. A dark foil gets a thin coral band, so coral stays an accent. Chris chose the dark foil for sparkling on 2026-11-03.
- **If data is missing:** Required.

### `quality_ladder`
- **Purpose:** The region's rank system, with this wine's rung in `hot`.
- **Inputs:** active tier. Tier names default to Burgundy's four.
- **Size:** Widths 76, 104, 132, 160, height 22, gap 2. Steps 12 px, 800.
- **Rungs:** four use the `widths` token. Any other count widens evenly from `min_width`. The profile may give short `labels`, such as First to Fifth for the 1855 growths.
- **If data is missing:** Drop it and widen the story text. Pomerol needs this. **Built:** the tiers come from the region profile's `story.signature`, and a profile with no signature reflows the story row.
- **Known gap:** White on coral is 4.28:1, under the 4.5:1 rule, on the active rung. It's on the approved sheet, so changing it needs Chris's approval.

### `ava_nest`
- **Purpose:** Where does this AVA sit? The wine's AVA inside the AVAs that hold it, outermost first, each with the year it was established. The wine's AVA is in `hot`.
- **Inputs:** the wine's `level` (its AVA's name). The render builds the chain from `regions/sources/us-ava.json` (the TTB data via UC Davis) and the profile's short names.
- **Size:** 160 wide, padding 6, label rows 18, gap 3. Boxes alternate `panel` and `paper`. Sits in the story row's 164 px column.
- **If data is missing:** Without a `level` the story row reflows. **Built.**

### `blend`
- **Purpose:** What's in it? A stacked bar of the grapes, with a key of shares, leading the facts row and spanning two of its five columns.
- **Inputs:** the record's `identity.grapes`, when the profile sets `facts_blend`, the wine has more than one grape and every share is sourced for this vintage and sums to 100. The wine then gives three other facts.
- **Size:** bar 16 px, gap 2 between grapes, key in `fact_note` with 9 px swatches. Grape colors in `tokens.json` under `grape`.
- **If data is missing:** No blend bar. The facts row is five facts as before. **Built.**

### `dosage_scale`
- **Purpose:** How dry is it? The label terms for sugar in sparkling wine, driest at the top, with this wine's term in `hot`.
- **Inputs:** the wine's `level` (a term) and the profile's signature: `terms`, each a name and a range in grams per liter. Champagne's come from EU Regulation 2019/33, Annex III, Part A.
- **Size:** 160 wide, rows 18 tall, gap 2, padding 8. Term in `ladder_step`, range in `dosage_range` (12 px, 600). Sits in the story row's 164 px column, with `ladder_note` below for the wine's dosage.
- **Honesty:** the ranges are the law's. The wine's own figure goes in the note, only when sourced.
- **If data is missing:** Without a `level` the story row reflows. **Built.**

### `drink_window`
- **Purpose:** When to drink it.
- **Inputs:** first year, last year, current year.
- **Size:** One cell per year, bar 15 px, gap 2. Years in `accent`, the current year in `hot`. Year labels 12 px, the current one in `hot_text` at 800.
- **Stale risk:** The current year comes from `--year`. Print on demand.
- **Many years:** Past `max_ticks` years (10), only this year, the first and last years and every fifth year get a label, with at least one empty cell between labels. **Built.**
- **If data is missing:** Replace with a note. **Not built.**

## Sections

Bottoms are from the top of the page, measured on La Boudriotte.

### `hero`
- **Purpose:** Name the wine.
- **Inputs:** `eyebrow`, `title`, `subtitle`, `producer`, `intro`, `bottle_label`. Optional `title_px` for a long name.
- **Size:** 220 px tall, `tint` band, padding 10 and 28, columns 1fr and 140. Bottom at 260.
- **If data is missing:** Required. Cut `intro` before anything else.
- **Watch:** `title_px` lowers the title size. Use it only when a name can't fit at 56 px, and ask Chris first, since the rule is to cut copy, not shrink type. A name can't be cut.

### `facts_row`
- **Purpose:** Five hard facts.
- **Inputs:** `facts`, five `[label, value, note]` items.
- **Size:** 5 equal columns, gap 14, 1.5 px rule below. Bottom at 333.
- **If data is missing:** Replace a missing fact with another sourced fact. Never leave a blank. **Built as a rule for copy:** the grid is fixed at five, so a short list leaves a gap.

### `taste_row`
- **Purpose:** What will I taste?
- **Inputs:** `taste`, `taste_note`, `flavors` (6 items), `flavor_note`.
- **Size:** Two equal columns, gap 26. Bottom at 518.
- **If data is missing:** Fewer flavors, spaced evenly. **Built:** the row spreads what it gets.

### `serve_row`
- **Purpose:** When and how do I drink it?
- **Inputs:** `window`, `window_note`, `serve`, `decant`.
- **Size:** `panel` fill, padding 10 and 16, columns 1.75, 1, 1, gap 18. Icons 38 px. Bottom at 668.
- **Cells:** the region profile's `serve_cells` list them after the window: Serve and Decant by default, Serve and The glass for Champagne.
- **If data is missing:** A cell drops out when the wine has no text for it, and the columns close up. **Built.**

### `pairing_row`
- **Purpose:** What do I eat with it?
- **Inputs:** `pairs` (3 to 5), `pair_note`.
- **Size:** Equal columns, gap 8. Bottom at 819.
- **If data is missing:** Fewer items, spaced evenly. **Built:** the grid uses the item count.

### `story_row`
- **Purpose:** Why is it special?
- **Inputs:** `level`, `ladder_note`, optional `ladder_title`, `family`, `vintage`.
- **Size:** Columns 164, 1.25, 1, gap 22, 1.5 px rule above. Fills to the page bottom at 1016.
- **Signature:** the profile's `story.signature` picks the left graphic, `quality_ladder` or `dosage_scale`. Headings come from `story.labels`, then the producer's `story_title`, then the wine's own `family_title` and `vintage_title`.
- **If data is missing:** Reflow to two columns when there's no signature or no `level`. **Built.**

### `place_header`
- **Purpose:** Title the back page.
- **Inputs:** optional `place_title`, `place_subtitle`. The defaults are Burgundy copy.
- **Size:** Poppins 800, 30 px, with a 14 px subtitle on the same baseline. Bottom at 73.

### `map_block`
- **Purpose:** Where is it from?
- **Inputs:** the locked `map.svg` for the wine. See `maps.md`.
- **Size:** 736 by 752. Bottom at 835.
- **If data is missing:** Fall back to the lowest precision tier the data supports. **Not built:** only the parcel tier exists.

### `notes_row`
- **Purpose:** The spot, the soil, the name.
- **Inputs:** `place`, three `[heading, text]` pairs.
- **Size:** 3 equal columns, gap 20, 13 px text. Bottom at 959.
- **If data is missing:** 2 or 3 columns. **Not built:** the grid is fixed at three.

### `credits_footer`
- **Purpose:** Sources, every time.
- **Inputs:** `credits`, after the profile's map credit line (`map.credit`).
- **Size:** 10.5 px, 1 px rule above. Bottom at 1016.
- **If data is missing:** Required.

## Page

`page` wraps each side: 816 by 1056, 40 px padding, `paper` ground. Front gap 11 and line height 1.42. Back gap 10 and line height 1.4. If a page overflows, the render fails and `report.json` names the last blocks. Cut copy. Never shrink type.

## Rules for new components

From `DESIGN_SYSTEM.md` section 7. Fit the page grid. Use existing tokens and roles. Have an empty state. Carry sourced data only. Adapt a component before adding one. A component that serves one wine doesn't belong here.

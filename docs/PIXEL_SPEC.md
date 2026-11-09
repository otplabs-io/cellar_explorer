# Pixel spec: La Boudriotte 2019

The source of truth is `reference/La-Boudriotte-2019-Print.pdf`, and `make verify` is the test. This document explains the measurements. `reference/layout.json` lists the box, font, size, weight, color and text of all 168 text elements, for anyone rebuilding in another stack.

## What "pixel-perfect" means here

Both PDFs are rasterized by PyMuPDF at 300 dpi (2550 by 3300 px), and every pixel is compared with no tolerance. Page size, extracted text and embedded fonts must match too. The PDF file hash isn't used, because PDFs embed a creation time.

## How the PDF is made

- Chromium through Playwright, `page.pdf(width='8.5in', height='11in', print_background=True, prefer_css_page_size=True)`
- Viewport 816 by 2112, device scale factor 1.6, 800 ms wait, then `document.fonts.ready`
- CSS: `@page { size: 8.5in 11in; margin: 0 }`, and each page wrapped in `.pg { width: 816px; height: 1056px; overflow: hidden; break-after: page }`
- Print double-sided, flipped on the long edge

## Page

816 by 1056 px at 96 px per inch, which is 612 by 792 pt. Padding 40 px on all sides, giving a 736 px content width. White ground. Nothing bleeds, so home printers lose nothing.

## Front, top to bottom

Gap 11 px, line height 1.42. Bottoms are measured from the top of the page.

| Block | Bottom | Key measurements |
|---|---|---|
| hero | 260 | Height 220. Gold tint. Padding 10 and 28. Columns 1fr and 140, gap 20. Bottle 136 by 200 |
| facts | 333 | 5 equal columns, gap 14. Padding-bottom 9. Rule 1.5 ink below |
| taste | 518 | 2 equal columns, gap 26. Dots 18 px, gap 4, in 5s. Row columns 78, 118, 1fr. Flavor icons 50 px in 62 px cells |
| serve | 668 | Sand fill. Padding 10 and 16. Columns 1.75fr, 1fr, 1fr, gap 18. Window bar 15 px high, gap 2. Serving icons 38 px |
| pairings | 819 | 5 equal columns, gap 8. Circles 54 px, sand. Icons 38 px |
| story | 1016 | Columns 164, 1.25fr, 1fr, gap 22. Rule 1.5 ink above, padding-top 10. Ladder widths 76, 104, 132, 160, height 22, gap 2 |

## Back, top to bottom

Gap 10 px, line height 1.4.

| Block | Bottom | Key measurements |
|---|---|---|
| place-header | 73 | 30 px title, baseline-aligned with 14 px subtitle |
| map | 835 | 736 by 752 SVG |
| notes | 959 | 3 equal columns, gap 20. 13 px text, line height 1.36 |
| credits | 1016 | Rule 1 ink above, padding-top 5. 10.5 px text, line height 1.28 |

## Map, in SVG pixels

| Panel | Origin | Size | Content |
|---|---|---|---|
| 1 Burgundy | 0, 0 | 292 by 330 | Wine communes shaded by subregion, department lines dashed, France locator 56 by 58 at lower left |
| 2 Côte de Beaune | 304, 0 | 432 by 330 | All communes, wine communes tinted, vineyards gold, target village coral, Grand Cru plum |
| 3 Chassagne-Montrachet | 0, 340 | 736 by 412 | Village, Premier Cru and Grand Cru land, target coral, parent cru teal outline |
| Plot inset | 514, 458 | 212 by 146 | Numbered plots, key at 14 px rows, total, legend |

Lambert-93 projection (EPSG:2154). Labels are doubled text elements, a stroked copy under a filled copy, so a halo survives any renderer. No `paint-order` and no clip paths.

## Type

Poppins 800 for sheet and page titles, 700 for section heads and fact values, 600 for the subtitle. Nunito Sans for everything else, with 800 for labels. Exact sizes are in `design-system/tokens.json` and `layout.json`.

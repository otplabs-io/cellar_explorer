---
description: Build the next sheets from the cellar queue
argument-hint: [count] [region id] [iWine]   e.g. "3", "3 france/margaux", "2301597"
---
Build pour sheets from the cellar queue: $ARGUMENTS

Read CLAUDE.md first, and follow every rule in it. Then work through the queue one wine at a time. With no count, do one wine. A region id limits the queue to that place. An iWine (a number of six digits or more) builds that wine.

**Who does what.** You (the main thread) pick wines, write copy, fix maps and judge weak claims. Research goes to agents, each pinned to its model in `.claude/agents/`:
- `context-researcher` (Sonnet): one vintage in one region, or one place, written once to `research/` and reused by every wine from there.
- `wine-researcher` (Sonnet): the claims for one wine, into `research/wines/<id>.json`.

Run research for several wines in parallel, then write them one by one. If the agent types aren't loaded in this session, use `general-purpose` with `model: sonnet` and tell it to follow the agent file.

**For each wine**

1. **Pick it.** Run `.venv/bin/python src/work.py next` (add `--region <id>` if given), or take a named iWine. Then run `src/pipeline.py brief <iWine>`. The brief lists the place, the producer record, the shared research that already exists and the pattern sheet.
   - If the label is unclear or the region node looks wrong, run `work.py skip <iWine> "<reason>"`.
2. **Research.**
   - Start a `context-researcher` for each missing vintage or place file the wine needs.
   - Start a `wine-researcher` with the brief.
   - Its output must pass `pipeline.py check`. Read its gaps and weak claims, not the pages it read.
3. **Scaffold.** Run `src/pipeline.py scaffold <iWine> [--id <id>] [--like <wine-id>]`. It copies the structure of the nearest sheet: map fields, serve, decant, level and taste rows. It fills the CellarTracker window, and marks everything left to write as TODO.
4. **Write the copy** from the claims, and only from the claims.
   - Fill every TODO and every taste row (see below).
   - Write the producer record if it's new.
   - Add claims with source `reading` or `estimate` to the research file for the taste dots and any estimated window.
   - Then run `src/pipeline.py sources <id>`, which writes `sources.md`.
5. **Build.** Run `src/pipeline.py build <id> --map --lock`.
   - It draws the map, checks every label in Chromium and refuses to lock a map with a clipped or overlapping label. Fix those through `overrides` and rerun.
   - It then renders and runs `check-wines`.
   - Open `map.draft.png` or the page images only when a check fails, or the wine needed something new. If copy overflows, cut copy. Never shrink type.
6. **Prove nothing else moved.**
   - Run `make verify` after any change to `src/`, tokens or icons. It must report zero differing pixels.
   - Never edit `reference/`, `reference/mac-baseline/` or `reference-pipeline/`.
7. **Publish.** Run `work.py done <iWine> <id>`, then `make catalog`. Commit the wine, its producer, its map and its research, with a message that names the wine. End the message with the Co-Authored-By line from the session.

**Thin sources: build anyway.** Tech sheets that have vanished won't come back, so a wine with little producer data still gets a sheet. Use the best sources that exist, then fill the gaps with sourced context:
- the vintage: that year's weather and harvest in the region, from a vintage report;
- the place: what the vineyard, AVA or appellation is known for;
- the tier: grand vin or second wine, estate or négoce, a members-only or Hospices cuvée.
Notes on other vintages of the same cuvée may stand in for flavors. Never invent. Every claim goes in `sources.md` with its strength, and weak ones go in the report to the user.

**Every sheet gets a drinking window**. Use a critic's or the producer's window when one exists. Otherwise start with CellarTracker's range from the export. If CellarTracker has no range, or no end, estimate one from the growing area, the cru level, that year's climate and the producer's methods, anchored on CellarTracker windows of comparable wines in the cellar. Put the reasoning and the comparables in `sources.md` with strength "Estimate". The sheet states the window plainly.

**Pin the vineyard**. On the AVA, appellation and zone maps, the pin is `map_estate`: a name, a lon/lat and the source of that point.
- A single-vineyard wine (To Kalon, Monte Bello, a named lieu-dit) pins the vineyard. Ask the `wine-researcher` for its location from a public source, such as OpenStreetMap or the producer's own site or map, and write the source into `map_estate`.
- If the vineyard can't be sourced, or the wine has no named vineyard, pin the winery from a source. The pin's name says what it marks ("Robert Mondavi Winery", not the wine).
- With no sourced point at all, leave out the pin and let `map_estate_note` say why.
- Never estimate a point, and never move a pin by eye. Each pin's source goes in `sources.md`.
- Locked maps stay as they are. The rule applies to new and rebuilt sheets.

**No inline citations**. Sheet copy states facts plainly. It never names a critic, importer, tech sheet or other source, and never says a source is missing or that something is an estimate. Sources and their strength live in `sources.md`. The credits footer stays. `make check-wines` fails on source words in copy.

**Fill every taste row**. Red: Body, Tannin, Acidity. White: Sweetness, Body, Acidity, Oak. Sparkling: Sweetness, Body, Acidity, Mousse. With nothing definitive, give your best educated guess from the grape, place, vintage and winemaking, and note the reasoning in `sources.md`. `make check-wines` fails on a missing row.

**Set aside only for what sources can't fix.** If a check still fails after three tries, or the region node is wrong, or the wine needs a component or map the profile doesn't have, run `work.py skip <iWine> "<reason>"` and go to the next wine. If only the bottle can say which release it is, set it aside and ask the user for the back label.

**When the run is done,** report to the user for each wine:
- the PDF path;
- the weak claims, with their sources;
- what was set aside, and why.

Send the PDFs with SendUserFile. Then report the queue: run `work.py status`.

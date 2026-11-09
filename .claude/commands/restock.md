---
description: Take a new CellarTracker export into the app, build sheets for the new wines and publish
argument-hint: [path to the export, .csv or .xlsx]   (or attach the file to the message)
---
Restock the cellar from a CellarTracker export: $ARGUMENTS

Read CLAUDE.md first, and follow every rule in it. Keep the user informed only at the points below, and never publish a site that failed a check.

**1. Find the file.** Use the path in the arguments. If the file was attached to the message, use the path it was saved to. If there is neither, look for the newest `.csv` or `.xlsx` in `~/Downloads` with "cellar" or "CellarTracker" in its name, and tell the user which file you took. Never guess between two candidates: ask.

**2. Check it.** Run `.venv/bin/python src/restock.py check <file>`. It writes nothing.
- `RESULT: invalid`: stop and tell the user what is wrong, in one or two sentences, and how to export it ("My Cellar", CSV, all columns).
- `RESULT: unchanged`: tell the user nothing changed, and stop.
- `RESULT: confirm`: the export would archive a large share of the cellar. Show the user how many and a few names, and ask whether it is a full export. Go on with `apply --yes` only on their clear yes.
- `RESULT: ok`: go on without asking.

**3. Import it.** Run `.venv/bin/python src/restock.py apply <file>` (add `--yes` only after the user confirmed in step 2). It keeps a dated copy in `cellar/` without prices, archives what is gone, updates quantities, rebuilds the catalog and lists the queue.

**4. Build the new wines.** For every wine the queue lists as ready, follow `.claude/commands/bottle.md` exactly, as if the user had run `/bottle <iWine>` for each: research in parallel, then write and build one at a time. A wine that waits for a region profile is not built: it shows on the map with a basic card, and goes in the report. Wines flagged as placed only at a country or state, or not placed, are checked against the label and the locale before building; fix the placement or set the wine aside with the reason.

**5. Prove nothing else moved.** If anything in `src/`, tokens, fonts or icons changed, run `make verify`. It must report zero differing pixels.

**6. Publish.** Run `.venv/bin/python src/restock.py publish`. It builds the site in a new folder, runs `check_wines.py` and the app check (`tests/app_smoke.py`) against it, and only then switches the live app to it. If it fails, the live app is unchanged: read the reason, fix it, and publish again. Never switch the site by hand.

**7. Keep the record.** The wines, the export and the sheets are your own, and `.gitignore` keeps them out of git. Do not force-add them.

**8. Report to the user**, short, in this order:
- what changed: added, archived, new quantities;
- the sheets built, with their PDFs sent with SendUserFile;
- the weak claims, with their sources (as `/bottle` reports them);
- what waits for a region profile or was set aside, and why;
- that the app is updated, at the address `src/serve.py` prints.

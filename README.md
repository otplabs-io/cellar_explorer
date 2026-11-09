# Cellar Explorer

Turn your wine cellar into something guests can explore. Browse your bottles on a globe, filter them by grape, place, aroma or drinking window, and open a one-page learning sheet for any wine, on a phone or as a printable PDF.

It runs on your own computer and shares over your Wi-Fi. There are no accounts, and prices never reach the app.

This repository includes five example wines, so you can see it working before you add your own.

## Try it with the examples

You need Python 3.13 and `make`. Run these from this folder:

```bash
make setup
```

```bash
make demo
```

```bash
make serve
```

The last command prints an address. Open it on your computer, or on any phone on the same Wi-Fi.

## Add your own cellar

### 1. Get your inventory

**If you use [CellarTracker](https://www.cellartracker.com/):** export "My Cellar" as CSV, with every column.

**If you don't:** make a CSV by hand with one row per wine in each bottle size. Copy the layout of `examples/cellar-export.csv`. These columns are required:

| Column | What goes in it | Example |
|---|---|---|
| `iWine` | A number that identifies the wine. Any unique number works, but keep it the same every time | `1001` |
| `Wine` | The full name | `Ridge Cabernet Sauvignon Estate` |
| `Vintage` | The year. Use `1001` for non-vintage | `2021` |
| `Quantity` | How many bottles you have | `3` |
| `Locale` | Country, then region, then appellation, separated by commas | `USA, California, Santa Cruz Mountains` |
| `Type` | The style | `Red` |

Adding `Size`, `Producer`, `Varietal`, `Color`, `BeginConsume` and `EndConsume` gives the sheets more to work with. Any price columns are dropped when the file is read.

### 2. Bring it in and build the sheets

The sheets are researched and written by [Claude Code](https://claude.com/claude-code), using the commands in `.claude/commands/`. Open Claude Code in this folder and run:

```
/restock path/to/your-export.csv
```

It checks the file, updates your inventory, researches each new wine, writes and builds its sheet, tests the site and publishes it. To build only a few at a time, import the file and then use `/bottle`:

```bash
make import CSV=path/to/your-export.csv
```

```
/bottle 3
```

Only wines with a sheet appear in the app, so a bottle shows up once its sheet is built.

### 3. Keep it up to date

When bottles come and go, export again and run `/restock`. New bottles get sheets. Quantities update. Bottles missing from the export are archived, and nothing is deleted. If an export would archive a large share of your cellar, it stops and asks first, since that's usually a partial export.

If you'd rather not start from the examples, delete `data/pour.db` before your first import.

## Share it around the house

```bash
make serve
```

On a Mac, keep it running in the background, even after a restart:

```bash
.venv/bin/python src/service.py install
```

## What gets drawn

A wine's sheet needs a map, and maps are set up region by region in `regions/profiles/`. Many places in France, Italy, Spain and the United States are covered, and coverage elsewhere varies. `make queue` shows which of your wines are ready and which are waiting for a region to be added.

## Your data stays yours

`.gitignore` keeps your exports, wines, producers, inventory and builds out of git. Only the five examples are tracked. Avoid `git add -f` on those folders, or your cellar will end up in your repository.

Because of that, git is not backing up your cellar. Keep your own copy of the `wines/`, `producers/`, `research/wines/`, `cellar/` and `data/` folders.

## What's in here

| Folder | What it holds |
|---|---|
| `app/` | The browsing app |
| `wines/`, `producers/`, `research/` | Each wine's record, its map and its researched facts |
| `examples/` | A sample inventory file |
| `regions/` | Every wine place, what each region's sheet shows, and the map shapes |
| `design-system/` | Colors, type, fonts and icons |
| `src/` | The Python that builds sheets and the site |
| `reference/`, `tests/` | The approved sheet and the checks that compare against it |

## Links to the Appellation Atlas

To link each wine to its place in Appellation Atlas, put the Atlas address in `app/site.json`. Leave it empty to hide the links.

## Credits

Boundaries come from the Candiago et al. EU wine PDO inventory, the UC Davis AVA Project, Eurostat GISCO, geoBoundaries and INAO via OpenDataWine. Each example wine's `sources.md` lists the sources behind its facts. Check each source's own terms before you reuse its data. The fonts are Poppins and Nunito Sans, with their licenses in `design-system/fonts/`.

## License

The code is under the [MIT License](LICENSE). The data sources and fonts listed above keep their own terms.

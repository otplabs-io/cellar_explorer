---
description: Make a printable learning sheet for one wine
argument-hint: <wine name and vintage, or a CellarTracker iWine>
---
Make a sheet for: $ARGUMENTS

If the wine is in the cellar, this is `/bottle <iWine>`. Find the iWine with `.venv/bin/python src/work.py list`, then follow `.claude/commands/bottle.md` for that one wine.

If it isn't in the cellar, follow the same steps without the queue commands. Give the identity block an empty `cellartracker` list. Stop to ask only if you can't tell which wine this is.

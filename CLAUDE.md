# Cellar Explorer

A browsing app and printable learning sheets for the wines in a personal cellar. To add or remove bottles, run `/restock` with a new CellarTracker export. Personal wines, exports and builds stay out of git through `.gitignore`. Never force-add them.

- Run `make verify` after any change to `src/`, `design-system/tokens.json`, fonts or icons. It must report zero differing pixels. On macOS it checks against `reference/mac-baseline/`. Do not edit the reference files, the Mac baseline or `reference-pipeline/` to make it pass.
- Build component work on `src/blocks.py` and follow `design-system/DESIGN_SYSTEM.md`.
- No pricing on sheets unless asked. Never invent facts, metrics or attributions. Every claim goes in the wine's `sources.md`.
- Copy: short sentences, plain and friendly, no em dashes, no "not only...but also", no corporate language.
- If copy overflows, cut copy. Never shrink type.
- Copy is data in `wine.json`. Region differences are data in profiles. Do not create a template per region.

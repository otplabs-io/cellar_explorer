# Frozen reference pipeline

The scripts that drew the approved La Boudriotte map, with the raw data they read. Only import paths and the output folder were changed, plus a saved file of commune codes in their original order, because draw order affects the output. `make verify-map` proves it still gives the same bytes.

Do not extend or refactor this. New work goes in `src/`. `pages_original.py` and `topdf_original.py` are records of how the first pages were written, and the build doesn't run them.

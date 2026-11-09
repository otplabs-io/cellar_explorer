---
description: Prove the sheet still matches the approved reference
---
Run `make verify` and `make verify-map`. Report the differing pixel counts. On macOS, `make verify` checks against `reference/mac-baseline/` and also reports the accepted difference from the master, and `make verify-map` skips because it is Linux only. If either fails, open the diff images in `build/la-boudriotte-2019/` and name the change that caused it. Do not edit the reference files, `reference/mac-baseline/` or `reference-pipeline/`.

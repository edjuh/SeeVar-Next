# Postflight

Postflight is the first real module in SeeVar Next.

Postflight is F1-F8:

1. `F1` dark closure
2. `F2` one accepted stack per target
3. `F3` stack WCS solve
4. `F4` photometry
5. `F5` AAVSO report staging
6. `F6` retry list for failed science targets
7. `F7` pretty-target plan when time remains
8. `F8` park or shutdown policy

## Contract

One target folder must produce:

- one accepted stacked FITS
- one JPEG preview
- one photometry CSV
- one staged AAVSO Extended report
- one JSONL proof ledger

If any required step fails, the target fails.

## Current Gates

- FITS frames must exist
- frames must be two-dimensional
- saturated frames are rejected before stacking
- low-contrast frames are rejected before stacking
- stack must contain celestial WCS
- photometry requires at least one comparison star

## Current Limits

- external plate solving is not wired yet
- trail/blur QC is not complete
- comparison stars are supplied by local JSON, not fetched yet
- AAVSO upload is not implemented

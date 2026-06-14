# Postflight

Postflight is the first real module in SeeVar Next.

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

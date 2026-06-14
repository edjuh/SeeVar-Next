# Architecture

SeeVar Next is deliberately small.

## Boundaries

- `preflight`: target accounting and plan generation
- `flight`: adapter around `seestarpy` / `seestar_alp`
- `postflight`: FITS QC, stack, solve, photometry, report
- `proof`: JSONL evidence for every step

## Ownership

SeeVar Next owns science proof.

Seestar tooling owns telescope execution where possible.

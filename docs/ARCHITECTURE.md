# Architecture

SeeVar Next is deliberately small.

## Boundaries

- `preflight`: target accounting and plan generation
- `flight`: adapter around `seestarpy` with optional `seestar_alp` fallback; all submits/status reads write proof
- `postflight`: FITS QC, stack, solve, photometry, report
- `proof`: JSONL evidence for every step

## Ownership

SeeVar Next owns science proof.

Seestar tooling owns telescope execution where possible.

`seestar_alp` is treated as an external daemon/service, not a Python package dependency inside this repo.

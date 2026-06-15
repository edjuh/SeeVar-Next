# SeeVar Next Roadmap

SeeVar Next exists to produce trustworthy AAVSO-ready variable-star observations with less custom control code.

The roadmap is the project control document. Every feature must map to a milestone here, and every milestone must define proof of success.

## Goal

Build a small, strict observatory pipeline:

1. select due and observable AAVSO targets
2. hand a clear plan to Seestar tooling
3. monitor execution with proof records
4. fetch accepted observations
5. stack, solve, measure, and report
6. block AAVSO upload unless every proof passes

## Design Rules

- Prefer `astropy`, `photutils`, and `seestarpy` over custom astronomy/control code.
- Keep telescope execution thin: plan, submit, monitor, download.
- Keep science strict: no WCS, no photometry; no stack, no object success.
- One target per night produces one accepted stack, one preview JPEG, one photometry result, one report row.
- Every phase writes JSON proof records.
- Pretty-picture work is out of scope until AAVSO flow is reliable.

## Milestone 0: Skeleton And Doctrine

Status: current

Deliverables:

- package skeleton
- strict roadmap
- proof-ledger model
- preflight/flight/postflight boundaries
- tests for ledger and contracts

Proof:

- `pytest` passes
- roadmap exists before feature work
- README explains the pipeline in one screen

## Milestone 1: Postflight First

Goal: turn a folder of FITS frames into one accepted science product or one clear failure reason.

Status: in progress

Deliverables:

- FITS ingestion via `astropy.io.fits` - started
- frame QC: saturation and low-contrast rejection - started
- trail/blur detection - pending
- stack candidate builder - started
- solve stack first - pending external solver; current gate requires valid stack WCS
- WCS proof object - started
- aperture photometry via `photutils` - started
- comparison-star matching against supplied catalog JSON - started
- AAVSO Extended report staging - started

Proof:

- synthetic FITS test produces one stack/report - passing
- bad frames are rejected before stacking - passing
- missing WCS blocks photometry - passing
- missing comparison stars blocks report - passing

## Milestone 2: Preflight Planner

Goal: build a real nightly target list from SeeVar catalogs and AAVSO cadence needs.

Status: started

Deliverables:

- load variable-star catalog JSON - started
- load ledger/history
- compute dark window with `astropy` - started
- apply altitude and dark gates - started
- apply horizon, moon, weather, cadence
- assign scopes
- export seestarpy-compatible plan - started
- optional seestar_alp-compatible plan

Proof:

- three-object dry run shows all planned steps - started
- compact monitor status JSON - started
- stale catalog/ledger/weather gets explicit warning
- generated plan is accepted by adapter validation - pending

## Milestone 3: Thin Flight Adapter

Goal: use Seestar tooling for execution while SeeVar records proof.

Deliverables:

- `seestarpy` adapter
- optional `seestar_alp` plan export
- target state monitor
- stack/download monitor
- timeout and fail-reason handling

Proof:

- dry-run adapter emits connect, slew, solve, track, stack, download proofs
- real adapter can run one target without SeeVar steering individual frames
- connection loss produces failed proof, not silent success

## Milestone 4: AAVSO Gate

Goal: never upload weak science.

Deliverables:

- report validator
- AAVSO staging folder
- optional upload probe
- explicit operator approval path

Proof:

- valid report stages
- invalid WCS/photometry/report blocks upload
- manual submission files are easy to find

## Milestone 5: Two-Scope Operation

Goal: Wilhelmina and Anna can run independent assignments without shared-state collisions.

Deliverables:

- scope inventory
- per-scope proof ledgers
- per-scope downloads
- postflight grouping by target/scope/night

Proof:

- fake two-scope run creates separated state
- one failed scope does not poison the other

## Review Rhythm

Review this roadmap often:

- before each coding session
- after each real observing night
- after every failed proof chain
- before merging feature branches

Open questions stay in this file until answered or moved to issues.

## Open Questions

- Primary execution path: `seestarpy`, `seestar_alp`, or both?
- Exact local catalog format to carry over from SeeVar.
- Minimum FITS headers required for accepted postflight.
- Whether AAVSO upload should remain manual-only until first validated month.

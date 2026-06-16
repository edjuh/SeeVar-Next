# Logic Salvage

Useful carry-over from old SeeVar:

## High value

- `AAVSO_LOGIC.MD`
  - target classes
  - cadence defaults
  - TG / green-channel photometry rules
  - AUID and report constraints

- `CADENCE.MD`
  - due-target rules
  - ledger timing logic

- `PHOTOMETRICS.MD`
  - channel extraction
  - comparison-star logic
  - error expectations

- `PREFLIGHT.MD`
  - go / no-go structure
  - target selection gates

- `FLIGHT.MD`
  - target-by-target proof chain
  - mount/session safety expectations

- `POSTFLIGHT.MD`
  - acceptance contract
  - accountant/report flow

## Transport / control reference

- `API_PROTOCOL.MD`
- `ALPACA_BRIDGE.MD`
- `SEESTAR_ALP_API.MD`
- `COMMUNICATION.MD`
- `STATE_MACHINE.MD`

These should inform adapters and failure handling, not re-expand control complexity.

## Data reference

- `DATA_DICTIONARY.MD`
- `DATA_MAPPING.MD`
- `DATALOGIC.MD`

These are worth mining for field names, ledger shape, and report staging.

## Rule for SeeVar Next

Reuse old logic when it adds:

- scientific rules
- proven field names
- cadence logic
- transport facts

Do not carry over:

- dead helpers
- panorama/horizon experiments
- obsolete direct-control complexity without proof value

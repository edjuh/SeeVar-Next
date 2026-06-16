# Flight

Flight is the strict per-target chain.

The top-level proof codes stay `A1-A12`, but each code contains smaller checks. A target only advances when the previous code has proven success.

## A1-A12

1. `A1` Target lock
   - pick one target/scope assignment
   - freeze target coordinates, duration, cadence intent, and required frame count
   - record the exact target being attempted

2. `A2` Zero-state and safety gate
   - scope reachable
   - adapter session healthy
   - mount not in fault state
   - weather/readiness still acceptable
   - no conflicting active run on that scope

3. `A3` Session telemetry valid
   - read mount/camera/filter state
   - read tracking/slewing state
   - confirm timestamps and basic telemetry are fresh

4. `A4` Slew command
   - send target slew through primary adapter
   - record command issue time and target coordinates

5. `A5` Slew completion proof
   - confirm slew stopped
   - confirm mount reports target vicinity rather than old position
   - fail here on timeout or motion fault

6. `A6` Settle after slew
   - short settle wait
   - verify no residual slewing
   - verify tracking state is acceptable for next step

7. `A7` Fresh pointing solve
   - capture or fetch solve evidence
   - compare solved center to requested target
   - fail if no fresh solve proof exists

8. `A8` Corrective nudge / retry
   - only if solve residual exceeds tolerance
   - apply one corrective move
   - re-solve
   - fail if still outside tolerance after allowed attempts

9. `A9` Exposure plan
   - determine exposure length
   - determine required accepted frame count
   - determine refresh cadence for new solve proof
   - mark whether target is science or pretty-picture secondary

10. `A10` Expose and download
    - start exposure
    - wait for completion
    - download/store FITS
    - repeat until success, timeout, or frame quota reached

11. `A11` Frame QC and FITS accept
    - reject empty/broken files
    - reject trailed or bad frames
    - reject frames that violate hard science rules
    - count accepted vs rejected frames
    - request fresh solve again after configured frame interval

12. `A12` Commit success or fail
    - success only if solve/tracking/frame-count proofs all passed
    - write target result and failure reason if any
    - hand accepted frames to postflight
    - queue retry if policy allows

## Hard Rules

- no first exposure without fresh solve proof
- no continued run after tracking-off proof
- no silent partial success for science targets
- no target success on missing solve, tracking off, or too few accepted frames
- failed target stops with a clear reason
- pretty targets only run after science targets if time remains

## Evidence Expected

Each target should leave proof for:

- selected target
- scope readiness
- telemetry snapshot
- slew issued
- slew complete
- settle complete
- solve residual
- corrective retry result if used
- exposure plan
- accepted/rejected frames
- final target verdict

## Dry Run

```bash
seevar-next-flight steps \
  --plan data/tonights_plan.json \
  --proof data/flight_runs/flight_steps.jsonl \
  --human
```

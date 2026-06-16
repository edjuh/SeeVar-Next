# Flight

Flight is A1-A12 per target.

1. `A1` target lock
2. `A2` zero-state and safety gate
3. `A3` session telemetry valid
4. `A4` slew command
5. `A5` slew completion proof
6. `A6` settle after slew
7. `A7` fresh pointing solve
8. `A8` corrective nudge / retry when solve is off
9. `A9` exposure plan
10. `A10` expose and download
11. `A11` frame QC and FITS accept
12. `A12` commit success or fail for that target

Rules:

- no first exposure without fresh solve proof
- no target success on missing solve, tracking off, or too few accepted frames
- failed target stops with a clear reason
- pretty targets only run after science targets if time remains

Dry-run the full chain:

```bash
seevar-next-flight steps \
  --plan data/tonights_plan.json \
  --proof data/flight_runs/flight_steps.jsonl \
  --human
```

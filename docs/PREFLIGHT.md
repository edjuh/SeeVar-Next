# Preflight

Preflight is P1-P8:

1. `P1` load SeeVar catalogs from `catalogs/`
2. `P2` check weather and safety readiness
3. `P3` apply cadence and due-target filtering
4. `P4` compute dark window, horizon, moon, and altitude gates with `astropy`
5. `P5` probe enabled telescope inventory
6. `P6` require 3-point alignment / pointing model proof
7. `P7` write `data/tonights_plan.json` and export seestarpy JSON
8. `P8` final GO / NO-GO gate before submit

Old horizon panorama, fog, cloud, dashboard-only, and telescope-debug helpers are intentionally not carried forward.

## Commands

```bash
seevar-next-fetch-aavso --output catalogs/campaign_targets.json
seevar-next-fetch-vsx catalogs/campaign_targets.json --output data/vsx_catalog.json
seevar-next-preflight --catalog campaign_targets --lat 52.39 --lon 4.61 --output data/tonights_plan.json
seevar-next-seestarpy-plan --input data/tonights_plan.json --output data/seestarpy_plan.json
seevar-next-dryrun --plan data/tonights_plan.json --proof data/flight_runs/dryrun.jsonl --status data/status.json --limit 3
seevar-next-status --proof data/flight_runs/dryrun.jsonl --plan data/tonights_plan.json
seevar-next-readiness --config config/seevar-next.json
seevar-next-flight steps --plan data/tonights_plan.json --proof data/flight_runs/flight_steps.jsonl --human
seevar-next-flight validate --plan data/seestarpy_plan.json
seevar-next-flight submit --plan data/seestarpy_plan.json
seevar-next-flight status
```

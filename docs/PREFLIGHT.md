# Preflight

Preflight is now limited to useful work:

1. load SeeVar catalogs from `catalogs/`
2. optionally refresh AAVSO Target Tool and VSX cache
3. compute dark and observable windows with `astropy`
4. write `data/tonights_plan.json`
5. export the plan to seestarpy named-plan JSON
6. write proof rows for catalog and plan stages

Old horizon panorama, fog, cloud, dashboard-only, and telescope-debug helpers are intentionally not carried forward.

## Commands

```bash
seevar-next-fetch-aavso --output catalogs/campaign_targets.json
seevar-next-fetch-vsx catalogs/campaign_targets.json --output data/vsx_catalog.json
seevar-next-preflight --catalog campaign_targets --lat 52.39 --lon 4.61 --output data/tonights_plan.json
seevar-next-seestarpy-plan --input data/tonights_plan.json --output data/seestarpy_plan.json
seevar-next-dryrun --plan data/tonights_plan.json --proof data/flight_runs/dryrun.jsonl --status data/status.json --limit 3
seevar-next-status --proof data/flight_runs/dryrun.jsonl --plan data/tonights_plan.json
seevar-next-flight validate --plan data/seestarpy_plan.json
seevar-next-flight submit --plan data/seestarpy_plan.json
seevar-next-flight status
```

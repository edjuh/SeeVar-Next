# SeeVar Next Manual

SeeVar Next is a strict AAVSO workflow.

## Install

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Normal Use

```bash
seevar-next
```

Pick:

- `1` build tonight's plan
- `2` dry-run 3 targets
- `3` show status
- `4` refresh AAVSO catalog
- `5` submit seestarpy plan
- `6` show seestarpy plan status

Configuration lives in `config/seevar-next.json`.
Set `sun_alt_limit_deg` stricter or looser for your site and season.

## Daily Automatic Run

See [SYSTEMD.md](SYSTEMD.md).

## Manual Commands

Use these when debugging.

## Refresh Catalogs

```bash
export AAVSO_TARGET_TOOL_API_KEY="..."
seevar-next-fetch-aavso --output catalogs/campaign_targets.json
seevar-next-fetch-vsx catalogs/campaign_targets.json --output data/vsx_catalog.json --limit 20
```

## Build Tonight's Plan

```bash
seevar-next-preflight \
  --catalog campaign_targets \
  --lat 52.39 \
  --lon 4.61 \
  --output data/tonights_plan.json
```

## Export For Seestar

```bash
seevar-next-seestarpy-plan \
  --input data/tonights_plan.json \
  --output data/seestarpy_plan.json
```

## Submit Or Monitor Flight

```bash
seevar-next-flight validate --plan data/seestarpy_plan.json
seevar-next-flight submit --plan data/seestarpy_plan.json
seevar-next-flight status
seevar-next-flight stop
```

## Dry Run

```bash
seevar-next-dryrun \
  --plan data/tonights_plan.json \
  --proof data/flight_runs/dryrun.jsonl \
  --status data/status.json \
  --limit 3
```

## Status

```bash
seevar-next-status \
  --proof data/flight_runs/dryrun.jsonl \
  --plan data/tonights_plan.json \
  --output data/status.json
```

## Postflight

```bash
seevar-next-postflight /path/to/object_fits /path/to/photometry_catalog.json --output-dir data/postflight
```

## Success Rule

One object is successful only when proof exists for plan, execution, stack, WCS, photometry, and report.

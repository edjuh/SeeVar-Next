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
- `4` check readiness
- `5` refresh AAVSO catalog
- `6` submit seestarpy plan
- `7` show seestarpy plan status
- `8` show flight policy
- `9` show flight steps
- `10` monitor flight
- `11` start dashboard

Configuration lives in `config/seevar-next.json`.
Set `sun_alt_limit_deg` stricter or looser for your site and season.
Weather gates and telescope probe ports live in the same config.

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
seevar-next readiness
seevar-next-flight policy
seevar-next-flight steps --plan data/tonights_plan.json --proof data/flight_runs/flight_steps.jsonl --human
seevar-next-flight validate --plan data/seestarpy_plan.json
seevar-next-flight submit --plan data/seestarpy_plan.json
seevar-next-flight status --human --timeout-sec 12
seevar-next-flight monitor --human --samples 0 --interval-sec 30
seevar-next-flight stop
```

`seevar-next readiness` writes:

- `data/readiness.txt`: human-readable GO / NO-GO
- `data/readiness.json`: machine-readable state
- `data/flight_runs/readiness.jsonl`: proof rows

The operator `flight-submit` command runs readiness first and blocks submit on weather or telescope connection failure.

Flight status writes:

- `data/flight_policy.txt`: human-readable flight rules
- `data/flight_policy.json`: machine-readable flight rules
- `data/flight_steps.txt`: human-readable P/A/F chain dry run
- `data/flight_steps.json`: machine-readable P/A/F chain dry run
- `data/flight_status.txt`: human-readable running plan state
- `data/flight_status.json`: machine-readable running plan state
- `data/flight_runs/flight.jsonl`: proof rows

Current flight policy:

- submit whole plans, do not micromanage individual exposures unless forced
- primary adapter: `seestarpy`
- fallback adapter: `seestar_alp`
- target fails on missing solve, tracking off, or too few accepted frames
- failed science targets are reported and retried when time allows
- pretty targets are allowed only after science work has spare time

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

## Dashboard

```bash
seevar-next dashboard
```

Open `http://192.168.178.57:8765/`.

The dashboard is intentionally small: readiness, flight status, tonight's targets, proof status, and links to raw files.

## Postflight

```bash
seevar-next-postflight /path/to/object_fits /path/to/photometry_catalog.json --output-dir data/postflight
```

## Success Rule

One object is successful only when proof exists for plan, execution, stack, WCS, photometry, and report.

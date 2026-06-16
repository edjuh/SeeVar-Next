# SeeVar Next

Clean reboot of SeeVar: AAVSO-first, proof-driven, and built around standard astronomy libraries.

## Pipeline

1. **Preflight**: load catalogs, cadence, weather, dark window, horizon, and scope inventory.
2. **Flight**: submit/monitor a plan through `seestarpy` or `seestar_alp`.
3. **Postflight**: reject bad frames, stack, plate-solve, run photometry, stage AAVSO report.
4. **Proof**: every step writes JSON evidence and a clear pass/fail reason.

Workflow codes:

- `P1-P8` preflight
- `A1-A12` flight per target
- `F1-F8` postflight

## First Rule

No target is successful unless the whole chain passes:

`plan -> execute -> download -> QC -> stack -> solve -> photometry -> report`

## Development Start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[seestar,dev]"
pytest
```

## First Postflight Command

```bash
seevar-next-postflight /path/to/object_frames /path/to/catalog.json --output-dir data/postflight
```

The catalog is intentionally small at this stage:

```json
{
  "target": "ST Boo",
  "ra_deg": 210.0,
  "dec_deg": 40.0,
  "filter_name": "TG",
  "observer_code": "YOUR_AAVSO_CODE",
  "comparison_stars": [
    {"id": "C1", "ra_deg": 210.01, "dec_deg": 40.0, "mag": 12.1}
  ]
}
```

`TST`, `TEST`, and `UNKNOWN` are blocked before AAVSO report staging.

## Roadmap

Start with [ROADMAP.md](ROADMAP.md). It is the control document for this repo.

## First Preflight Commands

```bash
seevar-next
```

Or run directly:

```bash
seevar-next-preflight --catalog campaign_targets --lat 52.39 --lon 4.61 --output data/tonights_plan.json
seevar-next-seestarpy-plan --input data/tonights_plan.json --output data/seestarpy_plan.json
seevar-next-readiness --config config/seevar-next.json
```

`seevar-next-readiness` writes `data/readiness.txt` for humans and blocks unattended submit when weather or telescope connection checks fail.

Human flight status and dashboard:

```bash
seevar-next-flight steps --plan data/tonights_plan.json --proof data/flight_runs/flight_steps.jsonl --human
seevar-next-flight status --human
seevar-next dashboard
```

Use the configured dashboard URL from `config/seevar-next.json`. The default is `http://127.0.0.1:8765/`.

## Control Adapters

- `seestarpy` is the primary Python adapter: `pip install -e ".[seestar,dev]"`
- `seestar_alp` is a fallback control path, but not packaged as a Python dependency in this repo yet
- if you want fallback support, install and run the `seestar_alp` daemon separately

See [docs/MANUAL.md](docs/MANUAL.md), [docs/PREFLIGHT.md](docs/PREFLIGHT.md), [docs/FLIGHT.md](docs/FLIGHT.md), [docs/POSTFLIGHT.md](docs/POSTFLIGHT.md), [docs/SYSTEMD.md](docs/SYSTEMD.md), [docs/SALVAGE.md](docs/SALVAGE.md), and [CHANGELOG.md](CHANGELOG.md).

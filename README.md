# SeeVar Next

Clean reboot of SeeVar: AAVSO-first, proof-driven, and built around standard astronomy libraries.

## Pipeline

1. **Preflight**: load catalogs, cadence, weather, dark window, horizon, and scope inventory.
2. **Flight**: submit/monitor a plan through `seestarpy` or `seestar_alp`.
3. **Postflight**: reject bad frames, stack, plate-solve, run photometry, stage AAVSO report.
4. **Proof**: every step writes JSON evidence and a clear pass/fail reason.

## First Rule

No target is successful unless the whole chain passes:

`plan -> execute -> download -> QC -> stack -> solve -> photometry -> report`

## Development Start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
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
  "observer_code": "TST",
  "comparison_stars": [
    {"id": "C1", "ra_deg": 210.01, "dec_deg": 40.0, "mag": 12.1}
  ]
}
```

## Roadmap

Start with [ROADMAP.md](ROADMAP.md). It is the control document for this repo.

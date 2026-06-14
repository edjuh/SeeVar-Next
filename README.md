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

## Roadmap

Start with [ROADMAP.md](ROADMAP.md). It is the control document for this repo.

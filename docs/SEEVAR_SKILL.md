# SeeVar Next Skill

Use this project with the same discipline as SeeVar:

- no guessed telescope methods, ports, or payloads
- prove each phase before the next one starts
- keep planning, flight, and postflight separated
- prefer `astropy`, `photutils`, `seestarpy`
- treat `seestar_alp` as fallback, not default complexity
- no science success without solve, accepted frames, stack, photometry, and report
- document every operational rule in `ROADMAP.md`, `PREFLIGHT.md`, `FLIGHT.md`, or `POSTFLIGHT.md`
- mine old SeeVar logic docs before inventing new rules; start with `LOGIC_SALVAGE.md`

Current local rules:

- AAVSO-first
- one accepted science product per target per night
- failed targets get a clear reason and optional retry
- park when observations stop unless the next planned task requires the mount to stay live

# systemd

Use this when SeeVar Next should prepare or run unattended.

The supplied unit assumes the repo lives at `~/SeeVar-Next`.

## Automated Nightly Run

This builds the plan, checks weather and telescope reachability, then submits the seestarpy plan only if readiness passes.

```bash
mkdir -p ~/.config/systemd/user
cp deploy/systemd/seevar-next-nightly.service ~/.config/systemd/user/
cp deploy/systemd/seevar-next-nightly.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now seevar-next-nightly.timer
```

Check:

```bash
systemctl --user list-timers seevar-next-nightly.timer
journalctl --user -u seevar-next-nightly.service -n 100
cat ~/SeeVar-Next/data/readiness.txt
```

## Dashboard

```bash
mkdir -p ~/.config/systemd/user
cp deploy/systemd/seevar-next-dashboard.service ~/.config/systemd/user/
cp deploy/systemd/seevar-next-flight-monitor.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now seevar-next-dashboard.service
systemctl --user enable --now seevar-next-flight-monitor.service
```

Open `http://192.168.178.57:8765/`.

## Preflight Only

```bash
mkdir -p ~/.config/systemd/user
cp deploy/systemd/seevar-next-preflight.service ~/.config/systemd/user/
cp deploy/systemd/seevar-next-preflight.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now seevar-next-preflight.timer
```

## Check

```bash
systemctl --user list-timers seevar-next-preflight.timer
journalctl --user -u seevar-next-preflight.service -n 100
```

## Run Now

```bash
systemctl --user start seevar-next-preflight.service
systemctl --user start seevar-next-nightly.service
```

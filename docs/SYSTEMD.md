# systemd

Use this when SeeVar Next should prepare the plan every evening.

The supplied unit assumes the repo lives at `~/SeeVar-Next`.

## Install

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
```

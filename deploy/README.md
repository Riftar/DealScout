# EC2 deploy (builder-operated)

One **t3.small** in **us-east-1** on **Hackathon_VPC** serves the Dashboard at a public URL
and fires each Job once a day. AWS changes are the builder's; this folder holds the files
and the steps.

Three pieces run on the instance:

| Piece | What it does | File |
|---|---|---|
| Dashboard | `dealscout dashboard` on 127.0.0.1:8000: define Jobs, read a Job's Listing list | `dealscout-dashboard.service` |
| Tick | `dealscout tick` every minute: queues the Jobs whose daily time has come, carries out one queued Run | `dealscout.cron`, `tick.sh` |
| nginx | Publishes the Dashboard on port 80 and rate-limits writes | `nginx-dealscout.conf` |

Jobs and their Listing lists live in `data/state/jobs.sqlite`. Each Job's daily time is in
Asia/Jakarta and the tick converts it, so the instance clock stays on UTC. "Run now" on the
Dashboard starts a tick at once instead of waiting for cron. Runs never overlap: a tick that
finds a Run going exits.

## Prerequisites

- Ubuntu 22.04 or 24.04 AMI
- Outbound HTTPS for Portals and the model endpoint
- Security group: port 80 open to the world (the Dashboard is public), SSH to builder IPs only
- `.env` on the instance (not in git): `LLM_*`, `NEATLOGS_API_KEY`
- Repo clone at `/opt/dealscout`, owned by `ubuntu`
- Listing URLs in `data/urls/*.txt`. A Job reads the ones on its Portals.

## One-time setup

```bash
sudo apt-get update && sudo apt-get install -y git curl nginx
curl -LsSf https://astral.sh/uv/install.sh | sh
cd /opt/dealscout && uv sync
cp .env.example .env   # then edit with real keys on the instance only
sudo mkdir -p /var/log/dealscout && sudo chown ubuntu /var/log/dealscout
```

## Dashboard

```bash
sudo cp deploy/dealscout-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now dealscout-dashboard
curl -s http://127.0.0.1:8000/healthz   # ok
```

## nginx

```bash
sudo cp deploy/nginx-dealscout.conf /etc/nginx/sites-available/dealscout
sudo ln -sf /etc/nginx/sites-available/dealscout /etc/nginx/sites-enabled/dealscout
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

## Daily Runs

```bash
sudo cp deploy/dealscout.cron /etc/cron.d/dealscout
tail -f /var/log/dealscout/tick.log   # one line per Run carried out
```

A tick started by "Run now" logs to `data/state/tick.log` instead.

## Limits on a public site

Anyone who has the URL can define a Job, and every Run spends model money and Portal
requests. There are no accounts. What holds spend down:

- `DASHBOARD_MAX_ACTIVE_JOBS` (default 20): Jobs with daily Runs switched on.
- `DASHBOARD_MAX_RUN_NOW_PER_DAY` (default 3): "Run now" per Job per Jakarta day.
- One Run at a time on the instance, and one waiting Run per Job from "Run now".
- nginx allows six writes a minute per address.

Set the two variables in `.env` and restart the Dashboard to change them.

## How long a Run takes

A Run is one model call after another. On 11 Oct a Run over the 12 seed URLs took 31
minutes on the builder's machine (`hackathon.md`). A Run still marked as going after two
hours is treated as dead and marked failed, so keep a Job's URL list small enough to
finish inside that, or raise `STALE_AFTER` in `src/dealscout/dashboard/store.py`.

## What stays off the site

- Snapshots carry agents' names and phone numbers. They stay in `data/snapshots/`, which
  nothing serves.
- The Dashboard reads only `jobs.sqlite`. A Listing list holds the confirmed numbers, the
  Portal's Listing id and a link to the Listing; it holds no title, description or quote.
- The per-Run `report.html` under `data/runs/` quotes page text. It is not published.

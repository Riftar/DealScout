# EC2 deploy (builder-operated)

Optional hackathon credit: one **t3.small** in **us-east-1** on **Hackathon_VPC**
runs DealScout on a schedule and serves the latest report. AWS changes are the
builder's; this lane only documents the steps.

## Prerequisites

- Ubuntu 22.04 or 24.04 AMI on the instance
- Outbound HTTPS for Portals and the model endpoint
- `.env` on the instance (not in git): `LLM_*`, `NEATLOGS_API_KEY`
- Repo clone at `/opt/dealscout` (or similar)

## One-time setup

```bash
sudo apt-get update && sudo apt-get install -y git curl
curl -LsSf https://astral.sh/uv/install.sh | sh
cd /opt/dealscout && uv sync
cp .env.example .env   # then edit with real keys on the instance only
```

## Scheduled Run

Use `run-scheduled.sh` from cron (example: daily 06:00 UTC):

```cron
0 6 * * * /opt/dealscout/deploy/run-scheduled.sh >> /var/log/dealscout-run.log 2>&1
```

## Serve report

After a Run, `data/runs/<timestamp>/report.html` is produced (once the report
lane is merged). Serve that directory with nginx or `python -m http.server`
behind the instance security group. Do not expose `.env` or `data/snapshots/`.

## Security

- Snapshots contain listing pages with agent contact details; keep them on disk only.
- Restrict SSH and HTTP to builder IPs during the demo.

# Runbook: simulated API outage

**Scope:** the local Compose api container only. The simulation intentionally stops it for a short time. Do not use against shared or production workloads.

## Before the exercise

- Confirm the API contains only disposable lab data.
- Confirm http://127.0.0.1:8080/healthz is healthy.
- Record current commit, start time and recent logs.

## Execute

    ./incident-response/simulate-outage.sh docker
    ./incident-response/simulate-outage.sh podman

Expected behavior: the health probe fails while the service is stopped; the script starts the service again; the health probe recovers within the polling window. If recovery does not occur, inspect Compose status/logs, then manually start the service.

## Diagnose if recovery fails

    docker compose ps
    docker compose logs --tail=100 api
    docker compose exec -T api python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8080/readyz', timeout=2).read().decode())"

Check container start errors, volume ownership, DATA_FILE, port conflicts and malformed JSON. Preserve the first failure output before changing settings.

## After recovery

Verify /healthz, /readyz and /api/notes; compare records against the pre-incident sample. Record timestamps, actual observed symptoms, diagnostic steps, recovery time, data-loss assessment and preventive follow-ups in docs/postmortems/. Do not write that the drill passed until it has actually been executed.

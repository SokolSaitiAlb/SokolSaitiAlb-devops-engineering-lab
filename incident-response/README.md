# Incident response exercise

Read docs/runbooks/incident-response.md first. The outage script deliberately stops the local Compose service api; do not run it against an environment with real users or active work.

    ./incident-response/simulate-outage.sh docker
    ./incident-response/simulate-outage.sh podman

The script requires a healthy service before starting, verifies the probe fails while the container is stopped, restarts it and polls until health returns. If interrupted after the stop step, recover with docker compose start api or podman compose start api.

This repository does not pre-fill an incident result. After a real run, write the actual symptoms, timestamps, diagnostic evidence, recovery time and follow-up action in docs/postmortems/.

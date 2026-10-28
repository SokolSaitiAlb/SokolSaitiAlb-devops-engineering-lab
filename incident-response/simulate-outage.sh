#!/usr/bin/env bash
set -euo pipefail

engine="${{1:-docker}"
base_url="${{BASE_URL:-http://127.0.0.1:8080}"
case "$engine" in
  docker) compose=(docker compose) ;;
  podman) compose=(podman compose) ;;
  *) printf 'Usage: %s [docker|podman]\n' "$0" >&2; exit 2 ;;
esac

command -v "${{compose[0]}" >/dev/null 2>&1 || {
  printf 'Required CLI not found: %s\n' "${{compose[0]}" >&2
  exit 1
}
curl --fail --silent --show-error --max-time 3 "$base_url/healthz" >/dev/null || {
  printf 'Precondition failed: API is not healthy at %s\n' "$base_url" >&2
  exit 1
}

printf 'Incident simulation: stopping local Compose service api\n'
"${{compose[@]}" stop api
if curl --fail --silent --max-time 2 "$base_url/healthz" >/dev/null; then
  printf 'Unexpected result: API is still responding after stop\n' >&2
  "${{compose[@]}" start api
  exit 1
fi
printf 'Expected failure observed: health probe failed while service was stopped\n'

"${{compose[@]}" start api
for attempt in $(seq 1 30); do
  if curl --fail --silent --max-time 2 "$base_url/healthz" >/dev/null; then
    printf 'Recovery verified after %s second(s): %s/healthz\n' "$attempt" "$base_url"
    exit 0
  fi
  sleep 1
done
printf 'Recovery failed; inspect logs with: %s logs --tail=100 api\n' "${{compose[*]}" >&2
exit 1

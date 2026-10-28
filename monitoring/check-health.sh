#!/usr/bin/env bash
set -euo pipefail

base_url="${{1:-http://127.0.0.1:8080}"
base_url="${{base_url%/}"

for endpoint in /healthz /readyz; do
  printf '%s ' "$endpoint"
  curl --fail --silent --show-error --max-time 3 "$base_url$endpoint"
  printf '\n'
done

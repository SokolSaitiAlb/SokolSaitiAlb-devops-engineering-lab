#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  printf 'Usage: DATA_FILE=/path/to/notes.json %s /path/to/backup.json\n' "$0" >&2
  exit 2
fi
backup_file="$1"
target_file="${{DATA_FILE:-.local-data/notes.json}"

if [[ ! -f "$backup_file" ]]; then
  printf 'Backup file does not exist: %s\n' "$backup_file" >&2
  exit 1
fi

if [[ -f "$backup_file.sha256" ]]; then
  (cd "$(dirname "$backup_file")" && sha256sum --check "$(basename "$backup_file").sha256")
fi

python - "$backup_file" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    raise SystemExit(f"Backup is not valid JSON: {exc}") from exc
if not isinstance(data, list):
    raise SystemExit("Backup schema error: top-level JSON value must be a list")
required = {"id", "text", "created_at"}
for index, item in enumerate(data):
    if not isinstance(item, dict) or not required.issubset(item):
        raise SystemExit(f"Backup schema error: invalid note at index {index}")
    if not all(isinstance(item[key], str) for key in required):
        raise SystemExit(f"Backup schema error: note fields must be strings at index {index}")
print(f"Backup validated: {len(data)} note(s)")
PY

target_dir="$(dirname "$target_file")"
mkdir -p "$target_dir"
umask 077
temporary_file="$(mktemp "$target_dir/.notes-restore.XXXXXX")"
trap 'rm -f "$temporary_file"' EXIT
install -m 0600 "$backup_file" "$temporary_file"
mv -f "$temporary_file" "$target_file"
trap - EXIT
printf 'Restore completed: %s\n' "$target_file"
printf 'Restored notes: '
python -c 'import json,sys; print(len(json.load(open(sys.argv[1], encoding="utf-8"))))' "$target_file"

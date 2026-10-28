#!/usr/bin/env bash
set -euo pipefail

source_file="${{DATA_FILE:-.local-data/notes.json}"
backup_dir="${{BACKUP_DIR:-backups}"

if [[ ! -f "$source_file" ]]; then
  printf 'Source data file does not exist: %s\n' "$source_file" >&2
  exit 1
fi

umask 077
mkdir -p "$backup_dir"
chmod 700 "$backup_dir"
timestamp="$(date -u +%Y%m%dT%H%M%S%NZ)"
backup_file="$backup_dir/notes-$timestamp.json"
install -m 0600 "$source_file" "$backup_file"
(cd "$backup_dir" && sha256sum "$(basename "$backup_file")" > "$(basename "$backup_file").sha256")
printf 'Backup created: %s\n' "$backup_file"
printf 'Checksum: '
cat "$backup_file.sha256"

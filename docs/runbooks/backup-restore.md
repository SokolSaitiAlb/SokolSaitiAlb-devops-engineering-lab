# Runbook: backup and restore

## Local-file or systemd mode

1. Identify the exact DATA_FILE path and confirm available disk space.
2. Stop writes (for systemd: sudo systemctl stop ops-notes-api).
3. Back up with DATA_FILE=/path/to/notes.json BACKUP_DIR=/safe/path ./backup-restore/backup.sh.
4. Verify the backup file and its .sha256 checksum.
5. For restore, run DATA_FILE=/path/to/notes.json ./backup-restore/restore.sh /safe/path/notes-TIMESTAMP.json.
6. Start the service, probe /healthz and /readyz, then read /api/notes and verify expected note count/content.
7. Restore file/directory ownership and permissions for the service account. Record the observed result and elapsed time.

## Compose named-volume mode

Compose stores data in the notes-data named volume. To back up through the running service container (from the repository root):

    mkdir -p backups
    umask 077
    docker compose exec -T api cat /data/notes.json > backups/notes-compose.json
    sha256sum backups/notes-compose.json > backups/notes-compose.json.sha256

For Podman, replace docker compose with podman compose. Verify the file parses as a list of notes and store it off the host in a real deployment. To restore, stop the API first, copy the backup into the service container or a temporary helper container with the named volume mounted, verify JSON schema/checksum, then replace /data/notes.json atomically within that volume. Start the API and read the notes back. Do not mount a file onto /data/notes.json while the application is writing to it.

The commands above are a local exercise, not an off-site backup strategy. Define retention, encryption, access controls and recovery objectives when a real environment exists.

# Backup and restore drill

The scripts operate on a filesystem JSON file, such as .local-data/notes.json for local execution or /var/lib/ops-notes-api/notes.json for a systemd installation.

## Create a backup

    DATA_FILE=.local-data/notes.json BACKUP_DIR=backups ./backup-restore/backup.sh

The script writes a mode-0600 copy and SHA-256 checksum in a mode-0700 directory. Save backups outside the data disk in a real deployment; the local folder is only an exercise.

## Restore a backup

    DATA_FILE=.local-data/notes.json ./backup-restore/restore.sh backups/notes-TIMESTAMP.json

The restore checks the optional checksum, validates JSON shape, and replaces the target atomically. Stop writes before restoring and verify /api/notes afterwards. For systemd, stop the service before restore and start it again after validating ownership. For the Compose named volume, use the volume-aware procedure in docs/runbooks/backup-restore.md; do not assume a host path maps directly to /data.

A restore is not proven until the restored records are read back successfully. Record backup time, source, checksum, restore time and verification result.

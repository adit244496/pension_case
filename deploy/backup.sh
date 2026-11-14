#!/usr/bin/env bash
# Back up the database and generated documents.
#   sudo bash deploy/backup.sh [destination]
# Add to cron:  0 21 * * * /opt/pension/deploy/backup.sh >> /var/log/pension-backup.log 2>&1
set -euo pipefail

DATA_DIR="${DATA_DIR:-/var/lib/pension}"
DEST="${1:-/var/backups/pension}"
STAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$DEST"

# SQLite must be copied with its own backup command, not cp, so a write in
# progress cannot produce a torn file.
sqlite3 "$DATA_DIR/pension.db" ".backup '$DEST/pension-$STAMP.db'"

tar -czf "$DEST/storage-$STAMP.tar.gz" -C "$DATA_DIR" storage

# Keep a fortnight.
find "$DEST" -name 'pension-*.db' -mtime +14 -delete
find "$DEST" -name 'storage-*.tar.gz' -mtime +14 -delete

echo "$(date -Is) backup written to $DEST"

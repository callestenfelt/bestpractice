#!/usr/bin/env bash
# Daily SQLite backup for bestpractice.db.
#
# Uses `sqlite3 .backup` (online, lock-safe — safe to run while the Flask
# app is serving) into a temp file, gzips it, atomically renames into
# place, then prunes anything older than RETAIN_DAYS.
#
# Invoked by bestpractice-backup.service (systemd, daily timer).
# Exit non-zero on any failure so systemd marks the unit failed and
# `systemctl status` surfaces it.

set -euo pipefail

DB="${BESTPRACTICE_DB:-/opt/bestpractice/data/bestpractice.db}"
DEST_DIR="${BESTPRACTICE_BACKUP_DIR:-/var/backups/bestpractice}"
RETAIN_DAYS="${BESTPRACTICE_BACKUP_RETAIN_DAYS:-14}"

if [[ ! -f "$DB" ]]; then
  echo "backup_db: source DB not found at $DB" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FINAL="$DEST_DIR/bestpractice-$STAMP.db.gz"
TMP_DB="$DEST_DIR/.bestpractice-$STAMP.db.tmp"
TMP_GZ="$DEST_DIR/.bestpractice-$STAMP.db.gz.tmp"

cleanup() { rm -f "$TMP_DB" "$TMP_GZ"; }
trap cleanup EXIT

# `.backup` honors WAL + concurrent readers/writers and produces a
# consistent snapshot. `cp` on a live DB can produce a corrupt file.
sqlite3 "$DB" ".backup '$TMP_DB'"

# Quick smoke test — fail fast if the snapshot is unreadable.
sqlite3 "$TMP_DB" "PRAGMA integrity_check;" > /dev/null

gzip -c "$TMP_DB" > "$TMP_GZ"
mv "$TMP_GZ" "$FINAL"
rm -f "$TMP_DB"
trap - EXIT

# Retention: delete backups older than RETAIN_DAYS. -mtime +N means
# "modified more than N*24h ago", so +14 keeps roughly two weeks.
find "$DEST_DIR" -maxdepth 1 -type f -name 'bestpractice-*.db.gz' \
  -mtime "+$RETAIN_DAYS" -delete

echo "backup_db: wrote $FINAL"

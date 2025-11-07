#!/usr/bin/env python3
"""
Restore the `outputs/` folder from the most recent `outputs_backup_YYYYMMDD_HHMMSS` directory.

Usage: python scripts/restore_outputs_from_backup.py [--backup <path>] [--dry-run]

- If --backup is provided, restores from that specific backup directory.
- If not provided, the script picks the newest outputs_backup_* directory in the repo root.
- --dry-run will only print actions without performing filesystem changes.

This script will:
- remove the current `outputs/` directory (after backing it up to a temp folder named outputs_before_restore_TIMESTAMP)
- copy the chosen backup into `outputs/`

Use with care. The backup folder created earlier by the assistant is safe and timestamped.
"""
import argparse
import shutil
from pathlib import Path
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'

parser = argparse.ArgumentParser(description='Restore outputs from a backup folder')
parser.add_argument('--backup', '-b', help='Path to backup folder to restore from')
parser.add_argument('--dry-run', action='store_true', help='Print actions without performing them')
args = parser.parse_args()

# find backup
if args.backup:
    backup_path = Path(args.backup)
    if not backup_path.exists():
        print('Specified backup does not exist:', backup_path)
        sys.exit(2)
else:
    # find newest outputs_backup_* folder in ROOT
    backups = sorted([p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith('outputs_backup_')], key=lambda p: p.stat().st_mtime)
    if not backups:
        print('No outputs_backup_* folders found in', ROOT)
        sys.exit(1)
    backup_path = backups[-1]

print('Will restore from backup:', backup_path)
print('Target outputs folder:', OUT)
if args.dry_run:
    print('Dry run - no changes will be made.')
    sys.exit(0)

# create a before-restore snapshot in case user wants to recover
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
before = ROOT / f'outputs_before_restore_{ts}'
if OUT.exists():
    print('Backing current outputs to', before)
    shutil.copytree(OUT, before)
else:
    print('No existing outputs folder to back up')

# remove current outputs
if OUT.exists():
    print('Removing current outputs folder:', OUT)
    shutil.rmtree(OUT)

# copy backup to outputs
print('Copying', backup_path, '->', OUT)
shutil.copytree(backup_path, OUT)

print('Restore complete. A snapshot of the replaced outputs is at:', before)
print('If you want to revert this restore, you can run this script again and pass --backup', before)

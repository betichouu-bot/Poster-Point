Restore instructions for `outputs/` backups

What I created
- `scripts/restore_outputs_from_backup.py` — a small Python helper that restores the project's `outputs/` directory from the most recent `outputs_backup_YYYYMMDD_HHMMSS` folder (or from a backup you provide).
- Earlier, I created a timestamped backup of `outputs/` (for example: `outputs_backup_20251103_150102`).
- The inputs renames mapping is in `rename_map_inputs.csv` (you can inspect or use it to undo input renames manually).

How to restore the outputs (safe)
1. Stop any running server that may be serving files from this folder.
2. Run the restore script in a terminal from the repo root.

PowerShell example (dry-run first):

```powershell
# dry-run - see what would happen
python .\scripts\restore_outputs_from_backup.py --dry-run

# actually restore (will back the current outputs to outputs_before_restore_<ts>)
python .\scripts\restore_outputs_from_backup.py

# or restore from a specific backup
python .\scripts\restore_outputs_from_backup.py --backup .\outputs_backup_20251103_150102
```

Notes
- The script will create a snapshot of the current `outputs/` as `outputs_before_restore_<timestamp>` before it overwrites it.
- If you want an undo for input renames, use `rename_map_inputs.csv` in the repo root — it lists old_path,new_path for the images under `images/PINTEREST IMAGES/`.
- If you want me to create a dedicated undo script for input renames or to reconstruct an outputs mapping CSV, I can do that next.

# Zoom 1132 reset helper

This repository provides a small, cross-platform Python command-line utility to reset Zoom after encountering the **1132** error. The script:

- Detects and terminates running Zoom-related processes (optional).
- Backs up Zoom configuration, cache, preference, web data, and log files across Windows, macOS, and Linux (including Flatpak installs).
- Moves the files to a timestamped backup directory so you can restore them if needed.

## Usage

1. Ensure Python 3.9+ is installed.
2. Run the tool directly:

```bash
python -m zoom_reset           # Performs the reset
python -m zoom_reset --dry-run # Show what would happen without changes
```

Options:
- `--dry-run` – print actions without terminating processes or moving files.
- `--skip-kill` – skip terminating running Zoom processes.
- `--backup-dir PATH` – override the backup location (defaults to `~/.zoom-reset-backups`).

After the tool completes, reopen Zoom and sign in again.

### Create a single-file macOS executable

If you want a double-clickable, single-file version for macOS, generate a `.pyz` executable using Python’s built-in `zipapp`:

```bash
python package_macos.py --output zoom-reset-1132-macos.pyz
```

Then transfer `zoom-reset-1132-macos.pyz` to your macOS machine, make sure it is executable (`chmod +x zoom-reset-1132-macos.pyz` if needed), and run it directly:

```bash
./zoom-reset-1132-macos.pyz --dry-run --skip-kill
```

## Notes

- The utility supports Windows, macOS, and Linux. Unsupported systems will report an error and exit safely.
- Files are **moved**, not deleted, to make recovery easy.
- On macOS, caches, cookies, logs, and WebKit data are cleared in addition to the main `zoom.us` folder to address stubborn 1132 cases.
- On Windows, both Roaming and Local AppData Zoom folders (including ZoomOpener and temp data) are cleared to eliminate corrupted profiles.
- On Linux (including Flatpak installs), configuration, cache, and legacy `~/.zoom` data are cleared.
- If you are running the script on Windows, open the terminal with administrator privileges to ensure processes can be terminated.

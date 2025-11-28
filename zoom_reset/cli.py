from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import platform
import shutil
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


@dataclass
class ProcessInfo:
    pid: int
    name: str
    command: str | None = None


SUPPORTED_SYSTEMS = {
    "Windows": "windows",
    "Darwin": "macos",
    "Linux": "linux",
}


class UnsupportedSystemError(RuntimeError):
    pass


def detect_system() -> str:
    raw_name = platform.system()
    if raw_name not in SUPPORTED_SYSTEMS:
        raise UnsupportedSystemError(f"Unsupported platform: {raw_name}")
    return SUPPORTED_SYSTEMS[raw_name]


def parse_ps_output(output: str) -> List[ProcessInfo]:
    processes: List[ProcessInfo] = []
    for line in output.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) < 2:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        name = parts[1]
        command = parts[2] if len(parts) > 2 else None
        text = " ".join(parts[1:]).lower()
        if "zoom" in text:
            processes.append(ProcessInfo(pid=pid, name=name, command=command))
    return processes


def parse_tasklist_output(output: str) -> List[ProcessInfo]:
    processes: List[ProcessInfo] = []
    reader = csv.reader(output.splitlines())
    for row in reader:
        if not row:
            continue
        name = row[0].strip()
        if not name:
            continue
        if "zoom" not in name.lower():
            continue
        try:
            pid = int(row[1]) if len(row) > 1 else None
        except ValueError:
            pid = None
        if pid is None:
            continue
        processes.append(ProcessInfo(pid=pid, name=name))
    return processes


def list_zoom_processes(system_name: str) -> List[ProcessInfo]:
    if system_name in {"macos", "linux"}:
        output = subprocess.check_output(["ps", "-eo", "pid,comm,args"], text=True)
        return parse_ps_output(output)
    if system_name == "windows":
        output = subprocess.check_output(["tasklist", "/FO", "CSV", "/NH"], text=True)
        return parse_tasklist_output(output)
    raise UnsupportedSystemError(system_name)


def kill_processes(processes: Sequence[ProcessInfo], dry_run: bool = False) -> None:
    for proc in processes:
        if dry_run:
            print(f"Would terminate {proc.name} (PID {proc.pid})")
            continue
        try:
            os.kill(proc.pid, signal.SIGTERM)
            print(f"Terminated {proc.name} (PID {proc.pid})")
        except ProcessLookupError:
            print(f"Process {proc.pid} not found; skipping")
        except PermissionError as exc:
            print(f"Permission denied terminating {proc.pid}: {exc}")


def _append_unique(paths: List[Path], path: Path) -> None:
    if path not in paths:
        paths.append(path)


def zoom_paths(system_name: str, *, env: os._Environ[str] | None = None, home: Path | None = None) -> List[Path]:
    """Return the set of Zoom-related paths to clear for a full 1132 reset."""

    env = env or os.environ
    home = home or Path.home()
    paths: List[Path] = []

    if system_name == "windows":
        appdata = Path(env.get("APPDATA", home / "AppData" / "Roaming"))
        localappdata = Path(env.get("LOCALAPPDATA", home / "AppData" / "Local"))

        for candidate in [
            appdata / "Zoom",
            localappdata / "Zoom",
            appdata / "zoom.us",
            localappdata / "zoom.us",
            localappdata / "ZoomOpener",
            localappdata / "Temp" / "zoom",
        ]:
            _append_unique(paths, candidate)

    elif system_name == "macos":
        base = home / "Library"
        for candidate in [
            base / "Application Support" / "zoom.us",
            base / "Application Support" / "ZoomOpener",
            base / "Preferences" / "us.zoom.xos.plist",
            base / "Caches" / "us.zoom.xos",
            base / "Logs" / "zoom.us",
            base / "WebKit" / "us.zoom.xos",
            base / "Cookies" / "us.zoom.xos.binarycookies",
        ]:
            _append_unique(paths, candidate)

    elif system_name == "linux":
        for candidate in [
            home / ".config" / "zoom",
            home / ".cache" / "zoom",
            home / ".zoom",
            home / ".var" / "app" / "us.zoom.Zoom",
            home / ".cache" / "ZoomOpener",
        ]:
            _append_unique(paths, candidate)
    else:
        raise UnsupportedSystemError(system_name)

    return paths


def ensure_backup_root(path: Path | None = None) -> Path:
    if path is None:
        path = Path.home() / ".zoom-reset-backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def timestamped_backup_dir(root: Path) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = root / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def backup_and_remove(target: Path, backup_root: Path, *, dry_run: bool = False) -> None:
    if not target.exists():
        return
    destination = backup_root / target.name
    if destination.exists():
        destination = Path(f"{destination}-{dt.datetime.now().strftime('%H%M%S')}")
    if dry_run:
        print(f"Would move {target} to {destination}")
        return
    print(f"Moving {target} to backup {destination}")
    shutil.move(str(target), str(destination))


def perform_reset(
    *, dry_run: bool = False, backup_root: Path | None = None, skip_process_kill: bool = False
) -> None:
    system_name = detect_system()
    print(f"Detected system: {system_name}")

    if not skip_process_kill:
        processes = list_zoom_processes(system_name)
        if processes:
            print(f"Found {len(processes)} running Zoom process(es)")
            kill_processes(processes, dry_run=dry_run)
        else:
            print("No Zoom processes found")
    else:
        print("Skipping process termination step")

    backup_root = ensure_backup_root(backup_root)
    backup_dir = timestamped_backup_dir(backup_root)

    targets = zoom_paths(system_name)
    for path in targets:
        backup_and_remove(path, backup_dir, dry_run=dry_run)

    print("Reset complete. You can reopen Zoom and sign in again.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reset Zoom data after a 1132 error")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without executing them")
    parser.add_argument(
        "--skip-kill", action="store_true", help="Do not attempt to terminate running Zoom processes"
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="Directory to store backups (default: ~/.zoom-reset-backups)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        perform_reset(
            dry_run=args.dry_run, backup_root=args.backup_dir, skip_process_kill=args.skip_kill
        )
    except UnsupportedSystemError as exc:
        parser.error(str(exc))
        return 1
    except subprocess.CalledProcessError as exc:
        parser.error(f"Failed to query running processes: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

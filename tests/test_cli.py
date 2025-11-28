import os
from pathlib import Path

import zoom_reset.cli as cli


def test_parse_ps_output_finds_zoom():
    sample = """  PID COMMAND         ARGS
 1234 Zoom            /Applications/zoom.us/Zoom.exe
 4321 otherproc       /bin/other
"""
    procs = cli.parse_ps_output(sample)
    assert len(procs) == 1
    assert procs[0].pid == 1234
    assert procs[0].name == "Zoom"


def test_parse_tasklist_output_finds_zoom():
    sample = """"Zoom.exe","1234","","",""
"Other.exe","5678","","",""
"""
    procs = cli.parse_tasklist_output(sample)
    assert len(procs) == 1
    assert procs[0].pid == 1234
    assert procs[0].name == "Zoom.exe"


def test_zoom_paths_windows_env_overrides(tmp_path, monkeypatch):
    env = {"APPDATA": str(tmp_path / "roam"), "LOCALAPPDATA": str(tmp_path / "local")}
    paths = cli.zoom_paths("windows", env=env, home=Path("/unused"))
    assert tmp_path / "roam" / "Zoom" in paths
    assert tmp_path / "local" / "Zoom" in paths
    assert tmp_path / "local" / "ZoomOpener" in paths


def test_zoom_paths_macos():
    home = Path("/Users/tester")
    paths = cli.zoom_paths("macos", home=home)
    assert home / "Library" / "Application Support" / "zoom.us" in paths
    assert home / "Library" / "Preferences" / "us.zoom.xos.plist" in paths
    assert home / "Library" / "Cookies" / "us.zoom.xos.binarycookies" in paths


def test_zoom_paths_linux():
    home = Path("/home/tester")
    paths = cli.zoom_paths("linux", home=home)
    assert home / ".config" / "zoom" in paths
    assert home / ".var" / "app" / "us.zoom.Zoom" in paths


def test_backup_directory_created(tmp_path):
    root = cli.ensure_backup_root(tmp_path / "backups")
    assert root.exists()
    backup_dir = cli.timestamped_backup_dir(root)
    assert backup_dir.exists()


def test_backup_and_remove_moves_path(tmp_path):
    target = tmp_path / "Zoom"
    target.mkdir()
    (target / "data").write_text("sample")

    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()

    cli.backup_and_remove(target, backup_dir)
    assert not target.exists()
    moved = backup_dir / "Zoom"
    assert moved.exists()
    assert (moved / "data").read_text() == "sample"

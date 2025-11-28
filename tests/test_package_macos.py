import subprocess
import sys
from pathlib import Path

from package_macos import build_single_file


def test_builds_single_file_executable(tmp_path: Path) -> None:
    output = tmp_path / "zoom-reset-1132-macos.pyz"
    built = build_single_file(output)

    assert built == output
    assert output.exists()

    run_output = subprocess.check_output(
        [sys.executable, str(output), "--dry-run", "--skip-kill", "--backup-dir", str(tmp_path / "backup")],
        text=True,
    )

    assert "Detected system" in run_output

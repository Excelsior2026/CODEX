"""Create a single-file macOS-friendly executable for the Zoom 1132 reset tool.

Usage:
    python package_macos.py --output zoom-reset-1132-macos.pyz
"""
from __future__ import annotations

import argparse
import shutil
import stat
import tempfile
import zipapp
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PACKAGE_DIR = PROJECT_ROOT / "zoom_reset"
DEFAULT_OUTPUT = PROJECT_ROOT / "zoom-reset-1132-macos.pyz"


class PackageError(RuntimeError):
    pass


def build_single_file(output: Path = DEFAULT_OUTPUT) -> Path:
    if not PACKAGE_DIR.exists():
        raise PackageError(f"Zoom reset package not found at {PACKAGE_DIR}")

    with tempfile.TemporaryDirectory() as tmpdir:
        staging = Path(tmpdir) / "app"
        staging.mkdir(parents=True, exist_ok=True)

        shutil.copytree(PACKAGE_DIR, staging / "zoom_reset")

        zipapp.create_archive(
            source=staging,
            target=output,
            interpreter="/usr/bin/env python3",
            main="zoom_reset.__main__:main",
            compressed=True,
        )

    output.chmod(output.stat().st_mode | stat.S_IEXEC)
    return output


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package the Zoom reset tool into a single macOS executable")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,\



        
        help=f"Output path for the executable (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output = build_single_file(args.output)
    print(f"Wrote macOS single-file executable to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic
"""Bump version across all files that track it.

Usage:
    python bump_version.py 0.2.0
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

FILES = {
    "VERSION": None,
    "watch/__init__.py": re.compile(r'(__version__\s*=\s*")[^"]+(")', re.MULTILINE),
    "frontend/package.json": None,
}


def bump(version: str) -> None:
    # VERSION
    (ROOT / "VERSION").write_text(version + "\n")
    print(f"  VERSION -> {version}")

    # watch/__init__.py
    init = ROOT / "watch/__init__.py"
    text = init.read_text()
    text = FILES["watch/__init__.py"].sub(rf"\g<1>{version}\2", text)
    init.write_text(text)
    print(f"  watch/__init__.py -> {version}")

    # frontend/package.json
    pkg = ROOT / "frontend/package.json"
    data = json.loads(pkg.read_text())
    data["version"] = version
    pkg.write_text(json.dumps(data, indent=2) + "\n")
    print(f"  frontend/package.json -> {version}")

    print(f"\nDone. All files updated to {version}.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <version>")
        sys.exit(1)
    version = sys.argv[1]
    if not re.match(r"^\d+\.\d+\.\d+(-\w+(\.\d+)?)?$", version):
        print(f"Invalid version: {version}")
        sys.exit(1)
    bump(version)

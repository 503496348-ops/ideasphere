#!/usr/bin/env python3
"""One-click setup for this product repository.

Default mode installs lightweight declared dependencies when possible.
Set ONECLICK_SKIP_DEP_INSTALL=1 to run structural setup checks without network installs.
"""
from __future__ import annotations
import os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(cmd: list[str], *, optional: bool=False) -> None:
    print("$ " + " ".join(cmd))
    try:
        subprocess.check_call(cmd, cwd=ROOT)
    except FileNotFoundError:
        if optional:
            print(f"SKIP: command not found: {cmd[0]}")
            return
        raise


def main() -> int:
    print(f"== One-click setup: {ROOT.name} ==")
    py = sys.executable
    skip_install = os.environ.get("ONECLICK_SKIP_DEP_INSTALL") == "1"
    reqs = [p for p in [ROOT/'requirements.txt', ROOT/'requirements-dev.txt'] if p.exists()]
    if reqs:
        if skip_install:
            print("SKIP dependency install because ONECLICK_SKIP_DEP_INSTALL=1")
        else:
            run([py, '-m', 'pip', 'install', '-r', str(reqs[0])])
    pkg = ROOT/'package.json'
    lock = ROOT/'package-lock.json'
    if pkg.exists() and lock.exists():
        if skip_install:
            print("SKIP npm ci because ONECLICK_SKIP_DEP_INSTALL=1")
        else:
            run(['npm', 'ci'], optional=True)
    elif pkg.exists() and (ROOT/'node_modules').exists():
        print("node_modules already present")
    print("setup complete; running doctor next")
    run([py, 'scripts/doctor.py'])
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

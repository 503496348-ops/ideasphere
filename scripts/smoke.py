#!/usr/bin/env python3
"""One-click smoke test: verifies the repository can be exercised after setup.

This smoke intentionally avoids vendored research snapshots, docs examples, build
artifacts, and archived subprojects. Historical repositories may contain those
files and still be usable through the declared product entrypoints.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_PARTS = {'.git','node_modules','.venv','venv','__pycache__','.pytest_cache','dist','build','docs','examples','example','redteam','AIG-PromptSecurity'}

def run(cmd: list[str]) -> None:
    print('$ ' + ' '.join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)

def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_PARTS for part in path.relative_to(ROOT).parts)

def declared_python_targets() -> list[Path]:
    targets = [ROOT/'scripts/doctor.py', ROOT/'scripts/setup.py', ROOT/'scripts/smoke.py']
    gate = ROOT/'scripts/product_convergence_gate.py'
    if gate.exists():
        targets.append(gate)
    cfg = ROOT/'product_convergence.json'
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text())
            for key in ('entrypoints','smoke_targets'):
                for rel in data.get(key, []) or []:
                    p = ROOT/rel
                    if p.exists() and p.suffix == '.py' and not is_excluded(p):
                        targets.append(p)
        except Exception as exc:
            print(f'WARN: product_convergence.json not parsed for compile targets: {exc}')
    # include importable first-party packages only, not arbitrary vendored trees
    for p in ROOT.iterdir():
        if p.is_dir() and not is_excluded(p) and (p/'__init__.py').exists():
            targets.append(p)
    seen=[]
    for p in targets:
        if p.exists() and p not in seen:
            seen.append(p)
    return seen

def main() -> int:
    print(f"== Smoke: {ROOT.name} ==")
    run([sys.executable, 'scripts/doctor.py'])
    gate = ROOT/'scripts/product_convergence_gate.py'
    if gate.exists():
        run([sys.executable, 'scripts/product_convergence_gate.py', '--json'])
    targets = declared_python_targets()
    print('compile targets:', ', '.join(str(p.relative_to(ROOT)) for p in targets))
    for p in targets:
        if p.is_dir():
            run([sys.executable, '-m', 'compileall', '-q', str(p.relative_to(ROOT))])
        else:
            run([sys.executable, '-m', 'py_compile', str(p.relative_to(ROOT))])
    print('smoke result: PASS')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Human-readable environment doctor for one-click users."""
from __future__ import annotations
import json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def check(name: str, ok: bool, fix: str="") -> bool:
    mark = "OK" if ok else "FAIL"
    print(f"[{mark}] {name}" + (f" — {fix}" if (not ok and fix) else ""))
    return ok


def main() -> int:
    print(f"== Doctor: {ROOT.name} ==")
    ok = True
    ok &= check('README.md exists', (ROOT/'README.md').exists(), '缺 README，用户无法按步骤安装')
    ok &= check('SKILL.md exists', (ROOT/'SKILL.md').exists(), '缺 SKILL.md，产品说明不完整')
    ok &= check('install.sh exists', (ROOT/'install.sh').exists(), '运行: bash install.sh')
    ok &= check('setup.py exists', (ROOT/'scripts/setup.py').exists(), '缺一键 setup 入口')
    ok &= check('smoke.py exists', (ROOT/'scripts/smoke.py').exists(), '缺核心 smoke 入口')
    ok &= check('python available', shutil.which('python3') is not None or shutil.which('python') is not None, '请安装 Python 3')
    pkg = ROOT/'package.json'
    if pkg.exists():
        try:
            scripts = json.loads(pkg.read_text()).get('scripts', {})
        except Exception as exc:
            ok &= check('package.json parseable', False, f'JSON 解析失败: {exc}')
            scripts = {}
        for script in ['setup','doctor','smoke','test']:
            ok &= check(f'npm script {script}', script in scripts, f'在 package.json scripts 中补充 {script}')
    else:
        print('[INFO] package.json absent; shell/python one-click path is primary')
    gate = ROOT/'scripts/product_convergence_gate.py'
    if gate.exists():
        try:
            subprocess.check_call([sys.executable, str(gate), '--json'], cwd=ROOT, stdout=subprocess.DEVNULL)
            ok &= check('product convergence gate', True)
        except Exception:
            ok &= check('product convergence gate', False, '运行 python scripts/product_convergence_gate.py --json 查看详情')
    print('doctor result:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1

if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Human-readable environment doctor for one-click users."""
from __future__ import annotations
import json, shutil, subprocess, sys
from anti_ai_style_guard import collect_style_guard_report
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def collect_run_report(root: Path | None = None) -> dict:
    root = root or ROOT
    checks: list[dict] = []
    ok = True

    def add(name: str, passed: bool, fix: str = "") -> None:
        nonlocal ok
        ok &= passed
        checks.append({'name': name, 'ok': passed, 'fix': fix})

    add('README.md exists', (root/'README.md').exists(), '缺 README，用户无法按步骤安装')
    add('SKILL.md exists', (root/'SKILL.md').exists(), '缺 SKILL.md，产品说明不完整')
    add('install.sh exists', (root/'install.sh').exists(), '运行: bash install.sh')
    add('setup.py exists', (root/'scripts/setup.py').exists(), '缺一键 setup 入口')
    add('smoke.py exists', (root/'scripts/smoke.py').exists(), '缺核心 smoke 入口')
    add('python available', shutil.which('python3') is not None or shutil.which('python') is not None, '请安装 Python 3')

    pkg = root/'package.json'
    if pkg.exists():
        try:
            scripts = json.loads(pkg.read_text()).get('scripts', {})
            for script in ['setup','doctor','smoke','test']:
                add(f'npm script {script}', script in scripts, f'在 package.json scripts 中补充 {script}')
        except Exception as exc:
            add('package.json parseable', False, f'JSON 解析失败: {exc}')
    else:
        print('[INFO] package.json absent; shell/python one-click path is primary')

    slop = collect_style_guard_report(root)
    for item in slop.get('checks', []):
        checks.append(item)

    gate = root/'scripts/product_convergence_gate.py'
    if gate.exists():
        try:
            subprocess.check_call([sys.executable, str(gate), '--json'], cwd=root, stdout=subprocess.DEVNULL)
            add('product convergence gate', True)
        except Exception:
            add('product convergence gate', False, '运行 python scripts/product_convergence_gate.py --json 查看详情')

    return {
        'checked_at': datetime.utcnow().isoformat() + 'Z',
        'passed': ok,
        'checks': checks,
    }


def check(name: str, ok: bool, fix: str = "") -> bool:
    mark = "OK" if ok else "FAIL"
    print(f"[{mark}] {name}" + (f" — {fix}" if (not ok and fix) else ""))
    return ok


def main() -> int:
    report = collect_run_report(ROOT)
    for item in report['checks']:
        mark = 'OK' if item['ok'] else 'FAIL'
        print(f"[{mark}] {item['name']}" + (f" — {item['fix']}" if (not item['ok'] and item['fix']) else ""))
    print('doctor result:', 'PASS' if report['passed'] else 'FAIL')
    if '--format' in sys.argv and 'json' in sys.argv:
        print(json.dumps({'passed': report['passed'], 'checks': report['checks'], 'checked_at': report['checked_at']}, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

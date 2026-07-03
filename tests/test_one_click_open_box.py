from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_one_click_files_exist():
    for rel in ['install.sh', 'scripts/setup.py', 'scripts/doctor.py', 'scripts/smoke.py']:
        assert (ROOT / rel).exists(), f'missing {rel}'


def test_readme_has_three_command_quickstart():
    readme = (ROOT / 'README.md').read_text(encoding='utf-8', errors='ignore')
    assert '一键安装' in readme or 'One-click' in readme
    assert 'bash install.sh' in readme
    assert 'python3 scripts/doctor.py' in readme
    assert 'python3 scripts/smoke.py' in readme


def test_package_scripts_when_present():
    pkg = ROOT / 'package.json'
    if not pkg.exists():
        return
    scripts = json.loads(pkg.read_text(encoding='utf-8')).get('scripts', {})
    for name in ['setup', 'doctor', 'smoke', 'test']:
        assert name in scripts, f'package.json missing npm script: {name}'


def test_doctor_and_smoke_entrypoints_run():
    env = os.environ.copy()
    env['ONECLICK_SKIP_DEP_INSTALL'] = '1'
    subprocess.check_call([sys.executable, 'scripts/doctor.py'], cwd=ROOT, env=env)
    subprocess.check_call([sys.executable, 'scripts/smoke.py'], cwd=ROOT, env=env)

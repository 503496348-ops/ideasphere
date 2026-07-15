#!/usr/bin/env python3
"""Anti-AI static style guard for Ideasphere.

This script emits non-blocking checks aligned with kill-ai-slop + jakub style hygiene:
- excessive emoji density
- repeated gradient usage markers
- excessive all-caps tokens
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]

RULES = [
    {
        "name": "文本 emoji 过密（可能偏机器默认语体）",
        "pattern": re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]"),
        "limit": 28,
    },
    {
        "name": "过多渐变/滤镜式视觉标记（模板化倾向）",
        "pattern": re.compile(r"linear-gradient\(|radial-gradient\(|conic-gradient\(|filter:\s*blur\(|backdrop-filter", re.IGNORECASE),
        "limit": 44,
    },
    {
        "name": "过量全大写词（口号化倾向）",
        "pattern": re.compile(r"\b[A-Z]{5,}\b"),
        "limit": 28,
    },
]

TARGET_EXTENSIONS = {".md", ".txt", ".py", ".json", ".yml", ".yaml", ".js", ".ts", ".tsx", ".css", ".html", ".mdx"}


def _iter_text_files(root: Path):
    for p in root.rglob('*'):
        if not p.is_file():
            continue
        if '.git' in p.parts or p.name == 'anti_ai_style_guard.py':
            continue
        if p.suffix.lower() not in TARGET_EXTENSIONS:
            continue
        yield p


def collect_style_guard_report(root: Path | None = None) -> Dict[str, Any]:
    root = root or ROOT
    checks = []

    for rule in RULES:
        total = 0
        samples = []
        for p in _iter_text_files(root):
            try:
                text = p.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            hits = rule['pattern'].findall(text)
            if hits:
                total += len(hits)
                if len(samples) < 2:
                    samples.append(str(p.relative_to(root)))

        checks.append(
            {
                "name": rule['name'],
                "ok": total <= rule['limit'],
                "count": total,
                "limit": rule['limit'],
                "sample_files": samples,
                "fix": "建议按 kill-ai-slop 与 jakub 风格建议降低模板化痕迹：优化配色层次与文案节奏",
            }
        )

    anti_doc = root / 'references' / 'content-guidelines.md'
    checks.append(
        {
            "name": "反AI风格执行文档",
            "ok": anti_doc.exists(),
            "fix": "补齐反AI风格文档，形成可复用修复动作清单",
            "sample_files": [str(anti_doc.relative_to(root))] if anti_doc.exists() else [],
        }
    )

    return {
        "checks": checks,
        "passed": all(item['ok'] for item in checks),
    }

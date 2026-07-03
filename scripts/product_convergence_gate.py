#!/usr/bin/env python3
"""Product convergence gate.

Checks whether a product is more than a pile of fused modules: docs, code,
tests, entrypoints and declared smoke paths must agree. The gate is deliberately
local and dependency-light so it can run in a fresh clone.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

EXCLUDED_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache", "venv", ".venv", "dist", "build"}
BRAND_PATTERNS = (
    "融合自", "融合来源", "inspired by", "CrewAI", "Dify", "ComfyUI", "outlines",
    "gpt_academic", "diffusers", "transformers", "obsidian-livesync",
)
CODE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"}


def iter_files(root: Path, suffixes: set[str] | None = None):
    for path in root.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.is_file() and (suffixes is None or path.suffix in suffixes):
            yield path


def load_manifest(root: Path) -> dict[str, Any]:
    path = root / "product_convergence.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"entrypoints": [], "smoke_targets": [], "known_external_reference_files": []}


def rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def audit(root: Path) -> dict[str, Any]:
    manifest = load_manifest(root)
    issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    skill = root / "SKILL.md"
    readme = root / "README.md"
    code_files = list(iter_files(root, CODE_SUFFIXES))
    tests = list((root / "tests").rglob("test_*.py")) if (root / "tests").exists() else []

    if not readme.exists():
        issues.append({"rule": "DOC_001", "message": "README.md missing"})
    if not skill.exists():
        issues.append({"rule": "SKILL_001", "message": "SKILL.md missing"})
    else:
        text = skill.read_text(encoding="utf-8", errors="ignore")
        if not text.startswith("---"):
            issues.append({"rule": "SKILL_002", "message": "SKILL.md frontmatter missing"})
        if "triggers:" not in text:
            issues.append({"rule": "SKILL_003", "message": "SKILL.md triggers missing"})
    if len(code_files) < 1:
        issues.append({"rule": "CODE_001", "message": "no source code files found"})
    if not tests:
        warnings.append({"rule": "TEST_001", "message": "no pytest test files found"})

    entrypoints = manifest.get("entrypoints", [])
    missing_entrypoints = [p for p in entrypoints if not (root / p).exists()]
    for p in missing_entrypoints:
        issues.append({"rule": "ENTRY_001", "message": f"declared entrypoint missing: {p}"})

    smoke_targets = manifest.get("smoke_targets", [])
    missing_smoke = [p for p in smoke_targets if not (root / p).exists()]
    for p in missing_smoke:
        issues.append({"rule": "SMOKE_001", "message": f"declared smoke target missing: {p}"})
    if not smoke_targets:
        warnings.append({"rule": "SMOKE_002", "message": "no smoke targets declared"})

    allowed = set(manifest.get("known_external_reference_files", []))
    external_hits = []
    for path in iter_files(root, {".py", ".md"}):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.lower() in text.lower() for pattern in BRAND_PATTERNS):
            r = rel(path, root)
            if r not in allowed:
                external_hits.append(r)
    for r in sorted(external_hits)[:50]:
        warnings.append({"rule": "BRAND_001", "message": f"unreviewed external/fusion reference: {r}"})

    doc_text = ""
    for p in (readme, skill):
        if p.exists():
            doc_text += p.read_text(encoding="utf-8", errors="ignore") + "\n"
    if "product_convergence_gate.py" not in doc_text and "产品收敛门禁" not in doc_text:
        warnings.append({"rule": "DOC_002", "message": "convergence gate command not documented"})

    return {
        "repo": root.name,
        "ok": not issues,
        "issues": issues,
        "warnings": warnings,
        "metrics": {
            "code_files": len(code_files),
            "test_files": len(tests),
            "entrypoints": len(entrypoints),
            "smoke_targets": len(smoke_targets),
            "unreviewed_external_refs": len(external_hits),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run product convergence gate")
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args()
    result = audit(Path.cwd())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if result["ok"] else "FAIL"
        print(f"{status} {result['repo']} issues={len(result['issues'])} warnings={len(result['warnings'])}")
        for item in result["issues"]:
            print(f"ISSUE {item['rule']}: {item['message']}")
        for item in result["warnings"][:20]:
            print(f"WARN {item['rule']}: {item['message']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

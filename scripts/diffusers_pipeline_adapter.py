#!/usr/bin/env python3
"""Diffusers modular pipeline adapter for Ideasphere.

用于把 Diffusers 模块化 pipeline 改动中的结构化块，转成 Ideasphere 可消费的
stage 清单。目标：让竞品能力可在无外部服务条件下“可复用配置化”并快速注入。

支持输入：
- JSON 文件 / dict（包含 blocks / modules / pipeline）
- 兼容 `before_denoise` 风格测试片段
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


KNOWN_SECTIONS = {
    "before_denoise": "降噪前处理",
    "anima": "动画模组",
    "sampler": "采样器",
    "decoder": "解码阶段",
    "safety": "安全检查",
    "postprocess": "后处理",
}


@dataclass
class DiffusersBlock:
    """单个可执行块"""

    block_id: str
    block_type: str
    path: str = ""
    source_file: str = ""
    weight: int = 0

    def to_ideasphere_stage(self) -> Dict[str, Any]:
        """导出为 Ideasphere 的 stage 描述。"""
        return {
            "stage_id": self.block_id,
            "stage_type": self.block_type,
            "label": KNOWN_SECTIONS.get(self.block_type, "通用模块"),
            "source_file": self.source_file,
            "entry_path": self.path,
            "weight": self.weight,
            "description": self._desc(),
        }

    def _desc(self) -> str:
        if self.path:
            return f"调用模块路径：{self.path}"
        if self.source_file:
            return f"来源文件：{self.source_file}"
        return "结构化 stage 占位"


def _collect_candidates(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """把竞品 payload 中的块抽平。"""
    if not isinstance(payload, dict):
        return []

    if "blocks" in payload and isinstance(payload["blocks"], list):
        return payload["blocks"]

    if "modules" in payload and isinstance(payload["modules"], list):
        return payload["modules"]

    if "pipeline" in payload and isinstance(payload["pipeline"], dict):
        blocks = []
        pipeline = payload["pipeline"]
        for key, value in pipeline.items():
            if isinstance(value, list):
                for idx, item in enumerate(value):
                    if isinstance(item, dict):
                        block = dict(item)
                        block.setdefault("block_type", key)
                        block.setdefault("block_id", f"{key}-{idx}")
                        blocks.append(block)
                    else:
                        blocks.append({"block_type": key, "block_id": f"{key}-{idx}", "path": str(item)})
            elif isinstance(value, dict):
                block = dict(value)
                block.setdefault("block_type", key)
                block.setdefault("block_id", f"{key}-0")
                blocks.append(block)
        return blocks

    # 兼容直接将模块写在根级：{"before_denoise": [...], ...}
    blocks = []
    for key in KNOWN_SECTIONS:
        value = payload.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, dict):
                    item = dict(item)
                    item.setdefault("block_type", key)
                    item.setdefault("block_id", f"{key}-{idx}")
                    blocks.append(item)
                else:
                    blocks.append({"block_type": key, "block_id": f"{key}-{idx}", "path": str(item)})
        elif isinstance(value, (str, dict)):
            block = value if isinstance(value, dict) else {"path": value}
            block = dict(block)
            block.setdefault("block_type", key)
            block.setdefault("block_id", f"{key}-0")
            blocks.append(block)
    return blocks


def parse_blocks(payload: Dict[str, Any]) -> List[DiffusersBlock]:
    """按固定顺序解析可用块。未知块保留并标记。"""
    raw = _collect_candidates(payload)
    parsed: List[DiffusersBlock] = []

    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            parsed.append(
                DiffusersBlock(
                    block_id=f"unknown-{idx}",
                    block_type="unknown",
                    source_file="unknown.json",
                    weight=0,
                )
            )
            continue

        block_type = str(item.get("block_type") or item.get("type") or item.get("name") or "unknown")
        parsed.append(
            DiffusersBlock(
                block_id=str(item.get("block_id") or f"{block_type}-{idx}"),
                block_type=block_type,
                path=str(item.get("path") or item.get("file") or item.get("entry") or ""),
                source_file=str(item.get("source_file") or ""),
                weight=int(item.get("weight", idx)),
            )
        )

    # 给 unknown 放最后，不改变已识别块顺序
    parsed.sort(key=lambda b: (b.block_type == "unknown", b.weight, b.block_id))
    return parsed


def build_manifest(payload: Dict[str, Any], *, title: str = "Diffusers融合清单") -> Dict[str, Any]:
    blocks = parse_blocks(payload)
    return {
        "title": title,
        "total": len(blocks),
        "stages": [b.to_ideasphere_stage() for b in blocks],
        "supported_section_count": len(KNOWN_SECTIONS),
        "block_types": sorted({b.block_type for b in blocks}),
    }


def load_payload(source: str) -> Dict[str, Any]:
    """读取 JSON 内容。"""
    text = Path(source)
    if text.exists():
        with open(text, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.loads(source)
    if not isinstance(data, dict):
        raise ValueError("payload 必须是 JSON 对象")
    return data


def run_cli() -> int:
    parser = argparse.ArgumentParser(description="Diffusers 到 Ideasphere 的桥接适配器")
    parser.add_argument("--input", required=True, help="输入 JSON 文件路径（竞品 diffusers payload）")
    parser.add_argument("--title", default="Diffusers融合清单", help="清单标题")
    parser.add_argument("--output", help="输出 manifest JSON 路径（缺省打印到 stdout）")
    parser.add_argument("--compact", action="store_true", help="紧凑输出")
    args = parser.parse_args()

    payload = load_payload(args.input)
    manifest = build_manifest(payload, title=args.title)
    dump = json.dumps(manifest, ensure_ascii=False, indent=None if args.compact else 2)

    if args.output:
        Path(args.output).write_text(dump, encoding="utf-8")
        print(f"manifest saved: {args.output}")
    else:
        print(dump)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())

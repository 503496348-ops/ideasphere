"""
Pipeline Orchestrator — 多阶段管道编排引擎
融合自 KrillinAI v2.0 的 CLI + Skills + Pipeline 编排模式。
支持阶段化执行、断点续传、JSON manifest 传递、Agent 可调用。
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)


@dataclass
class StageResult:
    """单阶段执行结果"""
    stage_name: str
    status: str  # "success", "failed", "skipped"
    duration_ms: float = 0.0
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class PipelineManifest:
    """管道执行清单（JSON 可序列化）"""
    pipeline_id: str
    stages: List[str] = field(default_factory=list)
    results: List[StageResult] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    workdir: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """序列化为 JSON"""
        data = asdict(self)
        return json.dumps(data, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "PipelineManifest":
        """从 JSON 反序列化"""
        data = json.loads(text)
        data["results"] = [StageResult(**r) for r in data.get("results", [])]
        return cls(**data)

    def save(self, path: str) -> None:
        """保存清单到文件"""
        Path(path).write_text(self.to_json())

    @classmethod
    def load(cls, path: str) -> "PipelineManifest":
        """从文件加载清单"""
        return cls.from_json(Path(path).read_text())


class PipelineStage:
    """管道阶段定义"""

    def __init__(
        self,
        name: str,
        func: Callable[..., Dict[str, Any]],
        depends_on: Optional[List[str]] = None,
        description: str = "",
        required: bool = True,  # False = 失败不阻断管道
        timeout: float = 300.0,  # 超时秒数
    ):
        self.name = name
        self.func = func
        self.depends_on = depends_on or []
        self.description = description
        self.required = required
        self.timeout = timeout


class PipelineOrchestrator:
    """
    多阶段管道编排引擎。

    特性：
    1. 阶段化执行：每个阶段有明确输入/输出，通过 manifest 传递
    2. 依赖解析：自动拓扑排序，确保依赖先执行
    3. 断点续传：manifest 保存到磁盘，可从失败点恢复
    4. Agent 可调用：每个阶段可独立 CLI 调用
    5. 结构化输出：JSON manifest 便于 Agent 解析

    用法：
        orch = PipelineOrchestrator("video-localization")
        orch.add_stage("download", download_video)
        orch.add_stage("transcribe", transcribe_audio, depends_on=["download"])
        orch.add_stage("translate", translate_text, depends_on=["transcribe"])
        orch.add_stage("dub", tts_dub, depends_on=["translate"])
        orch.add_stage("render", render_video, depends_on=["download", "dub"])

        result = orch.run(workdir="/tmp/output")
    """

    def __init__(self, name: str, workdir: str = "."):
        self._name = name
        self._stages: Dict[str, PipelineStage] = {}
        self._execution_order: List[str] = []
        self._workdir = workdir
        self._manifest: Optional[PipelineManifest] = None

    @property
    def name(self) -> str:
        return self._name

    def add_stage(
        self,
        name: str,
        func: Callable,
        depends_on: Optional[List[str]] = None,
        description: str = "",
        required: bool = True,
        timeout: float = 300.0,
    ) -> "PipelineOrchestrator":
        """添加阶段"""
        self._stages[name] = PipelineStage(
            name=name, func=func, depends_on=depends_on or [],
            description=description, required=required, timeout=timeout,
        )
        self._execution_order = self._resolve_order()
        return self

    def _resolve_order(self) -> List[str]:
        """拓扑排序"""
        visited = set()
        order = []

        def dfs(name):
            if name in visited:
                return
            visited.add(name)
            stage = self._stages[name]
            for dep in stage.depends_on:
                if dep in self._stages:
                    dfs(dep)
            order.append(name)

        for name in self._stages:
            dfs(name)
        return order

    def run(
        self,
        workdir: Optional[str] = None,
        resume: bool = False,
        stages: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> PipelineManifest:
        """
        执行管道。

        Args:
            workdir: 工作目录
            resume: 是否从上次中断点恢复
            stages: 指定执行的阶段子集
            dry_run: 只验证不执行

        Returns:
            执行清单
        """
        target_workdir = workdir or self._workdir
        os.makedirs(target_workdir, exist_ok=True)
        manifest_path = os.path.join(target_workdir, f"{self._name}_manifest.json")

        # 恢复或新建 manifest
        if resume and os.path.exists(manifest_path):
            manifest = PipelineManifest.load(manifest_path)
            completed = {r.stage_name for r in manifest.results if r.status == "success"}
            logger.info(f"[Pipeline] Resuming: {len(completed)} stages already done")
        else:
            manifest = PipelineManifest(
                pipeline_id=self._name,
                stages=list(self._execution_order),
                workdir=target_workdir,
                start_time=time.time(),
            )
            completed = set()

        self._manifest = manifest
        manifest.status = "running"

        # 过滤目标阶段
        target_stages = set(stages) if stages else set(self._execution_order)

        for stage_name in self._execution_order:
            if stage_name not in target_stages:
                continue
            if stage_name in completed:
                continue

            stage = self._stages[stage_name]

            # 检查依赖
            failed_deps = [d for d in stage.depends_on if not any(
                r.stage_name == d and r.status == "success" for r in manifest.results
            )]
            if failed_deps:
                if stage.required:
                    manifest.status = "failed"
                    manifest.end_time = time.time()
                    manifest.save(manifest_path)
                    raise RuntimeError(f"Stage '{stage_name}' depends on failed stages: {failed_deps}")
                else:
                    manifest.results.append(StageResult(
                        stage_name=stage_name, status="skipped",
                        error=f"Dependencies failed: {failed_deps}",
                    ))
                    continue

            if dry_run:
                logger.info(f"[Pipeline] Dry run: would execute '{stage_name}'")
                manifest.results.append(StageResult(stage_name=stage_name, status="success"))
                continue

            # 执行
            logger.info(f"[Pipeline] Executing stage: {stage_name}")
            stage_start = time.time()

            try:
                # 收集前序阶段的输出
                previous_outputs = {}
                for r in manifest.results:
                    if r.status == "success":
                        previous_outputs.update(r.outputs)

                outputs = stage.func(
                    workdir=target_workdir,
                    manifest=manifest,
                    previous_outputs=previous_outputs,
                )

                duration = (time.time() - stage_start) * 1000
                manifest.results.append(StageResult(
                    stage_name=stage_name, status="success",
                    duration_ms=duration, outputs=outputs or {},
                ))
                manifest.save(manifest_path)
                logger.info(f"[Pipeline] Stage '{stage_name}' done in {duration:.0f}ms")

            except Exception as e:
                duration = (time.time() - stage_start) * 1000
                manifest.results.append(StageResult(
                    stage_name=stage_name, status="failed",
                    duration_ms=duration, error=str(e),
                ))
                manifest.save(manifest_path)
                logger.error(f"[Pipeline] Stage '{stage_name}' failed: {e}")

                if stage.required:
                    manifest.status = "failed"
                    manifest.end_time = time.time()
                    manifest.save(manifest_path)
                    raise

        manifest.status = "completed"
        manifest.end_time = time.time()
        manifest.save(manifest_path)
        logger.info(
            f"[Pipeline] Complete: {len(manifest.results)} stages, "
            f"total {(manifest.end_time - manifest.start_time):.1f}s"
        )
        return manifest

    def describe(self) -> List[Dict[str, Any]]:
        """描述管道结构"""
        return [
            {
                "name": name,
                "description": stage.description,
                "depends_on": stage.depends_on,
                "required": stage.required,
            }
            for name, stage in self._stages.items()
        ]

    @property
    def manifest(self) -> Optional[PipelineManifest]:
        return self._manifest

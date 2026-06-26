"""
Modular Pipeline — 可组合式扩散管道系统
融合自 HuggingFace diffusers v0.37 的 Modular Diffusers 架构。
将扩散管道拆分为可复用积木块，支持自由组合拼装。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Type, Union

logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    """管道上下文：在模块间传递的状态"""
    latent: Optional[Any] = None
    image: Optional[Any] = None
    conditioning: Optional[Any] = None
    negative_conditioning: Optional[Any] = None
    embeddings: Optional[Any] = None
    mask: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    step: int = 0
    total_steps: int = 0
    timestep: float = 0.0
    seed: Optional[int] = None
    device: str = "cpu"
    dtype: str = "float16"


class PipelineBlock(ABC):
    """
    管道积木块基类。

    每个块是一个原子操作：编码、采样、解码、后处理等。
    块之间通过 PipelineContext 传递数据。

    生命周期：
        block.validate(ctx) → block.prepare(ctx) → block(ctx) → block.cleanup(ctx)
    """

    name: str = "base_block"
    category: str = "general"  # encode, decode, sample, postprocess, control
    required_inputs: List[str] = []  # ctx 中必须存在的字段
    optional_inputs: List[str] = []

    def validate(self, ctx: PipelineContext) -> None:
        """验证输入完整性"""
        for field_name in self.required_inputs:
            if getattr(ctx, field_name, None) is None:
                raise ValueError(f"Block '{self.name}' requires ctx.{field_name}")

    def prepare(self, ctx: PipelineContext) -> None:
        """预处理（可选）"""
        pass

    @abstractmethod
    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        """执行块操作"""
        ...

    def cleanup(self, ctx: PipelineContext) -> None:
        """后清理（可选）"""
        pass


class ModularPipeline:
    """
    可组合式管道。

    将扩散过程拆分为独立的积木块，自由组合。
    每个块是 PipelineBlock 的子类。

    用法：
        pipe = ModularPipeline()
        pipe.add(TextEncoder(model="clip-vit-large"))
        pipe.add(NoiseGenerator(shape=(1, 4, 64, 64)))
        pipe.add(DenoiserScheduler(scheduler="euler", steps=20))
        pipe.add(VAEDecoder(vae=my_vae))
        pipe.add(ImagePostProcessor(output_format="png"))

        ctx = PipelineContext(seed=42, device="cuda:0")
        result = pipe.run(ctx)
    """

    def __init__(self, name: str = "default"):
        self._name = name
        self._blocks: List[PipelineBlock] = []
        self._block_registry: Dict[str, Type[PipelineBlock]] = {}

    @property
    def name(self) -> str:
        return self._name

    def add(self, block: PipelineBlock) -> "ModularPipeline":
        """添加积木块"""
        self._blocks.append(block)
        logger.debug(f"[Pipeline:{self._name}] Added block: {block.name} ({block.category})")
        return self  # 链式调用

    def insert(self, index: int, block: PipelineBlock) -> "ModularPipeline":
        """在指定位置插入积木块"""
        self._blocks.insert(index, block)
        return self

    def remove(self, block_name: str) -> "ModularPipeline":
        """移除指定名称的积木块"""
        self._blocks = [b for b in self._blocks if b.name != block_name]
        return self

    def replace(self, block_name: str, new_block: PipelineBlock) -> "ModularPipeline":
        """替换指定名称的积木块"""
        for i, b in enumerate(self._blocks):
            if b.name == block_name:
                self._blocks[i] = new_block
                logger.debug(f"[Pipeline:{self._name}] Replaced '{block_name}' with '{new_block.name}'")
                return self
        raise ValueError(f"Block '{block_name}' not found in pipeline")

    def run(self, ctx: Optional[PipelineContext] = None) -> PipelineContext:
        """执行完整管道"""
        if ctx is None:
            ctx = PipelineContext()

        logger.info(f"[Pipeline:{self._name}] Running {len(self._blocks)} blocks")

        for i, block in enumerate(self._blocks):
            ctx.step = i
            block_name = block.name

            try:
                block.validate(ctx)
                block.prepare(ctx)
                ctx = block(ctx)
                block.cleanup(ctx)
                logger.debug(f"[Pipeline:{self._name}] Block {i+1}/{len(self._blocks)}: {block_name} ✓")
            except Exception as e:
                logger.error(f"[Pipeline:{self._name}] Block '{block_name}' failed: {e}")
                raise RuntimeError(f"Pipeline block '{block_name}' failed: {e}") from e

        logger.info(f"[Pipeline:{self._name}] Complete")
        return ctx

    async def run_async(self, ctx: Optional[PipelineContext] = None) -> PipelineContext:
        """异步执行（支持 async 块）"""
        import asyncio
        if ctx is None:
            ctx = PipelineContext()

        for i, block in enumerate(self._blocks):
            ctx.step = i
            block.validate(ctx)
            block.prepare(ctx)
            if asyncio.iscoroutinefunction(block.__call__):
                ctx = await block(ctx)
            else:
                ctx = block(ctx)
            block.cleanup(ctx)

        return ctx

    def describe(self) -> List[Dict[str, Any]]:
        """描述管道结构"""
        return [
            {
                "index": i,
                "name": block.name,
                "category": block.category,
                "required_inputs": block.required_inputs,
            }
            for i, block in enumerate(self._blocks)
        ]

    def clone(self) -> "ModularPipeline":
        """克隆管道（浅拷贝块列表）"""
        new_pipe = ModularPipeline(name=f"{self._name}_clone")
        new_pipe._blocks = list(self._blocks)
        return new_pipe

    def __len__(self) -> int:
        return len(self._blocks)

    def __repr__(self) -> str:
        blocks_str = " → ".join(b.name for b in self._blocks)
        return f"ModularPipeline('{self._name}': {blocks_str})"


# ── 常用积木块 ──


class TextEncoderBlock(PipelineBlock):
    """文本编码块"""
    name = "text_encoder"
    category = "encode"
    required_inputs = []

    def __init__(self, encoder: Any, tokenizer: Any, max_length: int = 77):
        self._encoder = encoder
        self._tokenizer = tokenizer
        self._max_length = max_length

    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        prompt = ctx.metadata.get("prompt", "")
        negative = ctx.metadata.get("negative_prompt", "")

        # 编码正向提示词
        text_inputs = self._tokenizer(
            prompt, padding="max_length", max_length=self._max_length,
            truncation=True, return_tensors="pt",
        )
        ctx.conditioning = self._encoder(text_inputs.input_ids.to(ctx.device))[0]

        # 编码负向提示词
        if negative:
            neg_inputs = self._tokenizer(
                negative, padding="max_length", max_length=self._max_length,
                truncation=True, return_tensors="pt",
            )
            ctx.negative_conditioning = self._encoder(neg_inputs.input_ids.to(ctx.device))[0]

        return ctx


class NoiseGeneratorBlock(PipelineBlock):
    """噪声生成块"""
    name = "noise_generator"
    category = "sample"
    required_inputs = []

    def __init__(self, shape: Optional[tuple] = None):
        self._shape = shape

    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        import torch
        shape = self._shape or ctx.metadata.get("latent_shape", (1, 4, 64, 64))
        generator = torch.Generator(device=ctx.device)
        if ctx.seed is not None:
            generator.manual_seed(ctx.seed)
        ctx.latent = torch.randn(shape, generator=generator, device=ctx.device, dtype=torch.float16)
        return ctx


class VAEDecoderBlock(PipelineBlock):
    """VAE 解码块"""
    name = "vae_decoder"
    category = "decode"
    required_inputs = ["latent"]

    def __init__(self, vae: Any, scaling_factor: float = 0.18215):
        self._vae = vae
        self._scaling_factor = scaling_factor

    def __call__(self, ctx: PipelineContext) -> PipelineContext:
        import torch
        with torch.no_grad():
            latents = ctx.latent / self._scaling_factor
            ctx.image = self._vae.decode(latents).sample
        return ctx

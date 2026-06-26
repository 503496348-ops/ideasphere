"""
Multi-ASR Backend — 多语音识别后端抽象层
融合自 KrillinAI 的多 ASR 服务支持架构。
统一接口适配 OpenAI Whisper / FasterWhisper / WhisperKit / WhisperCpp / 阿里云 ASR。
"""

from __future__ import annotations

import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TranscriptSegment:
    """转录片段"""
    text: str
    start_ms: int
    end_ms: int
    confidence: float = 1.0
    language: str = ""
    speaker: Optional[str] = None


@dataclass
class TranscriptResult:
    """转录结果"""
    segments: List[TranscriptSegment]
    language: str = ""
    duration_ms: int = 0
    backend: str = ""
    processing_time_ms: float = 0.0

    @property
    def full_text(self) -> str:
        return " ".join(seg.text for seg in self.segments)

    def to_srt(self) -> str:
        """导出为 SRT 格式"""
        lines = []
        for i, seg in enumerate(self.segments, 1):
            start = self._ms_to_srt_time(seg.start_ms)
            end = self._ms_to_srt_time(seg.end_ms)
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(seg.text)
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _ms_to_srt_time(ms: int) -> str:
        h = ms // 3600000
        m = (ms % 3600000) // 60000
        s = (ms % 60000) // 1000
        ms_r = ms % 1000
        return f"{h:02d}:{m:02d}:{s:02d},{ms_r:03d}"


class ASRBackend(ABC):
    """ASR 后端基类"""

    name: str = "base"
    supported_languages: List[str] = []  # 空=全部

    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        **kwargs,
    ) -> TranscriptResult:
        """转录音频文件"""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """检查后端是否可用"""
        ...

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        ...


class OpenAIWhisperBackend(ASRBackend):
    """OpenAI Whisper API（云端）"""
    name = "openai"

    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1"):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._model = model

    def is_available(self) -> bool:
        return self._api_key is not None

    def transcribe(self, audio_path: str, language: Optional[str] = None, **kwargs) -> TranscriptResult:
        start = time.time()
        try:
            import openai
            client = openai.OpenAI(api_key=self._api_key)
            with open(audio_path, "rb") as f:
                response = client.audio.transcriptions.create(
                    model=self._model, file=f,
                    language=language, response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )
            segments = [
                TranscriptSegment(
                    text=seg.text, start_ms=int(seg.start * 1000),
                    end_ms=int(seg.end * 1000), confidence=getattr(seg, "avg_logprob", 1.0),
                )
                for seg in (response.segments if hasattr(response, "segments") else [])
            ]
            elapsed = (time.time() - start) * 1000
            return TranscriptResult(
                segments=segments, language=getattr(response, "language", language or ""),
                duration_ms=int(getattr(response, "duration", 0) * 1000),
                backend=self.name, processing_time_ms=elapsed,
            )
        except ImportError:
            raise RuntimeError("openai package not installed")

    def health_check(self) -> Dict[str, Any]:
        return {"backend": self.name, "available": self.is_available(), "model": self._model}


class FasterWhisperBackend(ASRBackend):
    """FasterWhisper 本地推理"""
    name = "fasterwhisper"

    def __init__(self, model_size: str = "large-v2", device: str = "auto"):
        self._model_size = model_size
        self._device = device
        self._model = None

    def is_available(self) -> bool:
        try:
            import fasterwhisper  # noqa: F401
            return True
        except ImportError:
            return False

    def _load_model(self):
        if self._model is None:
            from fasterwhisper import WhisperModel
            compute_type = "float16" if self._device != "cpu" else "int8"
            self._model = WhisperModel(self._model_size, device=self._device, compute_type=compute_type)

    def transcribe(self, audio_path: str, language: Optional[str] = None, **kwargs) -> TranscriptResult:
        start = time.time()
        self._load_model()
        segments_iter, info = self._model.transcribe(audio_path, language=language, beam_size=5)
        segments = []
        for seg in segments_iter:
            segments.append(TranscriptSegment(
                text=seg.text.strip(), start_ms=int(seg.start * 1000),
                end_ms=int(seg.end * 1000), confidence=seg.avg_logprob,
            ))
        elapsed = (time.time() - start) * 1000
        return TranscriptResult(
            segments=segments, language=info.language,
            duration_ms=int(info.duration * 1000),
            backend=self.name, processing_time_ms=elapsed,
        )

    def health_check(self) -> Dict[str, Any]:
        return {"backend": self.name, "available": self.is_available(), "model_size": self._model_size}


class MultiASRRouter:
    """
    多 ASR 后端路由器。

    自动选择最优后端，支持降级。

    用法：
        router = MultiASRRouter()
        router.register(OpenAIWhisperBackend())
        router.register(FasterWhisperBackend())
        result = router.transcribe("audio.wav", preferred="openai")
    """

    def __init__(self, fallback_order: Optional[List[str]] = None):
        self._backends: Dict[str, ASRBackend] = {}
        self._fallback_order = fallback_order or []

    def register(self, backend: ASRBackend) -> "MultiASRRouter":
        """注册后端"""
        self._backends[backend.name] = backend
        if backend.name not in self._fallback_order:
            self._fallback_order.append(backend.name)
        return self

    def transcribe(
        self,
        audio_path: str,
        preferred: Optional[str] = None,
        language: Optional[str] = None,
        **kwargs,
    ) -> TranscriptResult:
        """转录（自动选择后端）"""
        order = []
        if preferred and preferred in self._backends:
            order.append(preferred)
        order.extend(b for b in self._fallback_order if b != preferred)

        last_error = None
        for backend_name in order:
            backend = self._backends.get(backend_name)
            if backend is None or not backend.is_available():
                logger.debug(f"[ASR] Skipping unavailable backend: {backend_name}")
                continue
            try:
                logger.info(f"[ASR] Using backend: {backend_name}")
                return backend.transcribe(audio_path, language=language, **kwargs)
            except Exception as e:
                logger.warning(f"[ASR] Backend '{backend_name}' failed: {e}")
                last_error = e

        raise RuntimeError(f"All ASR backends failed. Last error: {last_error}")

    def list_backends(self) -> List[Dict[str, Any]]:
        """列出所有后端状态"""
        return [
            {
                "name": name,
                "available": backend.is_available(),
                "health": backend.health_check(),
            }
            for name, backend in self._backends.items()
        ]

---
name: 灵感象限-Ideasphere
description: "自媒体视频创作引擎。去静音→Whisper字幕→翻译→烧录→平台适配一站式处理。当需要处理视频、添加字幕、翻译视频内容、生成短视频时使用。"
license: MIT
metadata:
  author: 503496348-ops
  version: 1.6.0
triggers:
  - 视频剪辑流水线
  - 灵感象限
  - 批量处理视频
  - 视频去静音
  - 字幕生成
  - 字幕翻译
  - 双语字幕
  - 视频拼接
  - 口播剪辑
  - 平台适配渲染
  - TTS配音
  - 语音合成
  - 视频下载
  - 在线视频
  - YouTube下载
  - B站下载
  - 视频处理
  - 视频优化
  - 视频格式转换
---

# 灵感象限-Ideasphere

> 📖 详细文档见 `references/` 目录

**自媒体视频一站式剪辑技能包**

## When to Use

- 用户需要批量处理视频
- 用户需要生成字幕
- 用户需要翻译字幕
- 用户需要双语字幕
- 用户需要视频配音
- 用户需要平台适配渲染
- 用户需要下载在线视频
- 视频处理和优化（格式转换、质量调整、帧提取）

## 技术架构

| 模块 | 实现 | 职责 |
|------|------|------|
| 解析器 | `parser.py` (1126行) | 从聊天中识别思维模式和认知特征 |
| 孵化器 | `incubator.py` | 约束松弛+随机重组生成创意 |
| 记忆系统 | `memory.py` (1029行) | 跨会话学习+偏好沉淀 |
| 创意生成 | `generators/*.py` | 6种类型：故事/方案/类比/实验/反转/跨界 |

Pipeline: 聊天解析 → 思维模式提取 → 约束松弛 → 创意生成 → 记忆沉淀

## 快速开始

```bash
# 1. 检查依赖
python3 scripts/pipeline.py --check-deps

# 2. 配置 API Key
export MINIMAX_API_KEY="your-key"

# 3a. 从本地素材处理
python3 scripts/pipeline.py --all \
  --input "/path/to/videos" \
  --output "/path/to/output" \
  --target-lang "English" \
  --bilingual \
  --platform douyin

# 3b. 从在线 URL 下载并处理
python3 scripts/video_download.py "https://www.youtube.com/watch?v=xxx" -o ./downloads
python3 scripts/pipeline.py --all \
  --input "./downloads" \
  --output "/path/to/output" \
  --target-lang "English"
```

## 工作流

### Step 1: 需求确认

确认用户意图属于以下哪个分支：

| 分支 | 触发词 | 入口脚本 |
|------|--------|----------|
| 完整流水线 | "处理视频""剪辑""加字幕" | `scripts/pipeline.py --all` |
| 仅下载 | "下载视频""YouTube""B站" | `scripts/video_download.py` |
| 仅视频处理 | "压缩""转格式""提帧" | `modules/video_processor.py` |
| 仅字幕 | "字幕翻译""双语字幕" | `scripts/translate_subtitle.py` |
| 仅配音 | "TTS""配音""语音合成" | `scripts/tts_dubbing.py` |

### Step 2: 环境预检

```bash
# 检查核心依赖
python3 scripts/pipeline.py --check-deps

# 必需依赖
# - ffmpeg (系统包)
# - auto-editor (pip install auto-editor)
# - faster-whisper (pip install faster-whisper)
# - yt-dlp (pip install yt-dlp) — 仅下载分支需要
# - edge-tts (pip install edge-tts) — 仅TTS分支需要
```

### Step 3: 执行

根据分支选择对应命令。完整流水线参数：

```bash
python3 scripts/pipeline.py --all \
  --input <输入目录或文件> \
  --output <输出目录> \
  --target-lang <目标语言，如 English/中文/日本語> \
  --bilingual \          # 可选：生成双语字幕
  --platform <平台>      # 可选：douyin/youtube/bilibili/xiaohongshu
```

### Step 4: 输出验证

```bash
# 检查输出文件
ls -lh <output_dir>/

# 预期产物：
# - *_trimmed.mp4       — 去静音后视频
# - *_subtitled.mp4     — 烧录字幕后视频
# - *.srt               — 字幕文件
# - *_dubbed.mp4        — TTS配音视频（如启用）
# - *_<platform>.mp4    — 平台适配版本（如指定）
```



## 详细文档

完整内容见 `references/full-skill.md`。

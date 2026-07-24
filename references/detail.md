��分支选择对应命令。完整流水线参数：

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

## 技术参考

### 平台适配预设

| 平台 | 分辨率 | 画面比例 | 最大时长 |
|------|--------|----------|----------|
| 抖音 / 快手 | 1080×1920 | 9:16 | 15min |
| 微信视频号 | 1080×1920 | 9:16 | 30min |
| 小红书 | 1080×1440 | 3:4 | 15min |
| YouTube | 1920×1080 | 16:9 | 无限制 |
| B站 | 1920×1080 | 16:9 | 无限制 |

### 视频处理模块

```python
from modules.video_processor import VideoProcessor, VideoQuality

processor = VideoProcessor()

# 获取视频信息
info = processor.get_video_info("/path/to/video.mp4")

# 优化视频
result = processor.optimize_video(
    "/path/to/video.mp4",
    quality=VideoQuality.HIGH,
    target_format=VideoFormat.MP4,
)

# 提取视频帧
frames = processor.extract_frames(
    "/path/to/video.mp4",
    "/path/to/frames",
    frame_interval=1.0,
    max_frames=100,
)
```

质量预设：
- LOW: 480×360, 500kbps
- MEDIUM: 720×480, 1Mbps
- HIGH: 1280×720, 2Mbps
- ULTRA: 1920×1080, 4Mbps

### 依赖说明

| 依赖 | 用途 | 安装 |
|------|------|------|
| ffmpeg | 视频剪辑/烧录/渲染 | `apt install ffmpeg` |
| auto-editor | 去静音检测 | `pip install auto-editor` |
| faster-whisper | 语音转文字 | `pip install faster-whisper` |
| yt-dlp | 在线视频下载 | `pip install yt-dlp` |
| edge-tts | TTS配音 | `pip install edge-tts` |
| openai | LLM字幕纠错/翻译 | `pip install openai` |

### API 配置

| 环境变量 | 用途 | 必需 |
|----------|------|------|
| `MINIMAX_API_KEY` | LLM字幕纠错和翻译 | 字幕翻译分支需要 |
| `OPENAI_API_KEY` | 备用LLM（可选） | 否 |

## Pitfalls

1. **Whisper 模型首次运行会下载模型文件**（~1.5GB），网络慢时会卡住。建议预先 `faster-whisper download-model large-v3`。
2. **auto-editor 对纯音乐片段误判率高**，有大量BGM的视频建议手动检查去静音结果。
3. **yt-dlp 版权保护视频**（如会员专享）无法下载，会返回错误但不中断流水线。
4. **双语字幕烧录后文字可能溢出**，短字幕（<10字）效果最佳，长句会被自动折行。
5. **Edge TTS 中文音色**推荐 `zh-CN-XiaoxiaoNeural`（女声）和 `zh-CN-YunxiNeural`（男声）。
6. **MiniMax TTS**（融合自 KrillinAI v2.1.0）提供更高质量的中文语音合成，使用 `speech-2.8-hd` 模型。需设置 `MINIMAX_API_KEY` 环境变量。
6. **大文件处理**（>1GB）建议先用 `optimize_video(quality=VideoQuality.MEDIUM)` 压缩再进流水线。

## 2026-07-03 产品收敛门禁

- 新增 `scripts/product_convergence_gate.py`：从远端干净 clone 后可运行 `python3 scripts/product_convergence_gate.py --json`，检查 SKILL/README、入口文件、smoke 目标、测试与外部融合引用是否自洽。
- 新增 `tests/test_product_convergence_gate.py`：确保门禁在产品仓库中真实可执行，避免后续增强只停留在孤岛模块。

## 一键开箱交付

本仓库提供标准一键入口：

- `install.sh`：用户的一条命令安装与冒烟入口。
- `scripts/setup.py`：安装声明依赖并串联 doctor。
- `scripts/doctor.py`：检查 README、SKILL、入口脚本、package scripts 与产品收敛门禁。
- `scripts/smoke.py`：运行 doctor、产品收敛门禁与 Python 编译级冒烟。
- `tests/test_one_click_open_box.py`：契约测试，防止 README 写了但脚本缺失。

# 自媒体视频创作双技能套件
## 艺术生花 × 灵感象限 — 使用说明书

> **版本**：v1.0.0
> **维护者**：Hermes Agent（欣欣）
> **最后更新**：2026-05-16

---

## 一、概览

本套件包含两个协同工作的技能：

| 技能 | 名称 | 职能 | 输入 | 输出 |
|------|------|------|------|------|
| 🎯 **艺术生花** | Aestheflow | 抖音视频深度分析 | 抖音分享链接 | 分析报告（数据+结构+视觉+文案） |
| ✂️ **灵感象限** | Ideasphere | 视频剪辑流水线 | 本地视频素材 | 带字幕的成片 |

```
抖音链接  ────→  艺术生花  ────→  分析报告  ────→  灵感象限  ────→  成片
                   (拆解爆款)        (策略参考)        (剪辑制作)
```

**推荐工作流**：先用艺术生花分析竞品/对标视频的结构，用提炼出的爆款要素指导剪辑策略，再交给灵感象限执行成品制作。

---

## 二、艺术生花（Aestheflow）

### 2.1 这是什么

深度拆解抖音视频的技能。输入一条抖音分享链接，自动完成：无水印下载 → 智能抽帧 → 视觉+文案+结构全维拆解 → 输出完整分析报告。

### 2.2 适用场景

- 🔍 想深度拆解竞品/对标账号的爆款视频结构
- 📊 选题调研阶段需要量化数据支撑（点赞/评论/转发比、完播率推算）
- 🎨 需要提取视频的视觉语言、镜头语言、情绪曲线
- 📝 需要生成完整的爆款要素分析报告（文案+视觉+结构三维度）
- 🧠 学习爆款公式，为自己的内容找方向

### 2.3 使用方式

**通过 Hermes Agent 调用**（推荐）：
直接向欣欣发送：
> "帮我分析这个抖音视频：[链接]"

欣欣会自动执行完整流程。

**手动命令行调用**：
```bash
node ~/.hermes/skills/social-media/douyin-video-analyzer/scripts/analyze.js "https://v.douyin.com/xxxxx"
```

### 2.4 输出内容

分析报告存放于 `/tmp/douyin_data/{video_id}/report.md`，包含：

| 模块 | 内容 |
|------|------|
| 📊 **基础数据** | 点赞/评论/转发数推算，完播率评估 |
| 🔥 **爆款结构拆解** | 开头钩子 / 中段节奏 / 结尾引导拆解 |
| 🎨 **视觉语言分析** | 色调、构图、情绪、镜头语言 |
| ✍️ **文案钩子提炼** | 标题公式、口播金句、字幕特点 |
| 📈 **爆款要素总结** | 数据+视觉双维度提炼共性特征 |

### 2.5 注意事项

| ⚠️ | 说明 |
|----|------|
| 链接格式 | 必须使用 `https://v.douyin.com/xxxxx` 格式，分享码无法直接解析 |
| 批量分析 | 抖音接口有频率限制，批量分析时建议适当间隔 |
| 抽帧依赖 | 需要系统已安装 `ffmpeg`（`ffmpeg -version` 验证） |
| 输出位置 | 默认 `/tmp/douyin_data/{video_id}/`，重复分析会覆盖 |

---

## 三、灵感象限（Ideasphere）

### 3.1 这是什么

一站式视频剪辑流水线技能。输入本地素材，自动完成：去静音剪辑 → 语音转字幕 → LLM 智能纠错 → 字幕烧录 → 多平台导出。

### 3.2 适用场景

- 🎙️ 批量处理口播/访谈视频，自动去除静音片段
- 📹 已有素材，需要快速生成带字幕的成片
- 📤 需要导出为抖音/视频号/YouTube 适配格式
- ✏️ 需要 LLM 级别的字幕智能纠错（过滤语气词、修正错别字）
- 🔗 多段视频需要拼接合并为一个完整成品
- 🪄 希望分步执行（先剪辑确认 → 再转写 → 再烧录），精细化控制

### 3.3 核心流程

```
步骤 1          步骤 2          步骤 3          步骤 4
去静音剪辑   →   语音转字幕   →   字幕烧录     →   多平台导出
(auto-editor)    (Whisper+LLM)   (ffmpeg)        (格式适配)
```

### 3.4 使用方式

**通过 Hermes Agent 调用**（推荐）：
直接向欣欣发送：
> "帮我剪辑这个视频：[文件路径]"

欣欣会自动检测素材、执行流水线、确认关键节点。

**手动命令行调用**：

```bash
# 第一步：检查依赖是否就绪
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/pipeline.py --check-deps

# 第二步：扫描素材（只列出，不执行）
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/pipeline.py \
  --list --input "/path/to/videos"

# 第三步：执行完整流程
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/pipeline.py \
  --all \
  --input "/path/to/videos" \
  --output "/path/to/output" \
  --notify false
```

**分步执行（精细化控制）**：

```bash
# 只做步骤 1：去静音剪辑
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/pipeline.py \
  --step 1 --input "/path/to/videos" --output "/path/to/output"

# 只做步骤 2：语音转字幕
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/pipeline.py \
  --step 2 --input "/path/to/clipped" --output "/path/to/output"

# ...以此类推
```

**带确认模式（每步人工审核）**：
```bash
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/pipeline.py \
  --all --input "/path/to/videos" --output "/path/to/output" --confirm
```

### 3.5 各模块详解

#### 模块 1：视频剪辑（去静音）
```bash
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/video_clip.py \
  --input "raw.mp4" --output "clipped.mp4" --threshold -40
```
自动切除静音片段，保留有效说话内容。`--threshold` 默认 -40dB，嘈杂环境可调高至 -35。

#### 模块 2：语音转字幕（Whisper + LLM 纠错）
```bash
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/video_to_text.py \
  --input "clipped.mp4" --output "subtitle.srt" --model small
```
用 Faster Whisper 识别语音 → 生成 SRT 字幕 → 调用 MiniMax LLM 做词级纠错（过滤"嗯""啊""这个"等语气词）。

**Whisper 模型选择**：

| 模型 | 内存占用 | 速度 | 推荐场景 |
|------|----------|------|----------|
| tiny | ~1GB | 最快 | 快速测试 |
| **small** | ~2GB | 较快 | ✅ 日常使用 |
| base | ~3GB | 中等 | 高质量需求 |

#### 模块 3：字幕烧录
```bash
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/burn_subtitle.py \
  --input "clipped.mp4" --subtitle "subtitle.srt" --output "final.mp4"
```
将 SRT 字幕烧录进视频，输出即成片。

#### 模块 4：FFmpeg 工具箱
```bash
# 拼接多个视频
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/ffmpeg_tools.py concat \
  --inputs "1.mp4" "2.mp4" --output "merged.mp4"

# 格式转换
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/ffmpeg_tools.py convert \
  --input "video.mov" --output "video.mp4"

# 查看视频信息
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/ffmpeg_tools.py info \
  --input "/path/to/videos"
```

### 3.6 输出目录结构

```
输入目录/
├── 文字稿/              # SRT 字幕文件
├── 项目名/              # 处理过程中的视频
│   ├── 1_已剪辑.mp4
│   └── 2_已剪辑.mp4
└── 项目名_成品/        # 最终成品
    └── 合并视频.mp4
```

### 3.7 注意事项

| ⚠️ | 说明 |
|----|------|
| FFmpeg 路径 | 确认 `which ffmpeg` 有输出，部分系统需要完整路径 `/usr/bin/ffmpeg` |
| 内存不足 | 使用 `--model tiny`，仅需 ~1GB 内存 |
| 长音频 | 超过 30 分钟建议分段处理，避免时间戳漂移 |
| 输出覆盖 | 默认会覆盖已有文件，先确认输出目录无同名文件 |
| API Key | 必须设置 `MINIMAX_API_KEY` 环境变量（用于 LLM 字幕纠错） |

---

## 四、智能串联：艺术生花 → 灵感象限

两个技能可以协同使用，分析为剪辑提供策略依据：

```
① 艺术生花分析爆款视频
   ↓
② 提取爆款要素（开头公式/节奏节点/情绪曲线）
   ↓
③ 将要素作为剪辑参考，交给灵感象限执行
```

**示例**：

> 欣欣，帮我分析 [抖音链接]，然后用同样的爆款结构剪辑我这条素材：
> - 开头用同样的钩子公式
> - 保留那个视频里的节奏节点
> - 字幕样式参考它的风格

欣欣会：
1. 执行艺术生花分析
2. 读取分析报告中的爆款公式
3. 调用灵感象限流水线，按报告策略执行剪辑

---

## 五、快速上手

### 环境准备（首次使用）

```bash
# 1. 检查依赖
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/pipeline.py --check-deps

# 2. 安装缺失依赖
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/pipeline.py --install-deps

# 3. 配置 MiniMax API Key（用于字幕 LLM 纠错）
export MINIMAX_API_KEY="你的API密钥"
```

### 日常使用

| 需求 | 操作 |
|------|------|
| 分析抖音视频 | 向欣欣发送："分析 [链接]" |
| 剪辑本地素材 | 向欣欣发送："剪辑 [文件路径]" |
| 串联分析+剪辑 | 向欣欣发送："用 [链接] 的爆款结构剪辑 [文件路径]" |

---

## 六、常见问题

### Q：提示 "ffmpeg 未安装"
**A**：Ubuntu/Debian: `sudo apt install ffmpeg` | macOS: `brew install ffmpeg`

### Q：提示 "MINIMAX_API_KEY 未设置"
**A**：`export MINIMAX_API_KEY="你的密钥"`（或运行时用 `--api-key` 参数传入）

### Q：显存不够，Whisper 跑不动
**A**：使用 `--model tiny` 参数，只需 ~1GB 内存

### Q：抖音链接是分享码，不是 v.douyin.com 格式
**A**：先用浏览器或抖音 App 打开分享码，获取重定向后的 v.douyin.com 链接

### Q：批量处理多个视频
**A**：`--input` 传入目录路径，流水线会自动扫描目录下所有视频并逐个处理

### Q：字幕时间戳有偏移
**A**：Whisper 在长音频（>30分钟）中可能出现时间偏移，建议分段处理

---

## 七、技术支持

- **欣欣（Hermes Agent）**：随时可以向阿秋的欣欣发送求助
- **GitHub 仓库**：
  - 艺术生花：https://github.com/503496348-ops/hermes-skill-aestheflow
  - 灵感象限：https://github.com/503496348-ops/hermes-skill-ideasphere

# Pipeline 参数模板

## 标准批量执行模板

```bash
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/pipeline.py \
  --all \
  --input "/path/to/raw_footage" \
  --output "/path/to/finished_videos" \
  --subtitle "/path/to/subtitles" \
  --api-key "${MINIMAX_API_KEY}"
```

## 分步执行模板

### 步骤1：仅剪辑（去静音）
```bash
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/pipeline.py \
  --step 1 \
  --input "/path/to/raw_footage" \
  --output "/path/to/clipped_videos"
```

### 步骤2：仅转写（生成字幕）
```bash
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/pipeline.py \
  --step 2 \
  --input "/path/to/clipped_videos" \
  --output "/path/to/subtitles" \
  --api-key "${MINIMAX_API_KEY}"
```

### 步骤3：仅烧录
```bash
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/pipeline.py \
  --step 3 \
  --input "/path/to/clipped_videos" \
  --output "/path/to/burned_videos" \
  --subtitle "/path/to/subtitles"
```

## 竖屏口播视频推荐参数

```bash
python3 ~/.hermes/skills/media/video-pipeline-bundle/scripts/video_clip.py \
  --input "/path/to/raw.mp4" \
  --output "/path/to/clipped.mp4" \
  --threshold -40 \
  --margin 0.3
```

## Whisper 模型参数

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `--model` | Whisper 模型 | `small` |
| `--margin` | 静音片段缓冲秒数 | `0.3~0.5` |
| `--threshold` | 音频阈值(dBFS) | `-40` |

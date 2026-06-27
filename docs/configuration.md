---
layout: page
title: Configuration
nav_order: 6
parent: Introduction
---

# Configuration (`config.json`)

`slidemovie` allows you to customize video resolution, audio quality, and TTS settings via JSON configuration files.

## Configuration Loading Order

The program loads settings in the following order (later sources override earlier ones):

1.  **Built-in Defaults**: Hardcoded in the program.
2.  **User Config**: `~/.config/slidemovie/config.json` (Home directory).
    *   **Note**: If this file does not exist, it will be automatically created with default values on the first run.
3.  **Local Config**: `./config.json` (Current working directory).
4.  **CLI Arguments**: Command-line flags (highest priority for specific settings).

## Configuration Options

Here is a complete list of available keys in `config.json`.

### Text-to-Speech (TTS)

See [multiai-tts](https://sekika.github.io/multiai-tts/#supported-ai-providers) for supported providers and models.

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `tts_provider` | string | `"google"` | The AI provider (`google`, `openai`, or `azure`). |
| `tts_model` | string | `"gemini-2.5-flash-..."` | The specific model name. Required for Google and OpenAI; ignored for Azure. |
| `tts_voice` | string | `"sadaltager"` | The voice ID (e.g., `alloy` for OpenAI, `en-US-AvaMultilingualNeural` for Azure and English). |
| `tts_use_prompt`| bool | `true` | Whether to send a system prompt to the TTS API. Set `true` for google and `false` for OpenAI and Azure. |
| `prompt` | string | `"Please speak..."` | The system instruction for the TTS engine. |
| `chunk_size` | int / null | `null` | Max characters per chunk for long narration. `null` disables splitting (default behavior). Measured against the spoken text only, not the prompt. See [Long narration](advanced-usage.md#long-narration-automatic-chunking). |
| `split_chars` | string | `"。．.!！?？\n"` | Candidate characters where the text may be split into chunks. |
| `chunk_overflow` | string | `"extend"` | Behavior when no split candidate is found within `chunk_size`: `"extend"` reads on to the next candidate; `"error"` stops with an error. |

### Video Format

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `screen_size` | [int, int] | `[1280, 720]` | Resolution `[width, height]`. Slide images are normalized to this size. |
| `image_pad_color` | string | `"white"` | Padding color used when a slide's aspect ratio differs from `screen_size`. The image is scaled to fit and centered, with even letterbox/pillarbox padding of this color. Any ImageMagick color name/value is accepted (e.g. `"black"`). |
| `video_fps` | int | `30` | Frames per second. |
| `video_codec` | string | `"libx264"` | Video encoding codec. |
| `video_pix_fmt` | string | `"yuv420p"` | Pixel format (compatibility). |

### Audio Format

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `audio_codec` | string | `"aac"` | Audio encoding codec. |
| `sample_rate` | int | `44100` | Sample rate in Hz. |
| `audio_bitrate` | string | `"192k"` | Audio quality bitrate. |
| `audio_channels`| int | `2` | 1 (Mono) or 2 (Stereo). |

### General / Processing

| Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `silence_sec` | float | `2.5` | Silence duration added before each slide speaks. |
| `max_retry` | int | `2` | Number of retries if TTS API fails. |
| `ffmpeg_loglevel`| string | `"error"` | Log verbosity for FFmpeg processes. |
| `show_skip` | bool | `false` | If `true`, logs "skipped" tasks (unchanged files) to the console. Can be enabled via `--debug`. |
| `output_root` | string | `null` | Custom root directory for video output. Can be overridden by the `-o` CLI option. |
| `output_filename` | string | `null` | Output video filename (without extension). Defaults to project ID. Can be overridden by the `-f` CLI option. |

## Example `config.json`

To create a **Full HD (1080p)** video using **OpenAI**, save this as `config.json` in your project folder:

```json
{
    "tts_provider": "openai",
    "tts_model": "gpt-4o-mini-tts",
    "tts_voice": "alloy",
    "tts_use_prompt": false,
    "screen_size": [1920, 1080]
}
```

> **Warning:** Once you start building a project, the `screen_size` and FPS are recorded in the status file (`status.json`). If you change these settings halfway through, `slidemovie` will detect an inconsistency and abort to prevent video corruption. To apply new video settings, you may need to delete the files in `movie/` directory to rebuild from scratch.

---
layout: page
title: CLI Reference
nav_order: 5
parent: Introduction
---

# Command Line Interface Reference

The `slidemovie` command is the primary entry point for all operations.

## Basic Syntax

```bash
slidemovie [PROJECT_NAME] [OPTIONS]
```

## Positional Arguments

*   **`PROJECT_NAME`** (Required)
    *   The identifier for your project.
    *   The tool looks for `{PROJECT_NAME}.md` in the source directory.
    *   If using Subproject Mode (`--sub`), this argument specifies the **Parent** directory name (used for output categorization).

## Options

### Mode Flags (At least one is required)

*   **`-p`, `--pptx`**
    *   **Action**: Converts the source Markdown file into a PowerPoint (`.pptx`) file.
    *   **Use Case**: Initial draft creation or updating slide text.
    *   **Note**: This overwrites existing PPTX files in the source directory unless configured otherwise.

*   **`-v`, `--video`**
    *   **Action**: Builds the complete video.
    *   **Steps**:
        1.  Generates Audio (TTS) from Markdown notes.
        2.  Exports Images from the PPTX file.
        3.  Combines Audio and Images into slide clips.
        4.  Concatenates clips into the final movie.
    *   **Use Case**: Final production.

### Path & Structure

*   **`-s DIR`, `--source-dir DIR`**
    *   **Default**: `.` (Current directory)
    *   **Description**: The directory containing your source Markdown and PPTX files.
    *   **Example**: `slidemovie myproject -s ./docs` (Looks for `./docs/myproject.md`)

*   **`--sub SUB_NAME`**
    *   **Description**: Enables **Hierarchical (Subproject) Mode**.
    *   **Behavior**:
        *   `PROJECT_NAME` is used for the output parent folder.
        *   `SUB_NAME` becomes the **Child** folder (Subproject).
        *   Input Source: `{Child}/{Child}.md`
        *   Output Video: `movie/{Parent}/{Child}/{Child}.mp4`
    *   **Example**: `slidemovie Season1 --sub Episode1`

*   **`-o DIR`, `--output-root DIR`**
    *   **Default**: `./movie` (relative to the source directory)
    *   **Description**: Specifies a custom root directory for all generated video artifacts.
    *   **Note**: This can also be configured via `output_root` in `config.json`. If the specified directory does not exist, an error will occur if `output_root` is explicitly set. If it is not set, the default directory will be created automatically.

*   **`-f NAME`, `--filename NAME`**
    *   **Default**: Same as the project ID.
    *   **Description**: Specifies the filename of the final `.mp4` video (without extension).

### TTS Overrides (Temporary)

These options override settings defined in `config.json` for the current run only.

*   **`--tts-provider NAME`**: e.g., `google`, `openai`, `azure`.
*   **`--tts-model NAME`**: e.g., `gpt-4o-mini-tts`, `gemini-2.5-flash-preview-tts`.
*   **`--tts-voice NAME`**: e.g., `cedar`, `charon`.
*   **`--prompt TEXT`**: Overrides the system prompt and enables prompt usage (`tts_use_prompt=True`).
*   **`--no-prompt`**: Disables the use of a system prompt (`tts_use_prompt=False`).

### Debugging

*   **`--debug`**
    *   Enables detailed logging (INFO/DEBUG level).
    *   Shows skipped tasks and internal processing details.
    *   Sets FFmpeg log level to `info`.

---

## Examples

**1. Basic draft generation:**
```bash
slidemovie tutorial -p
```

**2. Building a video in a specific folder:**
```bash
slidemovie tutorial -s ./content -v
```

**3. Building a subproject with OpenAI TTS:**
```bash
slidemovie Course101 --sub Lesson01 -v --tts-provider openai --tts-model gpt-4o-mini-tts --no-prompt --tts-voice alloy
```

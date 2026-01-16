---
layout: page
title: Markdown Syntax
nav_order: 7
parent: Introduction
---

# Markdown Syntax Guide

The Markdown file acts as the "source code" for your video. `slidemovie` parses this file to understand the structure, visuals, and audio script.

## Slide Structure

Each slide is defined by a **Level 1 Header** (`#`).

```markdown
# Slide Title

- Bullet point 1
- Bullet point 2

::: notes
Script for narration.
:::
```

*   **Headers**: Only `#` (H1) creates a new slide. `##` (H2) or lower will remain as text on the current slide.
*   **Content**: You can use standard Markdown (lists, bold, code blocks, images).
*   **Notes**: The `::: notes` block is mandatory for narration.

## Special Comments

`slidemovie` supports special HTML-comment-style tags to control advanced behavior.

### 1. Slide ID (`<!-- slide-id: ... -->`)

When you run the tool, it automatically assigns a stable ID to each slide.

```markdown
<!-- slide-id: myproject-01 -->
# My Slide
```

*   **Purpose**: This ID links the Markdown section to the generated image file (`myproject-01.png`) and audio file (`myproject-01.wav`).
*   **Auto-Generation**: If you don't write this, `slidemovie` inserts it automatically on the first run.
*   **Best Practice**: Do not modify these manually once generated, or you might lose synchronization with existing assets.

#### Managing Slides and IDs

*   **Inserting a New Slide**: Write the new slide content (header, notes) **without** a `slide-id`. `slidemovie` will automatically assign a new, unique ID upon the next execution.
*   **Reordering Slides**: If you want to change the order, move the **entire block including the `slide-id`**.
*   **Order**: The final video follows the order of slides in the Markdown file, **not** the alphanumeric order of the Slide IDs.
*   **Validation**: Duplicate Slide IDs are not allowed. If detected, the program will exit with an error.

### 2. Video Insertion (`<!-- video-file: ... -->`)

You can replace a static slide with a video file (e.g., a screen recording or demo).

```markdown
<!-- slide-id: myproject-05 -->
# Demo Video
<!-- video-file: demo_clip.mp4 -->

::: notes
(This part is ignored if a video file is provided, OR used for timing depending on implementation. Usually, the duration of the inserted video takes precedence.)
:::
```

*   **Usage**: Place the `demo_clip.mp4` file inside the `movie/{project_name}/` directory.
*   **Behavior**: Instead of generating a static image + TTS, the tool will pick up `demo_clip.mp4`, resize it to fit the screen configuration (padding if necessary), and insert it into the final timeline.

## Notes Block Rules

The `::: notes` block is passed directly to the TTS engine.

1.  **Empty Line**: Always leave an empty line before `::: notes`.
    *   **Good**:
        ```markdown
        - item
        
        ::: notes
        ```
    *   **Bad**:
        ```markdown
        - item
        ::: notes
        ```
2.  **Plain Text**: Write the script as you want it spoken. Avoid Markdown formatting (like `**bold**`) inside the notes block unless you are sure the TTS engine ignores it.

```markdown
::: notes
Hello everyone. Today we will discuss Python.
:::
```

---
layout: page
title: Advanced Usage
nav_order: 8
parent: Introduction
---

# Advanced Usage & Internals

This section covers features for power users, including the incremental build system, direct state manipulation, and troubleshooting.

## Incremental Build System

Video generation can be slow and expensive (TTS API costs). `slidemovie` is designed to be **incremental**.

### How it works
The tool maintains a `status.json` file in your source directory. This file records:
*   The hash (fingerprint) of the Markdown content for each slide.
*   The hash of the PowerPoint file.
*   The hash of generated audio and video files.
*   The configuration used (resolution, FPS).

### Logic
When you run `slidemovie -v`:
1.  **Check PPTX**: If the PPTX file hasn't changed since the last run, image conversion is skipped.
2.  **Check Audio**: For each slide, it compares the current text in `::: notes` with the recorded hash.
    *   **Match**: Reuses the existing WAV file.
    *   **Mismatch**: Calls the AI API to regenerate audio for *only that slide*.
3.  **Check Video**: If the image and audio haven't changed, the MP4 generation for that slide is skipped.

This allows you to fix a typo in slide #10 and regenerate the whole video in seconds, without paying for TTS on slides #1-9.

## Managing State (`status.json`)

The `status.json` file is not just a cache; you can edit it to control generation behavior at a granular level.

### Custom Prompt per Slide

While the `prompt` in `config.json` sets the global system instruction for the TTS engine, you can add specific instructions for individual slides by editing `status.json`.

1.  Run the tool once to generate the initial `status.json`.
2.  Open `status.json` and find the target slide under the `"slides"` object.
3.  Locate the `"audio"` section and the `"additional_prompt"` field.
4.  Enter your custom instruction string.

**Example `status.json` snippet:**
```json
"myproject-05": {
  "title": "Introduction",
  "audio": {
    "status": "generated",
    "wav_file": "myproject-05.wav",
    "additional_prompt": "Speak this sentence with an excited tone."
  }
}
```

*   **Effect**: When regenerating audio for this slide, the TTS engine will receive: `Global Prompt` + `Additional Prompt` + `Slide Notes`.
*   **Triggering Regeneration**: After editing `additional_prompt`, you must force regeneration. The easiest way is to change the `"status"` value from `"generated"` to something else (e.g., `"missing"` or `"update"`) in `status.json`.

## Subprojects (Folder Management)

For creating a series of videos (e.g., an online course), use the `--sub` option.

**Directory Layout:**
```text
MyCourse/               <-- Parent Project Root
├── config.json         <-- Shared configuration
├── Section01/          <-- Subproject 1
│   ├── Section01.md
│   └── Section01.pptx
└── Section02/          <-- Subproject 2
    ├── Section02.md
    └── Section02.pptx
```

**Commands:**
```bash
# Build Section 1
slidemovie MyCourse --sub Section01 -v

# Build Section 2
slidemovie MyCourse --sub Section02 -v
```

The outputs will be organized cleanly in the output directory:
`movie/MyCourse/Section01/Section01.mp4`

## Troubleshooting

### "Movie class is not defined"
*   Ensure the package is installed correctly.
*   Check if `slidemovie` is imported in your script (if running from Python).

### Audio/Video Sync Issues
*   **Cause**: Did you delete or reorder slides in PowerPoint?
*   **Fix**: `slidemovie` relies on the slide count matching.
    1.  Check the generated `movie/{project}/slide_*.png` files.
    2.  Ensure the number of slides in Markdown matches the number of slides in the PPTX.
    3.  If they are desynchronized, it is safest to delete the `movie/{project}` folder and run `-v` again to rebuild.

### "build_config inconsistency detected"
*   **Cause**: You changed `screen_size` or `video_fps` in `config.json` after running the project once.
*   **Fix**: You cannot mix resolutions in one project.
    1.  Delete `status.json` in your source directory.
    2.  Delete the `movie/{project}` output directory.
    3.  Re-run the build.

### Debug Mode
If the tool crashes or behaves unexpectedly, run with `--debug`:

```bash
slidemovie myproject -v --debug
```

This will print detailed logs about:
*   Which files are being skipped.
*   FFmpeg command outputs.

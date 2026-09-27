---
layout: page
title: GUI Guide
nav_order: 4
parent: Introduction
---

# GUI Guide

The Tkinter GUI provides the same build workflow as the command line without requiring every option to be typed.

## Start the GUI

Run the following after installing slidemovie:

```bash
slidemovie -g
```

Command-line values can prefill the GUI. For example, `slidemovie demo -g --video` enters `demo` and selects video generation.

## Build a project

1. Set **Source folder** and **Project name**.
2. Under **Actions**, select **Build PPTX**, **Build video**, or both.
3. For a video made from a PDF, select **PDF** under **Video source**.
4. Click **Run**.

Use **Input files** and **Output files** under **Open folder** to open the actual project source and output directories in your file manager.

## Settings

The **Settings** tab initially shows the effective values from `config.json`.

- **TTS settings** include the provider, model, voice, prompt, prompt use, prompt separator, and narration splitting settings.
- **Video format** includes `screen_size`, `image_pad_color`, and `video_fps`.
- **General** includes `silence_sec`.

For the prompt separator and split characters, line breaks are shown as `\n` in the fields and are converted to actual line breaks when the build runs. **Restore settings** returns the fields to the values loaded from configuration.

## Project status and recorded settings

The **Project status** panel summarizes `status.json`: the PPTX and image tasks, slide counts, audio-file generation counts, and recorded TTS provider/model/voice. It does not display narration text, prompts, hashes, or credentials.

When the current TTS settings differ from `status.json`, choose one of the following:

- **Use status.json settings**: uses the recorded settings and copies every recorded TTS and build setting into the Settings tab.
- **Overwrite with current settings**: continues with the current GUI settings and updates the recorded TTS settings.
- **Cancel**: stops before building.

The interface is available in English and Japanese. The **Website** button opens the official site for the selected language.

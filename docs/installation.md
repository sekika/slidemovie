---
layout: page
title: Installation
nav_order: 2
parent: Introduction
---

# Installation & Preparation

Before you can generate videos, you need to set up the Python package and several external dependencies.

## 1. Install the Python Package

The easiest way to install `slidemovie` is via pip. Open your terminal or command prompt and run:

```bash
pip install slidemovie
```

This will automatically install the necessary Python dependencies, including `multiai-tts` and `pptxtoimages`.

## 2. Install External Tools

`slidemovie` acts as a conductor for several powerful command-line tools. You must install these on your system for the program to work.

### Required Tools

1.  **FFmpeg**: Used for processing audio and combining images and audio into a video file.
2.  **Pandoc**: Used to convert your Markdown text file into a PowerPoint (`.pptx`) file.
3.  **LibreOffice**: Used in "headless mode" to convert PowerPoint slides into high-resolution images.
4.  **Poppler (pdftoppm)**: A PDF rendering library used to extract images from the slides.

### Installation Commands

#### For macOS (using Homebrew)
If you do not have Homebrew installed, please visit [brew.sh](https://brew.sh/).

```bash
brew install ffmpeg pandoc poppler
brew install --cask libreoffice
```

#### For Ubuntu / Debian
```bash
sudo apt update
sudo apt install ffmpeg pandoc libreoffice poppler-utils
```

#### For Windows
1.  **FFmpeg**: Download from [ffmpeg.org](https://ffmpeg.org/), extract it, and **add the `bin` folder to your System PATH**.
2.  **Pandoc**: Download the installer from [pandoc.org](https://pandoc.org/).
3.  **LibreOffice**: Install the standard desktop version. Ensure the command line `soffice` is in your PATH.
4.  **Poppler**: Download binary release for Windows and add the `bin` folder to your PATH.

## 3. Setup AI API Keys

`slidemovie` uses the `multiai-tts` library to generate narration audio. You need to configure the model selection and the API keys.

### 1. Select the TTS Model

First, run the `slidemovie` command without any arguments:

```bash
slidemovie
```

Since no options are provided, this will result in an error. **This is expected behavior.** By running this command, a default configuration file is automatically created at:

`~/.config/slidemovie/config.json`

Next, please refer to the **[Configuration](../configuration/)** page. Edit the `tts_provider`, `tts_model`, and `tts_voice` settings in this file to select the Text-to-Speech model you wish to use.

### 2. Configure API Credentials

The configuration file handles model selection, but the API Key configuration follows the multiai settings.

Please refer to the official **[multiai documentation](https://sekika.github.io/multiai/)** for detailed instructions on how to configure your API keys.

> **Note:** Without a valid API key configuration matching your selected provider (Google Gemini, OpenAI or Azure), the audio generation step will fail.

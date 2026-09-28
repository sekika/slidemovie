---
layout: page
title: Installation
nav_order: 2
parent: Introduction
---

# Installation & Preparation

Before you can generate videos, you need to set up the Python package and several external dependencies.

## Prerequisite: Python 3

`slidemovie` requires Python 3.8 or later. Install [Python 3](https://www.python.org/) for your operating system before continuing, then confirm it is available:

```bash
python3 --version
```

Use `python3 -m pip` in the following commands when your system distinguishes Python 3 from an older Python installation.

If `pip` is not available yet, run the following commands before installing the package:

```bash
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip
```

## 1. Install the Python Package

The easiest way to install `slidemovie` is via pip. On Windows, open [PowerShell](https://learn.microsoft.com/powershell/scripting/windows-powershell/starting-windows-powershell); on macOS or Linux, open a terminal. Then run:

```bash
python3 -m pip install slidemovie
```

This will automatically install the necessary Python dependencies, including `multiai-tts` and `pptxtoimages`.

## 2. Install External Tools

`slidemovie` acts as a conductor for several powerful command-line tools. You must install these on your system for the program to work.

### Required Tools

1.  **FFmpeg**: Used for processing audio and combining images and audio into a video file.
2.  **Pandoc**: Used to convert your Markdown text file into a PowerPoint (`.pptx`) file.
3.  **LibreOffice**: Used in "headless mode" to convert PowerPoint slides into high-resolution images.
4.  **Poppler (pdftoppm)**: A PDF rendering library used to extract images from the slides.
5.  **ImageMagick (`convert`/`magick`)**: Used to normalize slide images to the configured `screen_size`, preserving aspect ratio with even padding (letterbox/pillarbox).

### Installation Commands

#### For macOS (using Homebrew)
If you do not have Homebrew installed, please visit [brew.sh](https://brew.sh/).

```bash
brew install ffmpeg pandoc poppler imagemagick
brew install --cask libreoffice
```

#### For Ubuntu / Debian
```bash
sudo apt update
sudo apt install ffmpeg pandoc libreoffice poppler-utils imagemagick
```

#### For Windows
On Windows, use Windows Package Manager (`winget`) to install the tools without downloading each archive or manually editing PATH. Open [PowerShell](https://learn.microsoft.com/powershell/scripting/windows-powershell/starting-windows-powershell) and run:

```powershell
winget install --id Gyan.FFmpeg --exact
winget install --id JohnMacFarlane.Pandoc --exact
winget install --id TheDocumentFoundation.LibreOffice --exact
winget install --id oschwartz10612.Poppler --exact
winget install --id ImageMagick.ImageMagick --exact
```

If `winget` is unavailable, update or install **App Installer** from the Microsoft Store. After installation, close PowerShell and open a new window, then verify the commands:

```powershell
ffmpeg -version
ffprobe -version
pandoc --version
pdftoppm -v
magick -version
```

If a command is still unavailable after installing with `winget`, sign out of Windows and sign in again before checking once more.

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

`slidemovie` uses `multiai-tts` for text-to-speech. API credentials are managed using the same configuration mechanism as [`multiai`](https://sekika.github.io/multiai/).

The easiest method is to set the credentials as environment variables.

For **Google Gemini**:

```sh
export GOOGLE_API_KEY="your-api-key"
```

For **OpenAI**:

```sh
export OPENAI_API_KEY="your-api-key"
```

For **Azure Speech**:

```sh
export AZURE_TTS_API_KEY="your-api-key"
export AZURE_TTS_REGION="japaneast"
```

Replace `japaneast` with the region of your Azure Speech resource. Note that Azure TTS uses an **Azure Speech API key**, not an Azure OpenAI API key.

Alternatively, the credentials can be stored in the `multiai` settings file. `multiai` reads settings from `~/.multiai` and then from `./.multiai`, with project-level settings taking precedence.

For example:

```ini
[api_key]
openai = (Your OpenAI API key)
google = (Your Gemini API key)
azure_tts = (Your Azure Speech API key)

[azure_tts]
region = japaneast
```

You only need to configure the credentials for the TTS provider selected by `tts_provider` in the `slidemovie` configuration file.

For more information, including the complete `multiai` configuration format, see the official [`multiai` documentation](https://sekika.github.io/multiai/).

> **Note:** Without valid credentials for the selected provider (`google`, `openai`, or `azure`), audio generation will fail.

> **VOICEVOX:** If you select the `voicevox` provider, no API key is required. Instead, the [VOICEVOX engine](https://voicevox.hiroshiba.jp/) must be running locally (default `http://127.0.0.1:50021`) before you build. See [Configuration](../configuration/) for `tts_voice` (speaker style ID) and `tts_voicevox_url`.

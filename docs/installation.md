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

#### Windows: add the `slidemovie` command to PATH

On Windows, run the following once in PowerShell to add Python's Scripts folder to your user PATH. This is required to run the `slidemovie` command directly:

```powershell
$scriptsDir = python3 -c "import sysconfig; print(sysconfig.get_path('scripts'))"
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ([string]::IsNullOrWhiteSpace($userPath)) {
    [Environment]::SetEnvironmentVariable('Path', $scriptsDir, 'User')
} elseif (($userPath -split ';') -notcontains $scriptsDir) {
    [Environment]::SetEnvironmentVariable('Path', "$userPath;$scriptsDir", 'User')
}
```

Close PowerShell, open a new window, and then verify it with:

```powershell
slidemovie -h
```

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
On Windows, use Windows Package Manager (`winget`) to install the tools without downloading each archive or manually editing PATH. Open [PowerShell](https://learn.microsoft.com/powershell/scripting/windows-powershell/starting-windows-powershell), then run the following commands **one at a time**. Confirm that each command finishes before proceeding to the next.

If `winget` is unavailable, first update or install **App Installer** from the Microsoft Store.

```powershell
winget install --id Gyan.FFmpeg --exact
winget install --id JohnMacFarlane.Pandoc --exact
winget install --id TheDocumentFoundation.LibreOffice --exact
winget install --id oschwartz10612.Poppler --exact
winget install --id ImageMagick.ImageMagick --exact
```

After all installations finish, close PowerShell and open a new window. This applies the PATH changes; then verify the commands:

```powershell
ffmpeg -version
ffprobe -version
pandoc --version
Get-Command pdftoppm
magick -version
```

If a command is still unavailable after installing with `winget`, sign out of Windows and sign in again before checking once more.

## 3. Setup AI API Keys

`slidemovie` uses the `multiai-tts` library to generate narration audio. You need to configure the model selection and the API keys.

### 1. Select the TTS Model

First, create the user configuration file:

```powershell
slidemovie --init-config
```

This command creates the default configuration file and exits. Its location is `~/.config/slidemovie/config.json` on macOS and Linux, and `C:\Users\<username>\.config\slidemovie\config.json` on Windows.

Next, please refer to the **[Configuration](../configuration/)** page. Edit the `tts_provider`, `tts_model`, and `tts_voice` settings in this file to select the Text-to-Speech model you wish to use.

### 2. Configure API Credentials

`slidemovie` uses `multiai-tts` for text-to-speech. API credentials are managed using the same configuration mechanism as [`multiai`](https://sekika.github.io/multiai/).

Credentials can be stored in the `multiai` settings file. `multiai` reads settings from `~/.multiai` and then from `./.multiai`, with project-level settings taking precedence. On Windows, open the user settings file in Notepad from PowerShell. `$HOME` expands to the user home directory (for example, `C:\Users\seki`):

```powershell
notepad "$HOME\.multiai"
```

On macOS, open it in TextEdit:

```bash
open -e ~/.multiai
```

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

For environment-variable setup and the complete `multiai` configuration format, see the official [`multiai` documentation](https://sekika.github.io/multiai/).

> **Note:** Without valid credentials for the selected provider (`google`, `openai`, or `azure`), audio generation will fail.

> **VOICEVOX:** If you select the `voicevox` provider, no API key is required. Instead, the [VOICEVOX engine](https://voicevox.hiroshiba.jp/) must be running locally (default `http://127.0.0.1:50021`) before you build. See [Configuration](../configuration/) for `tts_voice` (speaker style ID) and `tts_voicevox_url`.

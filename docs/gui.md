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

The **Settings** tab initially shows the effective values from [`config.json`]({{ '/configuration/' | relative_url }}).

- **TTS settings** include the provider, model, voice, prompt, prompt use, prompt separator, and narration splitting settings.
- **Video format** includes `screen_size`, `image_pad_color`, and `video_fps`.
- **General** includes `silence_sec`.

For the prompt separator and split characters, line breaks are shown as `\n` in the fields and are converted to actual line breaks when the build runs. **Restore settings** returns the fields to the values loaded from configuration.

## Project status and recorded settings

The **Project status** panel summarizes [`status.json`]({{ '/advanced-usage/' | relative_url }}): the PPTX and image tasks, slide counts, audio-file generation counts, and recorded TTS provider/model/voice. It does not display narration text, prompts, hashes, or credentials.

When the current TTS settings differ from `status.json`, choose one of the following:

- **Use status.json settings**: uses the recorded settings and copies every recorded TTS and build setting into the Settings tab.
- **Overwrite with current settings**: continues with the current GUI settings and updates the recorded TTS settings.
- **Cancel**: stops before building.

The interface is available in English and Japanese. The **Website** button opens the official site for the selected language.

## Create a GUI shortcut

If you use the GUI regularly, you can create a shortcut to open it from the desktop or Applications folder. Download the script and icon for your operating system below.

Download the script and its matching icon into the same folder:

- Windows: [shortcut script]({{ '/downloads/create-slidemovie-shortcut.ps1' | relative_url }}) and [icon (`.ico`)]({{ '/downloads/slidemovie.ico' | relative_url }})
- macOS: [app-creation script]({{ '/downloads/create-slidemovie-app.command' | relative_url }}) and [icon (`.icns`)]({{ '/downloads/slidemovie.icns' | relative_url }})

### Windows

Open PowerShell in the downloaded folder and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\create-slidemovie-shortcut.ps1
```

The script creates `SlideMovie.lnk` on the desktop. It automatically finds `pythonw.exe` and opens the GUI without showing a console window. It also records the creation-time `PATH` in a small launcher, so external tools such as FFmpeg remain available when you start the shortcut from Explorer. In the usual case, the command above is all you need; do not edit the script.

If the first attempt reports that Python cannot be found, paste and run these **two lines together** in PowerShell. The first line uses the Python Launcher to find `pythonw.exe`; the second passes that location to the shortcut-creation script. You do not need to edit either the shortcut or the script.

```powershell
$pythonw = & py -3 -c "import sys; print(sys.executable.replace('python.exe', 'pythonw.exe'))"
.\create-slidemovie-shortcut.ps1 -PythonPath $pythonw
```

The discovered `pythonw.exe` path becomes the launch target of the created `SlideMovie.lnk`.

### macOS

Open Terminal in the downloaded folder and run:

```bash
chmod +x create-slidemovie-app.command
./create-slidemovie-app.command
```

The script creates and opens `~/Applications/SlideMovie.app`. It explicitly passes the folder where you ran the creation script as `--source-dir`, so that folder becomes the initial source folder. Run the script from the folder you want to use. It also records the creation-time `PATH` so that external tools installed through Homebrew remain available when you open the app directly from Finder. Move the app to `/Applications` if you want it available to every user on the Mac. If startup fails, check `~/Library/Logs/SlideMovie.log`. The script records the current `slidemovie` command path; run `which slidemovie` first if you need to check which Python environment will be used.

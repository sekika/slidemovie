# slidemovie

[![PyPI version](https://badge.fury.io/py/slidemovie.svg)](https://badge.fury.io/py/slidemovie)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-github.io-blue)](https://sekika.github.io/slidemovie/)

**Markdown and PowerPoint to Narration Video Generator.**

`slidemovie` is a Python tool that automates the creation of professional narration videos. By combining the structural simplicity of **Markdown**, the design capabilities of **PowerPoint**, and the power of **AI Text-to-Speech**, you can produce high-quality videos without any video editing software.

---

## 📚 Documentation

**For full tutorials, installation guides, and configuration details, please visit:**

👉 **[https://sekika.github.io/slidemovie/](https://sekika.github.io/slidemovie/)**

---

## ✨ Features

*   **Markdown-Based**: Write your slide content and narration script in a single text file.
*   **AI Narration**: Automatically generates natural voiceovers using **Google Gemini** or **OpenAI** (via `multiai-tts`).
*   **PowerPoint Integration**: Use PowerPoint's AI "Designer" to create professional visuals instantly.
*   **No Video Editing**: Audio and visuals are automatically synchronized.
*   **Incremental Builds**: Only regenerates changed slides to save time and API costs.

## 🎥 Demo

**Watch a video generated entirely by slidemovie:**
[https://www.youtube.com/watch?v=9ZscwE06Pbo](https://www.youtube.com/watch?v=9ZscwE06Pbo)

## 🚀 Quick Start

### 1. Install

```bash
pip install slidemovie
```

*Note: You also need to install **FFmpeg**, **Pandoc**, **LibreOffice**, and **Poppler**, and set up your **AI API Key** (Google or OpenAI). See the [documentation](https://sekika.github.io/slidemovie/installation.html) for details.*

### 2. Create a Project

Create a Markdown file (e.g., `demo.md`):

```markdown
# Slide Title

- Bullet point 1
- Bullet point 2

::: notes
This text will be read aloud by the AI narrator.
:::
```

### 3. Generate Slides

Convert Markdown to a draft PowerPoint file:

```bash
slidemovie demo -p
```

Open `demo.pptx` in PowerPoint, apply a design, and save it.

### 4. Build Video

Generate the final video with AI narration:

```bash
slidemovie demo -v
```

The output will be saved in `movie/demo/demo.mp4`.

## 📄 License

MIT License

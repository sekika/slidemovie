---
layout: page
title: Workflow Guide
nav_order: 3
parent: Introduction
---

# Standard Workflow

Creating a video involves four distinct steps. This workflow ensures you have full control over the content and design while automating the tedious parts.

## Step 1: Create the Markdown File

Create a new file named `project_name.md`. This file serves as both your slide content and your narration script.

### Syntax Rules
1.  **Headers**: Use Level 1 Headers (`# Title`) for the title of each slide.
2.  **Content**: Use bullet points for the text displayed on the slide.
3.  **Speaker Notes**: Use a `::: notes` block for the narration.
4.  **Spacing**: **Crucial!** You must leave at least one empty line before `::: notes`.

### File Example (`demo.md`)

```markdown
# Introduction to Slidemovie

- Automate video creation
- Markdown + PowerPoint
- AI Narration

::: notes
Welcome to the introduction of Slidemovie. This tool allows you to automate video creation using Markdown and PowerPoint, powered by AI narration.
:::

# How it Works

1. Write Markdown
2. Generate PPTX
3. Edit Design
4. Build Video

::: notes
The process is simple. First, write your script in Markdown. Second, generate a PowerPoint file. Third, edit the design using PowerPoint's Designer. Finally, build the video with a single command.
:::
```

## Step 2: Generate Draft PowerPoint

Open your terminal and navigate to the folder containing your Markdown file. Run the following command using the `-p` (pptx) flag:

```bash
# Syntax: slidemovie [PROJECT_NAME] -p
slidemovie demo -p
```

This will read `demo.md` and create `demo.pptx`.

*   **Note**: At this stage, the PowerPoint file will look very plain (white background, black text). This is normal.

## Step 3: Edit Slide Design

This is the only manual step, allowing you to add human creativity.

1.  Open `demo.pptx` in **Microsoft PowerPoint**.
2.  Open the **"Designer"** pane (found under the **Home** or **Design** tab).
3.  Click on each slide and select a professional design suggested by the AI.
4.  (Optional) Add images, change fonts, or adjust colors.

### Important Warnings
*   **Do NOT change the order of the slides.**
*   **Do NOT delete slides.**
*   **Do NOT add new slides inside PowerPoint.**

The program links the audio to the slide based on the Markdown structure. Changing the slide count in PowerPoint will break the synchronization. If you need to add/remove slides, edit the **Markdown file** first, then run step 2 again (note: this will overwrite your design, so finalize your script early!).

## Step 4: Generate the Video

Once you have saved your beautiful PowerPoint file (overwriting the original `demo.pptx`), run the build command using the `-v` (video) flag:

```bash
# Syntax: slidemovie [PROJECT_NAME] -v
slidemovie demo -v
```

The program will:
1.  Read the Markdown notes and generate audio files (WAV).
2.  Convert the PowerPoint slides into images (PNG).
3.  Combine them into individual slide videos.
4.  Stitch them all together into one final movie.

### Output Location
The final video will be saved in:
`./movie/demo/demo.mp4`

---

## Subprojects (Hierarchical Mode)

If you want to organize your projects into folders, you can use the `--sub` option.

**Structure:**
```text
ParentProject/
  ├── ChildA/
  │   └── ChildA.md
  └── ChildB/
      └── ChildB.md
```

**Command:**
```bash
slidemovie ParentProject --sub ChildA -v
```

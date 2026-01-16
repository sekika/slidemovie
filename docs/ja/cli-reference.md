---
layout: page
title: CLI リファレンス
lang: ja
nav_order: 5
parent: はじめに
---

# コマンドラインインターフェース (CLI) リファレンス

`slidemovie` コマンドは、すべての操作の入り口となります。

## 基本的な構文

```bash
slidemovie [プロジェクト名] [オプション]
```

## 位置引数

*   **`PROJECT_NAME`** (必須)
    *   プロジェクトの識別子（名前）です。
    *   ツールはソースディレクトリ内の `{PROJECT_NAME}.md` を探します。
    *   サブプロジェクトモード (`--sub`) を使用する場合、この引数は **親フォルダ名** （出力の分類用）を指定します。

## オプション

### モード制御フラグ (少なくとも1つは必須)

*   **`-p`, `--pptx`**
    *   **動作**: ソースとなる Markdown ファイルを PowerPoint (`.pptx`) ファイルに変換します。
    *   **用途**: 初期ドラフトの作成、またはスライドテキストの更新。
    *   **注意**: 既存の PPTX ファイルがある場合、上書きされます（デザイン済みファイルがある場合は注意が必要です）。

*   **`-v`, `--video`**
    *   **動作**: 完全な動画をビルドします。
    *   **処理ステップ**:
        1.  Markdown のノートから音声 (TTS) を生成。
        2.  PPTX ファイルから画像をエクスポート。
        3.  音声と画像を結合してスライドごとのクリップを作成。
        4.  すべてのクリップを結合して最終的な動画ファイルを作成。
    *   **用途**: 最終的な動画制作。

### パス・プロジェクト構造

*   **`-s DIR`, `--source-dir DIR`**
    *   **デフォルト**: `.` (カレントディレクトリ)
    *   **説明**: ソースファイル (.md, .pptx) が存在するディレクトリを指定します。
    *   **例**: `slidemovie myproject -s ./docs` (`./docs/myproject.md` を探しに行きます)

*   **`--sub SUB_NAME`**
    *   **説明**: **階層構造（サブプロジェクト）モード** を有効にします。
    *   **挙動**:
        *   `PROJECT_NAME` は出力先の親フォルダ名として使用されます。
        *   `SUB_NAME` が **子** フォルダ（サブプロジェクト）になります。
        *   入力ソース: `{Child}/{Child}.md`
        *   出力動画: `movie/{Parent}/{Child}/{Child}.mp4`
    *   **例**: `slidemovie Season1 --sub Episode1`

*   **`-o DIR`, `--output-root DIR`**
    *   **デフォルト**: `./movie` (ソースディレクトリからの相対パス)
    *   **説明**: 生成されたすべての動画成果物を出力するルートディレクトリを指定します。
    *   **注意**: 設定ファイルの `output_root` でも指定可能です。指定されたディレクトリが存在しない場合は、デフォルトのディレクトリが自動的に作成されます。

*   **`-f NAME`, `--filename NAME`**
    *   **デフォルト**: プロジェクトIDと同じ。
    *   **説明**: 最終的に出力される `.mp4` ファイルの名前（拡張子なし）を指定します。

### TTS 設定の上書き (一時的)

これらのオプションは、`config.json` の設定を **今回の実行に限り** 上書きします。

*   **`--tts-provider NAME`**: 例: `google`, `openai`
*   **`--tts-model NAME`**: 例: `gpt-4o-mini-tts`, `gemini-2.5-flash-preview-tts`
*   **`--tts-voice NAME`**: 例: `cedar`, `charon`
*   **`--prompt TEXT`**: TTS生成時のシステムプロンプトを上書きし、プロンプトの使用を有効にします (`tts_use_prompt=True`)。
*   **`--no-prompt`**: システムプロンプトの使用を無効にします (`tts_use_prompt=False`)。

### デバッグ

*   **`--debug`**
    *   詳細なログ出力を有効にします (INFO/DEBUG レベル)。
    *   スキップされたタスクや内部処理の詳細を表示します。
    *   FFmpeg のログレベルを `info` に設定します。

---

## 実行例

**1. 基本的なドラフト生成:**
```bash
slidemovie tutorial -p
```

**2. 特定のフォルダにあるプロジェクトを動画化:**
```bash
slidemovie tutorial -s ./content -v
```

**3. サブプロジェクトを OpenAI の音声でビルド:**
```bash
slidemovie Course101 --sub Lesson01 -v --tts-provider openai --tts-voice alloy
```

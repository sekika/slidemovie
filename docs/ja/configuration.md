---
layout: page
title: 設定ファイル
lang: ja
nav_order: 6
parent: はじめに
---

# 設定 (`config.json`)

`slidemovie` では、JSON 設定ファイルを使用して、動画の解像度、音質、TTS の設定などをカスタマイズできます。

## 設定の読み込み順序

プログラムは以下の順序で設定を読み込みます（後から読み込まれたものが優先されます）。

1.  **組み込みのデフォルト値**: プログラム内にハードコードされています。
2.  **ユーザー設定**: `~/.config/slidemovie/config.json` (ホームディレクトリ)。
    *   **注意**: このファイルが存在しない場合、初回実行時にデフォルト値で自動的に作成されます。
3.  **ローカル設定**: `./config.json` (カレントディレクトリ)。
4.  **CLI 引数**: コマンドラインフラグ（特定の設定に対して最も高い優先度を持ちます）。

## 設定オプション一覧

`config.json` で使用可能なキーの一覧です。

### テキスト読み上げ (TTS)

サポートされているプロバイダーとモデルについては、[multiai-tts](https://sekika.github.io/multiai-tts/#supported-ai-providers)を参照してください。

| キー | 型 | デフォルト | 説明 |
| :--- | :--- | :--- | :--- |
| `tts_provider` | 文字列 | `"google"` | AI プロバイダー (`google`, `openai`, `azure` または `voicevox`)。 |
| `tts_model` | 文字列 | `"gemini-3.1-flash-tts-preview"` | 使用する具体的なモデル名。Google と OpenAI では使用し、Azure と VOICEVOX では不要。 |
| `tts_voice` | 文字列 | `"sadaltager"` | 話者 ID (例: OpenAI の場合は `alloy`、Azure で英語の場合は `en-US-AvaMultilingualNeural`)。VOICEVOX では **整数の話者 style ID**（例: `"3"`）。 |
| `tts_use_prompt`| 真偽値 | `true` | TTS API にシステムプロンプトを送信するかどうか。Google では true, OpenAI・Azure・VOICEVOX では false |
| `prompt` | 文字列 | `"Please speak..."` | TTS エンジンへのシステム指示（プロンプト）。 |
| `prompt_separator` | 文字列 | `""` | スタイルプロンプト（`prompt` ＋ スライドごとの `additional_prompt`）と読み上げ本文の間に挿入する区切り文字列。空で無効（デフォルト）。長いプロンプトで原稿の開始位置を明示したい場合に有用（例: `"\n\n## 原稿\n"`）。[スライドごとのカスタムプロンプト](advanced-usage.md#スライドごとのカスタムプロンプト) を参照。 |
| `chunk_size` | int / null | `null` | 長いナレーションを分割する際の 1 チャンクあたりの最大文字数。`null` で分割無効（デフォルト動作）。プロンプトは含めず読み上げ本文の長さのみで評価される。[長文ナレーション](advanced-usage.md#長文ナレーションの自動チャンク分割) を参照。 |
| `split_chars` | 文字列 | `"。．.!！?？\n"` | テキストを分割する候補となる文字。 |
| `chunk_overflow` | 文字列 | `"extend"` | `chunk_size` 以内に分割候補が見つからない場合の挙動。`"extend"` は次の候補まで読み進める。`"error"` はエラーで停止する。 |
| `tts_voicevox_url` | 文字列 / null | `null` | VOICEVOX エンジンの URL。`null` の場合は既定値（`http://127.0.0.1:50021`）を使用する。`tts_provider` が `voicevox` のときのみ使用される。 |

> **VOICEVOX について:** [VOICEVOX](https://voicevox.hiroshiba.jp/) は**ローカルエンジン**として動作し、ビルド前に起動しておく必要があります（既定 `http://127.0.0.1:50021`）。API キーは不要で、`tts_model` は無視され、`tts_voice` には整数の話者 style ID を指定します。スタイルプロンプトが読み上げられないよう `tts_use_prompt` は `false` に設定してください。

### 動画フォーマット

| キー | 型 | デフォルト | 説明 |
| :--- | :--- | :--- | :--- |
| `screen_size` | [int, int] | `[1280, 720]` | 解像度 `[幅, 高さ]`。スライド画像はこのサイズに正規化されます。 |
| `image_pad_color` | 文字列 | `"white"` | スライドのアスペクト比が `screen_size` と異なる場合の余白色。画像はアスペクト比を保って内接縮小し中央に配置され、不足分がこの色で均等に（上下または左右に）埋められます。ImageMagick が解釈する色名・値を指定できます（例: `"black"`）。 |
| `video_fps` | int | `30` | フレームレート (FPS)。 |
| `video_codec` | 文字列 | `"libx264"` | 映像コーデック。 |
| `video_pix_fmt` | 文字列 | `"yuv420p"` | ピクセルフォーマット（互換性のため）。 |

### 音声フォーマット

| キー | 型 | デフォルト | 説明 |
| :--- | :--- | :--- | :--- |
| `audio_codec` | 文字列 | `"aac"` | 音声コーデック。 |
| `sample_rate` | int | `44100` | サンプリングレート (Hz)。 |
| `audio_bitrate` | 文字列 | `"192k"` | 音声ビットレート。 |
| `audio_channels`| int | `2` | 1 (モノラル) または 2 (ステレオ)。 |

### 一般 / 処理設定

| キー | 型 | デフォルト | 説明 |
| :--- | :--- | :--- | :--- |
| `silence_sec` | 浮動小数 | `2.5` | 各スライドの音声の前に挿入される無音時間（秒）。 |
| `max_retry` | int | `2` | TTS API エラー時の最大リトライ回数。 |
| `ffmpeg_loglevel`| 文字列 | `"error"` | FFmpeg プロセスのログ出力レベル。 |
| `show_skip` | 真偽値 | `false` | `true` の場合、スキップされたタスク（変更のないファイル）をログに表示します。`--debug` でも有効化できます。 |
| `output_root` | 文字列 | `null` | 動画出力先のルートディレクトリを指定します。CLI の `-o` オプションで上書き可能です。 |
| `output_filename` | 文字列 | `null` | 出力される動画のファイル名（拡張子なし）。未設定の場合はプロジェクトIDが使用されます。CLI の `-f` オプションで上書き可能です。 |

## `config.json` の例

例えば、**フルHD (1080p)** の動画を **OpenAI** を使って作成したい場合、プロジェクトフォルダに以下の内容で `config.json` を保存します。

```json
{
    "tts_provider": "openai",
    "tts_model": "gpt-4o-mini-tts",
    "tts_voice": "alloy",
    "tts_use_prompt": false,
    "screen_size": [1920, 1080]
}
```

**VOICEVOX** を使う場合（先にローカルエンジンを起動してください）:

```json
{
    "tts_provider": "voicevox",
    "tts_voice": "3",
    "tts_use_prompt": false
}
```

> **警告:** 一度プロジェクトのビルドを開始すると、解像度 (`screen_size`) や FPS は状態ファイル (`status.json`) に記録されます。途中でこれらの設定を変更すると、`slidemovie` は不整合を検知して処理を中断します（動画が破損するのを防ぐため）。新しい動画設定を適用するには、`movie/` ディレクトリ内のファイルを削除して最初から再ビルドする必要があります。

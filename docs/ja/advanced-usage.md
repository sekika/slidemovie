---
layout: page
title: 高度な使い方
lang: ja
nav_order: 8
parent: はじめに
---

# 高度な使い方と内部構造

このセクションでは、差分ビルドシステム、ステータスファイルの直接操作、トラブルシューティングなど、パワーユーザー向けの機能を解説します。

## Python API を使う

コマンドラインの代わりに、Python から `Movie` を呼び出して動画を作成できます。複数のプロジェクトを順番にビルドする処理や、既存のPythonアプリケーションへの組み込みに便利です。API でも CLI と同じ `config.json`、差分ビルド、出力構成を使用します。

次の例は、`demo.md` とデザイン済みの `demo.pptx` がある `projects/demo` フォルダーから動画を生成します。

```python
from pathlib import Path

from slidemovie import Movie

project_name = "demo"
source_dir = Path("projects/demo")

# 1. 設定を読み込み、外部コマンドを確認する
movie = Movie()

# 2. 入力・出力パスを決める。ここで projects/demo/config.json も読み込まれる
movie.configure_project_paths(project_name, str(source_dir))

# 3. 必要な設定だけを Python 側で上書きする
movie.tts_provider = "openai"
movie.tts_model = "tts-1"
movie.tts_voice = "alloy"

# 4. 音声、スライド画像、動画を生成して結合する
movie.build_all()

print(f"完成: {movie.video_file}")
```

処理の流れは次のとおりです。

1. `Movie()` はユーザー設定と必要な外部コマンドを確認します。
2. `configure_project_paths()` は `<プロジェクト名>.md`、`<プロジェクト名>.pptx`、出力先を設定し、同じフォルダーの `config.json` を読み込みます。出力先を省略した場合は `projects/demo/movie/demo/demo.mp4` です。
3. TTS の声やモデルなど、Pythonから指定したい値はこの後に属性として設定します。これにより `config.json` の値を必要な項目だけ上書きできます。
4. `build_all()` は Markdown の `::: notes` から音声を生成し、PPTX を画像化してから動画を結合します。変更のない成果物は再利用されます。

PPTX の下書きを Markdown から作る場合は、`build_all()` の前に `movie.build_slide_pptx()` を呼びます。生成された PPTX を PowerPoint でデザイン・保存してから、改めて上のスクリプトで `build_all()` を実行してください。`build_all()` 自体は PPTX を更新しません。

## 差分ビルドシステム

動画生成には時間がかかり、TTS API のコストもかかります。そのため、`slidemovie` は **差分ビルド（インクリメンタルビルド）** を行うように設計されています。

### 仕組み
ツールはソースディレクトリに `status.json` というファイルを保持します。このファイルには以下が記録されています：
*   各スライドの Markdown コンテンツ（原稿）のハッシュ値
*   PowerPoint ファイルのハッシュ値
*   生成された音声・動画ファイルのハッシュ値
*   使用された設定（解像度、FPS）

### ロジック
`slidemovie -v` を実行したとき：
1.  **PPTX の確認**: PPTX ファイルが前回実行時から変更されていなければ、画像の再変換をスキップします。
2.  **音声の確認**: 各スライドについて、現在の `::: notes` のテキストと記録されたハッシュを比較します。
    *   **一致**: 既存の WAV ファイルを再利用します。
    *   **不一致**: そのスライドについてのみ、AI API を呼び出して音声を再生成します。
3.  **動画の確認**: 画像と音声に変更がなければ、そのスライドの MP4 生成をスキップします。

これにより、例えばスライド #10 の誤字を修正して再ビルドする場合でも、スライド #1〜#9 の TTS コストを払うことなく、数秒で動画全体を再生成できます。

## 状態ファイル (`status.json`) の管理

`status.json` は単なるキャッシュではなく、生成挙動を細かく制御するために編集することも可能です。

### スライドごとのカスタムプロンプト

`config.json` の `prompt` は TTS エンジン全体へのシステム指示を設定しますが、`status.json` を編集することで、特定のスライドだけに個別の追加指示を与えることができます。

1.  ツールを一度実行して、初期の `status.json` を生成させます。
2.  `status.json` を開き、`"slides"` オブジェクトの中から対象のスライドを探します。
3.  `"audio"` セクション内の `"additional_prompt"` フィールドを見つけます。
4.  追加したい指示を文字列として入力します。

**`status.json` の記述例:**
```json
"myproject-05": {
  "title": "導入",
  "audio": {
    "status": "generated",
    "wav_file": "myproject-05.wav",
    "additional_prompt": "この文は興奮した口調で話してください。"
  }
}
```

*   **効果**: このスライドの音声を再生成する際、TTS エンジンには `全体プロンプト` + `追加プロンプト` + `prompt_separator` + `スライドの原稿` が送信されます。
*   **再生成のトリガー**: `additional_prompt` を編集した後、再生成をトリガーする必要があります。最も簡単な方法は、`status.json` 内の `"status"` の値を `"generated"` から別の値（例: `"missing"` や `"update"`）に変更することです。

### プロンプトと原稿の区切り (`prompt_separator`)

`prompt` が長くなると、「どこまでが指示で、どこからが読み上げ原稿か」の境界を明示したくなります。このとき、区切り文字を **`prompt` の末尾に書いてはいけません**。スライドごとの `additional_prompt` は `prompt` の後ろに挿入されるため、`prompt` 末尾に区切りを置くと `additional_prompt` が原稿側に押し出されてしまいます。

代わりに `prompt_separator`（`config.json` または `--prompt-separator`）を設定します。これは指示部分と読み上げ本文の間に挿入されるため、エンジンが受け取る並びは常に次のようになります。

```
{prompt}{additional_prompt}{prompt_separator}{読み上げ本文}
```

`prompt` と `additional_prompt` は常に区切りの上（指示側）に残ります。ナレーションの言語に合わせて自然な文字列を指定してください。

```json
{
  "prompt": "あなたはプロのナレーターです。落ち着いた声で、聞き取りやすい速度で読んでください。",
  "prompt_separator": "\n\n## 原稿\n"
}
```

デフォルトは `""`（無効）なので、既存プロジェクトには影響しません。`prompt_separator` は記録される TTS 設定の一部であり、変更すると「TTS config change detected」の確認が表示されます（[長文ナレーション → 注意点](#注意点) を参照）。

## 長文ナレーションの自動チャンク分割

スライドのナレーション（`::: notes`）が長い場合、プロバイダのリクエスト長制限を超えたり、一部の Gemini モデルのように長文で品質が劣化したりすることがあります。`slidemovie` は、長いナレーションを小さなチャンクに自動分割し、それぞれを合成して音声を結合できます。

この機能は **デフォルトでは無効**（`chunk_size: null`）で、明示的に有効化しない限り従来どおりの動作です。

### 有効化の方法

`config.json` で `chunk_size` を設定するか、コマンドラインで `--chunk-size` を指定します。

```bash
# ナレーションを最大 800 文字程度のチャンクに分割
slidemovie myproject -v --chunk-size 800
```

| 設定 | CLI | 説明 |
| :--- | :--- | :--- |
| `chunk_size` | `--chunk-size N` | 1 チャンクあたりの最大文字数。設定したときのみ分割が有効になります。 |
| `split_chars` | `--split-chars STR` | 分割を許可する文字（デフォルト: `。．.!！?？` と改行）。`chunk_size` 以内で見つかった最も右側の候補の直後で分割します。 |
| `chunk_overflow` | `--chunk-overflow {extend,error}` | `chunk_size` 以内に候補が見つからない場合の挙動。`extend`（デフォルト）は次の候補（またはテキスト末尾）まで読み進めます。`error` は実行を停止します。 |

### プロンプトとチャンク分割の関係

スタイルプロンプト（`prompt` とスライドごとの `additional_prompt`）は、読み上げ本文とは **分離して** TTS エンジンに渡されます。その結果:

*   プロンプトは **各チャンクに再適用** されるため、ナレーション全体で声色・口調が一貫します。`prompt_separator` もスタイルプロンプトの一部として各チャンクに適用されます。
*   `chunk_size` は **読み上げ本文の長さのみ** で評価され、プロンプト長（`prompt_separator` を含む）は含まれません。

### 注意点

*   **チャンクの境界**: 個別に合成したチャンクを結合するため、つなぎ目でピッチやテンポがわずかに変化することがあります。`chunk_size` を大きくするほどつなぎ目は減ります。
*   **`extend` は `chunk_size` を超え得る**: `chunk_size` 以内に分割候補がない場合、`extend` は次の候補（またはテキスト末尾）まで読み進めるため、個々のチャンクが `chunk_size` を大きく超えることがあります。
*   **API の文字数上限はユーザー責任**: `chunk_size` はユーザーが指定する文字数であり、プロバイダの実際のリクエスト上限から自動算出されるものではありません。利用するプロバイダ／モデルの上限に収まる値を選んでください。
*   **再生成**: `chunk_size` / `split_chars` / `chunk_overflow` は `status.json` に記録される TTS 設定の一部です。これらを変更すると、声や モデルを変更したときと同様に「TTS config change detected」の確認プロンプトが表示されます。

## サブプロジェクト（フォルダ管理）

シリーズ動画（例：オンラインコース）を作成する場合、`--sub` オプションを使うと便利です。

**ディレクトリ構成:**
```text
MyCourse/               <-- 親プロジェクトルート
├── config.json         <-- 共通設定
├── Section01/          <-- サブプロジェクト 1
│   ├── Section01.md
│   └── Section01.pptx
└── Section02/          <-- サブプロジェクト 2
    ├── Section02.md
    └── Section02.pptx
```

**コマンド:**
```bash
# セクション 1 をビルド
slidemovie MyCourse --sub Section01 -v

# セクション 2 をビルド
slidemovie MyCourse --sub Section02 -v
```

出力ファイルは、出力ディレクトリ内で整理されて保存されます：
`movie/MyCourse/Section01/Section01.mp4`

## トラブルシューティング

### "Movie class is not defined"
*   パッケージが正しくインストールされているか確認してください。
*   Python スクリプトから呼び出している場合、`import slidemovie` がされているか確認してください。

### 音ズレが発生する / 音声と映像が合わない
*   **原因**: PowerPoint でスライドを削除したり、順番を入れ替えたりしていませんか？
*   **修正**: `slidemovie` はスライドの「数」と「順番」が一致していることを前提としています。
    1.  生成された `movie/{project}/slide_*.png` ファイルを確認してください。
    2.  Markdown のスライド数と、PPTX のスライド数が一致しているか確認してください。
    3.  同期が崩れてしまった場合、最も安全な方法は `movie/{project}` フォルダを削除して、再度 `-v` を実行して再ビルドすることです。

### "build_config inconsistency detected"
*   **原因**: プロジェクトを一度実行した後に、`config.json` で `screen_size` や `video_fps` を変更しました。
*   **修正**: 一つのプロジェクト内で異なる解像度を混在させることはできません。
    1.  ソースディレクトリ内の `status.json` を削除してください。
    2.  出力ディレクトリ `movie/{project}` を削除してください。
    3.  再ビルドを実行してください。

### デバッグモード
ツールがクラッシュしたり、予期しない挙動をする場合は、`--debug` を付けて実行してください：

```bash
slidemovie myproject -v --debug
```

これにより、以下のような詳細情報が表示されます：
*   どのファイルがスキップされたか
*   FFmpeg コマンドの出力結果

### 生成したスライド画像で文字が消える場合

生成したスライド画像の一部の文字が表示されない場合、LibreOffice が使用する fontconfig の環境設定が原因になっていることがあります。

まず、`FONTCONFIG_PATH` 環境変数が設定されているか確認してください。

```sh
echo "$FONTCONFIG_PATH"
```

macOS では、たとえば XQuartz の fontconfig ディレクトリが次のように設定されている場合があります。

```text
/opt/X11/lib/X11/fontconfig
```

この設定があると、LibreOffice がスライドを書き出す際に XQuartz 側の fontconfig 設定を使用し、LibreOffice Impress 上では正しく表示されている文字が、生成された画像や PDF では消えることがあります。数字やアルファベットだけが消える場合もあります。

`FONTCONFIG_PATH` が原因かどうかを確認するには、この環境変数を一時的に削除して LibreOffice を実行します。

```sh
env -u FONTCONFIG_PATH \
  /Applications/LibreOffice.app/Contents/MacOS/soffice \
  --headless \
  --convert-to pdf \
  --outdir ~/Downloads \
  example.pptx
```

この状態で文字が正しく表示される場合は、他のアプリケーションで特に必要としていなければ、シェルの設定から `FONTCONFIG_PATH` の設定を削除または修正してください。

たとえば fish shell では、次のような設定が

```fish
set -x FONTCONFIG_PATH /opt/X11/lib/X11/fontconfig
```

`~/.config/fish/config.fish` に記載されていることがあります。

設定を削除した後、新しいシェルを起動するか、現在のシェルで次のように環境変数を削除します。

```fish
set -e FONTCONFIG_PATH
```

これは `slidemovie` 自体の問題ではなく、LibreOffice と fontconfig の実行環境に起因する問題です。

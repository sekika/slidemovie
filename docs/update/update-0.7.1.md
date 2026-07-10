# 仕様: プロンプトと原稿の区切り (`prompt_separator`)

## 1. 背景と課題

TTS へ渡すスタイルプロンプト (`prompt`) が長くなると、モデルに対して
「ここから下が読み上げ対象の原稿である」という境界を明示したくなる。
自然な方法は、プロンプトの末尾に次のような区切りを入れることである。

```
\n## 原稿\n
```

しかし現状の実装では、この方法を使うと**スライドごとの追加指示
(`additional_prompt`) が原稿側に混入する**という問題が起きる。

### 現状の実装

`slidemovie/core.py` の `_speak_to_wav()` (現状 1516-1519 行付近):

```python
if self.tts_use_prompt:
    style_prompt = f'{self.prompt}{additional_prompt}'
else:
    style_prompt = ''
```

`style_prompt` は `multiai_tts` の `save_tts(text, ..., prompt=style_prompt)`
に渡され、`multiai_tts` 側で最終的に `style_prompt` + 読み上げ本文 (`text`)
が結合されてモデルに送られる。すなわちモデルが受け取る論理的な並びは:

```
{prompt}{additional_prompt}{text}
```

ここで区切りを `prompt` の末尾に書くと (`prompt = "…指示…\n## 原稿\n"`):

```
…指示…\n## 原稿\n{additional_prompt}{text}
                 ^^^^^^^^^^^^^^^^^ 指示なのに「## 原稿」の下＝原稿側に入ってしまう
```

`additional_prompt`（例: 「この文は興奮した口調で」）は**指示**であって
原稿ではないため、これは誤りである。

### 制約

* 区切り文字を常に挿入する仕組みが必要（区切りが安定していないと、
  プロンプトと原稿の境界が曖昧になる）。
* 一方で `## 原稿` のような文字列をコードに**固定**すると、英語など
  他言語のプロジェクトで不自然になる。
* ユーザーに過度な設定負担をかけない（区切りが不要なユーザーは
  何もしなくてよい）。

## 2. 設計方針

区切り文字を **`prompt` 本体から切り離した独立の設定 `prompt_separator`**
として導入する。スタイルプロンプトの組み立て順を次のように変更し、
区切りを `additional_prompt` の**後ろ**・本文の**前**に必ず挿入する。

```
{prompt}{additional_prompt}{prompt_separator}{text}
```

これにより:

* `prompt` と `additional_prompt`（どちらも指示）は常に区切りの**上**に残る
  → `additional_prompt` の原稿側への混入が構造的に起きない。
* 区切りは設定値なので、言語ごとにユーザーが自然な文字列を指定できる
  （日本語なら `"\n\n## 原稿\n"`、英語なら `"\n\nScript:\n"` など）。
* デフォルトを空文字列 `""` とすることで、既存プロジェクトの挙動・音声を
  一切変えない（完全な後方互換・オプトイン）。`chunk_size` を `None`
  デフォルトの opt-in 機能として導入した既存の方針と一致する。

区切りは「`prompt` の末尾に自分で書く」のではなく「`prompt_separator` に
書く」という置き場所を用意するだけで課題は解決する。ユーザーは区切りを
`prompt_separator` に移すだけでよく、負担は最小限。

## 3. 仕様詳細

### 3.1 新設定 `prompt_separator`

| 項目 | 内容 |
| :--- | :--- |
| キー名 | `prompt_separator` |
| 型 | `str` |
| デフォルト | `""`（空文字列＝現状の挙動を維持） |
| 意味 | スタイルプロンプト（`prompt` + `additional_prompt`）と読み上げ本文の間に挿入する区切り文字列 |
| 適用条件 | `tts_use_prompt` が `True` のときのみ |

### 3.2 デフォルト設定への追加

`_get_default_settings()` (現状 124-163 行) の TTS settings ブロックに追加:

```python
"prompt": 'Please speak the following.',
"prompt_separator": "",          # ← 追加
"chunk_size": None,
```

docstring にも 1 行説明を追記する:

```
prompt_separator (str): Separator inserted between the style prompt
    (prompt + additional_prompt) and the spoken text. Empty disables it
    (original behavior). Default: "".
```

### 3.3 `_speak_to_wav()` の変更

区切りをスタイルプロンプト末尾に連結する。`multiai_tts` はプロンプトを
各チャンクに再適用するため、区切りも自動的に各チャンクへ付与され、
チャンク分割との整合も取れる（区切りは本文長 `chunk_size` に含まれない）。

```python
if self.tts_use_prompt:
    style_prompt = f'{self.prompt}{additional_prompt}{self.prompt_separator}'
else:
    style_prompt = ''
```

* `tts_use_prompt` が `False` のときは従来通り `style_prompt = ''`
  （区切りも付かない）。
* `prompt` / `additional_prompt` が空でも、`prompt_separator` が設定されて
  いれば区切りは付与される（設定通りの明示的な挙動とする）。

### 3.4 TTS 設定としての記録とマイグレーション

区切りを変えると生成音声が変わるため、`prompt_separator` を TTS 設定の
一部として `status.json` に記録し、変更検知の対象にする。

`_get_tts_config()` (現状 1341-1354 行) に追加:

```python
return {
    "provider": self.tts_provider,
    "model": self.tts_model,
    "voice": self.tts_voice,
    "use_prompt": self.tts_use_prompt,
    "prompt": self.prompt,
    "prompt_separator": self.prompt_separator,   # ← 追加
    "chunk_size": self.chunk_size,
    "split_chars": self.split_chars,
    "chunk_overflow": self.chunk_overflow,
}
```

既存の `status.json` には `prompt_separator` キーが無いため、そのままでは
「TTS config change detected」の誤検知（不要な再生成プロンプト）が出る。
`_load_audio_state()` 内の chunk キー backfill（現状 1248-1260 行）と同じ
方式で、旧 state ファイルへデフォルト値を補完する。

```python
chunk_defaults = {
    "chunk_size": None,
    "split_chars": "。．.!！?？\n",
    "chunk_overflow": "extend",
    "prompt_separator": "",      # ← 追加。デフォルトは空＝旧挙動と一致
}
```

デフォルトが `""` かつ旧挙動と一致するため、既存プロジェクトでは補完後も
`stored_tts == current_tts` となり、再生成は発生しない。

### 3.5 CLI オプション `--prompt-separator`

`slidemovie/cli.py` に追加する。

引数定義（`--prompt` の定義付近, 現状 90-92 行の後）:

```python
parser.add_argument(
    "--prompt-separator",
    help="Separator inserted between the style prompt and the spoken text "
         '(e.g. "\\n\\n## 原稿\\n"). Empty by default.')
```

反映（`--prompt` の処理付近, 現状 139-143 行の後）。`--chunk-size` と同様に
`is not None` で判定し、空文字列 `""` を明示指定できるようにする:

```python
if args.prompt_separator is not None:
    movie.prompt_separator = args.prompt_separator
```

## 4. 動作例

設定:

```json
{
  "prompt": "あなたはプロのナレーターです。落ち着いた声で、聞き取りやすい速度で読んでください。",
  "prompt_separator": "\n\n## 原稿\n"
}
```

スライドの `additional_prompt`: `"この文は特にゆっくり読んでください。"`

**変更前（区切りを `prompt` 末尾に書いた場合）** — `additional_prompt` が原稿側に混入:

```
あなたはプロの…読んでください。
## 原稿
この文は特にゆっくり読んでください。{本文}
```

**変更後（`prompt_separator` を使用）** — 指示は区切りの上、本文だけが下:

```
あなたはプロの…読んでください。この文は特にゆっくり読んでください。
## 原稿
{本文}
```

## 5. ドキュメント更新

以下に `prompt_separator` の説明を追記する（英日両方）。

* `docs/configuration.md`, `docs/ja/configuration.md`
  … 設定一覧に `prompt_separator` を追加。
* `docs/advanced-usage.md`, `docs/ja/advanced-usage.md`
  … 「Custom Prompt per Slide」節に、長いプロンプトでの区切り利用と
  `additional_prompt` が指示側に保たれる旨を追記。「How prompts interact
  with chunking」節に、区切りも各チャンクへ再適用される旨を追記。
* `docs/cli-reference.md`, `docs/ja/cli-reference.md`
  … `--prompt-separator` を追加。

## 6. テスト

`tests/` に追加する（`multiai_tts.Prompt` はモックする）。

* `test_core.py`
  * `prompt_separator` のデフォルトが `""` であること。
  * `tts_use_prompt=True` のとき、`save_tts` に渡る `prompt` 引数が
    `prompt + additional_prompt + prompt_separator` になること。
  * `tts_use_prompt=False` のとき `prompt` 引数が `''`（区切りも付かない）こと。
  * `_get_tts_config()` に `prompt_separator` が含まれること。
  * 旧 `status.json`（`prompt_separator` 無し）読み込み時に backfill され、
    再生成プロンプトが出ないこと（`stored_tts == current_tts`）。
* `test_cli.py`
  * `--prompt-separator "..."` が `movie.prompt_separator` に反映されること。
  * `--prompt-separator ""`（空文字）が無視されず反映されること。

## 7. 影響範囲・互換性

* デフォルト `""` のため、既存プロジェクトの生成音声・`status.json` は不変。
* `status.json` の backfill により、旧ファイルでも不要な再生成は発生しない。
* `prompt_separator` を実際に設定した場合のみ音声が変わり、その際は
  既存の TTS 設定変更検知（`_load_audio_state()` の確認プロンプト）が
  正しく働き、再生成の要否をユーザーに確認する。

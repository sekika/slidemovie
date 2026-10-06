---
layout: page
title: "0.9.0 — Google TTS の構造化スタイルメタデータ"
version: "0.9.0"
lang: ja
---

## 1. 目的

`multiai-tts` 0.5.0 は、Google TTS へ話し方の指示を渡す形式として
`speech_metadata` を提供する。これは Gemini 3.8 を含む構造化 TTS メタデータ対応モデルで、原稿を逐語的な `text`、話し方を `speech_metadata.style` として分離する形式である。

従来のインライン形式では、スタイル指示と原稿を同じ入力に連結する。構造化形式へ同じ連結を行うと、指示や区切り文字まで原稿として音声化されるおそれがある。0.9.0 は、`slidemovie` がこの形式を明示的に選択・転送できるようにし、原稿以外を読み上げないことを保証する。

モデル名の接頭辞・接尾辞による判定は行わない。将来の Gemini モデルを含め、対応可否は利用者が設定する API 契約 `tts_prompt_mode` で決める。

## 2. 設定

`config.json`、`Movie` 属性、CLI、GUI に `tts_prompt_mode` を追加する。

| 値 | 意味 | 既定値 |
| :--- | :--- | :--- |
| `legacy_inline` | 従来の Google TTS 互換形式。スタイル指示と原稿の区切りとして `prompt_separator` を使える。 | はい |
| `speech_metadata` | 原稿を本文、スタイル指示を構造化メタデータとして送る。 | いいえ |

`legacy_inline` を既定にして、既存プロジェクトの出力と設定を維持する。未知の値は `multiai-tts` の設定エラーとして API 呼び出し前に失敗する。

```json
{
  "tts_provider": "google",
  "tts_model": "gemini-3.8-flash-tts",
  "tts_prompt_mode": "speech_metadata",
  "tts_use_prompt": true,
  "prompt": "大学教員が学生に語りかけるように、落ち着いた自然な抑揚で読む。",
  "prompt_separator": ""
}
```

CLI では次のように指定できる。

```console
slidemovie my-project --video \
  --tts-provider google \
  --tts-model gemini-3.8-flash-tts \
  --tts-prompt-mode speech_metadata
```

## 3. 原稿・プロンプト・区切りの扱い

`tts_use_prompt` が真の場合、`prompt` とスライドごとの `additional_prompt` をスタイル指示として `multiai-tts.Prompt.save_tts()` の `prompt` 引数へ渡す。偽の場合は従来どおり空のプロンプトを渡す。

| モード | 原稿 | スタイル指示 | `prompt_separator` |
| :--- | :--- | :--- | :--- |
| `legacy_inline` | 従来の `multiai-tts` 形式 | `prompt + additional_prompt + prompt_separator` | 使用する |
| `speech_metadata` | `text` として変更せず渡す | `speech_metadata.style` へ渡す | 使用しない |

`speech_metadata` では、設定値に `prompt_separator` が残っていてもスタイル指示へ追加しない。移行時は空文字列へ変更することを推奨する。`prompt` には読み上げ見出し、原稿の開始記号、原稿そのものを入れず、話し方だけを書く。

局所的な間や息継ぎはスタイルプロンプトではなく、対応モデルが定める原稿中のタグ（例: `<short pause>`）として `::: notes` に記述する。`slidemovie` は原稿のタグを変更しない。

## 4. チャンク処理と状態管理

`chunk_size`、`split_chars`、`chunk_overflow` は従来どおり原稿だけを対象にする。分割された各チャンクには、同じスタイル指示が再適用される。スタイルプロンプトや `prompt_separator` の長さはチャンク境界へ影響しない。

`tts_prompt_mode` は `status.json` の `tts_config.prompt_mode` に記録する。既存の状態ファイルにこの項目がない場合は `legacy_inline` として補完し、不要な設定変更確認を出さない。モードを変更した場合は他の TTS 設定と同様に変更確認の対象となり、音声の再生成を促す。

GUI はこの設定を「Google プロンプト形式」として表示・保存し、記録済みの TTS 設定を採用した場合にも復元する。

## 5. 依存関係と互換性

`speech_metadata` を使うには `multiai-tts>=0.5.0` が必要である。`slidemovie` の依存下限もこのバージョンへ更新する。

- OpenAI、Azure、VOICEVOX の送信内容は変更しない。
- Google で `legacy_inline` を選ぶ場合も従来どおりである。
- 対応可否をモデル名から推測しないため、構造化メタデータを受け付ける将来モデルは `speech_metadata` を明示するだけで利用できる。
- 構造化メタデータを受け付けないモデルで `speech_metadata` を指定した場合は、旧形式へ黙ってフォールバックせず、`multiai-tts` が返す明確なエラーを利用者へ示す。

## 6. テストと受け入れ条件

- 任意の Google モデル ID で `speech_metadata` を指定すると、その値が `Prompt.tts_prompt_mode` へ渡る。
- `speech_metadata` では `prompt_separator` が `save_tts()` の `prompt` に混入しない。
- `legacy_inline` では従来どおり `prompt + additional_prompt + prompt_separator` を渡す。
- CLI、GUI、`config.json`、`status.json` の各経路でモードが保持される。
- 原稿の分割結果と、OpenAI・Azure・VOICEVOX の既存挙動を変更しない。

---
layout: page
title: "0.7.0 — VOICEVOX 対応"
version: "0.7.0"
lang: ja
---

## 1. 目的・背景

`slidemovie` は `multiai-tts` を通じて TTS（音声合成）を行い、ナレーション動画を生成する。
現状 `slidemovie` が対応している TTS プロバイダは以下の 3 つである。

- `google`（Google GenAI）
- `openai`（OpenAI）
- `azure`（Azure Speech）

`multiai-tts` が新たに **VOICEVOX** に対応した（`dev/multiai-tts.md` 参照）。
本仕様書は、`slidemovie` を VOICEVOX に対応させるための変更点を定義する。

## 2. VOICEVOX の特徴（multiai-tts より）

`dev/multiai-tts.md` に基づく VOICEVOX の仕様は以下のとおり。

- **ローカルエンジン**として動作する。既定の接続先は `http://127.0.0.1:50021`。
  利用時にエンジンが起動している必要がある。
- **API キー不要**。
- **モデル指定は不要**（`set_tts_provider('voicevox')` のみで選択可能）。
- 話者は **整数の style ID** で選択する（`client.tts_voice_voicevox = 3` のように指定）。
- 接続先 URL は `client.tts_voicevox_url` で上書き可能（既定 `http://127.0.0.1:50021`）。
- エンジンに到達できない場合、`client.error` にエラーメッセージ（エンジンが起動しているか確認を促す内容）が設定される。
- 日本語音声に強い。

### multiai-tts での呼び出し方（参考）

```python
client = multiai_tts.Prompt()
client.set_tts_provider('voicevox')
client.tts_voice_voicevox = 3                          # 話者 style ID（整数）
# client.tts_voicevox_url = "http://127.0.0.1:50021"   # 既定。必要なら上書き
client.save_tts("こんにちは。", "output.wav")
```

## 3. 設計方針

### 3.1 プロバイダ選択の分岐追加

`slidemovie/core.py` の `_speak_to_wav()` に `voicevox` 用の分岐を追加する。
Azure と同様、`set_tts_provider('voicevox')` を呼ぶだけでよく、モデル指定は不要。

現状の分岐（抜粋）:

```python
if self.tts_provider == 'openai':
    client.set_tts_model(self.tts_provider, self.tts_model)
    client.tts_voice_openai = self.tts_voice
if self.tts_provider == 'google':
    client.set_tts_model(self.tts_provider, self.tts_model)
    client.tts_voice_google = self.tts_voice
if self.tts_provider == 'azure':
    client.set_tts_provider(self.tts_provider)
    client.tts_voice_azure = self.tts_voice
```

追加する分岐:

```python
if self.tts_provider == 'voicevox':
    client.set_tts_provider(self.tts_provider)
    client.tts_voice_voicevox = int(self.tts_voice)   # style ID は整数
    if self.tts_voicevox_url:
        client.tts_voicevox_url = self.tts_voicevox_url
```

### 3.2 話者 ID（`tts_voice`）の型変換

- `slidemovie` の既存設定 `tts_voice` は文字列として扱われている（例: `"sadaltager"`）。
- VOICEVOX は **整数の style ID** を要求する。
- 設定ファイル・CLI からは文字列（例 `"3"`）または整数（例 `3`）のどちらでも渡されうるため、
  VOICEVOX 分岐内で `int(self.tts_voice)` により整数へ変換する。
- 変換に失敗した場合（整数に変換できない値）は、分かりやすいエラーメッセージを出して終了する。

### 3.3 新規設定キー `tts_voicevox_url`

VOICEVOX エンジンの接続先を上書きできるよう、新しい設定キーを追加する。

| キー | 型 | 既定値 | 説明 |
| :--- | :--- | :--- | :--- |
| `tts_voicevox_url` | string / null | `null` | VOICEVOX エンジンの URL。`null` の場合は multiai-tts の既定（`http://127.0.0.1:50021`）を使用する。 |

対応する変更:

- `_get_default_settings()` に `"tts_voicevox_url": None` を追加。
- `_get_tts_config()` に `tts_voicevox_url` を含め、設定変更検知（status.json）の対象とする。
- `_load_audio_state()` の後方互換バックフィル（既存 status.json に本キーが無い場合に既定を補う処理）に `tts_voicevox_url` を追加し、既存プロジェクトで不要な変更検知プロンプトが出ないようにする。

### 3.4 プロンプト（`tts_use_prompt`）の扱い

- `multiai-tts` はスタイルプロンプトを本文に前置して合成する（全プロバイダ共通）。
- VOICEVOX でスタイルプロンプト（例 `"Please speak the following."`）を有効にすると、
  そのプロンプト文字列が**読み上げられてしまう**恐れがある。
- したがって VOICEVOX 使用時は **`tts_use_prompt` を `false` にすることを推奨**する
  （Azure・OpenAI と同様の運用）。既定値そのものは変更せず、ドキュメントで推奨を明記する。
- 実装上は既存の `tts_use_prompt` 判定ロジックをそのまま利用する（VOICEVOX 固有の強制無効化は行わない）。

### 3.5 CLI

- `--tts-provider voicevox` は既存の引数でそのまま指定可能（追加変更不要）。
- `--tts-voice` で style ID（整数値の文字列）を指定可能（追加変更不要）。
- 接続先 URL を CLI から上書きできるよう、任意で `--tts-voicevox-url` オプションを追加する。
  - `slidemovie/cli.py` に `parser.add_argument("--tts-voicevox-url", ...)` を追加。
  - `args.tts_voicevox_url` が指定された場合に `movie.tts_voicevox_url` を上書き。

## 4. 変更対象ファイル一覧

| ファイル | 変更内容 |
| :--- | :--- |
| `slidemovie/core.py` | `_speak_to_wav()` に `voicevox` 分岐を追加。`_get_default_settings()` / `_get_tts_config()` / `_load_audio_state()`（バックフィル）に `tts_voicevox_url` を追加。docstring 更新。 |
| `slidemovie/cli.py` | 任意で `--tts-voicevox-url` オプションを追加し、`movie.tts_voicevox_url` へ反映。 |
| `docs/configuration.md` | TTS 設定表に `voicevox` プロバイダ、`tts_voicevox_url` キー、および前提条件（ローカルエンジン起動）を追記。設定例を追加。 |
| `docs/ja/configuration.md`（存在する場合） | 日本語版ドキュメントの同様の更新。 |
| `README.md` | 対応プロバイダに VOICEVOX を追記。 |
| `tests/test_core.py` | VOICEVOX 分岐・`tts_voicevox_url` 設定・`tts_voice` の整数変換のテストを追加。 |

## 5. 前提条件・ドキュメント記載事項

利用者向けドキュメント（`docs/configuration.md` 等）に以下を明記する。

- VOICEVOX エンジンを**事前にローカルで起動**しておく必要があること。
- API キーは不要であること。
- `tts_model` は不要（無視される）であること。
- `tts_voice` には **話者の style ID（整数）** を指定すること。
- `tts_use_prompt` は `false` を推奨すること（プロンプトが読み上げられるのを防ぐため）。
- 既定の接続先は `http://127.0.0.1:50021`。変更する場合は `tts_voicevox_url`（または `--tts-voicevox-url`）を使用すること。

### 設定例（`config.json`）

```json
{
    "tts_provider": "voicevox",
    "tts_voice": "3",
    "tts_use_prompt": false
}
```

接続先を変更する場合:

```json
{
    "tts_provider": "voicevox",
    "tts_voice": "3",
    "tts_use_prompt": false,
    "tts_voicevox_url": "http://127.0.0.1:50021"
}
```

## 6. エラーハンドリング

- VOICEVOX エンジンに到達できない場合、`multiai-tts` が `client.error` を設定する。
  既存の `_speak_to_wav()` のリトライ／エラー処理に従い、エラーメッセージをログ出力する。
- エンジン未起動は**リトライしても解消しない決定的失敗**であるため、
  3 分待って再試行するのは無駄が大きい。既存の `RESOURCE_EXHAUSTED` や分割失敗と同様に、
  エンジン到達不可を示すエラーメッセージを検知したら即座に終了することが望ましい
  （エラーメッセージ文言に応じた判定を追加検討する）。
- `tts_voice` が整数へ変換できない場合は、設定ミスとして明確なメッセージを出し終了する。

## 7. テスト方針

`tests/test_core.py`（`multiai_tts` は `MagicMock` で差し替え済み）に以下を追加する。

1. `tts_provider = 'voicevox'` のとき `_speak_to_wav()` が
   `client.set_tts_provider('voicevox')` を呼び、`client.tts_voice_voicevox` に
   **整数**が設定されることを確認する。
2. `tts_voice = "3"`（文字列）が整数 `3` に変換されることを確認する。
3. `tts_voicevox_url` が設定されている場合、`client.tts_voicevox_url` に反映されることを確認する。
4. `tts_voicevox_url` が既定値（`None`）を含め、`_get_tts_config()` の戻り値に含まれることを確認する。
5. 既存 status.json に `tts_voicevox_url` が無くても、バックフィルにより変更検知プロンプトが
   発生しないことを確認する。

## 8. 互換性・影響範囲

- 既存の `google` / `openai` / `azure` の挙動には影響を与えない。
- `tts_voicevox_url` の既定値は `None` で、既存 status.json はバックフィルにより
  無用な変更検知を起こさない。
- 新規設定キーの追加のみで、既存設定ファイルはそのまま利用可能。

## 9. 作業手順（サマリ）

1. `core.py` に VOICEVOX 分岐と `tts_voicevox_url` を実装。
2. `cli.py` に `--tts-voicevox-url` を追加。
3. テストを追加し、`pytest` が通ることを確認。
4. ドキュメント（`docs/configuration.md`、日本語版、`README.md`）を更新。

---
layout: page
title: インストール
lang: ja
nav_order: 2
parent: はじめに
---

# インストールと準備

動画を生成する前に、Python パッケージといくつかの外部依存ツールをセットアップする必要があります。

## 1. Python パッケージのインストール

最も簡単な方法は pip を使うことです。ターミナル（またはコマンドプロンプト）を開き、以下を実行してください。

```bash
pip install slidemovie
```

これにより、`multiai-tts` や `pptxtoimages` を含む必要な Python ライブラリが自動的にインストールされます。

## 2. 外部ツールのインストール

`slidemovie` は、いくつかの強力なコマンドラインツールの指揮者のような役割を果たします。プログラムを動作させるには、以下のツールをシステムにインストールする必要があります。

### 必要なツール

1.  **FFmpeg**: 音声の処理や、画像と音声を結合して動画ファイルにするために使用します。
2.  **Pandoc**: Markdown テキストファイルを PowerPoint (`.pptx`) ファイルに変換するために使用します。
3.  **LibreOffice**: PowerPoint スライドを高解像度の画像に変換するために（ヘッドレスモードで）使用します。
4.  **Poppler (pdftoppm)**: スライドから画像を抽出するために使用される PDF レンダリングライブラリです。
5.  **ImageMagick (`convert`/`magick`)**: スライド画像を `screen_size` に正規化し、アスペクト比を保ったまま均等な余白（レターボックス／ピラーボックス）を付与するために使用します。

### インストールコマンド

#### macOS の場合 (Homebrew 使用)
Homebrew がインストールされていない場合は [brew.sh](https://brew.sh/index_ja) を参照してください。

```bash
brew install ffmpeg pandoc poppler imagemagick
brew install --cask libreoffice
```

#### Ubuntu / Debian の場合
```bash
sudo apt update
sudo apt install ffmpeg pandoc libreoffice poppler-utils imagemagick
```

#### Windows の場合
1.  **FFmpeg**: [ffmpeg.org](https://ffmpeg.org/) からダウンロードして解凍し、**`bin` フォルダをシステムの環境変数 PATH に追加**してください。
2.  **Pandoc**: [pandoc.org](https://pandoc.org/) からインストーラーをダウンロードして実行してください。
3.  **LibreOffice**: 標準のデスクトップ版をインストールしてください。コマンドラインの `soffice` が PATH に通っていることを確認してください。
4.  **Poppler**: Windows 用のバイナリリリースをダウンロードし、`bin` フォルダを PATH に追加してください。
5.  **ImageMagick**: [imagemagick.org](https://imagemagick.org/) からインストーラーをダウンロードし、`magick`（または `convert`）が PATH に通っていることを確認してください。

## 3. AI APIキーの設定

`slidemovie` は `multiai-tts` ライブラリを使用してナレーション音声を生成します。モデルの選択と API キーの設定が必要です。

### 1. TTS モデルの選択

まず、引数なしで `slidemovie` コマンドを実行してください。

```bash
slidemovie
```

オプションがないためエラーが出ますが、**これは想定された動作です**。この実行により、デフォルトの設定ファイルが `~/.config/slidemovie/config.json` に自動作成されます。

## GUI を起動する

Tkinter を利用できる Python 環境では、次のコマンドで GUI を起動できます。

```bash
slidemovie -g
```

たとえば `slidemovie demo -g --video` のように、既存のオプションを併用すると対応する GUI の入力欄に反映されます。

「プロジェクトの状態」には `status.json` の要約として、PPTX・画像タスク、記録済みの TTS プロバイダー／モデル／音声、音声ファイルの生成済み・未生成・失敗件数を表示します。原稿本文、プロンプト、ハッシュ、認証情報は表示しません。

現在の TTS 設定と `status.json` に記録された設定が異なる場合、GUI では次のいずれかを選択できます。

- **status.json の設定を使う**: 記録済みの TTS 設定で続行し、TTS の入力欄も同じ値に更新します。
- **現在の設定で上書きする**: 画面の現在値で続行し、記録済み TTS 設定を更新します。
- **キャンセル**: ビルドを開始しません。

次に、**[設定ファイル](../configuration/)** のページを参考にこのファイルを編集し、`tts_provider`, `tts_model`, `tts_voice` の項目を変更して、使用する TTS モデルを設定してください。

### 2. API認証情報の設定

`slidemovie` は音声合成に `multiai-tts` を使用しています。API認証情報は [`multiai`](https://sekika.github.io/multiai/) と同じ方法で設定します。

もっとも簡単なのは、環境変数に認証情報を設定する方法です。

**Google Gemini** の場合：

```sh
export GOOGLE_API_KEY="your-api-key"
```

**OpenAI** の場合：

```sh
export OPENAI_API_KEY="your-api-key"
```

**Azure Speech** の場合：

```sh
export AZURE_TTS_API_KEY="your-api-key"
export AZURE_TTS_REGION="japaneast"
```

`japaneast` の部分は、使用している Azure Speech リソースのリージョンに置き換えてください。Azure TTS で使用するのは **Azure Speech の API キー**であり、Azure OpenAI の API キーではありません。

環境変数の代わりに、`multiai` の設定ファイルに認証情報を保存することもできます。`multiai` は `~/.multiai`、続いて `./.multiai` の設定を読み込み、プロジェクト側の設定が優先されます。

例えば、次のように設定します。

```ini
[api_key]
openai = (OpenAI の API キー)
google = (Gemini の API キー)
azure_tts = (Azure Speech の API キー)

[azure_tts]
region = japaneast
```

`slidemovie` の設定ファイルで `tts_provider` に指定した TTS プロバイダについてのみ、認証情報を設定すれば利用できます。

設定方法や `multiai` の設定ファイル全体の形式については、公式の [`multiai` ドキュメント](https://sekika.github.io/multiai/) を参照してください。

> **注意:** 選択したプロバイダ（`google`、`openai`、`azure`）に対応する有効な認証情報が設定されていない場合、音声生成は失敗します。

> **VOICEVOX:** `voicevox` プロバイダを選択した場合、APIキーは不要です。代わりに、ビルド前に [VOICEVOX エンジン](https://voicevox.hiroshiba.jp/) をローカルで起動しておく必要があります（デフォルトは `http://127.0.0.1:50021`）。`tts_voice`（話者・スタイルID）と `tts_voicevox_url` については [設定](../configuration/) を参照してください。

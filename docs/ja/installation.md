---
layout: page
title: インストール
lang: ja
nav_order: 2
parent: はじめに
---

# インストールと準備

動画を生成する前に、Python パッケージといくつかの外部依存ツールをセットアップする必要があります。

## 前提条件: Python 3

`slidemovie` には Python 3.8 以降が必要です。先に使用している OS 向けの [Python 3](https://www.python.org/) をインストールし、次のコマンドで利用できることを確認してください。

```bash
python3 --version
```

Python 2 と Python 3 が区別される環境では、以降のコマンドも `python3 -m pip` を使用してください。

`pip` がまだ利用できない場合は、パッケージをインストールする前に次を実行してください。

```bash
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip
```

## 1. Python パッケージのインストール

最も簡単な方法は pip を使うことです。Windows では [PowerShell](https://learn.microsoft.com/powershell/scripting/windows-powershell/starting-windows-powershell) を、macOS / Linux ではターミナルを開き、以下を実行してください。

```bash
python3 -m pip install slidemovie
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
Homebrew がインストールされていない場合は [brew.sh](https://brew.sh/ja/) を参照してください。

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
Windows では、Windows Package Manager（`winget`）を使うと、各ツールを個別にダウンロードしたり PATH を手動で設定したりせずに導入できます。[PowerShell](https://learn.microsoft.com/powershell/scripting/windows-powershell/starting-windows-powershell) を開き、次を実行してください。

```powershell
winget install --id Gyan.FFmpeg --exact
winget install --id JohnMacFarlane.Pandoc --exact
winget install --id TheDocumentFoundation.LibreOffice --exact
winget install --id oschwartz10612.Poppler --exact
winget install --id ImageMagick.ImageMagick --exact
```

`winget` が見つからない場合は、Microsoft Store から「アプリ インストーラー」を更新またはインストールしてください。インストール後は PowerShell をいったん閉じて新しく開き、次のコマンドで確認します。

```powershell
ffmpeg -version
ffprobe -version
pandoc --version
pdftoppm -v
magick -version
```

`winget` による導入後もコマンドが見つからない場合は、Windows にサインインし直してからもう一度確認してください。

## 3. AI APIキーの設定

`slidemovie` は `multiai-tts` ライブラリを使用してナレーション音声を生成します。モデルの選択と API キーの設定が必要です。

### 1. TTS モデルの選択

まず、引数なしで `slidemovie` コマンドを実行してください。

```bash
slidemovie
```

オプションがないためエラーが出ますが、**これは想定された動作です**。この実行により、デフォルトの設定ファイルが `~/.config/slidemovie/config.json` に自動作成されます。

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

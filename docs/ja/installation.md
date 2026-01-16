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

### インストールコマンド

#### macOS の場合 (Homebrew 使用)
Homebrew がインストールされていない場合は [brew.sh](https://brew.sh/index_ja) を参照してください。

```bash
brew install ffmpeg pandoc poppler
brew install --cask libreoffice
```

#### Ubuntu / Debian の場合
```bash
sudo apt update
sudo apt install ffmpeg pandoc libreoffice poppler-utils
```

#### Windows の場合
1.  **FFmpeg**: [ffmpeg.org](https://ffmpeg.org/) からダウンロードして解凍し、**`bin` フォルダをシステムの環境変数 PATH に追加**してください。
2.  **Pandoc**: [pandoc.org](https://pandoc.org/) からインストーラーをダウンロードして実行してください。
3.  **LibreOffice**: 標準のデスクトップ版をインストールしてください。コマンドラインの `soffice` が PATH に通っていることを確認してください。
4.  **Poppler**: Windows 用のバイナリリリースをダウンロードし、`bin` フォルダを PATH に追加してください。

## 3. AI APIキーの設定

`slidemovie` は `multiai-tts` ライブラリを使用してナレーション音声を生成します。使用したい AI プロバイダー（Google Gemini または OpenAI）の API キーを用意する必要があります。

設定方法の詳細については、**[multiai の公式ドキュメント](https://sekika.github.io/multiai/)** を参照してください。

> **注意:** 正しい API キーが設定されていない場合、音声生成のステップでエラーとなります。

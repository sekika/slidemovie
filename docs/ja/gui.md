---
layout: page
title: GUI ガイド
lang: ja
nav_order: 4
parent: はじめに
---

# GUI ガイド

Tkinter GUI では、多数のオプションを毎回コマンドへ入力せずに、CLI と同じビルド手順を実行できます。

## GUI を起動する

slidemovie のインストール後、次を実行します。

```bash
slidemovie -g
```

コマンドラインの指定値を GUI の初期値にできます。たとえば `slidemovie demo -g --video` は、プロジェクト名に `demo` を入れ、動画生成を選択した状態で GUI を開きます。

## プロジェクトをビルドする

1. **ソースフォルダー** と **プロジェクト名** を指定します。
2. **実行内容** で **PPTX を生成**、**動画を生成**、または両方を選びます。
3. PDF から動画を作る場合は、**動画ソース** で **PDF** を選びます。
4. **実行** を押します。

**フォルダーを開く** の **入力ファイル**／**出力ファイル** を使うと、ファイルマネージャーでプロジェクトの実際のソース／出力ディレクトリーを開けます。

**出力ファイル名** は、出力される動画のファイル名（拡張子なし）です。未設定の場合はプロジェクトIDが使用されます。CLI の `-f` オプションで初期値の指定や上書きができます。

## 設定

**設定** タブには、最初に [`config.json`]({{ '/ja/configuration/' | relative_url }}) の有効値が表示されます。

- **TTS 設定**: プロバイダー、モデル、声、プロンプト、プロンプト使用有無、プロンプト区切り、原稿分割設定
- **動画フォーマット**: `screen_size`、`image_pad_color`、`video_fps`
- **一般**: `silence_sec`

プロンプト区切りと分割候補文字では、改行を入力欄で `\n` として表示し、ビルド時に実際の改行へ変換します。**設定から戻す** を押すと、設定ファイルから読み込んだ値へ戻ります。

**ローカル設定に保存** を押すと、設定の入力欄の値と出力ファイル名を、入力Markdownファイルと同じディレクトリの `config.json` へ保存し、次回の GUI 起動時にも読み込みます。出力先ルートは保存しません。通常のプロジェクトでは `ソースフォルダー/config.json`、サブプロジェクトでは `ソースフォルダー/サブプロジェクト/config.json` を使用します。既存の設定にある GUI で編集しない項目は保持されます。

## プロジェクトの状態と記録済み設定

**プロジェクトの状態** には、[`status.json`]({{ '/ja/advanced-usage/' | relative_url }}) の PPTX／画像タスク、スライド数、音声ファイルの生成状況、記録済み TTS のプロバイダー／モデル／音声を要約表示します。原稿本文、プロンプト、ハッシュ、認証情報は表示しません。

現在の TTS 設定と `status.json` の設定が異なるときは、次のいずれかを選びます。

- **status.json の設定を使う**: 記録済みの設定を使い、保存されている TTS／ビルド設定をすべて設定タブへ反映します。
- **現在の設定で上書きする**: GUI の現在値で続行し、記録済みの TTS 設定を更新します。
- **キャンセル**: ビルドを開始しません。

画面表示は日本語と英語を切り替えられます。

## About

**About** タブには、アイコン、実行中の `slidemovie` バージョン、選択中の言語に対応する **公式サイト** ボタン、GitHub Issues を開く **フィードバック** ボタンを表示します。また、OS、Python、Tk、ロケール、作業ディレクトリ、設定ファイルの場所、関連 Python パッケージ、FFmpeg・Pandoc・LibreOffice・Poppler・ImageMagick の検出パスとバージョンを確認できます。

**情報をクリップボードにコピー** を押すと、トラブルシューティングに必要な情報をまとめてコピーできます。API キー、プロンプト、`status.json` の内容、PATH は含めません。

## GUI のショートカットを作る

よく使う場合は、デスクトップやアプリケーションフォルダーから GUI を開けるショートカットを作成できます。以下から、お使いの OS 用のスクリプトとアイコンをダウンロードしてください。

スクリプトと対応するアイコンは、同じフォルダーへダウンロードしてください。

- Windows: [ショートカット作成スクリプト]({{ '/downloads/create-slidemovie-shortcut.ps1' | relative_url }}) と [アイコン（`.ico`）]({{ '/downloads/slidemovie.ico' | relative_url }})
- macOS: [アプリ作成スクリプト]({{ '/downloads/create-slidemovie-app.command' | relative_url }}) と [アイコン（`.icns`）]({{ '/downloads/slidemovie.icns' | relative_url }})

### Windows

ダウンロードしたフォルダーで PowerShell を開き、次を実行します。

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\create-slidemovie-shortcut.ps1
```

デスクトップに `SlideMovie.lnk` が作成されます。スクリプトは自動的に `pythonw.exe` を探し、コンソールを表示せずに GUI を起動します。また、作成時の `PATH` を専用ランチャーへ記録するため、Explorer から起動しても FFmpeg などの外部ツールを見つけられます。通常は上記のコマンドだけで完了し、スクリプトを書き換える必要はありません。

同じ Python 環境で `slidemovie` をアップグレードした場合は、ショートカットを作り直す必要はありません。ショートカットは同じ `pythonw.exe` から、アップグレード後のパッケージを起動します。別の Python 環境へ入れ直した場合だけ、ショートカットを作り直してください。

最初の実行で Python を見つけられないというエラーが出た場合は、次の **2 行を続けて** PowerShell へ貼り付けて実行してください。1 行目で Python Launcher から `pythonw.exe` の場所を取得し、2 行目でその場所を指定してショートカットを作成します。ショートカットやスクリプトのファイルを手で書き換える必要はありません。

```powershell
$pythonw = & py -3 -c "import sys; print(sys.executable.replace('python.exe', 'pythonw.exe'))"
.\create-slidemovie-shortcut.ps1 -PythonPath $pythonw
```

このコマンドでは、取得した `pythonw.exe` のパスが、作成される `SlideMovie.lnk` の起動先に設定されます。

### macOS

ダウンロードしたフォルダーでターミナルを開き、次を実行します。

```bash
chmod +x create-slidemovie-app.command
./create-slidemovie-app.command
```

`~/Applications/SlideMovie.app` が作成され、開かれます。アプリは、この作成スクリプトを実行したフォルダーを `--source-dir` で明示指定し、ソースフォルダーの初期値として開きます。使用したいフォルダーでスクリプトを実行してください。Finder から直接開く場合にも Homebrew などの外部ツールを見つけられるよう、作成時の `PATH` をアプリへ記録します。Mac のすべての利用者から開けるようにするには `/Applications` へ移動します。起動に失敗した場合は `~/Library/Logs/SlideMovie.log` を確認してください。スクリプトは実行時の `slidemovie` コマンドのパスを記録するため、使用する Python 環境を確認したい場合は事前に `which slidemovie` を実行してください。

同じ Python 環境で `slidemovie` をアップグレードした場合は、アプリを作り直す必要はありません。記録済みの `slidemovie` コマンドが同じ場所にあり、アップグレード後のパッケージを起動します。別の Python 環境へ入れ直した場合だけ、この作成スクリプトを再実行してください。

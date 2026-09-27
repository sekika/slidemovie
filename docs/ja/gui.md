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

## 設定

**設定** タブには、最初に [`config.json`]({{ '/ja/configuration/' | relative_url }}) の有効値が表示されます。

- **TTS 設定**: プロバイダー、モデル、声、プロンプト、プロンプト使用有無、プロンプト区切り、原稿分割設定
- **動画フォーマット**: `screen_size`、`image_pad_color`、`video_fps`
- **一般**: `silence_sec`

プロンプト区切りと分割候補文字では、改行を入力欄で `\n` として表示し、ビルド時に実際の改行へ変換します。**設定から戻す** を押すと、設定ファイルから読み込んだ値へ戻ります。

## プロジェクトの状態と記録済み設定

**プロジェクトの状態** には、[`status.json`]({{ '/ja/advanced-usage/' | relative_url }}) の PPTX／画像タスク、スライド数、音声ファイルの生成状況、記録済み TTS のプロバイダー／モデル／音声を要約表示します。原稿本文、プロンプト、ハッシュ、認証情報は表示しません。

現在の TTS 設定と `status.json` の設定が異なるときは、次のいずれかを選びます。

- **status.json の設定を使う**: 記録済みの設定を使い、保存されている TTS／ビルド設定をすべて設定タブへ反映します。
- **現在の設定で上書きする**: GUI の現在値で続行し、記録済みの TTS 設定を更新します。
- **キャンセル**: ビルドを開始しません。

画面表示は日本語と英語を切り替えられます。**公式サイト** は選択中の言語に対応する公式サイトを開きます。

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

デスクトップに `SlideMovie.lnk` が作成されます。スクリプトは自動的に `pythonw.exe` を探し、コンソールを表示せずに GUI を起動します。通常は上記のコマンドだけで完了し、スクリプトを書き換える必要はありません。

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

`~/Applications/SlideMovie.app` が作成され、開かれます。アプリは、この作成スクリプトを実行したフォルダーを `--source-dir` で明示指定し、ソースフォルダーの初期値として開きます。使用したいフォルダーでスクリプトを実行してください。Mac のすべての利用者から開けるようにするには `/Applications` へ移動します。スクリプトは実行時の `slidemovie` コマンドのパスを記録するため、使用する Python 環境を確認したい場合は事前に `which slidemovie` を実行してください。

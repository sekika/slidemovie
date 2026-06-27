# 仕様書: PDF からの画像生成と解像度・アスペクト比の統一

本仕様書は `dev/update.md` の修正方針に基づき、画像（PNG）生成処理を拡張するための設計をまとめたものである。

## 1. 目的

1. スライド画像（PNG）の作成手段として、PowerPoint（`.pptx`）に加えて **PDF ファイル（`.pdf`）からの変換** を提供する。
2. 生成する画像の解像度を、設定 `screen_size` と **常に一致** させる。
3. ソース（PDF / PPTX）のアスペクト比が `screen_size` と一致しない場合は、アスペクト比を保ったまま、左右または上下に **均等な余白** を付与して `screen_size` と同じ解像度の画像にする。
4. 上記 3 の余白付与処理は、PDF 由来・PPTX 由来のどちらの画像生成でも **同一に** 適用する。

## 2. 背景（現状の挙動）

- `Movie.build_slide_images()`（`slidemovie/core.py`）は `pptxtoimages.PPTXToImageConverter` を用いて、`{project}.pptx` を `slide_1.png, slide_2.png, ...` に変換し、Markdown の `slide-id` 順にリネームする。
  - `pptxtoimages` は内部で「PPTX → PDF（LibreOffice `soffice`）→ PNG（Poppler / `pdf2image`, `dpi=200`）」と変換する。生成される PNG の解像度はソースのページサイズと `dpi` に依存し、`screen_size` とは一致しない。
- 解像度の調整は後段の `Movie.build_slide_videos()` の静止画ブランチで `-vf scale={width}:{height}` により行われている。
  - この `scale` はアスペクト比を無視して `screen_size` に **引き伸ばす** ため、ソースのアスペクト比が `screen_size` と異なると画像が歪む。
- 動画ファイルを差し込むブランチ（`video_file` 指定時）は、`scale=...:force_original_aspect_ratio=decrease,pad=...` によりアスペクト比を保った余白付与（レターボックス）を行っており、静止画との挙動が一致していない。

本改修により、画像生成段階で `screen_size` への正規化（アスペクト比保持 + 均等余白）を行い、静止画と動画で挙動を統一する。

## 3. 用語

- **画面サイズ（`screen_size`）**: 設定値 `[width, height]`（デフォルト `[1280, 720]`）。出力動画の解像度。
- **レターボックス / ピラーボックス**: アスペクト比を保って縮小したうえで、不足分を上下（レターボックス）または左右（ピラーボックス）に均等な余白として付与すること。

## 4. 機能仕様

### 4.1 CLI オプションの追加

`slidemovie/cli.py` に `--pdf` オプションを追加する。

- 名称: `--pdf`
- 型: フラグ（`action="store_true"`）
- 説明: 画像生成のソースとして `.pptx` の代わりに `.pdf` を使用する。
- 利用条件: `-v` / `--video`（ビルドモード）と併用する。`--pdf` 単体や `-p` / `--pptx` との併用については 4.2 を参照。

CLI では、`args.pdf` を `Movie` インスタンスの属性 `movie.use_pdf` に反映する。

```
parser.add_argument(
    "--pdf",
    action="store_true",
    help="Use a PDF file ({project}.pdf) as the image source instead of PPTX."
)
...
movie.use_pdf = args.pdf
```

### 4.2 オプションの組み合わせと検証

- `-v --pdf`: PDF をソースとして動画をビルドする（本改修の主目的）。
- `-p`（PPTX 生成）は Markdown → PPTX の変換であり、PDF とは無関係。`-p --pdf` が指定された場合は、`--pdf` は PPTX 生成には影響しない（無視する）。警告ログを出してもよい。
- `--pdf` を付けず `-v` のみの場合は、従来どおり PPTX をソースとする。

`use_pdf` のデフォルトは `False`（PPTX モード）。設定ファイル（`config.json`）からの指定は必須としないが、`_get_default_settings()` に `"use_pdf": False` を追加して属性の初期化を保証する（CLI 指定があれば上書き）。

### 4.3 ソースファイルパス

`configure_project_paths()` および `configure_subproject_paths()` に PDF ファイルパスを追加する。ファイル名は `.pptx` を `.pdf` に置き換えたものとする。

- 標準モード: `self.pdf_file = f'{self.source_dir}/{project_name}.pdf'`
- サブプロジェクトモード: `self.pdf_file = f'{self.source_dir}/{subproject_name}.pdf'`

画像生成のソースは `use_pdf` に応じて決定する。

| `use_pdf` | 画像ソース | 変換経路 |
| --- | --- | --- |
| `False`（既定） | `self.slide_file`（`.pptx`） | PPTX → PDF → PNG（`pptxtoimages`） |
| `True` | `self.pdf_file`（`.pdf`） | PDF → PNG（直接） |

### 4.4 画像生成処理（`build_slide_images` の改修）

`build_slide_images()` を以下のように変更する。

1. **ソース選択と存在チェック**
   - `use_pdf` が `True` の場合はソースを `self.pdf_file`、`False` の場合は `self.slide_file` とする。
   - ソースが存在しなければエラーログを出して return（従来踏襲）。

2. **変更検知（ハッシュ）**
   - `images_task.source_hash` を、選択したソースファイルのハッシュ（`_hash_file`）で比較する。
   - `images_task.source_file` には選択したソースの basename を記録する。
   - スキップ条件は従来どおり `status == "generated"` かつ `source_hash` 一致かつ出力 PNG が存在すること。
     - 注: 余白付与は `screen_size` に依存する。`screen_size` は `build_config` に含まれ、`_load_audio_state()` で不一致時は中断（再生成ではなく abort）されるため、解像度変更時の整合は既存の仕組みで担保される。さらに余白色を変更可能にする場合（4.5 参照）は `build_config` に含め、変更時に整合チェックされるようにする。

3. **既存 PNG の削除**: `slide_*.png` を削除（従来踏襲）。

4. **ソース → PNG の生成（中間画像）**
   - **PPTX モード**: 従来どおり `PPTXToImageConverter(self.slide_file, self.movie_dir).convert()` を使用し、`slide_*.png` を得る。
   - **PDF モード**: `self.pdf_file` の各ページを直接 PNG 化し、`slide_1.png, slide_2.png, ...` を `self.movie_dir` に生成する。
     - 実装方式は `pptxtoimages` が依存する `pdf2image.convert_from_path(pdf_path, dpi=...)`（Poppler 利用）に揃える。これにより新規依存を増やさない。
     - もしくは Poppler の `pdftoppm` を直接呼び出す。いずれの場合も、後段の正規化で `screen_size` に合わせるため、中間画像の `dpi` はアスペクト比が保たれていれば厳密な指定は不要（既定 `dpi=200` を踏襲してよい）。

5. **解像度・アスペクト比の正規化（新規・PDF/PPTX 共通）**
   - 生成された各中間 PNG（`slide_*.png`）に対し、`screen_size`（`width` × `height`）への正規化を行う。
   - 処理内容（レターボックス / ピラーボックス）:
     1. アスペクト比を保ったまま `width` × `height` に収まるよう縮小（拡大は任意。基本は縮小で十分な解像度が得られる `dpi` を用いる）。
     2. 中央寄せで `width` × `height` の領域に配置し、不足分を均等な余白で埋める。
   - 余白はソースと `screen_size` のアスペクト比の関係により上下または左右のどちらか一方に均等に入る（両者一致時は余白なし）。
   - 実装は ImageMagick の `convert`（`-extent`）を用いる。標準的なコマンド例:

     ```
     convert <input.png> \
       -resize {width}x{height} \
       -background {pad_color} -gravity center \
       -extent {width}x{height} \
       <output.png>
     ```

     - `-resize {width}x{height}`: アスペクト比を保持して内接縮小。
     - `-gravity center` + `-extent {width}x{height}`: 中央配置で目標解像度のキャンバスに展開し、余白を均等付与。
     - `-background {pad_color}`: 余白の色（4.5 参照）。
   - Windows 等で `convert` が使用できない環境では `magick convert ...` を用いる。実装では `shutil.which("convert")` → なければ `magick` を試す、の順でコマンドを解決する。
   - 正規化後の PNG が `screen_size` と完全一致する解像度であることを保証する。

6. **slide-id によるリネーム**: 従来どおり、Markdown から得た `slide_id` の順序で `slide_*.png` を `{slide_id}.png` にリネームする。生成枚数と `slide_id` 数の不一致時はエラー終了（従来踏襲）。

7. **状態保存**: `images_task` を更新（`source_file` は選択ソースの basename、`source_hash` は選択ソースのハッシュ）。

#### 正規化のタイミングについて

正規化（リサイズ + 余白付与）は、リネーム前の `slide_*.png` 段階で各ファイルをインプレースに上書きする方式を基本とする。リネーム後に行ってもよいが、コードの差分を最小化するため、変換 → 正規化 → リネームの順とする。

### 4.5 余白色の設定

余白色は設定値で制御可能とする。

- 設定キー: `image_pad_color`
- デフォルト: `"white"`
  - スライドは白背景が一般的であり、白で揃えると余白が目立ちにくい。
  - レターボックス（黒）を望む利用者は `config.json` で `"black"` 等に変更できる。
- `_get_default_settings()` に追加し、`build_config`（`_get_build_config()`）にも含める。
  - `build_config` に含めることで、余白色を変更したまま既存プロジェクトを再ビルドしようとした際に不整合として検出される。

> 既存の動画差し込みブランチ（`build_slide_videos` の `video_file` 経路）は ffmpeg `pad` により黒余白を付与している。挙動を完全に統一したい場合は、当該ブランチの `pad` 色も `image_pad_color` に合わせる拡張を将来的に検討する（本改修の必須範囲外）。

### 4.6 `build_slide_videos` への影響

- 静止画ブランチの `-vf scale={width}:{height}` は、入力 PNG が既に `screen_size` と一致するため実質的に無変換（ノーオペ）となり、アスペクト比の歪みは発生しなくなる。
- 後方互換のため当該 `scale` はそのまま残してよい（既存 PNG が `screen_size` 一致を保証するための安全策）。
- PNG のハッシュ（`png_hash`）による再生成判定はそのまま機能する。正規化により PNG 内容が変わるため、本改修適用後の初回ビルドではスライド動画が再生成される。

## 5. 外部ツール依存

- 本改修で **ImageMagick（`convert` / `magick`）** が必須となる（PDF / PPTX いずれのモードでも正規化に使用するため）。
- `Movie._check_external_tools()` の必須ツール一覧に `convert`（または `magick`）の存在チェックを追加する。
  - `convert` と `magick` のいずれかが存在すれば可とする。
- PDF モードでは PPTX → PDF 変換（LibreOffice `soffice`）は不要だが、PNG 化のため Poppler（`pdftoppm`）は引き続き必要。PPTX モードでは従来どおり LibreOffice + Poppler が必要。
- ドキュメント（`docs/installation.md` 等）の依存関係に ImageMagick を追記する。

## 6. 設定（config.json）の追加・変更まとめ

| キー | 型 | デフォルト | 説明 |
| --- | --- | --- | --- |
| `use_pdf` | bool | `false` | 画像ソースに PDF を用いるか（通常は CLI `--pdf` で指定） |
| `image_pad_color` | str | `"white"` | 余白色（ImageMagick が解釈する色名 / 値） |

- `screen_size` は既存設定。正規化の目標解像度として使用する。
- `_get_build_config()` に `image_pad_color`（および既存の `screen.width/height`）を含め、整合チェックの対象とする。

## 7. CLI / ドキュメント更新

- `docs/cli-reference.md`: `--pdf` オプションの説明を追加。`-v` の Steps の「Exports Images from the PPTX file」を、`--pdf` 指定時は PDF からエクスポートする旨に補足。
- `docs/configuration.md`: `image_pad_color` を追記。
- `docs/installation.md`: ImageMagick を依存に追記。
- 日本語ドキュメント（`docs/ja/`）も同様に更新。

## 8. 受け入れ条件（テスト観点）

1. `slidemovie demo -v --pdf` で `demo.pdf` から各ページの PNG が生成され、`{slide_id}.png` にリネームされる。
2. 生成された全 PNG の解像度が `screen_size`（既定 `1280x720`）と完全一致する。
3. ソースのアスペクト比が `screen_size` と異なる場合（例: 4:3 PDF → 16:9）、画像が歪まず、上下または左右に均等な余白（`image_pad_color`）が付与される。
4. PPTX モード（`--pdf` なし）でも、同様に `screen_size` 一致・均等余白の PNG が生成される（歪みが解消される）。
5. PDF / PPTX のページ数（生成 PNG 数）と Markdown の `slide_id` 数が不一致の場合はエラー終了する（既存挙動を踏襲）。
6. ソースファイル未変更時は再生成がスキップされる。ソース変更時のみ再生成される。
7. `convert` / `magick` が見つからない場合は、起動時の外部ツールチェックでエラー終了する。

## 9. 実装上の注意

- 中間 PNG の生成枚数チェック（`len(slide_ids) != len(generated_files)`）は正規化の前後どちらでも成立するが、正規化前のファイル列挙（`slide_*.png`）を基準とする現行ロジックを維持する。
- `convert` コマンドはファイルごとに呼ぶ（ページ数ぶん）。失敗時は `subprocess` の戻り値を確認し、エラーログ（コマンド・stdout・stderr）を出して中断する（`build_slide_videos` 等の既存エラーハンドリング方針に倣う）。
- Windows パス対応として、`convert`/`magick` 呼び出しの入出力パスは絶対パスを用いる。
- `pptxtoimages` のバージョン依存を避けるため、PDF → PNG 直接変換は `pdf2image`（Poppler）か `pdftoppm` の直接呼び出しのいずれかで実装し、`PPTXToImageConverter` の内部実装には依存しない。

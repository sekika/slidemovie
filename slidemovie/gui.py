"""Tkinter frontend for slidemovie.

Tkinter is imported only when the GUI is started, so importing slidemovie
continues to work on servers and minimal Python installations.
"""

import json
import locale
import logging
import os
import queue
import sys
import threading
import traceback


SETTING_NAMES = (
    "tts_provider", "tts_model", "tts_voice", "tts_voicevox_url", "prompt",
    "prompt_separator", "chunk_size", "split_chars", "chunk_overflow",
)

TTS_STATUS_FIELDS = {
    "provider": "tts_provider",
    "model": "tts_model",
    "voice": "tts_voice",
    "use_prompt": "tts_use_prompt",
    "prompt": "prompt",
    "prompt_separator": "prompt_separator",
    "chunk_size": "chunk_size",
    "split_chars": "split_chars",
    "chunk_overflow": "chunk_overflow",
    "tts_voicevox_url": "tts_voicevox_url",
}


TEXT = {
    "en": {
        "title": "slidemovie 0.8.0", "project": "Project", "tts_tab": "TTS settings", "log_tab": "Log", "source": "Source folder",
        "name": "Project name", "sub_mode": "Use subproject", "sub": "Subproject name",
        "output": "Output root", "filename": "Output filename", "browse": "Browse",
        "actions": "Actions", "pptx": "Build PPTX", "video": "Build video",
        "debug": "Debug logging",
        "source_type": "Video image source", "settings": "TTS settings",
        "provider": "Provider", "model": "Model", "voice": "Voice / style ID",
        "voicevox": "VOICEVOX URL", "prompt": "Style prompt", "use_prompt": "Use prompt",
        "separator": "Prompt separator", "chunk": "Chunk size", "split": "Split characters",
        "overflow": "On no split", "restore": "Restore settings", "status": "Project status",
        "refresh": "Refresh status", "run": "Run", "clear": "Clear log", "exit": "Exit",
        "idle": "Idle", "running": "Running", "success": "Succeeded", "failed": "Failed",
        "config": "From configuration", "yes": "Use", "no": "Do not use",
        "missing": "status.json has not been created.", "no_project": "Enter a project name to view status.",
        "invalid": "Please correct the input.", "done": "Build completed.",
        "failed_message": "Build failed. See the log for details.",
        "confirm": "TTS settings differ from status.json. Choose which settings to use.",
        "use_status": "Use status.json settings", "overwrite": "Overwrite with current settings",
        "cancel": "Cancel",
        "close_running": "Wait for the current build to finish before closing.",
        "status_file": "State file", "project_id": "Project ID", "checked": "Last checked",
        "pptx_status": "PPTX", "images_status": "Images", "slides": "Slides",
        "tts": "Recorded TTS", "audio": "Audio files", "generated": "generated",
        "not_generated": "not generated", "unreadable": "Could not read status.json: ",
    },
    "ja": {
        "title": "slidemovie 0.8.0", "project": "プロジェクト", "tts_tab": "TTS 設定", "log_tab": "ログ", "source": "ソースフォルダー",
        "name": "プロジェクト名", "sub_mode": "サブプロジェクトを使用", "sub": "サブプロジェクト名",
        "output": "出力先ルート", "filename": "出力ファイル名", "browse": "参照",
        "actions": "実行内容", "pptx": "PPTX を生成", "video": "動画を生成",
        "debug": "デバッグログ",
        "source_type": "動画の画像ソース", "settings": "TTS 設定",
        "provider": "プロバイダー", "model": "モデル", "voice": "声 / style ID",
        "voicevox": "VOICEVOX URL", "prompt": "スタイルプロンプト", "use_prompt": "プロンプトを使用",
        "separator": "プロンプト区切り", "chunk": "チャンクサイズ", "split": "分割候補文字",
        "overflow": "分割不可時", "restore": "設定から戻す", "status": "プロジェクトの状態",
        "refresh": "状態を更新", "run": "実行", "clear": "ログを消去", "exit": "終了",
        "idle": "待機中", "running": "実行中", "success": "成功", "failed": "失敗",
        "config": "設定ファイルに従う", "yes": "使用する", "no": "使用しない",
        "missing": "status.json はまだ作成されていません。", "no_project": "状態を表示するにはプロジェクト名を入力してください。",
        "invalid": "入力内容を確認してください。", "done": "ビルドが完了しました。",
        "failed_message": "ビルドに失敗しました。詳細はログを確認してください。",
        "confirm": "TTS 設定が status.json と異なります。使用する設定を選択してください。",
        "use_status": "status.json の設定を使う", "overwrite": "現在の設定で上書きする",
        "cancel": "キャンセル",
        "close_running": "実行中の処理が完了してから終了してください。",
        "status_file": "状態ファイル", "project_id": "プロジェクト ID", "checked": "最終確認日時",
        "pptx_status": "PPTX", "images_status": "画像", "slides": "スライド",
        "tts": "記録済み TTS", "audio": "音声ファイル", "generated": "生成済み",
        "not_generated": "未生成", "unreadable": "status.json を読めません: ",
    },
}


def detect_language():
    """Return the UI language inferred from the system locale."""
    try:
        language = locale.getlocale()[0] or locale.getdefaultlocale()[0]
    except (ValueError, AttributeError):
        language = None
    return "ja" if language and language.lower().startswith("ja") else "en"


def options_from_args(args):
    """Translate argparse values into GUI initial values and explicit overrides."""
    values = {
        "project_name": args.project_name or "", "source_dir": args.source_dir,
        "subproject_name": args.sub or "", "output_root": args.output_root or "",
        "output_filename": args.filename or "", "build_pptx": bool(args.pptx),
        "build_video": bool(args.video), "use_pdf": bool(args.pdf),
        "debug": bool(args.debug), "overrides": set(),
    }
    mapping = {
        "tts_provider": args.tts_provider, "tts_model": args.tts_model,
        "tts_voice": args.tts_voice, "tts_voicevox_url": args.tts_voicevox_url,
        "prompt": args.prompt, "prompt_separator": args.prompt_separator,
        "chunk_size": args.chunk_size, "split_chars": args.split_chars,
        "chunk_overflow": args.chunk_overflow,
    }
    for name, value in mapping.items():
        if value is not None:
            values[name] = value
            values["overrides"].add(name)
    if args.prompt is not None:
        values["use_prompt"] = True
        values["overrides"].add("tts_use_prompt")
    if args.no_prompt:
        values["use_prompt"] = False
        values["overrides"].add("tts_use_prompt")
    for name, value in (("output_root", args.output_root), ("output_filename", args.filename)):
        if value is not None:
            values["overrides"].add(name)
    return values


def display_path_value(initial_options, settings, path_overrides, name):
    """Choose a displayed path, preferring CLI input only when it was explicit."""
    if name in path_overrides:
        return initial_options.get(name, "")
    return settings.get(name) or ""


def summarize_status(path):
    """Return a privacy-conscious, tolerant status.json summary."""
    if not os.path.isfile(path):
        return {"exists": False}
    try:
        with open(path, encoding="utf-8") as status_file:
            state = json.load(status_file)
    except (OSError, json.JSONDecodeError) as exc:
        return {"exists": True, "error": str(exc)}
    if not isinstance(state, dict):
        return {"exists": True, "error": "root value is not an object"}
    slides = state.get("slides") if isinstance(state.get("slides"), dict) else {}
    statuses = [item.get("status") for item in slides.values() if isinstance(item, dict)]
    done = sum(status in ("done", "completed", "success") for status in statuses)
    failed = sum(status in ("failed", "error") for status in statuses)
    audio_statuses = [
        item["audio"].get("status") for item in slides.values()
        if isinstance(item, dict) and isinstance(item.get("audio"), dict)
    ]
    audio_generated = sum(status == "generated" for status in audio_statuses)
    audio_failed = sum(status in ("failed", "error") for status in audio_statuses)
    def task(name):
        item = state.get(name)
        return item if isinstance(item, dict) else {}
    tts = state.get("tts_config") if isinstance(state.get("tts_config"), dict) else {}
    return {
        "exists": True, "project_id": state.get("project_id"), "last_checked": state.get("last_checked"),
        "pptx": task("pptx_task"), "images": task("images_task"),
        "slides_total": len(slides), "slides_done": done, "slides_failed": failed,
        "audio_total": len(audio_statuses), "audio_generated": audio_generated,
        "audio_failed": audio_failed,
        "tts": {key: tts.get(key) for key in ("provider", "model", "voice")},
    }


def load_stored_tts_config(path):
    """Return the complete recorded TTS config, or None when it is unavailable."""
    try:
        with open(path, encoding="utf-8") as status_file:
            state = json.load(status_file)
    except (OSError, json.JSONDecodeError):
        return None
    tts = state.get("tts_config") if isinstance(state, dict) else None
    return tts if isinstance(tts, dict) else None


def apply_stored_tts_config(movie, stored_tts):
    """Apply status.json TTS values to a Movie without changing the state file."""
    for status_name, movie_name in TTS_STATUS_FIELDS.items():
        if status_name in stored_tts:
            setattr(movie, movie_name, stored_tts[status_name])


class QueueLogHandler(logging.Handler):
    def __init__(self, event_queue):
        super().__init__()
        self.event_queue = event_queue

    def emit(self, record):
        self.event_queue.put(("log", self.format(record)))


def run_build(movie_factory, options, confirm_callback=None, tts_conflict_callback=None):
    """Run the shared Movie workflow; kept free of Tk for unit testing."""
    movie = movie_factory()
    for name, value in options.get("overrides", {}).items():
        setattr(movie, name, value)
    if confirm_callback:
        movie.confirm_tts_config_change = confirm_callback
    if options.get("debug"):
        movie.ffmpeg_loglevel = "info"
        movie.show_skip = True
    movie.use_pdf = bool(options.get("use_pdf"))
    if options.get("subproject_name"):
        movie.configure_subproject_paths(options["project_name"], options["subproject_name"],
                                         options["source_dir"], options.get("output_root") or None)
    else:
        movie.configure_project_paths(options["project_name"], options["source_dir"],
                                      options.get("output_root") or None)
    if tts_conflict_callback:
        stored_tts = load_stored_tts_config(movie.status_file)
        current_tts = movie._get_tts_config()
        if stored_tts is not None and stored_tts != current_tts:
            choice = tts_conflict_callback(stored_tts, current_tts)
            if choice == "use_status":
                apply_stored_tts_config(movie, stored_tts)
            elif choice != "overwrite":
                raise RuntimeError("Build cancelled by user.")
    if options.get("build_pptx"):
        movie.build_slide_pptx()
    if options.get("build_video"):
        movie.build_all()
    return getattr(movie, "video_file", None)


class SlideMovieApp:
    def __init__(self, root, initial_options=None, movie_factory=None):
        import tkinter as tk
        from tkinter import ttk
        self.tk, self.ttk = tk, ttk
        self.root = root
        self.movie_factory = movie_factory or self._movie_factory
        self.events = queue.Queue()
        self.worker = None
        self.running = False
        self.initial_options = initial_options or {"overrides": set()}
        self.language = detect_language()
        self._updating = False
        self.overrides = set(self.initial_options.get("overrides", set()))
        self.path_overrides = {name for name in ("output_root", "output_filename") if name in self.overrides}
        self._load_settings()
        self._make_variables()
        self._build()
        self._populate()
        self.refresh_status()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self._poll_events)

    @staticmethod
    def _movie_factory():
        from .core import Movie
        return Movie()

    def _load_settings(self):
        movie = self.movie_factory()
        self.settings = {name: getattr(movie, name, None) for name in SETTING_NAMES}
        self.settings["tts_use_prompt"] = getattr(movie, "tts_use_prompt", True)
        self.settings["output_root"] = getattr(movie, "output_root", None)
        self.settings["output_filename"] = getattr(movie, "output_filename", None)

    def _make_variables(self):
        tk = self.tk
        initial = self.initial_options
        self.source_var = tk.StringVar(value=initial.get("source_dir", "."))
        self.project_var = tk.StringVar(value=initial.get("project_name", ""))
        self.sub_var = tk.StringVar(value=initial.get("subproject_name", ""))
        self.sub_mode_var = tk.BooleanVar(value=bool(initial.get("subproject_name")))
        output_root = display_path_value(initial, self.settings, self.path_overrides, "output_root")
        output_filename = display_path_value(initial, self.settings, self.path_overrides, "output_filename")
        self.output_var = tk.StringVar(value=output_root)
        self.filename_var = tk.StringVar(value=output_filename)
        self.pptx_var = tk.BooleanVar(value=bool(initial.get("build_pptx")))
        self.video_var = tk.BooleanVar(value=bool(initial.get("build_video")))
        self.pdf_var = tk.BooleanVar(value=bool(initial.get("use_pdf")))
        self.debug_var = tk.BooleanVar(value=bool(initial.get("debug")))
        self.use_prompt_var = tk.StringVar(value="config")
        self.setting_vars = {name: tk.StringVar() for name in SETTING_NAMES if name not in ("prompt", "prompt_separator")}
        self.status_var = tk.StringVar()

    def _build(self):
        ttk, tk = self.ttk, self.tk
        self.root.title(TEXT[self.language]["title"])
        # Fit the initial window into small displays.  Content that does not
        # fit is separated into tabs; the settings tab also scrolls.
        screen_width, screen_height = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        width, height = min(900, max(320, screen_width - 40)), min(680, max(300, screen_height - 80))
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(min(640, width), min(400, height))
        outer = ttk.Frame(self.root, padding=10)
        outer.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1); self.root.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1); outer.rowconfigure(0, weight=1)
        self.labels = {}
        self.interactive_widgets = []
        self.notebook = ttk.Notebook(outer); self.notebook.grid(row=0, column=0, sticky="nsew")
        self.project_tab = ttk.Frame(self.notebook, padding=6)
        self.settings_tab = ttk.Frame(self.notebook, padding=0)
        self.log_tab = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(self.project_tab); self.notebook.add(self.settings_tab); self.notebook.add(self.log_tab)
        self.project_tab.columnconfigure(0, weight=1)
        self.project_frame = ttk.LabelFrame(self.project_tab); self.project_frame.grid(row=0, column=0, sticky="ew")
        self.project_frame.columnconfigure(1, weight=1)
        self._row(self.project_frame, 0, "source", self.source_var, browse="dir")
        self._row(self.project_frame, 1, "name", self.project_var)
        self.sub_check = ttk.Checkbutton(self.project_frame, variable=self.sub_mode_var, command=self._sub_changed)
        self.sub_check.grid(row=2, column=0, columnspan=2, sticky="w", padx=4, pady=2); self.labels["sub_mode"] = self.sub_check
        self.interactive_widgets.append(self.sub_check)
        self.sub_label, self.sub_entry = self._row(self.project_frame, 3, "sub", self.sub_var)
        self._row(self.project_frame, 4, "output", self.output_var, browse="dir")
        self._row(self.project_frame, 5, "filename", self.filename_var)
        self.action_frame = ttk.LabelFrame(self.project_tab); self.action_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.pptx_check = ttk.Checkbutton(self.action_frame, variable=self.pptx_var); self.pptx_check.grid(row=0, column=0, padx=4)
        self.video_check = ttk.Checkbutton(self.action_frame, variable=self.video_var); self.video_check.grid(row=0, column=1, padx=4)
        self.pdf_check = ttk.Checkbutton(self.action_frame, variable=self.pdf_var); self.pdf_check.grid(row=0, column=2, padx=4)
        self.debug_check = ttk.Checkbutton(self.action_frame, variable=self.debug_var); self.debug_check.grid(row=0, column=3, padx=4)
        self.interactive_widgets.extend((self.pptx_check, self.video_check, self.pdf_check, self.debug_check))
        self.settings_canvas = tk.Canvas(self.settings_tab, highlightthickness=0)
        settings_scroll = ttk.Scrollbar(self.settings_tab, orient="vertical", command=self.settings_canvas.yview)
        self.settings_canvas.configure(yscrollcommand=settings_scroll.set)
        self.settings_canvas.grid(row=0, column=0, sticky="nsew")
        settings_scroll.grid(row=0, column=1, sticky="ns")
        self.settings_tab.columnconfigure(0, weight=1); self.settings_tab.rowconfigure(0, weight=1)
        settings_inner = ttk.Frame(self.settings_canvas, padding=6)
        self.settings_window = self.settings_canvas.create_window((0, 0), window=settings_inner, anchor="nw")
        settings_inner.bind("<Configure>", lambda _event: self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all")))
        self.settings_canvas.bind("<Configure>", lambda event: self.settings_canvas.itemconfigure(self.settings_window, width=event.width))
        self.settings_frame = ttk.LabelFrame(settings_inner); self.settings_frame.grid(row=0, column=0, sticky="ew")
        settings_inner.columnconfigure(0, weight=1)
        self.settings_frame.columnconfigure(1, weight=1)
        for row, (key, name) in enumerate((("provider", "tts_provider"), ("model", "tts_model"), ("voice", "tts_voice"), ("voicevox", "tts_voicevox_url"), ("chunk", "chunk_size"), ("split", "split_chars"))):
            self._setting_row(row, key, name)
        self._setting_row(6, "overflow", "chunk_overflow", values=("extend", "error"))
        self.use_prompt_label = ttk.Label(self.settings_frame); self.use_prompt_label.grid(row=7, column=0, sticky="nw", padx=4, pady=2)
        self.use_prompt_combo = ttk.Combobox(self.settings_frame, state="readonly", textvariable=self.use_prompt_var)
        self.use_prompt_combo.grid(row=7, column=1, sticky="ew", padx=4, pady=2)
        self.interactive_widgets.append(self.use_prompt_combo)
        self.prompt_label = ttk.Label(self.settings_frame); self.prompt_label.grid(row=8, column=0, sticky="nw", padx=4, pady=2)
        self.prompt_text = tk.Text(self.settings_frame, height=3, width=50); self.prompt_text.grid(row=8, column=1, sticky="ew", padx=4, pady=2)
        self.separator_label = ttk.Label(self.settings_frame); self.separator_label.grid(row=9, column=0, sticky="nw", padx=4, pady=2)
        self.separator_text = tk.Text(self.settings_frame, height=2, width=50); self.separator_text.grid(row=9, column=1, sticky="ew", padx=4, pady=2)
        self.interactive_widgets.extend((self.prompt_text, self.separator_text))
        self.restore_button = ttk.Button(self.settings_frame, command=self.restore_settings); self.restore_button.grid(row=10, column=1, sticky="e", padx=4, pady=4)
        self.interactive_widgets.append(self.restore_button)
        self.status_frame = ttk.LabelFrame(self.project_tab); self.status_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.status_frame.columnconfigure(0, weight=1)
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var, justify="left", wraplength=max(250, width - 100)); self.status_label.grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.refresh_button = ttk.Button(self.status_frame, command=self.refresh_status); self.refresh_button.grid(row=0, column=1, padx=4, pady=4)
        self.log_tab.columnconfigure(0, weight=1); self.log_tab.rowconfigure(0, weight=1)
        self.log = tk.Text(self.log_tab, height=12, wrap="none", state="disabled"); self.log.grid(row=0, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(self.log_tab, orient="vertical", command=self.log.yview); log_scroll.grid(row=0, column=1, sticky="ns")
        log_xscroll = ttk.Scrollbar(self.log_tab, orient="horizontal", command=self.log.xview); log_xscroll.grid(row=1, column=0, sticky="ew")
        self.log.configure(yscrollcommand=log_scroll.set, xscrollcommand=log_xscroll.set)
        controls = ttk.Frame(outer); controls.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.language_combo = ttk.Combobox(controls, state="readonly", values=("日本語", "English"), width=10); self.language_combo.grid(row=0, column=0, sticky="w")
        self.language_combo.bind("<<ComboboxSelected>>", self._change_language)
        self.run_button = ttk.Button(controls, command=self.start); self.run_button.grid(row=0, column=1, padx=4)
        self.clear_button = ttk.Button(controls, command=self.clear_log); self.clear_button.grid(row=0, column=2, padx=4)
        self.exit_button = ttk.Button(controls, command=self.close); self.exit_button.grid(row=0, column=3, padx=4)
        self.state_label = ttk.Label(controls); self.state_label.grid(row=0, column=4, sticky="e", padx=8)
        controls.columnconfigure(4, weight=1)
        self.interactive_widgets.append(self.language_combo)
        for name, var in self.setting_vars.items():
            var.trace_add("write", lambda *_args, key=name: self._mark_override(key))
        self.use_prompt_var.trace_add("write", lambda *_: self._mark_override("tts_use_prompt"))
        self.prompt_text.bind("<<Modified>>", lambda _event: self._text_changed("prompt", self.prompt_text))
        self.separator_text.bind("<<Modified>>", lambda _event: self._text_changed("prompt_separator", self.separator_text))
        for variable in (self.source_var, self.project_var, self.sub_var):
            variable.trace_add("write", lambda *_: self.refresh_status())
        self.output_var.trace_add("write", lambda *_: self._mark_path_override("output_root"))
        self.filename_var.trace_add("write", lambda *_: self._mark_path_override("output_filename"))
        self._set_language()

    def _row(self, parent, row, key, variable, browse=None):
        label = self.ttk.Label(parent); label.grid(row=row, column=0, sticky="w", padx=4, pady=2); self.labels[key] = label
        entry = self.ttk.Entry(parent, textvariable=variable); entry.grid(row=row, column=1, sticky="ew", padx=4, pady=2)
        self.interactive_widgets.append(entry)
        if browse:
            button = self.ttk.Button(parent, command=lambda: self._browse(variable)); button.grid(row=row, column=2, padx=4, pady=2); self.labels[key + "_browse"] = button
            self.interactive_widgets.append(button)
        return label, entry

    def _setting_row(self, row, label_key, name, values=None):
        label = self.ttk.Label(self.settings_frame); label.grid(row=row, column=0, sticky="w", padx=4, pady=2); self.labels[label_key] = label
        if values:
            widget = self.ttk.Combobox(self.settings_frame, textvariable=self.setting_vars[name], values=values)
        else:
            widget = self.ttk.Entry(self.settings_frame, textvariable=self.setting_vars[name])
        widget.grid(row=row, column=1, sticky="ew", padx=4, pady=2)
        self.interactive_widgets.append(widget)

    def _set_language(self):
        text = TEXT[self.language]
        choice = self._prompt_choice()
        self._updating = True
        self.root.title(text["title"])
        for name, widget in self.labels.items():
            key = name.replace("_browse", "")
            widget.configure(text=text["browse"] if name.endswith("_browse") else text[key])
        self.project_frame.configure(text=text["project"]); self.action_frame.configure(text=text["actions"]); self.settings_frame.configure(text=text["settings"]); self.status_frame.configure(text=text["status"])
        self.notebook.tab(self.project_tab, text=text["project"])
        self.notebook.tab(self.settings_tab, text=text["tts_tab"])
        self.notebook.tab(self.log_tab, text=text["log_tab"])
        self.pptx_check.configure(text=text["pptx"]); self.video_check.configure(text=text["video"]); self.pdf_check.configure(text="PDF"); self.debug_check.configure(text=text["debug"])
        self.use_prompt_label.configure(text=text["use_prompt"]); self.prompt_label.configure(text=text["prompt"]); self.separator_label.configure(text=text["separator"])
        self.restore_button.configure(text=text["restore"]); self.refresh_button.configure(text=text["refresh"]); self.run_button.configure(text=text["run"]); self.clear_button.configure(text=text["clear"]); self.exit_button.configure(text=text["exit"])
        self.use_prompt_combo.configure(values=(text["config"], text["yes"], text["no"]))
        self.use_prompt_combo.set({"config": text["config"], "yes": text["yes"], "no": text["no"]}[choice])
        self.language_combo.set("日本語" if self.language == "ja" else "English")
        self._updating = False
        self._set_state("running" if self.running else "idle")

    def _change_language(self, _event=None):
        self.language = "ja" if self.language_combo.get() == "日本語" else "en"
        self._set_language(); self.refresh_status()

    def _populate(self):
        self._updating = True
        for name, variable in self.setting_vars.items():
            value = self.initial_options[name] if name in self.overrides and name in self.initial_options else self.settings.get(name)
            variable.set("" if value is None else str(value))
        for name, widget in (("prompt", self.prompt_text), ("prompt_separator", self.separator_text)):
            value = self.initial_options[name] if name in self.overrides and name in self.initial_options else self.settings.get(name) or ""
            widget.delete("1.0", "end"); widget.insert("1.0", str(value)); widget.edit_modified(False)
        if "tts_use_prompt" in self.overrides:
            value = self.initial_options.get("use_prompt", self.settings["tts_use_prompt"])
            choice = "yes" if value else "no"
        else:
            choice = "config"
        text = TEXT[self.language]
        self.use_prompt_var.set({"config": text["config"], "yes": text["yes"], "no": text["no"]}[choice])
        self._updating = False
        self._toggle_sub()

    def _mark_override(self, name):
        if not self._updating:
            if name == "tts_use_prompt" and self._prompt_choice() == "config":
                self.overrides.discard(name)
                return
            self.overrides.add(name)

    def _mark_path_override(self, name):
        if not self._updating:
            self.path_overrides.add(name)

    def _prompt_choice(self):
        current = self.use_prompt_var.get()
        for language in TEXT.values():
            for choice in ("config", "yes", "no"):
                if current == language[choice]:
                    return choice
        return "config"

    def _text_changed(self, name, widget):
        if widget.edit_modified():
            self._mark_override(name); widget.edit_modified(False)

    def restore_settings(self):
        self.overrides.difference_update(set(SETTING_NAMES) | {"tts_use_prompt"})
        self.initial_options = {**self.initial_options, "overrides": self.overrides}
        self._populate()

    def _toggle_sub(self):
        self.sub_entry.configure(state="normal" if self.sub_mode_var.get() else "disabled")

    def _sub_changed(self):
        self._toggle_sub()
        self.refresh_status()

    def _browse(self, variable):
        from tkinter import filedialog
        value = filedialog.askdirectory(initialdir=variable.get() or ".")
        if value:
            variable.set(value)

    def _status_path(self):
        source = self.source_var.get().strip()
        if self.sub_mode_var.get():
            source = os.path.join(source, self.sub_var.get().strip())
        return os.path.join(source, "status.json")

    def refresh_status(self):
        if not hasattr(self, "status_var"):
            return
        text = TEXT[self.language]
        if not self.project_var.get().strip():
            self.status_var.set(text["no_project"]); return
        summary = summarize_status(self._status_path())
        if not summary["exists"]:
            self.status_var.set(text["missing"]); return
        if "error" in summary:
            self.status_var.set(text["unreadable"] + summary["error"]); return
        def task(item):
            status = item.get("status", "-")
            generated = item.get("generated_at")
            return status + (" (" + str(generated) + ")" if generated else "")
        tts = summary["tts"]
        self.status_var.set("\n".join((
            f"{text['status_file']}: {self._status_path()}",
            f"{text['project_id']}: {summary.get('project_id') or '-'}    {text['checked']}: {summary.get('last_checked') or '-'}",
            f"{text['pptx_status']}: {task(summary['pptx'])}    {text['images_status']}: {task(summary['images'])}",
            f"{text['slides']}: {summary['slides_total']} (done: {summary['slides_done']}, failed: {summary['slides_failed']})",
            f"{text['audio']}: {summary['audio_total']} ({text['generated']}: {summary['audio_generated']}, {text['not_generated']}: {summary['audio_total'] - summary['audio_generated'] - summary['audio_failed']}, {text['failed']}: {summary['audio_failed']})",
            f"{text['tts']}: {tts.get('provider') or '-'} / {tts.get('model') or '-'} / {tts.get('voice') or '-'}",
        )))

    def _options(self):
        overrides = {}
        for name in self.overrides:
            if name in self.setting_vars:
                value = self.setting_vars[name].get()
                overrides[name] = int(value) if name == "chunk_size" and value else value
            elif name == "prompt":
                overrides[name] = self.prompt_text.get("1.0", "end-1c")
            elif name == "prompt_separator":
                overrides[name] = self.separator_text.get("1.0", "end-1c")
            elif name == "tts_use_prompt":
                overrides[name] = self._prompt_choice() == "yes"
        if "output_filename" in self.path_overrides:
            overrides["output_filename"] = self.filename_var.get().strip()
        return {"project_name": self.project_var.get().strip(), "source_dir": self.source_var.get().strip(),
                "subproject_name": self.sub_var.get().strip() if self.sub_mode_var.get() else "",
                "output_root": self.output_var.get().strip() if "output_root" in self.path_overrides else "", "build_pptx": self.pptx_var.get(),
                "build_video": self.video_var.get(), "use_pdf": self.pdf_var.get(),
                "debug": self.debug_var.get(), "overrides": overrides}

    def _validate(self):
        options = self._options()
        if not options["project_name"] or not options["source_dir"] or not (options["build_pptx"] or options["build_video"]): return False
        if self.sub_mode_var.get() and not options["subproject_name"]: return False
        if options["output_root"] and not os.path.isdir(options["output_root"]): return False
        chunk = self.setting_vars["chunk_size"].get().strip()
        return not chunk or (chunk.isdigit() and int(chunk) > 0)

    def start(self):
        from tkinter import messagebox
        if not self._validate():
            messagebox.showerror(TEXT[self.language]["invalid"], TEXT[self.language]["invalid"], parent=self.root); return
        self.running = True; self._set_controls("disabled"); self._set_state("running")
        options = self._options()
        tts_conflict_choice = {"value": None}
        def confirm(_stored, _current):
            if tts_conflict_choice["value"] == "overwrite":
                return True
            request = {"event": threading.Event(), "answer": False}
            self.events.put(("confirm", request)); request["event"].wait(); return request["answer"]
        def resolve_tts_conflict(stored, current):
            request = {"event": threading.Event(), "stored": stored, "current": current,
                       "answer": "cancel"}
            self.events.put(("tts_conflict", request)); request["event"].wait()
            tts_conflict_choice["value"] = request["answer"]
            return request["answer"]
        def worker():
            try:
                path = run_build(self.movie_factory, options, confirm, resolve_tts_conflict)
                self.events.put(("result", "success", path))
            except SystemExit as exc:
                self.events.put(("result", "failed", f"Exited with status {exc.code}"))
            except Exception:
                self.events.put(("log", traceback.format_exc()))
                self.events.put(("result", "failed", None))
        self.worker = threading.Thread(target=worker, daemon=False); self.worker.start()

    def _poll_events(self):
        from tkinter import messagebox
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "log": self.append_log(event[1])
                elif event[0] == "confirm":
                    event[1]["answer"] = messagebox.askyesno(TEXT[self.language]["confirm"], TEXT[self.language]["confirm"], parent=self.root); event[1]["event"].set()
                elif event[0] == "tts_conflict":
                    event[1]["answer"] = self._ask_tts_conflict(event[1]["stored"], event[1]["current"])
                    if event[1]["answer"] == "use_status":
                        self._populate_stored_tts_config(event[1]["stored"])
                    event[1]["event"].set()
                elif event[0] == "result":
                    self.running = False; self._set_controls("normal"); success = event[1] == "success"; self._set_state("success" if success else "failed")
                    if success: self.append_log(event[2] or TEXT[self.language]["done"]); messagebox.showinfo(TEXT[self.language]["success"], TEXT[self.language]["done"], parent=self.root)
                    else: messagebox.showerror(TEXT[self.language]["failed"], TEXT[self.language]["failed_message"], parent=self.root)
                    self.refresh_status()
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)

    def _ask_tts_conflict(self, _stored, _current):
        """Ask on the Tk thread whether to preserve or replace recorded TTS settings."""
        text = TEXT[self.language]
        dialog = self.tk.Toplevel(self.root)
        dialog.title(text["confirm"])
        dialog.transient(self.root)
        dialog.resizable(False, False)
        choice = self.tk.StringVar(value="cancel")
        self.ttk.Label(dialog, text=text["confirm"], wraplength=420,
                       justify="left").grid(row=0, column=0, columnspan=3, padx=14, pady=(14, 10))

        def select(value):
            choice.set(value)
            dialog.destroy()

        self.ttk.Button(dialog, text=text["use_status"], command=lambda: select("use_status")).grid(row=1, column=0, padx=(14, 4), pady=(0, 14))
        self.ttk.Button(dialog, text=text["overwrite"], command=lambda: select("overwrite")).grid(row=1, column=1, padx=4, pady=(0, 14))
        self.ttk.Button(dialog, text=text["cancel"], command=dialog.destroy).grid(row=1, column=2, padx=(4, 14), pady=(0, 14))
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return choice.get()

    def _populate_stored_tts_config(self, stored_tts):
        """Reflect the recorded TTS configuration in the GUI after selecting it."""
        self._updating = True
        try:
            for status_name, movie_name in TTS_STATUS_FIELDS.items():
                if status_name not in stored_tts:
                    continue
                value = stored_tts[status_name]
                if movie_name in self.setting_vars:
                    self.setting_vars[movie_name].set("" if value is None else str(value))
                elif movie_name == "prompt":
                    self.prompt_text.delete("1.0", "end")
                    self.prompt_text.insert("1.0", "" if value is None else str(value))
                    self.prompt_text.edit_modified(False)
                elif movie_name == "prompt_separator":
                    self.separator_text.delete("1.0", "end")
                    self.separator_text.insert("1.0", "" if value is None else str(value))
                    self.separator_text.edit_modified(False)
                elif movie_name == "tts_use_prompt":
                    self.use_prompt_var.set(TEXT[self.language]["yes"] if value else TEXT[self.language]["no"])
                self.overrides.add(movie_name)
        finally:
            self._updating = False

    def append_log(self, line):
        self.log.configure(state="normal"); self.log.insert("end", line + "\n"); self.log.see("end"); self.log.configure(state="disabled")

    def clear_log(self):
        self.log.configure(state="normal"); self.log.delete("1.0", "end"); self.log.configure(state="disabled")

    def _set_state(self, state):
        self.state_label.configure(text=TEXT[self.language][state])

    def _set_controls(self, state):
        for widget in self.interactive_widgets + [self.run_button, self.clear_button, self.exit_button, self.refresh_button]:
            widget.configure(state=state)
        if state == "normal":
            self.use_prompt_combo.configure(state="readonly")
            self.language_combo.configure(state="readonly")
            self._toggle_sub()

    def close(self):
        from tkinter import messagebox
        if self.running:
            messagebox.showwarning(TEXT[self.language]["running"], TEXT[self.language]["close_running"], parent=self.root); return
        self.root.destroy()


def main(initial_options=None):
    """Start the GUI, reporting a useful error when Tk is unavailable."""
    try:
        import tkinter as tk
    except ImportError:
        print("Tkinter is unavailable. Install your operating system's Python Tk package.", file=sys.stderr)
        return 1
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"Tkinter is unavailable: {exc}", file=sys.stderr)
        return 1
    events = queue.Queue()
    handler = QueueLogHandler(events)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(handler)
    try:
        app = SlideMovieApp(root, initial_options)
        # Reuse the handler's queue for the app after construction.
        app.events = events
        root.mainloop()
    except SystemExit as exc:
        print(f"Could not initialize slidemovie: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Could not initialize slidemovie GUI: {exc}", file=sys.stderr)
        return 1
    finally:
        logging.getLogger().removeHandler(handler)
    return 0

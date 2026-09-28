import json
import os
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

from slidemovie.gui import (apply_stored_tts_config, display_path_value, display_setting_value, open_folder,
                            build_settings_from_status, load_stored_tts_config, official_website_url, options_from_args,
                            display_prompt_separator, display_source_path, parse_prompt_separator, parse_screen_size, project_folder_paths, run_build, SlideMovieApp,
                            default_project_name_from_status, FOREST_THEME_PATH, gui_title, load_local_config, local_config_path, pptx_display_status, run_preflight_message, save_local_config, summarize_status, TEXT)
from slidemovie.gui import (_windows_libreoffice_detail, load_window_size,
                            save_window_size, window_size_for_screen)


def _args(**changes):
    values = {
        "project_name": None, "source_dir": ".", "sub": None,
        "output_root": None, "filename": None, "pptx": False, "video": False,
        "pdf": False, "debug": False, "tts_provider": None, "tts_model": None,
        "tts_voice": None, "tts_voicevox_url": None, "prompt": None,
        "no_prompt": False, "prompt_separator": None, "chunk_size": None,
        "split_chars": None, "chunk_overflow": None,
    }
    values.update(changes)
    return SimpleNamespace(**values)


def test_options_from_args_preserves_only_explicit_overrides():
    options = options_from_args(_args(project_name="demo", video=True,
                                      tts_provider="openai", prompt="Read clearly"))

    assert options["project_name"] == "demo"
    assert options["build_video"] is True
    assert options["tts_provider"] == "openai"
    assert {"tts_provider", "prompt", "tts_use_prompt"} <= options["overrides"]
    assert "tts_model" not in options["overrides"]


def test_run_build_stops_before_starting_work_when_cancelled():
    cancelled = threading.Event()
    cancelled.set()
    movie = SimpleNamespace()

    try:
        run_build(lambda: movie, {"source_dir": ".", "overrides": {}},
                  cancel_event=cancelled)
    except InterruptedError:
        pass
    else:
        raise AssertionError("a pending cancellation must stop the build")


def test_display_path_value_uses_config_unless_cli_path_is_explicit():
    initial = {"output_root": "", "output_filename": ""}
    settings = {"output_root": "/Volumes/back/slidemovie", "output_filename": "movie"}

    assert display_path_value(initial, settings, set(), "output_root") == "/Volumes/back/slidemovie"
    assert display_path_value(initial, settings, {"output_root"}, "output_root") == ""


def test_configured_filename_is_shown_when_only_cli_paths_are_prioritized():
    initial = {"output_filename": ""}
    settings = {"output_filename": "configured-movie"}

    assert display_path_value(initial, settings, set(), "output_filename") == "configured-movie"


def test_display_source_path_expands_the_current_or_relative_directory():
    assert display_source_path(".") == os.getcwd()
    assert display_source_path("project") == os.path.join(os.getcwd(), "project")


def test_gui_title_is_not_hard_coded_to_the_initial_gui_release():
    assert gui_title().startswith("slidemovie")
    assert TEXT["ja"]["title"] == gui_title()


def test_forest_theme_assets_are_bundled():
    assert FOREST_THEME_PATH.is_file()
    assert (FOREST_THEME_PATH.parent / "forest-light").is_dir()


def test_window_size_preferences_save_only_dimensions_and_fit_the_display(tmp_path):
    path = tmp_path / "gui.json"
    save_window_size(1200, 800, str(path))

    assert json.loads(path.read_text(encoding="utf-8")) == {"width": 1200, "height": 800}
    assert load_window_size(str(path)) == (1200, 800)
    assert window_size_for_screen((1200, 800), 1000, 700) == (960, 620)


def test_invalid_window_size_preferences_are_ignored(tmp_path):
    path = tmp_path / "gui.json"
    path.write_text('{"width": true, "height": 600}', encoding="utf-8")

    assert load_window_size(str(path)) is None


def test_windows_libreoffice_version_is_read_without_running_soffice(tmp_path):
    executable = tmp_path / "soffice.exe"
    (tmp_path / "version.ini").write_text(
        "[Version]\nBuildVersion=26.8.0.3\n", encoding="utf-8")

    assert _windows_libreoffice_detail(str(executable)) == f"26.8.0.3 ({executable})"


def test_local_config_path_is_next_to_the_subproject_markdown_input():
    assert local_config_path("/work", "") == "/work/config.json"
    assert local_config_path("/work", "chapter-1") == "/work/chapter-1/config.json"


def test_status_project_id_is_a_default_only_with_its_matching_markdown(tmp_path):
    (tmp_path / "status.json").write_text(
        json.dumps({"project_id": "demo"}), encoding="utf-8")
    assert default_project_name_from_status(str(tmp_path)) == ""

    (tmp_path / "demo.md").write_text("# Demo", encoding="utf-8")
    assert default_project_name_from_status(str(tmp_path)) == "demo"


def test_source_change_uses_the_valid_status_project_default(tmp_path):
    (tmp_path / "status.json").write_text(
        json.dumps({"project_id": "demo"}), encoding="utf-8")
    (tmp_path / "demo.md").write_text("# Demo", encoding="utf-8")

    class Variable:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    app = SimpleNamespace(
        initial_options={"project_name": None}, source_var=Variable(str(tmp_path)),
        project_var=Variable("old-project"), _input_changed=MagicMock(),
    )
    SlideMovieApp._source_changed(app)

    assert app.project_var.get() == "demo"
    app._input_changed.assert_called_once()


def test_pptx_display_status_distinguishes_generated_present_and_missing(tmp_path):
    pptx = tmp_path / "demo.pptx"
    assert pptx_display_status("ja", {"status": "generated"}, str(pptx)) == "未生成"

    pptx.write_text("pptx", encoding="utf-8")
    assert pptx_display_status("ja", {"status": "missing"}, str(pptx)) == "ファイル有"
    assert pptx_display_status("ja", {"status": "generated"}, str(pptx)) == "生成済み"


def test_run_preflight_checks_project_inputs_in_display_order(tmp_path):
    missing = str(tmp_path / "missing")
    assert run_preflight_message("ja", missing, "demo", False, "", False, True, False) == "ソースフォルダが存在しません。"

    source = tmp_path / "source"
    source.mkdir()
    assert run_preflight_message("ja", str(source), "", False, "", False, True, False) == "プロジェクト名を入れてください。"
    assert run_preflight_message("ja", str(source), "demo", True, "", False, True, False) == "サブプロジェクト名を入れてください。"
    assert run_preflight_message("ja", str(source), "demo", True, "child", False, True, False) == f"入力ファイルのフォルダー ({source / 'child'}) が存在しません。"
    assert run_preflight_message("ja", str(source), "demo", False, "", False, True, False) == "マークダウンファイル (demo.md) が存在しません。"

    (source / "demo.md").write_text("# Demo", encoding="utf-8")
    assert run_preflight_message("ja", str(source), "demo", False, "", False, False, False) == "実行内容を選んでください。"
    assert run_preflight_message("ja", str(source), "demo", False, "", False, True, False) == "まずは PPTX を生成してください。"
    assert run_preflight_message("ja", str(source), "demo", False, "", False, True, True) == "PDFファイル (demo.pdf) が存在しません。"

    (source / "demo.pdf").write_text("pdf", encoding="utf-8")
    assert run_preflight_message("ja", str(source), "demo", False, "", False, True, True) == ""


def test_run_preflight_rejects_a_status_file_for_another_project(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "demo.md").write_text("# Demo", encoding="utf-8")
    (source / "status.json").write_text(
        json.dumps({"project_id": "other-project"}), encoding="utf-8")

    assert run_preflight_message("ja", str(source), "demo", False, "", True, False, False) == (
        "status.json のプロジェクト ID が現在のプロジェクトと一致しません。")

    child = source / "child"
    child.mkdir()
    (child / "child.md").write_text("# Child", encoding="utf-8")
    (child / "status.json").write_text(
        json.dumps({"project_id": "parent-other"}), encoding="utf-8")
    assert run_preflight_message("ja", str(source), "parent", True, "child", True, False, False) == (
        "status.json のプロジェクト ID が現在のプロジェクトと一致しません。")


def test_save_local_config_preserves_unrelated_keys(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"custom_key": "keep", "video_fps": 24,
                                "output_root": "/old", "output_filename": "old"}), encoding="utf-8")

    save_local_config(str(path), {"video_fps": 30, "screen_size": [1920, 1080],
                                  "output_filename": "new"})

    assert json.loads(path.read_text(encoding="utf-8")) == {
        "custom_key": "keep", "video_fps": 30, "screen_size": [1920, 1080],
        "output_filename": "new",
    }
    assert load_local_config(str(path))["video_fps"] == 30


def test_local_config_values_come_from_the_current_form_inputs():
    class Variable:
        def __init__(self, value): self.value = value
        def get(self): return self.value

    class Text:
        def __init__(self, value): self.value = value
        def get(self, *_args): return self.value

    app = SimpleNamespace(
        setting_vars={
            "tts_provider": Variable("openai"), "tts_model": Variable("gpt-4o-mini-tts"),
            "tts_voice": Variable("alloy"), "tts_voicevox_url": Variable(""),
            "chunk_size": Variable("900"), "split_chars": Variable("。\\n"),
            "chunk_overflow": Variable("extend"), "screen_size": Variable("1920x1080"),
            "image_pad_color": Variable("black"), "video_fps": Variable("60"),
            "silence_sec": Variable("1.5"),
        },
        prompt_text=Text("Speak clearly"), separator_text=Text("\\n"),
        output_var=Variable("/movies"), filename_var=Variable("demo"),
        _prompt_choice=lambda: "yes",
    )
    app._form_settings = lambda: SlideMovieApp._form_settings(app)

    values = SlideMovieApp._local_config_values(app)

    assert values["video_fps"] == 60
    assert values["screen_size"] == [1920, 1080]
    assert values["prompt"] == "Speak clearly"
    assert values["prompt_separator"] == "\n"
    assert values["tts_voicevox_url"] is None
    assert "output_root" not in values
    assert values["output_filename"] == "demo"


def test_options_apply_settings_loaded_from_local_config():
    class Variable:
        def __init__(self, value): self.value = value
        def get(self): return self.value

    class Text:
        def __init__(self, value): self.value = value
        def get(self, *_args): return self.value

    app = SimpleNamespace(
        overrides={"tts_provider", "tts_model", "tts_voice", "tts_voicevox_url",
                   "chunk_size", "split_chars", "chunk_overflow", "prompt",
                   "prompt_separator", "tts_use_prompt"},
        path_overrides={"output_filename"},
        setting_vars={
            "tts_provider": Variable("google"), "tts_model": Variable("model"),
            "tts_voice": Variable("voice"), "tts_voicevox_url": Variable(""),
            "chunk_size": Variable("700"), "split_chars": Variable("。\\n"),
            "chunk_overflow": Variable("error"),
        },
        prompt_text=Text("prompt"), separator_text=Text("\\n\\n## 原稿\\n"),
        filename_var=Variable("movie"), project_var=Variable("project"),
        source_var=Variable("/source"), sub_var=Variable(""),
        sub_mode_var=Variable(False), output_var=Variable(""), pptx_var=Variable(False),
        video_var=Variable(True), pdf_var=Variable(False), debug_var=Variable(False),
        _prompt_choice=lambda: "yes",
    )

    options = SlideMovieApp._options(app)

    assert options["overrides"]["tts_provider"] == "google"
    assert options["overrides"]["prompt_separator"] == "\n\n## 原稿\n"
    assert options["overrides"]["output_filename"] == "movie"


def test_setting_text_value_restores_a_disabled_widget_after_update():
    class Text:
        def __init__(self):
            self.state = "disabled"
            self.value = "old"

        def cget(self, name):
            assert name == "state"
            return self.state

        def configure(self, **kwargs):
            self.state = kwargs.get("state", self.state)

        def delete(self, *_args):
            self.value = ""

        def insert(self, _index, value):
            self.value = value

        def edit_modified(self, _value):
            pass

    text = Text()
    SlideMovieApp._set_text_value(text, "new value")

    assert text.value == "new value"
    assert text.state == "disabled"


def test_action_required_message_is_localized():
    assert TEXT["ja"]["action_required"] == "実行内容を選んでください。"
    assert TEXT["en"]["action_required"] == "Please select an action."


def test_open_folder_rejects_a_missing_path(tmp_path):
    assert open_folder(str(tmp_path / "missing")) is False


def test_project_folder_paths_use_project_and_subproject_directories():
    source, output = project_folder_paths("/work", "demo", "", "/output")
    assert source == "/work"
    assert output == "/output/demo"

    source, output = project_folder_paths("/work", "parent", "child", "/output")
    assert source == "/work/child"
    assert output == "/output/parent/child"


def test_official_website_url_matches_the_gui_language():
    assert official_website_url("en") == "https://sekika.github.io/slidemovie/"
    assert official_website_url("ja") == "https://sekika.github.io/slidemovie/ja/"


def test_build_settings_from_status_includes_every_editable_build_value():
    settings = build_settings_from_status({
        "screen": {"width": 1920, "height": 1080},
        "video": {"fps": 60}, "common": {"silence_sec": 1.5},
        "image_pad_color": "black",
    })

    assert settings == {"screen_size": [1920, 1080], "video_fps": 60,
                        "silence_sec": 1.5, "image_pad_color": "black"}
    assert parse_screen_size("1920x1080") == [1920, 1080]


def test_stored_tts_config_populates_all_text_inputs():
    class Variable:
        def __init__(self): self.value = None
        def set(self, value): self.value = value

    class Text:
        def __init__(self): self.value = ""
        def cget(self, _name): return "disabled"
        def configure(self, **_kwargs): pass
        def delete(self, *_args): self.value = ""
        def insert(self, _index, value): self.value = value
        def edit_modified(self, _value): pass

    app = SimpleNamespace(
        _updating=False, language="ja", overrides=set(),
        setting_vars={"tts_provider": Variable()}, prompt_text=Text(),
        separator_text=Text(), use_prompt_var=Variable(),
    )
    SlideMovieApp._populate_stored_tts_config(app, {
        "provider": "openai", "prompt": "記録済みプロンプト",
        "prompt_separator": "\n\n## 原稿\n", "use_prompt": True,
    })

    assert app.prompt_text.value == "記録済みプロンプト"
    assert app.separator_text.value == "\\n\\n## 原稿\\n"
    assert app.setting_vars["tts_provider"].value == "openai"
    assert "prompt" in app.overrides
    assert "prompt_separator" in app.overrides


def test_prompt_separator_displays_newline_notation_and_parses_it_back():
    assert display_prompt_separator("\n\n## 原稿\n") == "\\n\\n## 原稿\\n"
    assert parse_prompt_separator("\\n\\n## 原稿\\n") == "\n\n## 原稿\n"
    assert display_setting_value("split_chars", "。\n") == "。\\n"


def test_old_status_tts_config_defaults_the_prompt_separator(tmp_path):
    path = tmp_path / "status.json"
    path.write_text(json.dumps({"tts_config": {"provider": "openai"}}), encoding="utf-8")

    assert load_stored_tts_config(str(path))["prompt_separator"] == ""


def test_summarize_status_is_tolerant_and_does_not_return_prompt(tmp_path):
    missing = summarize_status(str(tmp_path / "status.json"))
    assert missing == {"exists": False}

    path = tmp_path / "status.json"
    path.write_text(json.dumps({
        "project_id": "demo", "last_checked": "2026-09-27",
        "pptx_task": {"status": "done"}, "images_task": {"status": "generated", "source_file": "demo.pptx"},
        "final_movie": {"status": "generated", "file_name": "demo.mp4", "duration_min": 3.5},
        "tts_config": {"provider": "openai", "model": "tts", "voice": "alloy", "prompt": "secret"},
        "slides": {
            "one": {"video": {"status": "generated"}, "audio": {"status": "generated"}},
            "two": {"video": {"status": "failed"}, "audio": {"status": "missing"}},
            "three": {"audio": {"status": "error"}},
        },
    }), encoding="utf-8")

    summary = summarize_status(str(path))
    assert summary["slides_total"] == 3
    assert summary["slides_done"] == 1
    assert summary["slides_failed"] == 1
    assert summary["pptx"]["status"] == "done"
    assert summary["final_video"]["duration_min"] == 3.5
    assert summary["final_video"]["file_name"] == "demo.mp4"
    assert summary["audio_total"] == 3
    assert summary["audio_generated"] == 1
    assert summary["audio_failed"] == 1
    assert summary["tts"] == {"provider": "openai", "model": "tts", "voice": "alloy"}
    assert "prompt" not in summary["tts"]


def test_run_build_uses_shared_movie_workflow():
    movie = MagicMock()
    movie.video_file = "movie/demo/demo.mp4"
    options = {
        "project_name": "demo", "source_dir": ".", "subproject_name": "",
        "output_root": "", "build_pptx": True, "build_video": True,
        "use_pdf": True, "debug": False, "overrides": {"tts_provider": "openai"},
    }

    result = run_build(lambda: movie, options)

    assert movie.tts_provider == "openai"
    assert movie.use_pdf is True
    movie.configure_project_paths.assert_called_once_with("demo", ".", None)
    movie.build_slide_pptx.assert_called_once()
    movie.build_all.assert_called_once()
    assert result == "movie/demo/demo.mp4"


def test_apply_stored_tts_config_uses_status_values_without_unrelated_changes():
    movie = SimpleNamespace(tts_provider="google", tts_model="new", tts_voice="new",
                            tts_use_prompt=True, prompt="new", chunk_size=500)

    apply_stored_tts_config(movie, {
        "provider": "openai", "model": "tts-1", "voice": "alloy",
        "use_prompt": False, "prompt": "recorded", "chunk_size": None,
    })

    assert movie.tts_provider == "openai"
    assert movie.tts_model == "tts-1"
    assert movie.tts_voice == "alloy"
    assert movie.tts_use_prompt is False
    assert movie.prompt == "recorded"
    assert movie.chunk_size is None


def test_run_build_can_use_recorded_tts_config(tmp_path):
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"tts_config": {
        "provider": "openai", "model": "tts-1", "voice": "alloy",
        "use_prompt": False, "prompt": "recorded", "prompt_separator": "",
        "chunk_size": None, "split_chars": ".", "chunk_overflow": "extend",
        "tts_voicevox_url": None,
    }}), encoding="utf-8")
    movie = MagicMock()
    movie.status_file = str(status_file)
    movie._get_tts_config.return_value = {"provider": "google"}
    options = {
        "project_name": "demo", "source_dir": ".", "subproject_name": "",
        "output_root": "", "build_pptx": False, "build_video": True,
        "use_pdf": False, "debug": False, "overrides": {},
    }

    run_build(lambda: movie, options, tts_conflict_callback=lambda stored, current: "use_status")

    assert movie.tts_provider == "openai"
    assert movie.tts_model == "tts-1"
    assert movie.tts_voice == "alloy"
    assert movie.tts_use_prompt is False
    movie.build_all.assert_called_once()

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from slidemovie.gui import apply_stored_tts_config, options_from_args, run_build, summarize_status


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


def test_summarize_status_is_tolerant_and_does_not_return_prompt(tmp_path):
    missing = summarize_status(str(tmp_path / "status.json"))
    assert missing == {"exists": False}

    path = tmp_path / "status.json"
    path.write_text(json.dumps({
        "project_id": "demo", "last_checked": "2026-09-27",
        "pptx_task": {"status": "done"}, "images_task": {"status": "missing"},
        "tts_config": {"provider": "openai", "model": "tts", "voice": "alloy", "prompt": "secret"},
        "slides": {
            "one": {"status": "done", "audio": {"status": "generated"}},
            "two": {"status": "failed", "audio": {"status": "missing"}},
            "three": {"audio": {"status": "error"}},
        },
    }), encoding="utf-8")

    summary = summarize_status(str(path))
    assert summary["slides_total"] == 3
    assert summary["slides_done"] == 1
    assert summary["slides_failed"] == 1
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

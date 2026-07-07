import os
import json
import pytest
import sys
from unittest.mock import MagicMock, patch

# Add parent directory to sys.path to import slidemovie module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock external libraries before importing core
sys.modules['multiai_tts'] = MagicMock()
sys.modules['pptxtoimages'] = MagicMock()
sys.modules['pptxtoimages.tools'] = MagicMock()

from slidemovie.core import Movie

@pytest.fixture
def mock_tools(mocker):
    """
    Mock shutil.which to bypass external tool checks (ffmpeg, pandoc)
    during initialization.
    """
    mocker.patch('shutil.which', return_value='/usr/bin/mocked_tool')

@pytest.fixture
def movie(mock_tools):
    """Fixture to create a Movie instance."""
    m = Movie()
    # Reset output_root to None to ensure tests rely on the source_dir structure
    m.output_root = None
    # Ensure output_filename is None by default (mimic init state)
    m.output_filename = None
    return m

class TestMovieConfig:
    def test_default_settings(self, movie):
        """Test if settings are loaded (checking key existence)."""
        assert hasattr(movie, 'tts_provider')
        assert hasattr(movie, 'screen_size')
        # [Fix] Check for output_filename
        assert hasattr(movie, 'output_filename')

    def test_load_settings_override(self, mock_tools, tmp_path):
        """Test overriding settings via config.json logic."""
        pass 

class TestPathConfiguration:
    def test_configure_project_paths_flat(self, movie, tmp_path):
        """Test path configuration for standard (flat) mode."""
        movie.output_root = None
        
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        
        movie.configure_project_paths(
            project_name="test_proj",
            source_dir=str(source_dir)
        )
        
        assert movie.project_id == "test_proj"
        assert movie.md_file == str(source_dir / "test_proj.md")
        
        # Default output: source_dir/movie/project_name
        expected_movie_dir = source_dir / "movie" / "test_proj"
        assert movie.movie_dir == str(expected_movie_dir)
        assert os.path.exists(movie.movie_dir)
        
        # [Fix] Verify default video filename (same as project name)
        assert movie.video_file.endswith("test_proj.mp4")

    def test_configure_project_paths_with_custom_filename(self, movie, tmp_path):
        """Test path configuration with custom output_filename attribute set."""
        source_dir = tmp_path / "src"
        source_dir.mkdir()
        
        # Manually set the attribute (as CLI or Config would do)
        movie.output_filename = "custom_output_name"
        
        movie.configure_project_paths(
            project_name="test_proj",
            source_dir=str(source_dir)
        )
        
        # Verify the filename uses the custom name, not project name
        assert movie.video_file.endswith("custom_output_name.mp4")
        assert "test_proj.mp4" not in movie.video_file

    def test_configure_subproject_paths(self, movie, tmp_path):
        """Test path configuration for subproject (Parent/Child) mode."""
        movie.output_root = None
        
        parent_dir = tmp_path / "parent"
        parent_dir.mkdir()
        
        movie.configure_subproject_paths(
            parent_project_name="parent_proj",
            subproject_name="child_sub",
            source_parent_dir=str(parent_dir)
        )
        
        assert movie.project_id == "parent_proj-child_sub"
        assert movie.source_dir == str(parent_dir / "child_sub")
        
        # Output: parent/movie/parent_proj/child_sub
        expected_movie_dir = parent_dir / "movie" / "parent_proj" / "child_sub"
        assert movie.movie_dir == str(expected_movie_dir)
        
        # [Fix] Verify default filename (Parent-Child)
        assert movie.video_file.endswith("parent_proj-child_sub.mp4")

class TestMarkdownProcessing:
    def test_ensure_slide_ids(self, movie, tmp_path):
        """Test if slide-ids are automatically injected into Markdown."""
        md_content = """# Slide 1
::: notes
Note 1
:::

# Slide 2
::: notes
Note 2
:::
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content, encoding='utf-8')
        
        movie.md_file = str(md_file)
        movie.project_id = "TEST"
        
        movie._ensure_slide_ids()
        
        updated_content = md_file.read_text(encoding='utf-8')
        assert "<!-- slide-id: TEST-01 -->" in updated_content
        assert "<!-- slide-id: TEST-02 -->" in updated_content

    def test_extract_slides_list(self, movie, tmp_path):
        """Test extracting slide information from Markdown."""
        md_content = """<!-- slide-id: s-01 -->
# Title A
::: notes
Note A
:::

<!-- slide-id: s-02 -->
<!-- video-file: demo.mp4 -->
# Title B
"""
        md_file = tmp_path / "extract.md"
        md_file.write_text(md_content, encoding='utf-8')
        movie.md_file = str(md_file)
        
        slides = movie._extract_slides_list()
        
        assert len(slides) == 2
        assert slides[0]['id'] == 's-01'
        assert slides[0]['title'] == 'Title A'
        
        assert slides[1]['id'] == 's-02'
        assert slides[1]['video_file'] == 'demo.mp4'

class TestBuildLogic:
    def test_build_slide_pptx(self, movie, tmp_path, mocker):
        """Test if the pandoc command is constructed and called correctly."""
        # Setup files
        md_file = tmp_path / "test.md"
        md_file.touch()
        movie.md_file = str(md_file)
        movie.slide_file = str(tmp_path / "test.pptx")
        movie.source_dir = str(tmp_path)
        
        # Manually set project_id as it is required by _init_audio_state
        movie.project_id = "test_project"
        
        # Mock status file
        movie.status_file = str(tmp_path / "status.json")
        
        # Mock subprocess
        mock_run = mocker.patch('subprocess.check_call')
        
        movie.build_slide_pptx()
        
        # Verify call
        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        command_str = args[0]
        assert "pandoc" in command_str
        assert str(md_file) in command_str

    def test_check_external_tools_missing(self, mocker):
        """Test if program exits when tools are missing."""
        mocker.patch('shutil.which', return_value=None)

        with pytest.raises(SystemExit) as e:
            Movie()
        assert e.value.code == 1

class TestVoicevox:
    def test_default_settings_include_voicevox_url(self, movie):
        """tts_voicevox_url exists as a setting and defaults to None."""
        assert hasattr(movie, 'tts_voicevox_url')
        assert movie.tts_voicevox_url is None

    def test_get_tts_config_includes_voicevox_url(self, movie):
        """tts_voicevox_url is part of the change-detection config."""
        cfg = movie._get_tts_config()
        assert 'tts_voicevox_url' in cfg

    def test_speak_to_wav_voicevox(self, movie):
        """VOICEVOX branch sets provider, integer style ID and URL."""
        movie.tts_provider = 'voicevox'
        movie.tts_voice = '3'  # string style ID from config/CLI
        movie.tts_voicevox_url = 'http://127.0.0.1:50021'
        movie.tts_use_prompt = False
        movie.max_retry = 2

        fake_client = MagicMock()
        fake_client.error = False
        fake_client.chunks = None

        with patch('slidemovie.core.multiai_tts.Prompt', return_value=fake_client):
            movie._speak_to_wav('こんにちは', '/tmp/out.wav')

        fake_client.set_tts_provider.assert_called_with('voicevox')
        # style ID must be converted to an integer
        assert fake_client.tts_voice_voicevox == 3
        assert isinstance(fake_client.tts_voice_voicevox, int)
        assert fake_client.tts_voicevox_url == 'http://127.0.0.1:50021'

    def test_speak_to_wav_voicevox_invalid_voice(self, movie):
        """A non-integer style ID exits with an error."""
        movie.tts_provider = 'voicevox'
        movie.tts_voice = 'sadaltager'  # not an integer
        movie.tts_voicevox_url = None
        movie.tts_use_prompt = False
        movie.max_retry = 2

        fake_client = MagicMock()
        fake_client.error = False
        fake_client.chunks = None

        with patch('slidemovie.core.multiai_tts.Prompt', return_value=fake_client):
            with pytest.raises(SystemExit):
                movie._speak_to_wav('こんにちは', '/tmp/out.wav')

    def test_backfill_voicevox_url_no_prompt(self, movie, tmp_path, mocker):
        """Old status files without tts_voicevox_url must not trigger a prompt."""
        movie.project_id = "test_proj"
        movie.md_file = str(tmp_path / "test.md")
        movie.slide_file = str(tmp_path / "test.pptx")
        movie.status_file = str(tmp_path / "status.json")

        # Build a state file whose tts_config lacks tts_voicevox_url but
        # otherwise matches the current settings.
        current = movie._get_tts_config()
        stored = dict(current)
        del stored['tts_voicevox_url']

        state = movie._init_audio_state(movie.status_file)
        state['build_config'] = movie._get_build_config()
        state['tts_config'] = stored
        with open(movie.status_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False)

        # If a prompt were triggered, input() would be called; make it fail loudly.
        input_mock = mocker.patch('builtins.input', side_effect=AssertionError("prompt triggered"))

        loaded = movie._load_audio_state()

        input_mock.assert_not_called()
        assert loaded['tts_config']['tts_voicevox_url'] is None

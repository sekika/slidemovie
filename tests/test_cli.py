import pytest
import sys
from unittest.mock import MagicMock, patch
import os

# Add parent directory to sys.path to ensure slidemovie module is found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import slidemovie.cli as cli

@pytest.fixture
def mock_movie_class(mocker):
    """Mock the slidemovie.Movie class."""
    return mocker.patch('slidemovie.Movie')

def test_cli_help(capsys):
    """Test that help is displayed and system exits if no args provided."""
    with patch.object(sys, 'argv', ['slidemovie']):
        with pytest.raises(SystemExit):
            cli.main()
        
        captured = capsys.readouterr()
        # Verify usage/help text is printed
        assert "usage:" in captured.err or "usage:" in captured.out

def test_cli_pptx_mode(mock_movie_class):
    """Test the --pptx option."""
    test_args = ['slidemovie', 'MyProject', '--pptx']
    
    # Get the mock instance
    mock_instance = mock_movie_class.return_value
    
    with patch.object(sys, 'argv', test_args):
        cli.main()
        
    # Check if Movie was instantiated
    mock_movie_class.assert_called_once()
    
    # Check if default path configuration was called (Flat mode)
    mock_instance.configure_project_paths.assert_called_with(
        project_name='MyProject',
        source_dir='.',
        output_root_dir=None,
        output_filename=None
    )
    
    # Check if correct build method was called
    mock_instance.build_slide_pptx.assert_called_once()
    # build_all should not be called in this mode
    mock_instance.build_all.assert_not_called()

def test_cli_video_mode_subproject(mock_movie_class):
    """Test --video option with --sub (Subproject mode) and debug flag."""
    test_args = ['slidemovie', 'ParentProj', '--sub', 'ChildProj', '--video', '--debug']
    
    mock_instance = mock_movie_class.return_value
    
    with patch.object(sys, 'argv', test_args):
        cli.main()
        
    # Verify debug settings applied
    assert mock_instance.ffmpeg_loglevel == 'info'
    assert mock_instance.show_skip is True
    
    # Verify subproject path configuration
    mock_instance.configure_subproject_paths.assert_called_with(
        parent_project_name='ParentProj',
        subproject_name='ChildProj',
        source_parent_dir='.',
        output_root_dir=None,
        output_filename=None
    )
    
    # Verify build_all was called
    mock_instance.build_all.assert_called_once()

def test_cli_override_tts_options(mock_movie_class):
    """Test if CLI arguments override TTS configuration."""
    test_args = [
        'slidemovie', 'Proj', '--video',
        '--tts-provider', 'openai',
        '--tts-model', 'gpt-4',
        '--tts-voice', 'alloy',
        '--prompt', 'New System Prompt'
    ]
    
    mock_instance = mock_movie_class.return_value
    
    with patch.object(sys, 'argv', test_args):
        cli.main()
        
    assert mock_instance.tts_provider == 'openai'
    assert mock_instance.tts_model == 'gpt-4'
    assert mock_instance.tts_voice == 'alloy'
    assert mock_instance.prompt == 'New System Prompt'

def test_cli_prompt_logic(mock_movie_class):
    """Test behavior of --prompt and --no-prompt flags."""
    mock_instance = mock_movie_class.return_value

    # Case 1: --prompt should enable usage and set text
    args_case1 = ['slidemovie', 'Proj', '--video', '--prompt', 'Custom Prompt']
    with patch.object(sys, 'argv', args_case1):
        cli.main()
    
    assert mock_instance.prompt == 'Custom Prompt'
    assert mock_instance.tts_use_prompt is True

    # Case 2: --no-prompt should disable usage
    # Reset mock for next call
    mock_movie_class.reset_mock()
    
    args_case2 = ['slidemovie', 'Proj', '--video', '--no-prompt']
    with patch.object(sys, 'argv', args_case2):
        cli.main()
        
    assert mock_instance.tts_use_prompt is False

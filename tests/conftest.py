import sys
from pathlib import Path
from unittest.mock import MagicMock

# Some Python installations resolve a previously installed ``slidemovie``
# before this checkout when pytest is launched through a global wrapper.
# Tests must always exercise the source tree being tested.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Stub heavy/optional runtime dependencies before any test module imports
# `slidemovie`, which imports `multiai_tts` (pulls in sounddevice/PortAudio)
# and `pptxtoimages` at load time. Tests never exercise the real engines;
# they patch these mocks as needed.
for _name in ("multiai_tts", "pptxtoimages", "pptxtoimages.tools"):
    sys.modules.setdefault(_name, MagicMock())

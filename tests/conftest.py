import sys
from unittest.mock import MagicMock

# Stub heavy/optional runtime dependencies before any test module imports
# `slidemovie`, which imports `multiai_tts` (pulls in sounddevice/PortAudio)
# and `pptxtoimages` at load time. Tests never exercise the real engines;
# they patch these mocks as needed.
for _name in ("multiai_tts", "pptxtoimages", "pptxtoimages.tools"):
    sys.modules.setdefault(_name, MagicMock())

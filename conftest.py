"""Pytest configuration to use local caldav library"""

import sys
from pathlib import Path

# Add the local caldav library to the path before system-wide caldav
caldav_path = Path(__file__).parent.parent / "caldav-synctokens"
if caldav_path.exists():
    sys.path.insert(0, str(caldav_path))

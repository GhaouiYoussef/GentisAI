"""Compatibility import for the packaged demo."""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("gentis_ai.demos.launch_war_room.gentis_setup")

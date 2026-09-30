"""Source-checkout entry point; installed users can run gentis demo."""

import runpy

runpy.run_module("gentis_ai.demos.launch_war_room.app", run_name="__main__")

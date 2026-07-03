import contextlib
import io
import re
import runpy
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestQuickstarts(unittest.TestCase):
    def test_examples_quick_mock_start_runs(self):
        with contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(ROOT / "examples" / "quick_mock_start.py"))

    def test_readme_quickstart_runs(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        match = re.search(
            r"# .+Quick Start.*?```python\n(.*?)```",
            readme,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        namespace = {"__name__": "__quickstart__"}
        with contextlib.redirect_stdout(io.StringIO()):
            exec(match.group(1), namespace)


if __name__ == "__main__":
    unittest.main()

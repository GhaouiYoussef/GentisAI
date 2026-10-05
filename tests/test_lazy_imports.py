import subprocess
import sys
from pathlib import Path


def test_demo_and_cli_import_without_loading_optional_provider_sdks():
    result = subprocess.run(
        [sys.executable, "-c", """
import sys
import gentis_ai.cli
from gentis_ai.demos.customer_rescue.gentis_setup import build_flow
from gentis_ai.providers import build_cloud_llm
build_cloud_llm('openai', {'OPENAI_API_KEY': 'test'}, openai_factory=lambda **kw: object())
loaded = [name for name in ('openai', 'google.genai', 'boto3', 'ollama') if name in sys.modules]
assert not loaded, loaded
"""],
        capture_output=True, text=True, timeout=60,
        cwd=Path(__file__).resolve().parents[1],
    )
    assert result.returncode == 0, result.stderr

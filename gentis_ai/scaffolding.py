from __future__ import annotations

from importlib import resources
from pathlib import Path


TEMPLATE_CHOICES = ("basic", "azure-support", "gemini-support", "support")
AZURE_SUPPORT_FILES = {
    "app.py": "app.py",
    "test_app.py": "test_app.py",
    "README.md": "README.md",
    "requirements.txt": "requirements.txt",
    ".env.example": "env.example",
    "gentis.json": "gentis.json",
    "Dockerfile": "Dockerfile",
}
GEMINI_SUPPORT_FILES = {
    "app.py": "app.py",
    "test_gemini_app.py": "test_gemini_app.py",
    "README.md": "README.md",
    "requirements.txt": "requirements.txt",
    ".env.example": "env.example",
    "gentis.json": "gentis.json",
    "Dockerfile": "Dockerfile",
}


def create_project(name: str, template: str = "basic") -> Path:
    if template not in TEMPLATE_CHOICES:
        choices = ", ".join(TEMPLATE_CHOICES)
        raise ValueError(f"Unknown template {template!r}. Choose from: {choices}.")

    root = Path(name)
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError(
            "Project destination must be new or empty; existing files are never overwritten."
        )
    root.mkdir(parents=True, exist_ok=True)
    if template == "support":
        source = resources.files("gentis_ai").joinpath(
            "templates", "provider_support.py"
        )
        (root / "app.py").write_text(
            source.read_text(encoding="utf-8"), encoding="utf-8"
        )
        (root / "gentis.json").write_text(
            '{"template": "support", "entrypoint": "app.py"}\n', encoding="utf-8"
        )
        (root / "requirements.txt").write_text(
            "gentis-ai>=0.2.2\npython-dotenv>=1.0.0\n", encoding="utf-8"
        )
        (root / ".gitignore").write_text(
            ".env\n.env.*\n__pycache__/\n.venv/\n", encoding="utf-8"
        )
        (root / "README.md").write_text(
            "# Your GentisAI Agent\n\nRun `gentis run` for an offline chat. Edit the experts and prompts in `app.py`.\n\n"
            'For a live provider, install its extra, for example `python -m pip install "gentis-ai[azure]"`, '
            "then run `gentis configure --provider azure`, `gentis doctor`, and `gentis run`. "
            "OpenAI, Gemini, and Bedrock also work with their corresponding extras and provider names.\n\n"
            "The working-directory .env is loaded; shell variables take precedence. Never commit credentials.\n",
            encoding="utf-8",
        )
    elif template == "azure-support":
        _copy_azure_support(root)
    elif template == "gemini-support":
        _copy_gemini_support(root)
    else:
        _write_basic(root, root.name)
    return root


def _copy_azure_support(root: Path) -> None:
    source_root = resources.files("gentis_ai").joinpath(
        "templates",
        "azure_support",
    )
    for output_name, source_name in AZURE_SUPPORT_FILES.items():
        content = source_root.joinpath(source_name).read_text(encoding="utf-8")
        (root / output_name).write_text(content, encoding="utf-8")


def _copy_gemini_support(root: Path) -> None:
    source_root = resources.files("gentis_ai").joinpath(
        "templates",
        "gemini_support",
    )
    for output_name, source_name in GEMINI_SUPPORT_FILES.items():
        content = source_root.joinpath(source_name).read_text(encoding="utf-8")
        (root / output_name).write_text(content, encoding="utf-8")


def _write_basic(root: Path, name: str) -> None:
    package_name = name.replace("-", "_")
    (root / "app.py").write_text(_app_template(package_name), encoding="utf-8")
    (root / "test_app.py").write_text(_test_template(), encoding="utf-8")
    (root / ".env.example").write_text("GOOGLE_API_KEY=\n", encoding="utf-8")
    (root / "Dockerfile").write_text(_dockerfile_template(), encoding="utf-8")


def _app_template(package_name: str) -> str:
    return f'''from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import MockLLM


llm = MockLLM(
    routing_rules={{"help": "support", "buy": "sales"}},
    responses={{"help": "I can help troubleshoot that.", "buy": "I can help with pricing."}},
)

support = Expert(name="support", description="Handles support requests.")
sales = Expert(name="sales", description="Handles sales requests.")

router = Router(experts=[support, sales], llm=llm)
flow = Flow(router=router, llm=llm)


def answer(message: str, session_id: str = "{package_name}-demo") -> str:
    return flow.process_turn(message, session_id=session_id).content


if __name__ == "__main__":
    print(answer("I need help with login."))
'''


def _test_template() -> str:
    return """from app import answer


def test_answer():
    assert "help" in answer("I need help with login.").lower()
"""


def _dockerfile_template() -> str:
    return """FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install gentis-ai
CMD ["python", "app.py"]
"""

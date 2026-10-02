from __future__ import annotations

import json
import keyword
from importlib import resources
from pathlib import Path

from gentis_ai.project_runtime import load_project_manifest, project_file

TEMPLATE_CHOICES = ("basic", "azure-support", "gemini-support", "support", "streamlit")
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
    if template == "streamlit":
        return init_project(root)
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
            ".env\n.env.*\n!.env.example\n__pycache__/\n.venv/\n", encoding="utf-8"
        )
        (root / ".env.example").write_text("GENTIS_PROVIDER=mock\n", encoding="utf-8")
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


STREAMLIT_FILES = (
    "app.py",
    "project.py",
    "streamlit_app.py",
    "README.md",
    "requirements.txt",
    "gentis.json",
    "agents/assistant.py",
    "tools/get_started.py",
    "prompts/assistant.md",
)


def init_project(root: Path | str = ".") -> Path:
    """Create an editable project without reading or replacing local credentials."""
    root = Path(root)
    if root.exists() and not root.is_dir():
        raise ValueError("Project destination must be a directory.")
    for relative in (*STREAMLIT_FILES, ".env.example", ".gitignore"):
        target = project_file(root, relative)
        if relative in {".env.example", ".gitignore"}:
            if target.exists() and not target.is_file():
                raise ValueError(f"Project target must be a file: {relative}.")
            continue
        if target.exists():
            raise ValueError(
                f"Project file already exists: {relative}; no files were changed."
            )
        for parent in target.parents:
            if parent == root.resolve():
                break
            if parent.exists() and not parent.is_dir():
                raise ValueError(
                    f"Project directory conflicts with an existing file: {relative}."
                )

    source = resources.files("gentis_ai").joinpath("templates", "streamlit")
    # Read all packaged assets before creating anything in the user's directory.
    contents = {
        relative: source.joinpath(relative).read_text(encoding="utf-8")
        for relative in STREAMLIT_FILES
    }
    example = source.joinpath("env.example").read_text(encoding="utf-8")
    gitignore = source.joinpath("gitignore").read_text(encoding="utf-8")
    root.mkdir(parents=True, exist_ok=True)
    for relative, content in contents.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    example_path = root / ".env.example"
    if not example_path.exists():
        example_path.write_text(example, encoding="utf-8")
    ignore_path = root / ".gitignore"
    if ignore_path.exists():
        existing = ignore_path.read_text(encoding="utf-8")
        gitignore = (
            existing.rstrip("\n") + "\n\n# GentisAI local configuration\n" + gitignore
        )
    ignore_path.write_text(gitignore, encoding="utf-8")
    return root


def _component_name(name: str) -> str:
    normalized = name.replace("-", "_").lower()
    reserved = {
        "con",
        "prn",
        "aux",
        "nul",
        *[f"com{i}" for i in range(1, 10)],
        *[f"lpt{i}" for i in range(1, 10)],
    }
    if (
        not normalized.isascii()
        or not normalized.isidentifier()
        or normalized.startswith("_")
        or keyword.iskeyword(normalized)
        or normalized in reserved
    ):
        raise ValueError(
            "Use a name starting with a letter, containing letters, digits, underscores or hyphens."
        )
    return normalized


def _new_component_files(root: Path, relatives: list[str]) -> list[Path]:
    targets = [project_file(root, relative) for relative in relatives]
    for target in targets:
        if target.exists():
            raise ValueError(
                f"Project file already exists: {target.relative_to(root.resolve())}."
            )
        if target.parent.exists() and not target.parent.is_dir():
            raise ValueError("A component directory conflicts with an existing file.")
    return targets


def add_agent(
    name: str, *, root: Path | None = None, description: str | None = None
) -> Path:
    """Register a new agent and its editable Markdown prompt."""
    root = root or Path.cwd()
    manifest = load_project_manifest(root)
    name = _component_name(name)
    if name in manifest["agents"]:
        raise ValueError(f"Agent {name!r} is already registered.")
    module, prompt = f"agents/{name}.py", f"prompts/{name}.md"
    module_path, prompt_path = _new_component_files(root, [module, prompt])
    description = description or f"Handles requests for {name.replace('_', ' ')}."
    code = (
        "from gentis_ai import Expert\n\n\n"
        "def build_agent(system_prompt: str) -> Expert:\n"
        "    return Expert(\n"
        f"        name={name!r},\n"
        f"        description={description!r},\n"
        "        system_prompt=system_prompt,\n"
        "    )\n"
    )
    for target, content in (
        (module_path, code),
        (
            prompt_path,
            f"You are the {name.replace('_', ' ')} agent. {description}\n"
            "Give clear, practical answers. Ask for missing details and do not invent facts.\n",
        ),
    ):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    manifest["agents"][name] = {"module": module, "prompt": prompt, "tools": []}
    (root / "gentis.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return module_path


def add_tool(
    name: str, *, agent: str, root: Path | None = None, description: str | None = None
) -> Path:
    """Create a query-based context tool and attach it to the selected agent."""
    root = root or Path.cwd()
    manifest = load_project_manifest(root)
    name, agent = _component_name(name), _component_name(agent)
    if agent not in manifest["agents"]:
        raise ValueError(
            f"Unknown agent {agent!r}. Add it with gentis add agent {agent}."
        )
    if name in manifest["tools"]:
        raise ValueError(f"Tool {name!r} is already registered.")
    relative = f"tools/{name}.py"
    (target,) = _new_component_files(root, [relative])
    description = description or f"Provides context for {name.replace('_', ' ')}."
    code = (
        f"def {name}(query: str) -> dict[str, str]:\n"
        f"    {description!r}\n"
        "    # Replace this placeholder with a read-only lookup using query.\n"
        "    return {\n"
        '        "status": "not_configured",\n'
        f'        "message": "Implement tools/{name}.py to return real context.",\n'
        "    }\n"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(code, encoding="utf-8")
    manifest["tools"][name] = {"module": relative, "function": name}
    manifest["agents"][agent]["tools"].append(name)
    (root / "gentis.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return target


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

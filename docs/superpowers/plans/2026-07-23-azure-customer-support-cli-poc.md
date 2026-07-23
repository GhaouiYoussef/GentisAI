# Azure Customer Support CLI POC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a CLI-generated Azure customer-support POC with exactly three agents, fast single-agent routing, measured routing latency, and an explicit credential-free mock fallback.

**Architecture:** Add a configurable routing output budget to the existing `Router`, keep project scaffolding in a focused module, and use an explicit `gentis.json` manifest for local project execution. Package the Azure support project as text resources so the generated code remains readable and independently testable.

**Tech Stack:** Python 3.10+, `argparse`, `importlib.resources`, `runpy`, GentisAI `Expert`/`Router`/`Flow`, `AzureOpenAILLM`, `MockLLM`, Pydantic, pytest/unittest.

## Global Constraints

- Preserve `gentis new NAME` as the existing basic scaffold.
- Preserve the built-in mock chat when `gentis run` finds no `gentis.json`.
- Register exactly `technical_support`, `billing_support`, and `account_support` in the Azure support POC.
- Use `account_support` as the explicit default and set `enable_hybrid=False`.
- Set `routing_max_tokens=96` in the POC while retaining `512` as the framework default.
- Use semantic `Router` classification in Azure mode; do not add regex-based production routing or a manager-agent loop.
- Select Azure only with an API key, endpoint/base URL, and deployment/model; otherwise announce the `MockLLM` fallback.
- Never print API keys, endpoints, deployment names, or raw environment values.
- Read process environment variables directly; do not load `.env` files.
- Measure routing latency from real `route_started` and `route_finished` events.
- Keep all tests offline and free of real Azure calls.

## File Map

- Modify `gentis_ai/routing/router.py`: accept and apply a validated routing token budget.
- Modify `tests/test_router.py`: prove default, custom, and invalid routing budgets.
- Create `gentis_ai/project_runner.py`: validate `gentis.json` and execute a safe local entry point.
- Create `tests/test_project_runner.py`: cover manifest absence, valid execution, unsafe paths, malformed input, and safe runtime errors.
- Create `gentis_ai/scaffolding.py`: own basic and resource-backed project creation.
- Create `gentis_ai/templates/azure_support/app.py`: generated three-agent terminal application.
- Create `gentis_ai/templates/azure_support/test_app.py`: generated offline POC tests.
- Create `gentis_ai/templates/azure_support/README.md`: generated step-by-step guide.
- Create `gentis_ai/templates/azure_support/requirements.txt`: generated dependency range.
- Create `gentis_ai/templates/azure_support/env.example`: source for generated `.env.example`.
- Create `gentis_ai/templates/azure_support/gentis.json`: generated project manifest.
- Create `gentis_ai/templates/azure_support/Dockerfile`: generated container entry point.
- Modify `pyproject.toml`: explicitly package every Azure support template asset.
- Create `tests/test_scaffolding.py`: verify generated files, provider selection, agents, routing, latency, and memory.
- Modify `gentis_ai/cli.py`: add `--template azure-support` and manifest-aware `gentis run`.
- Create `tests/test_cli.py`: exercise the public CLI behavior.
- Modify `README.md`: add the four-command Azure support POC.
- Modify `docs/getting-started.md`: add provider setup, walkthrough, prompts, and fallback explanation.

---

### Task 1: Configurable Fast Router Budget

**Files:**
- Modify: `tests/test_router.py`
- Modify: `gentis_ai/routing/router.py`

**Interfaces:**
- Consumes: existing `Router(experts, llm, ...)` construction.
- Produces: `Router(..., routing_max_tokens: int = 512)` and public `router.routing_max_tokens`.

- [ ] **Step 1: Write failing router-budget tests**

Add this helper and these methods to `tests/test_router.py`:

```python
class CapturingLLM(StaticLLM):
    def __init__(self, response):
        super().__init__(response)
        self.last_kwargs = {}

    def generate(
        self,
        messages,
        system_prompt=None,
        tools=None,
        stream=False,
        **kwargs,
    ):
        self.last_kwargs = kwargs
        return self.response
```

```python
    def test_default_routing_token_budget_is_preserved(self):
        llm = CapturingLLM(
            '{"experts":["support"],"mode":"single","confidence":0.9}'
        )
        router = Router(self.experts, llm)

        router.classify("help", "orchestrator")

        self.assertEqual(router.routing_max_tokens, 512)
        self.assertEqual(llm.last_kwargs["max_tokens"], 512)

    def test_custom_routing_token_budget_is_forwarded(self):
        llm = CapturingLLM(
            '{"experts":["support"],"mode":"single","confidence":0.9}'
        )
        router = Router(self.experts, llm, routing_max_tokens=96)

        router.classify("help", "orchestrator")

        self.assertEqual(router.routing_max_tokens, 96)
        self.assertEqual(llm.last_kwargs["max_tokens"], 96)

    def test_routing_token_budget_must_be_positive(self):
        with self.assertRaisesRegex(
            ValueError,
            "routing_max_tokens must be at least 1",
        ):
            Router(self.experts, self.mock_llm, routing_max_tokens=0)
```

- [ ] **Step 2: Run the tests and verify the new contract fails**

Run:

```powershell
python -m pytest tests/test_router.py -v
```

Expected: the new tests fail because `Router` does not accept `routing_max_tokens`.

- [ ] **Step 3: Implement the routing budget**

Append the argument in `gentis_ai/routing/router.py` so existing positional calls remain valid:

```python
    def __init__(
        self,
        experts: list[Expert],
        llm: BaseLLM | None = None,
        default_expert: Expert | None = None,
        enable_hybrid: bool = True,
        rules: dict[str, str | list[str]] | None = None,
        routing_strategy: RoutingStrategy | None = None,
        confidence_threshold: float = 0.35,
        fallback_strategy: str = "current",
        routing_max_tokens: int = 512,
    ):
        if routing_max_tokens < 1:
            raise ValueError("routing_max_tokens must be at least 1.")

        self.experts = {expert.name: expert for expert in experts}
        self.llm = llm
        self.enable_hybrid = enable_hybrid
        self.confidence_threshold = confidence_threshold
        self.fallback_strategy = fallback_strategy
        self.routing_max_tokens = routing_max_tokens
```

Replace the fixed generation argument:

```python
            raw_output = self.llm.generate(
                messages=[
                    Message(
                        role="user",
                        content=self._build_prompt(
                            user_message,
                            current_expert_name,
                            recent_history or [],
                        ),
                    )
                ],
                max_tokens=self.routing_max_tokens,
            )
```

- [ ] **Step 4: Verify router tests and lint**

Run:

```powershell
python -m pytest tests/test_router.py -v
python -m ruff check gentis_ai/routing/router.py tests/test_router.py
```

Expected: all router tests pass and Ruff reports no errors.

- [ ] **Step 5: Commit the router contract**

```powershell
git add gentis_ai/routing/router.py tests/test_router.py
git commit -m "feat: add configurable routing token budget"
```

---

### Task 2: Safe Manifest-Based Project Runner

**Files:**
- Create: `tests/test_project_runner.py`
- Create: `gentis_ai/project_runner.py`

**Interfaces:**
- Consumes: a project directory and optional `gentis.json`.
- Produces: `ProjectRunError` and `run_local_project(root: Path | None = None) -> bool`.

- [ ] **Step 1: Write failing project-runner tests**

Create `tests/test_project_runner.py`:

```python
import json
from pathlib import Path

import pytest

from gentis_ai.project_runner import ProjectRunError, run_local_project


def test_no_manifest_preserves_builtin_runner(tmp_path: Path):
    (tmp_path / "app.py").write_text(
        "raise AssertionError('must not execute')\n",
        encoding="utf-8",
    )

    assert run_local_project(tmp_path) is False


def test_valid_manifest_executes_relative_entrypoint(tmp_path: Path):
    marker = tmp_path / "ran.txt"
    (tmp_path / "gentis.json").write_text(
        json.dumps({"template": "azure-support", "entrypoint": "app.py"}),
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('yes', encoding='utf-8')\n",
        encoding="utf-8",
    )

    assert run_local_project(tmp_path) is True
    assert marker.read_text(encoding="utf-8") == "yes"


@pytest.mark.parametrize(
    "entrypoint",
    ["../outside.py", str(Path.cwd().anchor + "outside.py")],
)
def test_manifest_rejects_paths_outside_project(tmp_path: Path, entrypoint: str):
    (tmp_path / "gentis.json").write_text(
        json.dumps({"entrypoint": entrypoint}),
        encoding="utf-8",
    )

    with pytest.raises(ProjectRunError, match="entrypoint must be a relative file"):
        run_local_project(tmp_path)


def test_manifest_rejects_malformed_json(tmp_path: Path):
    (tmp_path / "gentis.json").write_text("{", encoding="utf-8")

    with pytest.raises(ProjectRunError, match="manifest is not valid JSON"):
        run_local_project(tmp_path)


def test_missing_entrypoint_fails_cleanly(tmp_path: Path):
    (tmp_path / "gentis.json").write_text(
        json.dumps({"template": "azure-support"}),
        encoding="utf-8",
    )

    with pytest.raises(ProjectRunError, match="entrypoint must be a relative file"):
        run_local_project(tmp_path)


def test_project_exception_is_wrapped_without_original_detail(tmp_path: Path):
    (tmp_path / "gentis.json").write_text(
        json.dumps({"entrypoint": "app.py"}),
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text(
        "raise RuntimeError('secret-runtime-detail')\n",
        encoding="utf-8",
    )

    with pytest.raises(ProjectRunError) as error:
        run_local_project(tmp_path)

    assert str(error.value) == (
        "Project failed to run. Run the entrypoint directly for a traceback."
    )
    assert "secret-runtime-detail" not in str(error.value)
```

- [ ] **Step 2: Run the new tests and verify the module is missing**

Run:

```powershell
python -m pytest tests/test_project_runner.py -v
```

Expected: collection fails with `ModuleNotFoundError: No module named 'gentis_ai.project_runner'`.

- [ ] **Step 3: Implement the project runner**

Create `gentis_ai/project_runner.py`:

```python
from __future__ import annotations

import json
import runpy
from pathlib import Path


class ProjectRunError(RuntimeError):
    """Raised when a local GentisAI project cannot be executed safely."""


def run_local_project(root: Path | None = None) -> bool:
    project_root = (root or Path.cwd()).resolve()
    manifest_path = project_root / "gentis.json"
    if not manifest_path.is_file():
        return False

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectRunError(
            "Gentis project manifest is not valid JSON."
        ) from exc

    entrypoint = manifest.get("entrypoint") if isinstance(manifest, dict) else None
    if not isinstance(entrypoint, str) or not entrypoint.strip():
        raise ProjectRunError(
            "Project entrypoint must be a relative file inside the project."
        )

    entrypoint_path = Path(entrypoint)
    candidate = (project_root / entrypoint_path).resolve()
    if entrypoint_path.is_absolute() or not candidate.is_relative_to(project_root):
        raise ProjectRunError(
            "Project entrypoint must be a relative file inside the project."
        )
    if not candidate.is_file():
        raise ProjectRunError("Project entrypoint does not exist.")

    try:
        runpy.run_path(str(candidate), run_name="__main__")
    except Exception as exc:
        raise ProjectRunError(
            "Project failed to run. Run the entrypoint directly for a traceback."
        ) from exc
    return True
```

- [ ] **Step 4: Verify project-runner tests and lint**

Run:

```powershell
python -m pytest tests/test_project_runner.py -v
python -m ruff check gentis_ai/project_runner.py tests/test_project_runner.py
```

Expected: all project-runner tests pass and Ruff reports no errors.

- [ ] **Step 5: Commit the project runner**

```powershell
git add gentis_ai/project_runner.py tests/test_project_runner.py
git commit -m "feat: run manifested Gentis projects safely"
```

---

### Task 3: Azure Customer Support Scaffold

**Files:**
- Create: `tests/test_scaffolding.py`
- Create: `gentis_ai/scaffolding.py`
- Create: `gentis_ai/templates/azure_support/app.py`
- Create: `gentis_ai/templates/azure_support/test_app.py`
- Create: `gentis_ai/templates/azure_support/README.md`
- Create: `gentis_ai/templates/azure_support/requirements.txt`
- Create: `gentis_ai/templates/azure_support/env.example`
- Create: `gentis_ai/templates/azure_support/gentis.json`
- Create: `gentis_ai/templates/azure_support/Dockerfile`
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: `Router(..., routing_max_tokens=96)`, `Flow.stream_turn()`, `AzureOpenAILLM`, and `MockLLM`.
- Produces: `TEMPLATE_CHOICES`, `create_project(name: str, template: str = "basic") -> Path`, plus generated `build_llm`, `build_flow`, `stream_support_turn`, and `main`.

- [ ] **Step 1: Write failing scaffold and generated-app tests**

Create `tests/test_scaffolding.py`:

```python
from __future__ import annotations

import importlib.util
import io
from pathlib import Path
from types import ModuleType

import pytest

from gentis_ai.llm import AzureOpenAILLM, MockLLM
from gentis_ai.scaffolding import TEMPLATE_CHOICES, create_project


AZURE_FILES = {
    "app.py",
    "test_app.py",
    "README.md",
    "requirements.txt",
    ".env.example",
    "gentis.json",
    "Dockerfile",
}


def load_generated_app(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("generated_support_app", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_template_choices_are_stable():
    assert TEMPLATE_CHOICES == ("basic", "azure-support")


def test_basic_template_keeps_existing_files(tmp_path: Path):
    root = create_project(str(tmp_path / "basic"))

    assert {path.name for path in root.iterdir()} == {
        "app.py",
        "test_app.py",
        ".env.example",
        "Dockerfile",
    }
    assert (root / ".env.example").read_text(encoding="utf-8") == (
        "GOOGLE_API_KEY=\n"
    )


def test_azure_support_template_generates_complete_project(tmp_path: Path):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )

    assert {path.name for path in root.iterdir()} == AZURE_FILES
    assert '"template": "azure-support"' in (
        root / "gentis.json"
    ).read_text(encoding="utf-8")
    compile((root / "app.py").read_text(encoding="utf-8"), "app.py", "exec")
    compile(
        (root / "test_app.py").read_text(encoding="utf-8"),
        "test_app.py",
        "exec",
    )


def test_missing_azure_config_uses_mock_and_names_missing_categories(
    tmp_path: Path,
):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")
    messages = []

    llm, provider = app.build_llm({}, output=messages.append)

    assert isinstance(llm, MockLLM)
    assert provider == "local mock"
    assert messages == [
        "[GentisAI] Azure OpenAI is not fully configured; "
        "using the local mock provider.",
        "[GentisAI] Missing: API key, endpoint, deployment.",
    ]


def test_partial_config_never_prints_environment_values(tmp_path: Path):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")
    messages = []
    environment = {
        "AZURE_OPENAI_API_KEY": "top-secret-key",
        "AZURE_OPENAI_ENDPOINT": "https://private.example",
    }

    llm, provider = app.build_llm(environment, output=messages.append)

    rendered = "\n".join(messages)
    assert isinstance(llm, MockLLM)
    assert provider == "local mock"
    assert "deployment" in rendered
    assert "top-secret-key" not in rendered
    assert "https://private.example" not in rendered


def test_complete_config_selects_azure_without_printing_values(tmp_path: Path):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")
    messages = []
    environment = {
        "AZURE_OPENAI_API_KEY": "top-secret-key",
        "AZURE_OPENAI_ENDPOINT": "https://private.example",
        "AZURE_OPENAI_DEPLOYMENT": "private-deployment",
    }

    llm, provider = app.build_llm(
        environment,
        azure_client=object(),
        output=messages.append,
    )

    rendered = "\n".join(messages)
    assert isinstance(llm, AzureOpenAILLM)
    assert provider == "Azure OpenAI"
    assert rendered == "[GentisAI] Provider: Azure OpenAI."
    assert "top-secret-key" not in rendered
    assert "https://private.example" not in rendered
    assert "private-deployment" not in rendered


def test_complete_config_accepts_base_url_and_model_aliases(tmp_path: Path):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")

    llm, provider = app.build_llm(
        {
            "AZURE_OPENAI_API_KEY": "key",
            "AZURE_OPENAI_BASE_URL": "https://example/openai/v1",
            "AZURE_OPENAI_MODEL": "deployment-alias",
        },
        azure_client=object(),
        output=lambda _: None,
    )

    assert isinstance(llm, AzureOpenAILLM)
    assert provider == "Azure OpenAI"


def test_complete_invalid_azure_config_does_not_fall_back(
    tmp_path: Path,
    monkeypatch,
):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")
    messages = []

    def fail_azure(**kwargs):
        raise ValueError("invalid Azure setup")

    monkeypatch.setattr(app, "AzureOpenAILLM", fail_azure)
    environment = {
        "AZURE_OPENAI_API_KEY": "key",
        "AZURE_OPENAI_ENDPOINT": "https://example",
        "AZURE_OPENAI_DEPLOYMENT": "deployment",
    }

    with pytest.raises(ValueError, match="invalid Azure setup"):
        app.build_llm(environment, output=messages.append)

    assert messages == []


def test_generated_flow_has_exactly_three_single_route_agents(tmp_path: Path):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")
    llm, _ = app.build_llm({}, output=lambda _: None)

    flow = app.build_flow(llm)

    assert set(flow.router.experts) == {
        "technical_support",
        "billing_support",
        "account_support",
    }
    assert flow.router.default_expert.name == "account_support"
    assert flow.router.enable_hybrid is False
    assert flow.router.routing_max_tokens == 96


def test_mock_routes_each_support_domain_and_keeps_follow_up(tmp_path: Path):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")
    llm, _ = app.build_llm({}, output=lambda _: None)
    flow = app.build_flow(llm)

    billing = flow.process_turn(
        "I was charged twice this month.",
        session_id="billing-session",
    )
    technical = flow.process_turn(
        "The dashboard crashes when I upload a file.",
        session_id="technical-session",
    )
    account = flow.process_turn(
        "I cannot sign in to my account.",
        session_id="account-session",
    )
    follow_up = flow.process_turn(
        "Can you explain the next step?",
        session_id="billing-session",
    )

    assert billing.agent_name == "billing_support"
    assert technical.agent_name == "technical_support"
    assert account.agent_name == "account_support"
    assert follow_up.agent_name == "billing_support"


def test_route_latency_is_measured_from_events(tmp_path: Path):
    root = create_project(
        str(tmp_path / "customer-support"),
        template="azure-support",
    )
    app = load_generated_app(root / "app.py")
    llm, _ = app.build_llm({}, output=lambda _: None)
    flow = app.build_flow(llm)
    stream = io.StringIO()
    ticks = iter([10.0, 10.184])

    content = app.stream_support_turn(
        flow,
        "I was charged twice this month.",
        stream=stream,
        clock=lambda: next(ticks),
    )

    rendered = stream.getvalue()
    assert "[route] billing_support selected in 184 ms" in rendered
    assert "[agent] billing_support" in rendered
    assert content
```

- [ ] **Step 2: Run scaffold tests and verify imports fail**

Run:

```powershell
python -m pytest tests/test_scaffolding.py -v
```

Expected: collection fails with `ModuleNotFoundError: No module named 'gentis_ai.scaffolding'`.

- [ ] **Step 3: Add the scaffold service**

Create `gentis_ai/scaffolding.py`:

```python
from __future__ import annotations

from importlib import resources
from pathlib import Path


TEMPLATE_CHOICES = ("basic", "azure-support")
AZURE_SUPPORT_FILES = {
    "app.py": "app.py",
    "test_app.py": "test_app.py",
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
    root.mkdir(parents=True, exist_ok=True)
    if template == "azure-support":
        _copy_azure_support(root)
    else:
        _write_basic(root, name)
    return root


def _copy_azure_support(root: Path) -> None:
    source_root = resources.files("gentis_ai").joinpath(
        "templates",
        "azure_support",
    )
    for output_name, source_name in AZURE_SUPPORT_FILES.items():
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
    return '''from app import answer


def test_answer():
    assert "help" in answer("I need help with login.").lower()
'''


def _dockerfile_template() -> str:
    return """FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install gentis-ai
CMD ["python", "app.py"]
"""
```

- [ ] **Step 4: Create the generated customer-support application**

Create `gentis_ai/templates/azure_support/app.py`:

```python
from __future__ import annotations

import os
import sys
import time
from collections.abc import Callable, Mapping
from typing import Any, TextIO

from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import AzureOpenAILLM, BaseLLM, MockLLM


SESSION_ID = "azure-support-poc"


def build_llm(
    environment: Mapping[str, str] | None = None,
    *,
    azure_client: Any = None,
    output: Callable[[str], None] = print,
) -> tuple[BaseLLM, str]:
    env = os.environ if environment is None else environment
    api_key = env.get("AZURE_OPENAI_API_KEY", "").strip()
    endpoint = env.get("AZURE_OPENAI_ENDPOINT", "").strip()
    base_url = env.get("AZURE_OPENAI_BASE_URL", "").strip()
    deployment = (
        env.get("AZURE_OPENAI_DEPLOYMENT", "").strip()
        or env.get("AZURE_OPENAI_MODEL", "").strip()
    )

    missing = []
    if not api_key:
        missing.append("API key")
    if not endpoint and not base_url:
        missing.append("endpoint")
    if not deployment:
        missing.append("deployment")

    if missing:
        output(
            "[GentisAI] Azure OpenAI is not fully configured; "
            "using the local mock provider."
        )
        output(f"[GentisAI] Missing: {', '.join(missing)}.")
        return _build_mock_llm(), "local mock"

    kwargs: dict[str, Any] = {
        "api_key": api_key,
        "model_name": deployment,
    }
    if azure_client is not None:
        kwargs["client"] = azure_client
    if endpoint:
        kwargs["azure_endpoint"] = endpoint
    else:
        kwargs["base_url"] = base_url

    llm = AzureOpenAILLM(**kwargs)
    output("[GentisAI] Provider: Azure OpenAI.")
    return llm, "Azure OpenAI"


def _build_mock_llm() -> MockLLM:
    return MockLLM(
        routing_rules={
            "charged": "billing_support",
            "invoice": "billing_support",
            "refund": "billing_support",
            "crash": "technical_support",
            "error": "technical_support",
            "upload": "technical_support",
            "sign in": "account_support",
            "login": "account_support",
            "account": "account_support",
        },
        responses={
            "charged": (
                "I found the billing issue. I will help verify the duplicate "
                "charge and explain the refund path."
            ),
            "invoice": "I can help review the invoice and payment details.",
            "refund": "I will explain the refund status and next step.",
            "crash": (
                "Let us isolate the crash, capture the failing step, and try "
                "a safe workaround."
            ),
            "upload": "I will help troubleshoot the upload failure.",
            "sign in": (
                "I will help restore access while keeping the account secure."
            ),
            "login": "I will help restore access to the account.",
            "account": "I can help with the account and access settings.",
        },
        default_response=(
            "I remember the current support context and will guide the next step."
        ),
    )


def build_flow(llm: BaseLLM) -> Flow:
    technical = Expert(
        name="technical_support",
        description="Application errors, bugs, outages, uploads, and troubleshooting.",
        system_prompt=(
            "You are a concise technical support agent. Diagnose safely, ask for "
            "the minimum useful detail, and give ordered troubleshooting steps."
        ),
    )
    billing = Expert(
        name="billing_support",
        description="Invoices, charges, refunds, subscriptions, and payments.",
        system_prompt=(
            "You are a concise billing support agent. Explain billing actions "
            "clearly and never invent account transactions."
        ),
    )
    account = Expert(
        name="account_support",
        description="Login, profile, access, and general account questions.",
        system_prompt=(
            "You are a concise account support agent. Protect account security "
            "and provide clear access-recovery steps."
        ),
    )
    router = Router(
        experts=[technical, billing, account],
        llm=llm,
        default_expert=account,
        enable_hybrid=False,
        fallback_strategy="default",
        routing_max_tokens=96,
    )
    return Flow(router=router, llm=llm)


def stream_support_turn(
    flow: Flow,
    message: str,
    *,
    stream: TextIO | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> str:
    destination = stream or sys.stdout
    route_started_at = 0.0
    final_content = ""

    for event in flow.stream_turn(message, session_id=SESSION_ID):
        if event.type == "route_started":
            route_started_at = clock()
        elif event.type == "route_finished":
            elapsed_ms = round((clock() - route_started_at) * 1000)
            decision = event.data["decision"]
            selected = decision["experts"][0]
            destination.write(f"[route] {selected} selected in {elapsed_ms} ms\n")
        elif event.type == "expert_started":
            destination.write(f"[agent] {event.agent_name}\n")
            destination.write("Agent: ")
        elif event.type == "token":
            destination.write(event.content)
            destination.flush()
        elif event.type == "error":
            destination.write("\n[error] The provider could not complete this turn.")
        elif event.type == "final":
            final_content = event.content

    destination.write("\n")
    return final_content


def main() -> int:
    try:
        llm, provider = build_llm()
    except (ImportError, ValueError):
        print(
            "[GentisAI] Azure provider setup failed. Verify the Azure extra "
            "and environment variables.",
            file=sys.stderr,
        )
        return 1

    flow = build_flow(llm)
    print(f"[GentisAI] Customer Support POC ready ({provider}).")
    print("[GentisAI] Agents: technical_support, billing_support, account_support")
    print("Try: I was charged twice this month.")
    print("Type 'exit' to quit.")

    while True:
        try:
            message = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return 0

        if message.lower() in {"exit", "quit"}:
            print("Goodbye.")
            return 0
        if not message:
            print("Please enter a support question.")
            continue
        stream_support_turn(flow, message)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Create the generated project tests**

Create `gentis_ai/templates/azure_support/test_app.py`:

```python
import io
import unittest

from gentis_ai.llm import MockLLM

from app import build_flow, build_llm, stream_support_turn


class AzureSupportPOCTests(unittest.TestCase):
    def setUp(self):
        self.messages = []
        self.llm, self.provider = build_llm(
            {},
            output=self.messages.append,
        )
        self.flow = build_flow(self.llm)

    def test_runs_without_azure_credentials(self):
        self.assertIsInstance(self.llm, MockLLM)
        self.assertEqual(self.provider, "local mock")
        self.assertIn("using the local mock provider", self.messages[0])

    def test_registers_exactly_three_agents(self):
        self.assertEqual(
            set(self.flow.router.experts),
            {
                "technical_support",
                "billing_support",
                "account_support",
            },
        )

    def test_routes_billing_question(self):
        response = self.flow.process_turn(
            "I was charged twice this month.",
            session_id="generated-test",
        )
        self.assertEqual(response.agent_name, "billing_support")

    def test_streams_visible_route_and_agent(self):
        output = io.StringIO()
        ticks = iter([2.0, 2.1])

        content = stream_support_turn(
            self.flow,
            "The dashboard crashes when I upload a file.",
            stream=output,
            clock=lambda: next(ticks),
        )

        self.assertIn(
            "[route] technical_support selected in 100 ms",
            output.getvalue(),
        )
        self.assertIn("[agent] technical_support", output.getvalue())
        self.assertTrue(content)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 6: Create the generated guide and support files**

Create `gentis_ai/templates/azure_support/README.md`:

````markdown
# GentisAI Azure Customer Support POC

This project shows how GentisAI routes each customer message to exactly one
specialist: `technical_support`, `billing_support`, or `account_support`.

## 1. Install

```bash
pip install "gentis-ai[azure]"
```

## 2. Run Immediately

```bash
gentis run
```

Without complete Azure configuration, the POC tells you it is using the local
deterministic mock. No credential is required for this first run.

## 3. Configure Azure OpenAI

Use an Azure deployment name, not only a model-family name.

PowerShell:

```powershell
$env:AZURE_OPENAI_API_KEY = "your-key"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com"
$env:AZURE_OPENAI_DEPLOYMENT = "your-deployment"
gentis run
```

POSIX shell:

```bash
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT="your-deployment"
gentis run
```

`AZURE_OPENAI_BASE_URL` can replace `AZURE_OPENAI_ENDPOINT`, and
`AZURE_OPENAI_MODEL` can replace `AZURE_OPENAI_DEPLOYMENT`.

## 4. Try The Three Routes

```text
I was charged twice this month.
The dashboard crashes when I upload a file.
I cannot sign in to my account.
```

Then ask `Can you explain the next step?` in the same session to see memory.

## 5. Read The Five Building Blocks

1. `build_llm()` selects Azure or the announced local fallback.
2. `build_flow()` defines three focused support agents.
3. `Router(..., routing_max_tokens=96, enable_hybrid=False)` makes one compact
   semantic routing decision in Azure mode.
4. `Flow` invokes only the selected agent and maintains the session.
5. `stream_support_turn()` displays measured routing latency and response tokens.

The mock provider uses deterministic fixtures only for an offline demonstration.
Azure mode uses the experts' descriptions for semantic routing. The displayed
milliseconds are observed routing latency, not total response latency or a
universal benchmark.

## Test

```bash
python -m pip install -r requirements.txt
python -m pytest -v
```

## Troubleshooting

- Mock mode appears: set an API key, endpoint/base URL, and deployment/model.
- Azure setup fails: verify `gentis-ai[azure]` is installed.
- Requests fail: confirm the deployment name and resource access in Azure.
- Run `python app.py` directly when you need a full local traceback.

The application never prints configured environment values.
````

Create `gentis_ai/templates/azure_support/requirements.txt`:

```text
gentis-ai[azure]>=0.2.1,<0.3
pytest>=8,<9
```

Create `gentis_ai/templates/azure_support/env.example`:

```text
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_BASE_URL=
AZURE_OPENAI_DEPLOYMENT=
AZURE_OPENAI_MODEL=
```

Create `gentis_ai/templates/azure_support/gentis.json`:

```json
{
  "template": "azure-support",
  "entrypoint": "app.py"
}
```

Create `gentis_ai/templates/azure_support/Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "app.py"]
```

- [ ] **Step 7: Include the resource files in built packages**

Update the existing package-data entry in `pyproject.toml`:

```toml
[tool.setuptools.package-data]
"gentis_ai" = [
    "prompts/**/*",
    "templates/**/*",
    "templates/azure_support/*",
]
```

- [ ] **Step 8: Run generated-project tests**

Run:

```powershell
python -m pytest tests/test_scaffolding.py -v
python -m ruff check gentis_ai/scaffolding.py gentis_ai/templates/azure_support/app.py gentis_ai/templates/azure_support/test_app.py tests/test_scaffolding.py
```

Expected: all scaffold tests pass and Ruff reports no errors.

- [ ] **Step 9: Generate a project and run its own tests**

Run:

```powershell
$pocRoot = Join-Path $env:TEMP ("gentis-azure-support-plan-" + [guid]::NewGuid())
python -c "from gentis_ai.scaffolding import create_project; create_project(r'$pocRoot', 'azure-support')"
python -m pytest "$pocRoot/test_app.py" -v
```

Expected: four generated-project tests pass without Azure credentials or network access.

- [ ] **Step 10: Commit the scaffold**

```powershell
git add gentis_ai/scaffolding.py gentis_ai/templates/azure_support tests/test_scaffolding.py pyproject.toml
git commit -m "feat: add Azure support POC scaffold"
```

---

### Task 4: Public CLI Integration

**Files:**
- Create: `tests/test_cli.py`
- Modify: `gentis_ai/cli.py`

**Interfaces:**
- Consumes: `TEMPLATE_CHOICES`, `create_project`, `ProjectRunError`, and `run_local_project`.
- Produces: `gentis new NAME --template azure-support` and manifest-aware `gentis run`.

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_cli.py`:

```python
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from gentis_ai.cli import main


def test_new_defaults_to_basic_template(tmp_path: Path, capsys):
    project = tmp_path / "basic"

    with patch.object(sys, "argv", ["gentis", "new", str(project)]):
        main()

    assert (project / "app.py").is_file()
    assert not (project / "gentis.json").exists()
    assert f"Created {project}" in capsys.readouterr().out


def test_new_azure_support_prints_next_steps(tmp_path: Path, capsys):
    project = tmp_path / "customer-support"

    with patch.object(
        sys,
        "argv",
        [
            "gentis",
            "new",
            str(project),
            "--template",
            "azure-support",
        ],
    ):
        main()

    output = capsys.readouterr().out
    assert (project / "gentis.json").is_file()
    assert f"Created {project}" in output
    assert f"cd {project}" in output
    assert "gentis run" in output


def test_new_rejects_unknown_template(tmp_path: Path):
    with patch.object(
        sys,
        "argv",
        [
            "gentis",
            "new",
            str(tmp_path / "invalid"),
            "--template",
            "unknown",
        ],
    ):
        with pytest.raises(SystemExit) as error:
            main()

    assert error.value.code == 2


def test_run_executes_manifested_project(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "gentis.json").write_text(
        json.dumps({"entrypoint": "app.py"}),
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text(
        "print('manifest-project-ran')\n",
        encoding="utf-8",
    )

    with patch.object(sys, "argv", ["gentis", "run"]):
        main()

    assert "manifest-project-ran" in capsys.readouterr().out


def test_run_without_manifest_keeps_builtin_chat(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with (
        patch.object(sys, "argv", ["gentis", "run"]),
        patch("gentis_ai.cli.run_mock_chat") as mock_chat,
    ):
        main()

    mock_chat.assert_called_once_with()


def test_run_reports_safe_project_error(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "gentis.json").write_text("{", encoding="utf-8")

    with patch.object(sys, "argv", ["gentis", "run"]):
        with pytest.raises(SystemExit) as error:
            main()

    assert error.value.code == 1
    assert "manifest is not valid JSON" in capsys.readouterr().err
```

- [ ] **Step 2: Run CLI tests and verify the new options fail**

Run:

```powershell
python -m pytest tests/test_cli.py -v
```

Expected: tests fail because `--template` and manifested project execution are not wired into `main`.

- [ ] **Step 3: Wire scaffolding and project execution into the CLI**

Update the imports at the top of `gentis_ai/cli.py`:

```python
from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import MockLLM
from gentis_ai.project_runner import ProjectRunError, run_local_project
from gentis_ai.scaffolding import TEMPLATE_CHOICES, create_project
```

Add the template option:

```python
    new_parser = subcommands.add_parser("new", help="Create a new GentisAI POC.")
    new_parser.add_argument("name")
    new_parser.add_argument(
        "--template",
        choices=TEMPLATE_CHOICES,
        default="basic",
        help="Project template (default: basic).",
    )
```

Replace command dispatch with:

```python
    args = parser.parse_args()
    if args.command == "new":
        root = create_project(args.name, template=args.template)
        print(f"Created {root}")
        if args.template == "azure-support":
            print("Next:")
            print(f"  cd {root}")
            print("  gentis run")
    elif args.command == "run":
        try:
            if run_local_project():
                return
        except ProjectRunError as exc:
            parser.exit(1, f"gentis run: {exc}\n")
        run_mock_chat()
    elif args.command == "eval":
        run_eval()
    elif args.command == "bench":
        run_bench()
```

Delete the old `create_project`, `_app_template`, `_test_template`, and `_dockerfile_template` definitions from `gentis_ai/cli.py`. Remove the unused `Path` import.

- [ ] **Step 4: Verify CLI tests, existing CLI commands, and lint**

Run:

```powershell
python -m pytest tests/test_cli.py tests/test_project_runner.py tests/test_scaffolding.py -v
python -m ruff check gentis_ai/cli.py tests/test_cli.py
python -m gentis_ai.cli eval
python -m gentis_ai.cli bench
```

Expected: all tests pass, Ruff reports no errors, eval reports accuracy `1.0`, and bench completes ten offline runs.

- [ ] **Step 5: Commit the CLI integration**

```powershell
git add gentis_ai/cli.py tests/test_cli.py
git commit -m "feat: add Azure support CLI template"
```

---

### Task 5: User Documentation And Release Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/getting-started.md`

**Interfaces:**
- Consumes: the finished `gentis new ... --template azure-support` and `gentis run` commands.
- Produces: a copyable top-level quickstart and a detailed provider guide.

- [ ] **Step 1: Add the root README quickstart**

Add this section immediately after the existing CLI command block in `README.md`:

````markdown
### Azure Customer Support POC

Create a three-agent customer-support demo in four commands:

```bash
pip install "gentis-ai[azure]"
gentis new customer-support --template azure-support
cd customer-support
gentis run
```

The POC routes each message to Technical, Billing, or Account Support. If the
Azure API key, endpoint, and deployment are not all configured, it clearly
announces the local mock fallback and still runs.
````

- [ ] **Step 2: Add the detailed getting-started walkthrough**

Append this section after `## CLI` in `docs/getting-started.md`:

````markdown
## Azure Customer Support POC

```bash
pip install "gentis-ai[azure]"
gentis new customer-support --template azure-support
cd customer-support
gentis run
```

The generated project contains three agents:

- `technical_support` for errors, outages, uploads, and troubleshooting.
- `billing_support` for invoices, charges, refunds, and payments.
- `account_support` for login, access, profile, and fallback questions.

The router performs one compact semantic classification with a 96-token output
budget, hybrid routing disabled, and only the selected agent invoked. The CLI
prints the actual time between `route_started` and `route_finished`; it does not
claim a fixed latency.

Run immediately without credentials to use the announced local mock. To use
Azure OpenAI, set:

```text
AZURE_OPENAI_API_KEY
AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_BASE_URL
AZURE_OPENAI_DEPLOYMENT or AZURE_OPENAI_MODEL
```

The deployment variable must identify an Azure deployment. The application
never prints configured values and does not load `.env` files.

Try these prompts:

```text
I was charged twice this month.
The dashboard crashes when I upload a file.
I cannot sign in to my account.
Can you explain the next step?
```

The first three demonstrate each route. The final prompt demonstrates the
stable CLI session.
````

- [ ] **Step 3: Verify documentation matches the public contract**

Run:

```powershell
rg -n "azure-support|routing_max_tokens|AZURE_OPENAI" README.md docs/getting-started.md gentis_ai/templates/azure_support
rg -n "api[_ -]?key.*print|endpoint.*print|deployment.*print" gentis_ai/templates/azure_support/app.py
```

Expected: the first command finds the documented template and Azure variables; the second command finds no secret-printing code.

- [ ] **Step 4: Run the complete automated verification**

Run:

```powershell
python -m pytest -q
python -m ruff check gentis_ai tests demos --exclude tests/sanity_check.py
python -m build --no-isolation
python -m twine check dist/gentis_ai-0.2.1*
```

Expected: the full suite passes, Ruff reports no new errors, both distributions build, and Twine reports `PASSED`.

- [ ] **Step 5: Verify the wheel contains the Azure template**

Run:

```powershell
python -c "import glob, zipfile; wheel=glob.glob('dist/gentis_ai-0.2.1-*.whl')[-1]; names=zipfile.ZipFile(wheel).namelist(); required=['gentis_ai/templates/azure_support/app.py','gentis_ai/templates/azure_support/README.md','gentis_ai/templates/azure_support/env.example','gentis_ai/templates/azure_support/gentis.json']; missing=[name for name in required if name not in names]; assert not missing, missing; print('Azure support template packaged')"
```

Expected: `Azure support template packaged`.

- [ ] **Step 6: Run the final credential-free CLI smoke test**

Run from a new temporary directory:

```powershell
$smokeRoot = Join-Path $env:TEMP ("gentis-azure-support-smoke-" + [guid]::NewGuid())
gentis new $smokeRoot --template azure-support
Push-Location $smokeRoot
"I was charged twice this month.`nexit" | gentis run
Pop-Location
```

Expected output contains:

```text
[GentisAI] Azure OpenAI is not fully configured; using the local mock provider.
[route] billing_support selected in
[agent] billing_support
Goodbye.
```

- [ ] **Step 7: Commit documentation**

```powershell
git add README.md docs/getting-started.md
git commit -m "docs: add Azure support POC quickstart"
```

- [ ] **Step 8: Confirm the branch is clean**

Run:

```powershell
git status --short --branch
```

Expected: `## codex/demos` with no modified or untracked files.

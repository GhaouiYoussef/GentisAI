"""Local setup and diagnostics; never send a request or print credentials."""

from __future__ import annotations

import getpass
import os
from pathlib import Path

from gentis_ai.config import load_environment
from gentis_ai.providers import ConfigurationError, ProviderSettings


_PROVIDER_FIELDS = {
    "mock": [],
    "openai": [
        ("OPENAI_API_KEY", ""),
        ("OPENAI_MODEL", "gpt-4o-mini"),
        ("OPENAI_BASE_URL", ""),
    ],
    "azure": [
        ("AZURE_OPENAI_API_KEY", ""),
        ("AZURE_OPENAI_ENDPOINT", ""),
        ("AZURE_OPENAI_DEPLOYMENT", ""),
        ("AZURE_OPENAI_API_VERSION", ""),
    ],
    "gemini": [("GOOGLE_API_KEY", ""), ("GEMINI_MODEL", "gemini-2.5-flash")],
    "bedrock": [("AWS_REGION", ""), ("AWS_BEDROCK_MODEL_ID", "")],
}
_BUDGET_DEFAULTS = {
    "GENTIS_MAX_TOKENS": "4096",
    "GENTIS_ROUTING_MAX_TOKENS": "1024",
    "GENTIS_TIMEOUT": "45",
}


def configuration_example(provider: str = "mock") -> str:
    """Return a shareable template without reading configuration or credentials."""
    if provider not in _PROVIDER_FIELDS:
        raise ConfigurationError("Unknown provider.")
    lines = [
        "# Copy settings into .env and enter your own credentials there.",
        "# Keep .env out of version control; this example contains no credentials.",
        "# Providers: mock (offline), openai, azure, gemini, bedrock.",
        f"GENTIS_PROVIDER='{provider}'",
    ]
    for option, fields in _PROVIDER_FIELDS.items():
        if not fields:
            continue
        lines.extend(
            ["", f"# {option}: set GENTIS_PROVIDER='{option}' and fill these settings."]
        )
        if option == "azure":
            lines.append(
                "# Use your deployment name. API version is optional for Azure v1."
            )
        if option == "bedrock":
            lines.append(
                "# Credentials use the AWS SDK chain (aws configure or AWS_PROFILE)."
            )
        prefix = "" if option == provider else "# "
        lines.extend(f"{prefix}{name}='{default}'" for name, default in fields)
        if option == "openai":
            lines.extend(
                [
                    "# For compatible endpoints that require it, use max_tokens instead.",
                    f"{prefix}GENTIS_TOKEN_PARAMETER='max_completion_tokens'",
                ]
            )
    lines.extend(
        [
            "",
            "# Positive maximum output tokens for agent and router calls.",
            f"GENTIS_MAX_TOKENS='{_BUDGET_DEFAULTS['GENTIS_MAX_TOKENS']}'",
            f"GENTIS_ROUTING_MAX_TOKENS='{_BUDGET_DEFAULTS['GENTIS_ROUTING_MAX_TOKENS']}'",
            "# Positive request timeout in seconds.",
            f"GENTIS_TIMEOUT='{_BUDGET_DEFAULTS['GENTIS_TIMEOUT']}'",
        ]
    )
    return "\n".join(lines) + "\n"


def _existing_regular_file(path: Path) -> bool:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ConfigurationError(
            "Configuration and example paths must be regular files, not directories or symbolic links."
        )
    return path.exists()


def _create_file(path: Path, content: str) -> bool:
    # Exclusive creation protects existing files, including races after the check.
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        _existing_regular_file(path)
        return False
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(content)
    return True


def configure(provider: str, output: Path = Path(".env")) -> Path:
    """Create local settings and a safe example, preserving existing files."""
    example_content = configuration_example(provider)
    example_path = output.with_name(output.name + ".example")
    config_exists = _existing_regular_file(output)
    _existing_regular_file(example_path)
    if config_exists:
        _create_file(example_path, example_content)
        return example_path

    values = {"GENTIS_PROVIDER": provider}
    print("Blank optional fields use defaults. API keys are hidden while typing.")
    if provider == "azure":
        print("Use your deployment name. API version is optional for Azure v1.")
    if provider == "bedrock":
        print(
            "AWS credentials use the standard AWS SDK chain (for example, aws configure or AWS_PROFILE)."
        )
    for name, default in _PROVIDER_FIELDS[provider]:
        prompt = f"{name}" + (f" [{default}]" if default else "") + ": "
        value = (
            getpass.getpass(prompt) if name.endswith("API_KEY") else input(prompt)
        ).strip() or default
        if "\n" in value or "\r" in value or "\0" in value:
            raise ConfigurationError(f"{name} must be a single line.")
        if value:
            values[name] = value
    ProviderSettings.from_environment(values)
    values.update(_BUDGET_DEFAULTS)
    lines = ["# Created by gentis configure. Keep credentials out of version control."]
    for name, value in values.items():
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        lines.append(f"{name}='{escaped}'")
    _create_file(example_path, example_content)
    created = _create_file(output, "\n".join(lines) + "\n")
    return output if created else example_path


def doctor(provider: str | None = None) -> ProviderSettings:
    settings = ProviderSettings.from_environment(load_environment(), provider)
    settings.check_dependencies()
    print(f"Provider: {settings.provider}. Local configuration and SDK checks passed.")
    print(
        "No API request was sent. Credentials, model access, and quotas are not verified."
    )
    print(
        "Shell variables override the working-directory .env. Restart the demo after changes."
    )
    return settings

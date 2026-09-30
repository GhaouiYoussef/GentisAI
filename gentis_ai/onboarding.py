"""Local setup and diagnostics; never send a request or print credentials."""

from __future__ import annotations

import getpass
import os
from pathlib import Path

from gentis_ai.config import load_environment
from gentis_ai.providers import ConfigurationError, ProviderSettings


def configure(provider: str, output: Path = Path(".env")) -> Path:
    if output.exists():
        raise ConfigurationError(
            "Configuration file already exists. Edit it yourself or choose --output with a new path; existing files are never overwritten."
        )
    values = {"GENTIS_PROVIDER": provider}
    fields = {
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
    if provider not in fields:
        raise ConfigurationError("Unknown provider.")
    print("Blank optional fields use defaults. API keys are hidden while typing.")
    if provider == "azure":
        print("Use your deployment name. API version is optional for Azure v1.")
    if provider == "bedrock":
        print(
            "AWS credentials use the standard AWS SDK chain (for example, aws configure or AWS_PROFILE)."
        )
    for name, default in fields[provider]:
        prompt = f"{name}" + (f" [{default}]" if default else "") + ": "
        value = (
            getpass.getpass(prompt) if name.endswith("API_KEY") else input(prompt)
        ).strip() or default
        if "\n" in value or "\r" in value or "\0" in value:
            raise ConfigurationError(f"{name} must be a single line.")
        if value:
            values[name] = value
    ProviderSettings.from_environment(values)
    values.update(
        GENTIS_MAX_TOKENS="4096", GENTIS_ROUTING_MAX_TOKENS="1024", GENTIS_TIMEOUT="45"
    )
    lines = ["# Created by gentis configure. Keep credentials out of version control."]
    for name, value in values.items():
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        lines.append(f"{name}='{escaped}'")
    # Exclusive creation protects existing files, including races after the check.
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return output


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

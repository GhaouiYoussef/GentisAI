"""Local environment loading and shared Azure configuration normalization."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit, urlunsplit


_ALIASES = {
    "GOOGLE_API_KEY": ("GEMINI_API_KEY",),
    "AZURE_OPENAI_API_KEY": ("AzureOpenAIKey",),
    "AZURE_OPENAI_ENDPOINT": ("AzureOpenAIEndpoint",),
    "AZURE_OPENAI_DEPLOYMENT": ("AZURE_OPENAI_DEPLOYMENT_NAME", "AZURE_OPENAI_MODEL"),
}


def normalize_environment(environment: Mapping[str, str]) -> dict[str, str]:
    values = {key: value.strip() for key, value in environment.items()}
    # Windows shell variable names are case insensitive; dotenv keys are not.
    by_upper = {key.upper(): value for key, value in values.items()}
    for canonical, aliases in _ALIASES.items():
        for name in (canonical, *aliases):
            value = by_upper.get(name.upper())
            if value:
                values[canonical] = value
                break
    return values


def load_environment(*dotenv_paths: str | Path) -> dict[str, str]:
    """Merge cwd .env, explicit files in order, then shell values without mutation."""
    values: dict[str, str] = {}
    paths = dict.fromkeys([Path.cwd() / ".env", *(Path(p).resolve() for p in dotenv_paths)])
    for path in paths:
        if not path.is_file():
            continue
        try:
            from dotenv import dotenv_values
        except ImportError as exc:
            raise ImportError("Install python-dotenv to load .env configuration.") from exc
        parsed = dotenv_values(path, encoding="utf-8-sig", interpolate=False)
        values.update(normalize_environment({key: value for key, value in parsed.items() if value is not None}))
    values.update(normalize_environment(os.environ))
    return values


@dataclass(frozen=True)
class AzureSettings:
    api_key: str | None = field(default=None, repr=False)
    endpoint: str | None = None
    base_url: str | None = None
    deployment: str | None = None
    api_version: str | None = None

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> AzureSettings:
        env = normalize_environment(environment)
        endpoint = env.get("AZURE_OPENAI_ENDPOINT") or None
        deployment = env.get("AZURE_OPENAI_DEPLOYMENT") or None
        version = env.get("AZURE_OPENAI_API_VERSION") or None
        if endpoint:
            parts = urlsplit(endpoint)
            if parts.scheme not in ("http", "https") or not parts.netloc or parts.username or parts.password:
                raise ValueError("Azure endpoint must be a plain HTTP(S) URL without embedded credentials.")
            path = parts.path.rstrip("/")
            if "/openai/deployments/" in path:
                prefix, deployment_path = path.split("/openai/deployments/", 1)
                segments = deployment_path.split("/")
                if not segments[0] or segments[1:] not in ([], ["chat", "completions"]):
                    raise ValueError("Azure endpoint must be a resource URL or deployment chat-completions URL.")
                deployment = deployment or unquote(segments[0])
                path = prefix
                version = version or parse_qs(parts.query).get("api-version", [None])[0]
                if not version:
                    raise ValueError("A deployment URL requires AZURE_OPENAI_API_VERSION or api-version in its query.")
            elif path.endswith("/openai/v1"):
                path = path[:-len("/openai/v1")]
            elif path.endswith("/openai"):
                path = path[:-len("/openai")]
            endpoint = urlunsplit((parts.scheme, parts.netloc, path, "", ""))
        base_url = env.get("AZURE_OPENAI_BASE_URL") or None
        if base_url:
            parts = urlsplit(base_url)
            if parts.scheme not in ("http", "https") or not parts.netloc or parts.username or parts.password:
                raise ValueError("Azure base_url must be a plain HTTP(S) URL without embedded credentials.")
            base_url = base_url.rstrip("/")
        return cls(
            api_key=env.get("AZURE_OPENAI_API_KEY") or None,
            endpoint=endpoint,
            base_url=base_url,
            deployment=deployment,
            api_version=version,
        )

    def missing(self) -> list[str]:
        return [name for name, present in (
            ("API key", self.api_key),
            ("endpoint", self.endpoint or self.base_url),
            ("deployment", self.deployment),
        ) if not present]

    def llm_options(self) -> dict[str, Any]:
        return {
            "api_key": self.api_key,
            "azure_endpoint": self.endpoint,
            "base_url": self.base_url,
            "model_name": self.deployment,
            "api_version": self.api_version,
            "environment": {},
        }

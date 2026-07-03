# Contributing to GentisAI

Thanks for helping improve GentisAI.

## Local Setup

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
python -m pytest
```

## Pull Requests

1. Keep changes focused.
2. Add or update tests for behavior changes.
3. Run `python -m pytest` before opening a PR.
4. Update docs/examples when public behavior changes.

## Code Style

- Preserve the simple `Expert + Router + Flow` API.
- Keep provider SDKs optional.
- Avoid broad silent fallbacks.
- Prefer explicit `session_id` in examples.

## License

Contributions are licensed under the MIT License.

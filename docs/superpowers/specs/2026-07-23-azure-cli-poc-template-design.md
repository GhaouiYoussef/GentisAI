# Azure CLI POC Template Design

**Date:** 2026-07-23
**Status:** Approved for implementation planning

## Objective

Add a reusable Azure proof-of-concept template to the GentisAI CLI so a new user can install GentisAI, scaffold a working multi-expert application, and run it in a few commands:

```powershell
pip install "gentis-ai[azure]"
gentis new my-azure-poc --template azure
cd my-azure-poc
gentis run
```

The generated application must use Azure OpenAI when it is fully configured. When Azure configuration is absent or incomplete, it must continue with a deterministic `MockLLM` and clearly tell the user that the local mock provider is active. It must never print secrets or environment values.

## Chosen Approach

Extend `gentis new` with an optional `--template` argument and add an `azure` template. Keep the existing scaffold as the default so `gentis new NAME` remains backward compatible.

Make `gentis run` project-aware through an explicit generated `gentis.json` manifest. When the manifest identifies a local entry point, the CLI executes that application. When no manifest is present, it preserves the current built-in mock chat even if the directory happens to contain an unrelated `app.py`.

This is preferred over a one-off `gentis demo azure` command because users receive a normal project they can inspect, edit, test, and present as their own POC. It is preferred over an interactive scaffold wizard because one copyable command is easier to teach and automate.

## CLI Contract

### Project Creation

The new command is:

```text
gentis new NAME --template azure
```

`--template` accepts:

- `basic`: the current generated project and the default when the option is omitted.
- `azure`: the new Azure multi-expert POC.

Unknown template names are rejected by `argparse` with a non-zero exit code and the supported choices. Project paths and names continue to use the existing CLI validation and creation behavior.

After generating the Azure template, the CLI prints:

```text
Created <project-path>
Next:
  cd <project-path>
  gentis run
```

### Project Execution

The Azure template includes this project manifest:

```json
{
  "template": "azure",
  "entrypoint": "app.py"
}
```

From that project, `gentis run` validates that the entry point is a relative file inside the current project and executes it as the main module. This preserves ordinary `if __name__ == "__main__"` behavior and avoids requiring the generated project to be installed as a package.

If the current directory has no `gentis.json`, `gentis run` starts the existing built-in mock chat. A missing, malformed, absolute, or escaping entry point produces a concise error and a non-zero exit code. Exceptions from the local application do the same; the CLI never silently switches execution targets.

## Generated Project

The Azure template creates:

```text
my-azure-poc/
|-- app.py
|-- test_app.py
|-- README.md
|-- requirements.txt
|-- .env.example
|-- gentis.json
`-- Dockerfile
```

### Application

`app.py` is a small interactive terminal POC built from public GentisAI APIs. It defines:

- `cloud_architect`: architecture, reliability, scaling, and migration guidance.
- `security_specialist`: identity, network security, secrets, and governance guidance.
- `cost_optimizer`: Azure consumption, sizing, and cost-control guidance.
- `azure_guide`: the default expert and hybrid-response synthesizer.

The application uses `Router`, `Flow`, explicit expert descriptions, and a stable CLI session ID. It accepts repeated questions until the user enters `exit` or `quit`, demonstrating conversational memory without extra infrastructure.

Each turn consumes `Flow.stream_turn()` events. The terminal displays the selected route and expert activity, streams response tokens, and prints the final answer without duplicating it. Example prompts shown at startup cover:

- a single architecture route;
- a single security route;
- a hybrid cost-and-reliability route;
- a memory-dependent follow-up.

The mock provider uses deterministic routing rules and responses so the generated tests and first-run experience need no network connection.

## Provider Selection

Provider selection is isolated in a small function that accepts an optional environment mapping for straightforward unit tests.

Azure OpenAI is selected only when all three configuration categories are present:

- API key: `AZURE_OPENAI_API_KEY`
- endpoint: `AZURE_OPENAI_ENDPOINT` or `AZURE_OPENAI_BASE_URL`
- deployment: `AZURE_OPENAI_DEPLOYMENT` or `AZURE_OPENAI_MODEL`

When all categories are present, the application constructs `AzureOpenAILLM` with the resolved deployment, endpoint or base URL, and API key. The deployment value is an Azure deployment name, not a model-family assumption.

When any category is missing, the application constructs `MockLLM` and prints:

```text
[GentisAI] Azure OpenAI is not fully configured; using the local mock provider.
[GentisAI] Missing: API key, endpoint, deployment.
```

Only missing category names are shown. API keys, endpoints, deployment names, and raw environment values are never logged.

If Azure is fully configured but client construction or a request fails, the application reports an actionable Azure error and exits the affected operation. It does not silently fall back to mock after selecting Azure, because that could make a real-provider demonstration appear successful when it was not.

## Documentation

The generated `README.md` is the step-by-step POC guide. It includes:

1. Installing `gentis-ai[azure]`.
2. Running immediately with the local mock provider.
3. Setting the three Azure environment categories in PowerShell and POSIX shells.
4. Running the same `gentis run` command with Azure.
5. Trying the included single-route, hybrid-route, and memory prompts.
6. Running `python -m pytest`.
7. Explaining the generated experts, routing, streaming events, and fallback behavior.
8. Troubleshooting incomplete configuration, missing optional dependencies, invalid deployment names, and Azure request failures.

`.env.example` documents variable names with empty values. The generated application reads process environment variables directly and does not parse `.env` files or add another runtime dependency.

`requirements.txt` contains a compatible `gentis-ai[azure]` version range. The Dockerfile installs the Azure extra and starts the generated application.

The repository getting-started documentation and root README gain a short Azure POC quick-start section using the same four commands.

## Error Handling

- Missing or partial Azure configuration produces the explicit mock-provider notice and continues locally.
- Complete but invalid Azure configuration does not downgrade silently; the user sees a concise setup or request error.
- Empty input is ignored with a short prompt instead of invoking the router.
- End-of-file and keyboard interruption exit the chat cleanly.
- Local project import or execution failures return a non-zero status without an internal traceback by default.
- Provider status messages never include secret or environment values.

## Testing

CLI tests will use temporary directories and patched process state; they will not access real Azure services or user environment files.

Coverage includes:

- `gentis new NAME` still generates the basic template.
- `gentis new NAME --template azure` generates every expected file.
- Generated Python files compile.
- `gentis run` executes the entry point declared by a valid generated manifest.
- Invalid or escaping manifest entry points fail safely.
- `gentis run` retains the built-in chat when no manifest exists.
- No Azure variables selects `MockLLM` and emits the fallback notice.
- Partial Azure configuration lists only missing category names.
- Complete Azure configuration selects `AzureOpenAILLM` using a stub client.
- Provider messages do not contain configured values.
- The generated mock POC routes single and hybrid prompts and preserves a session follow-up.
- The generated project test suite passes without Azure credentials or network access.

The full repository test suite, lint checks for changed files, generated-project compilation, and a CLI smoke run are required before completion.

## Acceptance Criteria

- A user can reach a working interactive POC using the four documented commands.
- The first run succeeds without Azure credentials and explicitly identifies `MockLLM`.
- Complete Azure configuration switches the same generated application to `AzureOpenAILLM`.
- Missing configuration is reported by category without revealing values.
- The terminal visibly demonstrates routing, expert activity, streamed output, and session memory.
- The generated README is sufficient for a new user to reproduce both mock and Azure modes.
- Existing CLI commands and the default scaffold remain backward compatible.
- No secret, credential, or populated environment file is committed.
- All new and existing tests pass without external network calls.

## Out Of Scope

- Provisioning Azure OpenAI resources or validating Azure subscriptions.
- Loading `.env` files.
- A general interactive template wizard.
- A web interface, Streamlit application, or deployment automation.
- Azure services other than Azure OpenAI.
- Autonomous tool execution or external cloud-management actions.
- Publishing a new package version as part of this change.

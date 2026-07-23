# Azure Customer Support CLI POC Template Design

**Date:** 2026-07-23
**Status:** Approved for implementation planning

## Objective

Add a reusable Azure customer-support proof-of-concept template to the GentisAI CLI so a new user can install GentisAI, scaffold a working three-agent application, and run it in a few commands:

```powershell
pip install "gentis-ai[azure]"
gentis new customer-support --template azure-support
cd customer-support
gentis run
```

The generated application must make GentisAI's core value obvious: a fast router reads each customer message, selects one of three focused support agents, and invokes only that agent. It uses Azure OpenAI when fully configured. When Azure configuration is absent or incomplete, it continues with a deterministic `MockLLM` and clearly tells the user that the local mock provider is active. It never prints secrets or environment values.

## Chosen Approach

Extend `gentis new` with an optional `--template` argument and add an `azure-support` template. Keep the existing scaffold as the default so `gentis new NAME` remains backward compatible.

Make `gentis run` project-aware through an explicit generated `gentis.json` manifest. When the manifest identifies a local entry point, the CLI executes that application. When no manifest is present, it preserves the current built-in mock chat even if the directory happens to contain an unrelated `app.py`.

This is preferred over a one-off `gentis demo azure` command because users receive a normal project they can inspect, edit, test, and present as their own POC. It is preferred over an interactive scaffold wizard because one copyable command is easier to teach and automate. A single-agent routing mode is preferred over hybrid fan-out because the example is intended to demonstrate low-overhead dispatch, not multi-agent synthesis.

## CLI Contract

### Project Creation

The new command is:

```text
gentis new NAME --template azure-support
```

`--template` accepts:

- `basic`: the current generated project and the default when the option is omitted.
- `azure-support`: the new Azure customer-support POC.

Unknown template names are rejected by `argparse` with a non-zero exit code and the supported choices. Project paths and names continue to use the existing CLI creation behavior.

After generating the Azure support template, the CLI prints:

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
  "template": "azure-support",
  "entrypoint": "app.py"
}
```

From that project, `gentis run` validates that the entry point is a relative file inside the current project and executes it as the main module. This preserves ordinary `if __name__ == "__main__"` behavior and avoids requiring the generated project to be installed as a package.

If the current directory has no `gentis.json`, `gentis run` starts the existing built-in mock chat. A missing, malformed, absolute, or escaping entry point produces a concise error and a non-zero exit code. Exceptions from the local application do the same; the CLI never silently switches execution targets.

## Generated Project

The Azure support template creates:

```text
customer-support/
|-- app.py
|-- test_app.py
|-- README.md
|-- requirements.txt
|-- .env.example
|-- gentis.json
`-- Dockerfile
```

### Three-Agent Application

`app.py` is a small interactive terminal POC built from public GentisAI APIs. It defines:

- `technical_support`: application errors, bugs, outages, and troubleshooting.
- `billing_support`: invoices, charges, refunds, subscriptions, and payments.
- `account_support`: login, profile, access, and general account questions; this is also the routing fallback.

These are the only three experts registered with the router. The application uses `Router`, `Flow`, concise expert descriptions, and a stable CLI session ID. It accepts repeated questions until the user enters `exit` or `quit`, demonstrating conversational memory without extra infrastructure.

Each turn consumes `Flow.stream_turn()` events. The terminal displays the selected route and expert activity, streams response tokens, and prints the final answer without duplicating it. Example prompts shown at startup cover:

- a billing route: "I was charged twice this month.";
- a technical route: "The dashboard crashes when I upload a file.";
- an account route: "I cannot sign in to my account.";
- a memory-dependent follow-up.

The mock provider uses deterministic routing rules and responses so the generated tests and first-run experience need no network connection.

### Fast Router

The POC uses GentisAI's normal semantic `Router`; it does not add regex-based production routing or a manager-agent loop. Azure mode makes one compact structured classification request per customer turn, then invokes only the selected support agent.

Append a backward-compatible `routing_max_tokens: int = 512` parameter to `Router.__init__()`. Values below one raise `ValueError` at construction. The Azure support template sets the limit to `96`, sets `enable_hybrid=False`, and uses `account_support` as the explicit default expert. Existing applications retain the current 512-token limit.

The generated CLI measures elapsed time between actual `route_started` and `route_finished` events and prints:

```text
[route] billing_support selected in 184 ms
```

The number is always measured at runtime and is never hard-coded. The documentation describes this as routing latency, not total response latency, and makes no universal performance claim. Mock measurements are labeled as local mock results and are not presented as Azure benchmarks.

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
5. Trying the included billing, technical, account, and memory prompts.
6. Running `python -m pytest`.
7. Walking through the code in five short steps: select the provider, define three agents, create the fast router, create the flow, and stream a support turn.
8. Explaining that Azure performs semantic routing while the offline mock uses deterministic fixtures only for a credential-free demo.
9. Troubleshooting incomplete configuration, missing optional dependencies, invalid deployment names, and Azure request failures.

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
- `gentis new NAME --template azure-support` generates every expected file.
- Generated Python files compile.
- `gentis run` executes the entry point declared by a valid generated manifest.
- Invalid or escaping manifest entry points fail safely.
- `gentis run` retains the built-in chat when no manifest exists.
- No Azure variables selects `MockLLM` and emits the fallback notice.
- Partial Azure configuration lists only missing category names.
- Complete Azure configuration selects `AzureOpenAILLM` using a stub client.
- Provider messages do not contain configured values.
- The router keeps the existing 512-token default and accepts a validated custom routing limit.
- The generated POC registers exactly three agents and disables hybrid routing.
- The generated mock POC routes billing, technical, and account prompts and preserves a session follow-up.
- Routing latency comes from observed route events rather than a fixed value.
- The generated project test suite passes without Azure credentials or network access.

The full repository test suite, lint checks for changed files, generated-project compilation, and a CLI smoke run are required before completion.

## Acceptance Criteria

- A user can reach a working interactive POC using the four documented commands.
- The first run succeeds without Azure credentials and explicitly identifies `MockLLM`.
- Complete Azure configuration switches the same generated application to `AzureOpenAILLM`.
- Missing configuration is reported by category without revealing values.
- The generated application contains exactly three customer-support agents.
- Every turn selects one agent through a single compact routing call; no broadcast or hybrid synthesis occurs.
- The terminal visibly demonstrates the selected agent, measured routing time, streamed output, and session memory.
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
- Hybrid agent execution inside the generated POC, autonomous tools, or external customer-support integrations.
- Publishing a new package version as part of this change.

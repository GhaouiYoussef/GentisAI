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

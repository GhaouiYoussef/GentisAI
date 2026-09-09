# AI Product Launch War Room

Install from the repository root:

```powershell
python -m pip install -e ".[azure,gemini,openai]"
python -m pip install "streamlit>=1.36,<2"
```

Mock mode is deterministic and remains the default:

```powershell
python -m streamlit run demos/launch_war_room/app.py
```

Run with Gemini:

```powershell
$env:GENTIS_PROVIDER="gemini"
$env:GOOGLE_API_KEY="your-key"
python -m streamlit run demos/launch_war_room/app.py
```

`GEMINI_API_KEY` is also accepted. Set `GEMINI_MODEL` to override the default
`gemini-2.5-flash` model.

Run with Azure OpenAI:

```powershell
$env:GENTIS_PROVIDER="azure"
$env:AZURE_OPENAI_API_KEY="your-key"
$env:AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
$env:AZURE_OPENAI_DEPLOYMENT="your-deployment"
python -m streamlit run demos/launch_war_room/app.py
```

Azure also accepts `AZURE_OPENAI_BASE_URL` instead of the endpoint and
`AZURE_OPENAI_MODEL` instead of the deployment variable. OpenAI-compatible
mode remains available through `GENTIS_PROVIDER=openai`, `OPENAI_API_KEY`, and
optional `OPENAI_MODEL`/`OPENAI_BASE_URL`.

Try risks, launch hooks, weekend feasibility, then the session follow-up. The
app displays actual routing confidence and measured elapsed time. Selected
providers fail with explicit setup guidance when required configuration is
missing.

## Configuration Files

Create a `.env` file with one plain-text assignment per line (URLs must not use
Markdown link syntax):

```dotenv
GENTIS_PROVIDER=azure
AzureOpenAIKey=your-real-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.4-mini
AZURE_OPENAI_API_VERSION=2025-04-01-preview
```

The app reads `.env` from the working directory, then its own directory. The
app-local file overrides working-directory values; shell variables override both.
Restart the app after changing configuration because the demo caches its provider.

`AZURE_OPENAI_API_KEY` also accepts `AzureOpenAIKey`; `AZURE_OPENAI_ENDPOINT`
also accepts `AzureOpenAIEndpoint`. Deployment aliases are
`AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_DEPLOYMENT_NAME`, and `AZURE_OPENAI_MODEL`
(in that order). Canonical names win within one source; shell aliases still
win over file values. A full deployment chat-completions URL is accepted and its
deployment and `api-version` are extracted when not explicitly configured.

With an API version configured, the adapter uses the versioned Azure SDK client.
Without one, it retains the `/openai/v1` API. Azure token budgets use
`max_completion_tokens`, including routing requests.

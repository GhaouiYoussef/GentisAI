# Customer Rescue Command Center

Install from the repository root:

```powershell
python -m pip install -e ".[azure,gemini,openai]"
python -m pip install "streamlit>=1.36,<2"
```

Mock mode is deterministic and remains the default:

```powershell
python -m streamlit run demos/customer_rescue/app.py
```

Run with Gemini:

```powershell
$env:GENTIS_PROVIDER="gemini"
$env:GOOGLE_API_KEY="your-key"
python -m streamlit run demos/customer_rescue/app.py
```

`GEMINI_API_KEY` is also accepted. Set `GEMINI_MODEL` to override the default
`gemini-2.5-flash` model.

Run with Azure OpenAI:

```powershell
$env:GENTIS_PROVIDER="azure"
$env:AZURE_OPENAI_API_KEY="your-key"
$env:AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
$env:AZURE_OPENAI_DEPLOYMENT="your-deployment"
python -m streamlit run demos/customer_rescue/app.py
```

Azure also accepts `AZURE_OPENAI_BASE_URL` instead of the endpoint and
`AZURE_OPENAI_MODEL` instead of the deployment variable. OpenAI-compatible
mode remains available through `GENTIS_PROVIDER=openai`, `OPENAI_API_KEY`, and
optional `OPENAI_MODEL`/`OPENAI_BASE_URL`.

Try a billing-only invoice request, the three-expert customer-rescue scenario,
then its session follow-up. Selected providers fail with explicit setup guidance
when required configuration is missing; the app never loads a `.env` file.

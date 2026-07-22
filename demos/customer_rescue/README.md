# Customer Rescue Command Center

Run from the repository root in deterministic offline mode:

```bash
python -m venv .venv
python -m pip install -e ".[openai]"
python -m pip install "streamlit>=1.36,<2"
python -m streamlit run demos/customer_rescue/app.py
```

After 0.2.1 is published, install `demos/customer_rescue/requirements.txt` instead. Mock mode is the default. For a real provider, set `GENTIS_PROVIDER=openai`, `OPENAI_API_KEY`, and optionally `OPENAI_MODEL` and `OPENAI_BASE_URL` in your shell; the app never loads a `.env` file.

Try a billing-only invoice request, the three-expert customer-rescue scenario, then its session follow-up. Missing keys produce an explicit setup error; switch deliberately to `GENTIS_PROVIDER=mock` for offline use.

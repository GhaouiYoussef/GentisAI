# Gemini Customer Support Demo

Install the project and provider dependency:

```powershell
python -m pip install -r requirements.txt
```

Set the API key in the same PowerShell session, then run the project:

```powershell
$env:GOOGLE_API_KEY="your-key"
gentis run
```

`GEMINI_API_KEY` is also accepted. The default model is `gemini-2.5-flash`;
override it with `GEMINI_MODEL` when needed. The app reads credentials from the
process environment and never prints them.

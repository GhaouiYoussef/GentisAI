# AI Product Launch War Room

Install and run without cloning the repository (requires the 0.2.2 release):

```bash
python -m pip install --upgrade "gentis-ai[demo]>=0.2.2"
gentis demo launch-war-room
```

Try Launch hooks, Full recommendation, then Session follow-up. Mock mode is the default and uses scripted answers. Use a real provider to evaluate contextual understanding.

For Azure, for example:

```bash
python -m pip install "gentis-ai[demo,azure]>=0.2.2"
gentis configure --provider azure
gentis doctor
gentis demo launch-war-room
```

OpenAI, Gemini, and Bedrock work with their corresponding extra and provider name. Configuration is read from the working-directory `.env`, with shell variables taking precedence. Restart the app after changing it. `gentis configure` never overwrites an existing file.

See the [main setup guide](../../README.md#connect-your-provider) for required settings, token limits, aliases, and troubleshooting. The implementation ships under `gentis_ai/demos/launch_war_room`; this directory preserves the older source-checkout entry point.

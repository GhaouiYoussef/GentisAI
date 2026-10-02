# Your GentisAI agents

Start here:

```sh
python -m pip install -r requirements.txt
gentis run --ui
```

Use `gentis run` for terminal chat. The project works offline without credentials.
Offline replies are simulated; choose an agent in the sidebar (or `/agent NAME`
in terminal chat) to exercise its registered tools. A connected provider selects
agents from their descriptions and the conversation, without keyword routing rules.

## Project map

```text
agents/             One Python Expert factory per agent
prompts/            One editable Markdown system prompt per agent
tools/              Read-only Python context tools
gentis.json         Explicit agent/tool registration and attachment
project.py          Shared build_flow() for any application
app.py              Terminal chat
streamlit_app.py    Streamlit chat with a separate Flow per browser session
.env.example        Safe configuration reference; credentials belong in .env
```

## Add an agent and tool

```sh
gentis add agent billing --description "Handles invoices, payments, and billing questions."
gentis add tool lookup_invoice --agent billing --description "Look up invoice details."
```

The commands create the files and register them in `gentis.json` automatically.
Edit `agents/billing.py` to describe when to route to it, `prompts/billing.md` for
its behavior, and `tools/lookup_invoice.py` for the actual lookup. Names may use
letters, digits, underscores, or hyphens; hyphens become underscores.
Existing files are never overwritten. Reload the Streamlit project after edits.

Each context tool accepts `query: str` and returns JSON-compatible data. All tools
attached to the selected agent run before its answer; their results appear in the
model context and in Streamlit's Tool results panel. New tools initially report
`not_configured`; implement a read-only lookup before relying on the result.
The manifest explicitly controls attachment. For tools requiring approvals, writes,
or different arguments, customize the Flow's `ToolPolicy` and `ToolExecutor`
instead of using this starter's read-only context policy. `Expert.tools` stays empty
because this flow executes context tools itself, independently of provider-native
function calling.

## Connect a provider

```sh
python -m pip install "gentis-ai[openai]"
gentis configure --provider openai
gentis doctor
gentis run --ui
```

Azure, Gemini, and Bedrock work with their matching extras and provider names.
Fill the generated `.env` locally. Existing `.env` files are preserved; use the
`.env.example` reference to add needed settings. Shell settings take precedence.
The `.gitignore` keeps credentials private while allowing `.env.example` in Git.

## Connect your own application

```python
from project import build_flow

flow = build_flow()  # Keep one Flow in each application's user session.
response = flow.process_turn("Hello", session_id="your-session-id")
print(response.content)
```

For Streamlit, store the Flow in `st.session_state`, as `streamlit_app.py` does.
Do not place it in a global `st.cache_resource`: that would share provider and
conversation state between browsers. For offline tests use `build_flow(environment={})`.

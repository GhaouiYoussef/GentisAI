# Customer Rescue Command Center

Install and run without cloning the repository (requires the 0.2.2 release):

```bash
python -m pip install --upgrade "gentis-ai[demo]>=0.2.2"
gentis demo
```

Click Customer rescue, then Session follow-up. Mock mode uses scripted routing and
replies grounded in the tool results. Use a live provider for contextual understanding.

For the permission demo, export with `gentis demo customer-rescue --export my-demo`
and run `gentis run` inside that folder. Choose Billing in the Agent sidebar and ask
for a ticket. It cannot create one until you change `AGENT_TOOLS` in
`demo_app/gentis_setup.py` to include:

```python
"billing": ("check_invoice", "create_support_ticket"),
```

Restart the app and repeat. Any agent can receive this tool; only Technical Support
has it initially. Each ticket gets a new ID and uses the customer's actual message
as its issue. The selected agents run their assigned tools once per turn, and shared
tools run only once. These are local demo tickets, not external help desk records.
Account lookup returns only Youssef Ghaoui, and the invoice stays static.

For Azure, for example:

```bash
python -m pip install "gentis-ai[demo,azure]>=0.2.2"
gentis configure --provider azure
gentis doctor
gentis demo
```

OpenAI, Gemini, and Bedrock work with their corresponding extra and provider name. Configuration is read from the working-directory `.env`, with shell variables taking precedence. Restart the app after changing it. `gentis configure` never overwrites an existing file.

See the [main setup guide](../../README.md#connect-your-provider) for required settings, token limits, aliases, and troubleshooting. The implementation ships under `gentis_ai/demos/customer_rescue`; this directory preserves the older source-checkout entry point.

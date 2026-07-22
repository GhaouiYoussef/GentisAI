# AI Product Launch War Room

From the repository root, run `python -m pip install -e ".[openai]"`, install `streamlit>=1.36,<2`, then start `python -m streamlit run demos/launch_war_room/app.py`.

Mock mode is deterministic and requires no key. For a real provider, set `GENTIS_PROVIDER=openai`, `OPENAI_API_KEY`, and optional `OPENAI_MODEL`/`OPENAI_BASE_URL` directly in your shell. Try risks, launch hooks, weekend feasibility, then the session follow-up. The app displays only actual routing confidence and measured elapsed time.

"""Render runtime events into a replaceable Streamlit trace panel."""

from html import escape
import json


def render_trace(placeholder, events):
    # Replace one element atomically so shorter traces cannot retain old rows.
    rows = []
    for event in events:
        kind = event["type"].replace("_", " ").upper()
        result = event.get("result", {})
        detail = result.get("name") or event.get("name") or ", ".join(event.get("experts", []))
        if event.get("confidence") is not None:
            detail += f" - confidence {event['confidence']:.2f}"
        row = f'<div class="event trace"><b>{escape(kind)}</b><br>{escape(detail)}'
        for payload in ([event["arguments"]] if "arguments" in event else []) + ([result] if result else []):
            row += (
                '<pre style="white-space:pre-wrap;overflow-wrap:anywhere">'
                + escape(json.dumps(payload, indent=2, default=str))
                + '</pre>'
            )
        if event.get("error"):
            row += '<p>The request could not be completed. Please try again.</p>'
        rows.append(row + '</div>')
    placeholder.markdown("".join(rows), unsafe_allow_html=True)

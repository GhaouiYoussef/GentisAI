from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_launch_kit_contains_every_required_deliverable():
    text = (ROOT / "docs" / "launch" / "gentisai-0.2.1-launch-kit.md").read_text(encoding="utf-8")
    for item in [
        "Customer Rescue Command Center", "AI Product Launch War Room",
        "```mermaid", "0-5 seconds", "5-15 seconds", "15-35 seconds",
        "35-55 seconds", "55-70 seconds", "70-90 seconds", "Video Titles",
        "Opening Hooks", "X Post", "LinkedIn Post", "Hacker News",
        "GitHub README Demo Section", "Launch-Readiness Checklist",
    ]:
        assert item in text


def test_readme_links_both_demos():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "demos/customer_rescue" in text
    assert "demos/launch_war_room" in text

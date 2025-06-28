from pathlib import Path
import os

# Get the actual project root (where pyproject.toml lives)
PROJECT_ROOT = Path(os.path.abspath(__file__)).parents[3]  # src/her/engine -> src/her -> src -> project_root
PROMPTS_ROOT = PROJECT_ROOT / "prompts"

print(f"Looking for prompts in: {PROMPTS_ROOT}")  # Debug print to verify path

PERSONALITY_FILE = PROMPTS_ROOT / "personality" / "personality.md"
FLOWS_DIR = PROMPTS_ROOT / "flows"

FLOW_STAGE_FILE_MAP = {
    "onboarding": PROMPTS_ROOT / "flows" / "onboarding.md",
    "followup":   PROMPTS_ROOT / "flows" / "followup.md",
    # add more as you create them
}

def build_prompt(flow_type: str) -> str:
    """
    Return a full system-prompt string for the given flow type.
    """
    try:
        stage_file = FLOW_STAGE_FILE_MAP[flow_type]
    except KeyError:
        raise ValueError(f"Unknown flow_type: {flow_type}")

    parts: list[str] = []

    # order matters – personality first, then stage-specific, then any extras
    parts.append(PERSONALITY_FILE.read_text())
    parts.append(stage_file.read_text())

    return "\n\n".join(parts)

def get_first_message(flow_type: str) -> str:
    """Get the first message for a given flow type."""
    return (FLOWS_DIR / f"{flow_type}_first_message.md").read_text()

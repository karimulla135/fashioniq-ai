
import os
from pathlib import Path

from dotenv import load_dotenv
from anthropic import Anthropic

# Locate the project's root directory
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

# Load .env BEFORE reading environment variables
load_dotenv(dotenv_path=ENV_FILE, override=True)

# Claude model configuration
HAIKU_MODEL = "claude-haiku-5-5"
SONNET_MODEL = "claude-sonnet-5-5"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", HAIKU_MODEL)


def get_anthropic_client():
    """Create an Anthropic API client."""

    if not ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY is missing. Check your .env file."
        )

    return Anthropic(api_key=ANTHROPIC_API_KEY)


def get_model(use_stronger_reasoning=False):
    """Select the Claude model."""

    if use_stronger_reasoning:
        return SONNET_MODEL

    return CLAUDE_MODEL

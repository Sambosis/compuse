from dotenv import load_dotenv
from pathlib import Path
import os

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent

# Load environment variables
load_dotenv()

# Constants
MAX_SUMMARY_MESSAGES = 25
MAX_SUMMARY_TOKENS = 8000
ICECREAM_OUTPUT_FILE = SCRIPT_DIR / "debug_log.json"
JOURNAL_DIR = SCRIPT_DIR / "journal"
JOURNAL_FILE = JOURNAL_DIR / "journal.log"
JOURNAL_ARCHIVE_FILE = JOURNAL_DIR / "journal.log.archive"
COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"
JOURNAL_MODEL = "claude-3-5-sonnet-latest"
SUMMARY_MODEL = "claude-3-5-sonnet-latest"
JOURNAL_MAX_TOKENS = 8000
JOURNAL_SYSTEM_PROMPT_FILE = JOURNAL_DIR / "journal_system_prompt.md"
SYSTEM_PROMPT_FILE = SCRIPT_DIR / "system_prompt.md"

# Create necessary directories
JOURNAL_DIR.mkdir(parents=True, exist_ok=True)

# Load journal system prompt
try:
    with open(JOURNAL_SYSTEM_PROMPT_FILE, 'r', encoding="utf-8") as f:
        JOURNAL_SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    JOURNAL_SYSTEM_PROMPT = ""
    print(f"Warning: Journal system prompt file not found at {JOURNAL_SYSTEM_PROMPT_FILE}")

# Load system prompt
try:
    with open(SYSTEM_PROMPT_FILE, 'r', encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    SYSTEM_PROMPT = ""
    print(f"Warning: System prompt file not found at {SYSTEM_PROMPT_FILE}")

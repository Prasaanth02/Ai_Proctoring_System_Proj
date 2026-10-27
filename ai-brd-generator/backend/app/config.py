import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "output")


def validate_config():
    if not OPENAI_API_KEY:
        raise EnvironmentError("OPENAI_API_KEY is not set in the .env file.")

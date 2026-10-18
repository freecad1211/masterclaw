import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load project-local .env when running from the repository or service working directory.
load_dotenv()


@dataclass
class Settings:
    database_path: str = os.getenv("FORGECLAW_DATABASE_PATH", "./data/forgeclaw.sqlite3")
    debate_max_rounds: int = int(os.getenv("FORGECLAW_DEBATE_MAX_ROUNDS", "3"))
    llm_base_url: str = os.getenv("LLM_BASE_URL", "").strip()
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "").strip()
    llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))


settings = Settings()

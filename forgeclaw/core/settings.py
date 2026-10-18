import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_path: str = os.getenv("FORGECLAW_DATABASE_PATH", "./data/forgeclaw.sqlite3")
    debate_max_rounds: int = int(os.getenv("FORGECLAW_DEBATE_MAX_ROUNDS", "3"))


settings = Settings()

import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    brapi_token: str = os.getenv("BRAPI_TOKEN", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

    target_positions: int = int(os.getenv("TARGET_POSITIONS", "4"))
    target_weight: float = float(os.getenv("TARGET_WEIGHT", "0.25"))

    w_quality: float = float(os.getenv("SCORE_W_QUALITY", "0.4"))
    w_valuation: float = float(os.getenv("SCORE_W_VALUATION", "0.3"))
    w_momentum: float = float(os.getenv("SCORE_W_MOMENTUM", "0.3"))

settings = Settings()

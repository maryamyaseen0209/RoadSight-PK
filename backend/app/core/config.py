from pathlib import Path
from typing import Any, List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    PROJECT_NAME: str = "RoadSight-PK"
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.strip().lower() in ("1", "true", "yes", "debug", "on")
        return bool(v)

    # Database
    DATABASE_URL: str = "sqlite:///./roadsight.db"

    # Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    OUTPUTS_DIR: str = "artifacts/outputs"
    CHECKPOINTS_DIR: str = "artifacts/checkpoints"
    METRICS_DIR: str = "experiments/metrics"

    # Model settings
    DEFAULT_MODEL_TYPE: str = "yolo"
    MODEL_WEIGHTS_PATH: str = "artifacts/checkpoints/best_yolo.pt"
    CONFIDENCE_THRESHOLD: float = 0.25
    IOU_THRESHOLD: float = 0.45

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @property
    def outputs_path(self) -> Path:
        p = self.BASE_DIR / self.OUTPUTS_DIR
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def metrics_path(self) -> Path:
        return self.BASE_DIR / self.METRICS_DIR


settings = Settings()

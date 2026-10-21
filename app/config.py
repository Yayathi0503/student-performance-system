from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    database_url: str = f"sqlite:///{(ROOT / 'performance.db').as_posix()}"
    jwt_secret: str = Field(min_length=32)
    access_token_minutes: int = Field(default=30, ge=1, le=1440)
    model_path: Path = ROOT / "artifacts" / "model.joblib"

    @field_validator("jwt_secret")
    @classmethod
    def reject_placeholder(cls, value):
        if value.startswith("replace-"):
            raise ValueError("Generate JWT_SECRET with scripts/setup_local.py")
        return value


def get_settings():
    return Settings()

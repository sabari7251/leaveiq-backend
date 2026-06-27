import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def get_env(name: str, default: str | None = None, required: bool = False) -> str | None:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"{name} environment variable is required")
    return value


def get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def get_list_env(name: str, default: list[str] | None = None) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


APP_NAME = get_env("APP_NAME", "LeaveIQ API")
ENVIRONMENT = get_env("ENVIRONMENT", "development")

CORS_ORIGINS = get_list_env(
    "CORS_ORIGINS",
    [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000",
    ],
)

JWT_SECRET_KEY = get_env("JWT_SECRET_KEY", required=True)
JWT_ALGORITHM = get_env("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = get_int_env("JWT_EXPIRE_MINUTES", 30)

OPENROUTER_API_KEY = get_env("OPENROUTER_API_KEY")
OPENROUTER_MODEL = get_env("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
GROQ_API_KEY = get_env("GROQ_API_KEY")
GROQ_MODEL = get_env("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

PINECONE_API_KEY = get_env("PINECONE_API_KEY")
PINECONE_INDEX = get_env("PINECONE_INDEX")

UPLOAD_DIR = Path(get_env("UPLOAD_DIR", str(BASE_DIR / "uploads"))).resolve()

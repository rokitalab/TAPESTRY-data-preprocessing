from __future__ import annotations
from dataclasses import dataclass
import os

# Auto-load .env if python-dotenv is available
try:  # pragma: no cover
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:  # pragma: no cover
    pass


@dataclass
class DBConfig:
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    user: str = os.getenv("POSTGRES_USER", "postgres")
    password: str = os.getenv("POSTGRES_PASSWORD", "")
    database: str = os.getenv("POSTGRES_DB", "tapestry")

    def dsn(self, *, admin: bool = False) -> str:
        db = "postgres" if admin else self.database
        auth = self.user
        if self.password:
            auth = f"{auth}:{self.password}"
        return f"postgresql://{auth}@{self.host}:{self.port}/{db}"

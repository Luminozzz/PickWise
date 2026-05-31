import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(BASE_DIR, ".env"))
except Exception:
    pass

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

DB_SCHEMA = os.environ.get("DB_SCHEMA", "lumino").strip()

if not DATABASE_URL:
    DATABASE_URL = f"sqlite+aiosqlite:///{BASE_DIR}/database/mouse.db"

import os

# Directs to Lumino-1 folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = f"sqlite+aiosqlite:///{BASE_DIR}/database/mouse.db"

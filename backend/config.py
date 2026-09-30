import os
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()  # This reads your .env file automatically


# Ensures backend directory is accurately detected
CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parent
BASE_DIR = BACKEND_DIR.parent

DOCS_DIR = BASE_DIR / "Data" / "Documents"
DB_PATH = BACKEND_DIR / "rag_knowledge.db"

DOCS_DIR.mkdir(parents=True, exist_ok=True)
#,
OPENAI_API_KEY = os.getenv("your_openai_api_key_here")

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
RRF_K = 60
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load .env from core/ so it works when running from core/backend/Response
_core_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(_core_dir / ".env")
load_dotenv()  # cwd as fallback

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
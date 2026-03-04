import sys
from pathlib import Path

# Ensure this server uses only backend code from core/backend (not top-level backend/)
_core_backend = Path(__file__).resolve().parent
if str(_core_backend) not in sys.path:
    sys.path.insert(0, str(_core_backend))

from dotenv import load_dotenv
load_dotenv(_core_backend.parent / ".env")
load_dotenv()  # cwd as fallback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from llama import ResponseGenerator
from chatgpt import generate_response_chatgpt
import user_retriever

# TODO: wrap your function file in a class called ResponseGenerator
# this allows us to import our function into another file!

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = "llama"

class ChatResponse(BaseModel):
    response: str

# TODO: fill out below

_repo_root = Path(__file__).resolve().parent.parent.parent

def _debug_log(location: str, message: str, data: dict, hypothesis_id: str):
    import json, time
    _log_path = _repo_root / ".cursor" / "debug.log"
    try:
        _log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(_log_path, "a") as f:
            f.write(json.dumps({"location": location, "message": message, "data": data, "timestamp": int(time.time() * 1000), "hypothesisId": hypothesis_id}) + "\n")
    except Exception:
        pass

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # #region agent log
        provider = (request.provider or "llama").lower()
        _debug_log("response.py:chat", "request received", {"raw_provider": request.provider, "provider": provider, "message_len": len(request.message or "")}, "B")
        # #endregion
        print("\n[API] /chat request received")
        print(f"[API] Incoming user message: {request.message!r}")
        print(f"[API] Provider: {provider}")

        if provider == "chatgpt":
            # #region agent log
            _debug_log("response.py:chat", "branch taken", {"branch": "chatgpt"}, "B")
            # #endregion
            response_text = generate_response_chatgpt(
                request.message,
                columns=['most_frequent_category', 'most_frequent_action', 'action_name', 'leaf_value'],
                user_id=user_retriever.CURRENT_USER_ID,
            )
        else:
            # #region agent log
            _debug_log("response.py:chat", "branch taken", {"branch": "llama"}, "B")
            # #endregion
            response_text = ResponseGenerator.generate_response(
                request.message,
                columns=['most_frequent_category', 'most_frequent_action', 'action_name', 'leaf_value'],
                user_id=user_retriever.CURRENT_USER_ID,
            )
        print("[API] Response successfully generated, sending back to client.")
        # #region agent log
        _debug_log("response.py:chat", "success", {"response_len": len(response_text or "")}, "H4")
        # #endregion
        return ChatResponse(response=response_text)
    except Exception as e:
        # #region agent log
        _debug_log("response.py:chat", "exception", {"error": str(e), "type": type(e).__name__}, "E")
        # #endregion
        print(f"[API] ERROR while processing /chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

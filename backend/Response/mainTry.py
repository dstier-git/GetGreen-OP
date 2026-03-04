from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sainikCopyLLAMA import ResponseGenerator

# Add core backend to path so ChatGPT provider can be used when running this app
_repo_root = Path(__file__).resolve().parent.parent.parent
_core_backend = _repo_root / "core" / "backend"
if _core_backend.exists():
    import sys
    sys.path.insert(0, str(_core_backend))
from dotenv import load_dotenv
load_dotenv(_repo_root / "core" / ".env")

# TODO: wrap your function file in a class called Response Generator
# TODO: RENAME your function file to have only letters or underscores
# TODO: replace '...' after from above with 'from your_response_file' with NO .py after
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

def _debug_log(location: str, message: str, data: dict, hypothesis_id: str):
    import json, time
    _log_path = _repo_root / ".cursor" / "debug.log"
    try:
        _log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(_log_path, "a") as f:
            f.write(json.dumps({"location": location, "message": message, "data": data, "timestamp": int(time.time() * 1000), "hypothesisId": hypothesis_id}) + "\n")
    except Exception:
        pass

def _get_chatgpt_generator():
    if not _core_backend.exists():
        _debug_log("mainTry:_get_chatgpt_generator", "core_backend missing", {"path": str(_core_backend)}, "M")
        return None
    try:
        from chatgpt import generate_response_chatgpt
        _debug_log("mainTry:_get_chatgpt_generator", "chatgpt import ok", {}, "M")
        return generate_response_chatgpt
    except Exception as e:
        _debug_log("mainTry:_get_chatgpt_generator", "chatgpt import failed", {"error": str(e), "type": type(e).__name__}, "M")
        return None

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        provider = (request.provider or "llama").lower()
        _debug_log("mainTry:chat", "request received", {"provider": provider, "message_len": len(request.message or "")}, "M")
        print("\n[API] /chat request received")
        print(f"[API] Incoming user message: {request.message!r}")
        print(f"[API] Provider: {provider}")

        if provider == "chatgpt":
            gen = _get_chatgpt_generator()
            if gen is None:
                _debug_log("mainTry:chat", "chatgpt gen is None", {}, "M")
                raise HTTPException(
                    status_code=500,
                    detail="ChatGPT provider not available. Run the backend from core/backend (uvicorn response:app --reload --port 8000) for ChatGPT support.",
                )
            _debug_log("mainTry:chat", "calling chatgpt gen", {}, "M")
            try:
                response_text = gen(
                    request.message,
                    columns=['most_frequent_category', 'most_frequent_action', 'action_name', 'leaf_value'],
                    user_id='62002cce-0993-4658-b6dd-ec2b10bd3337',
                )
                _debug_log("mainTry:chat", "chatgpt gen returned", {"response_len": len(response_text or "")}, "M")
            except Exception as e2:
                _debug_log("mainTry:chat", "chatgpt gen raised", {"error": str(e2), "type": type(e2).__name__}, "M")
                raise
        else:
            response_text = ResponseGenerator.generate_response(request.message,
                                          columns=['most_frequent_category', 'most_frequent_action', 'action_name', 'leaf_value'],
                                          user_id='62002cce-0993-4658-b6dd-ec2b10bd3337')
        print("[API] Response successfully generated, sending back to client.")
        return ChatResponse(response=response_text)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] ERROR while processing /chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

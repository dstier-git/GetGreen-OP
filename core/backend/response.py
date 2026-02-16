from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path
from llama import ResponseGenerator
from chatgpt import generate_response_chatgpt

# TODO: wrap your function file in a class called ResponseGenerator
# this allows us to import our function into another file!

_core_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(_core_dir / ".env")
load_dotenv()  # cwd as fallback

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

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        print("\n[API] /chat request received")
        print(f"[API] Incoming user message: {request.message!r}")
        provider = (request.provider or "llama").lower()
        print(f"[API] Provider: {provider}")

        if provider == "chatgpt":
            response_text = generate_response_chatgpt(
                request.message,
                columns=['most_frequent_category', 'most_frequent_action', 'action_name', 'leaf_value'],
                user_id='62002cce-0993-4658-b6dd-ec2b10bd3337',
            )
        else:
            response_text = ResponseGenerator.generate_response(
                request.message,
                columns=['most_frequent_category', 'most_frequent_action', 'action_name', 'leaf_value'],
                user_id='62002cce-0993-4658-b6dd-ec2b10bd3337',
            )
        print("[API] Response successfully generated, sending back to client.")
        return ChatResponse(response=response_text)
    except Exception as e:
        print(f"[API] ERROR while processing /chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

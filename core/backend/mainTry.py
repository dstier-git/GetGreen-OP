from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sainikCopyLLAMA import ResponseGenerator

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

class ChatResponse(BaseModel):
    response: str

# TODO: fill out below

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        print("\n[API] /chat request received")
        print(f"[API] Incoming user message: {request.message!r}")

        response_text = ResponseGenerator.generate_response(request.message, 
                                          columns=['most_frequent_category', 'most_frequent_action', 'action_name', 'leaf_value'], 
                                          user_id='62002cce-0993-4658-b6dd-ec2b10bd3337')
        print("[API] Response successfully generated, sending back to client.")
        return ChatResponse(response=response_text)
    except Exception as e:
        print(f"[API] ERROR while processing /chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

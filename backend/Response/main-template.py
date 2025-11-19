from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ... import ResponseGenerator

# TODO: wrap your response file in a class named ResponseGenerator
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
        response_text = ResponseGenerator.generate_response(request.message, 
                                          columns=['action_name', 'leaf_value'], 
                                          user_id='821ce161-3539-4b46-858a-437deb80e1b8')
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
## GPT / ChatGPT Feature Backup

This file captures the current GPT-related functionality (backend + frontend)
so it can be restored after a hard reset.

### Backend

#### `backend/Response/response_generator.py`

```python
import json
import os
from pathlib import Path

import pandas as pd
import requests

import user_data
from retrieval import retrieve_relevant_docs

MODEL_NAME = "llama3.2-11b-instruct-local"
OLLAMA_URL = "http://localhost:11434/api/generate"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are GetGreen.AI, a friendly and practical chatbot that helps people take small, realistic environmental actions every day.

Tone: upbeat, supportive, conversational, and action-oriented.
Focus areas: food, shopping, transportation, energy use, waste reduction.
Keep replies short (2-4 sentences), encouraging, and simple. Avoid lists unless needed.
Offer small, realistic tips and avoid guilt-based language.
Do not give technical, medical, or legal advice.
Do not include speaker labels like User: or Assistant: in your output.
"""

EXAMPLES = """Examples:
User: I'm going grocery shopping.
Assistant: Nice! Grab reusable bags and look for local produce, easy win for the planet.

User: I'm cooking dinner tonight.
Assistant: Fun! Try swapping in a plant-based protein this time. Even one meal makes a difference.

User: I'm heading to work now.
Assistant: If it's doable, try walking or biking part of the way. Little shifts add up fast.
"""


class ResponseGenerator:
    @staticmethod
    def _read_key_from_env_file():
        env_candidates = [
            Path(__file__).resolve().parents[2] / ".env",
            Path.cwd() / ".env",
        ]

        for env_path in env_candidates:
            if not env_path.exists():
                continue
            with env_path.open("r", encoding="utf-8") as env_file:
                for line in env_file:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#") or "=" not in stripped:
                        continue
                    key, value = stripped.split("=", 1)
                    if key.strip() == "OPEN_AI_KEY":
                        return value.strip().strip("'\"")
        return None

    @staticmethod
    def _get_openai_key():
        return os.getenv("OPEN_AI_KEY") or ResponseGenerator._read_key_from_env_file()

    @staticmethod
    def _table_to_context(data):
        df = pd.DataFrame(data)
        if df.empty:
            return "No data found for this user."

        lines = ["Relevant user information:"]
        for _, row in df.iterrows():
            parts = [f"{col}: {row[col]}" for col in df.columns]
            lines.append(" - " + ", ".join(parts))
        return "\n".join(lines)

    @staticmethod
    def _generate_with_ollama(full_prompt):
        with requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": full_prompt,
                "options": {
                    "temperature": 0.6,
                    "top_p": 0.95,
                    "num_predict": 200,
                    "repeat_penalty": 1.1,
                },
            },
            stream=True,
            timeout=180,
        ) as response:
            response.raise_for_status()
            generated_text = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode("utf-8"))
                    generated_text += data.get("response", "")
            return generated_text

    @staticmethod
    def _generate_with_openai(full_prompt):
        openai_key = ResponseGenerator._get_openai_key()
        if not openai_key:
            raise RuntimeError("OPEN_AI_KEY was not found. Add it to environment variables or .env.")

        response = requests.post(
            OPENAI_URL,
            headers={
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": full_prompt},
                ],
                "temperature": 0.6,
                "max_tokens": 200,
            },
            timeout=180,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def generate_response(prompt, columns, user_id, history=None, provider="llama"):
        article_context = retrieve_relevant_docs(prompt, k=2)
        user_rows = user_data.get_columns(columns, user_id)
        user_context = ResponseGenerator._table_to_context(user_rows)

        if history:
            convo = "\n".join(f"{role}: {text}" for role, text in history)
        else:
            convo = f"User: {prompt}"

        full_prompt = f"""
{SYSTEM_PROMPT}

[Examples]
{EXAMPLES}

[Relevant Articles]
{article_context if article_context else "No relevant articles found."}

[User Information]
{user_context}

[Conversation so far]
{convo}

Assistant:
""".strip()

        selected_provider = (provider or "llama").lower()
        if selected_provider == "openai":
            generated_text = ResponseGenerator._generate_with_openai(full_prompt)
        else:
            generated_text = ResponseGenerator._generate_with_ollama(full_prompt)

        assistant_response = generated_text.strip()
        assistant_response = assistant_response.split("You are GetGreen.AI")[0].strip()
        assistant_response = assistant_response.split("User:")[0].strip()
        return " ".join(assistant_response.split())
```

#### `backend/Response/api.py`

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

from response_generator import ResponseGenerator
from user_data import DATA_PATH

app = FastAPI(title="GetGreen API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    provider: str = "llama"


class ChatResponse(BaseModel):
    response: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        selected_provider = request.provider.lower().strip()
        if selected_provider not in {"llama", "openai"}:
            raise HTTPException(status_code=400, detail="provider must be 'llama' or 'openai'")

        # If ChatGPT/OpenAI is selected, expose all available user-data columns
        # so the model can decide which are most relevant. For local models,
        # keep using the curated subset.
        if selected_provider == "openai":
            try:
                # Read only the header to get column names
                df = pd.read_csv(DATA_PATH, nrows=0)
                columns = [col for col in df.columns if col != "user_id"]
            except Exception:
                # Fallback to the original minimal set if anything goes wrong
                columns = [
                    "most_frequent_category",
                    "most_frequent_action",
                    "action_name",
                    "leaf_value",
                ]
        else:
            columns = [
                "most_frequent_category",
                "most_frequent_action",
                "action_name",
                "leaf_value",
            ]

        response_text = ResponseGenerator.generate_response(
            request.message,
            columns=columns,
            user_id="62002cce-0993-4658-b6dd-ec2b10bd3337",
            provider=selected_provider,
        )
        return ChatResponse(response=response_text)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
```

#### `backend/Response/vector_retriever.py` (FAISS index + retrieval helper)

```python
from pathlib import Path
import threading

import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer


EMBED_DIM = 384
MODEL_NAME = "all-MiniLM-L6-v2"
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent.parent / "data" / "articles_cleaned_filtered.csv"
INDEX_PATH = BASE_DIR / "faiss_index.bin"

_documents = None
_index = None
_embed_model = None
_lock = threading.Lock()


def build_index_once() -> None:
    """
    Build the FAISS index over the articles corpus *once*.

    - Reads `articles_cleaned_filtered.csv`
    - Computes embeddings for all documents
    - Writes `faiss_index.bin`
    - Prints progress so you know when it's done
    """
    global _documents

    print(f"[vector_retriever] Starting one-time embedding + index build...")
    print(f"[vector_retriever] Corpus CSV: {DATA_PATH}")
    print(f"[vector_retriever] Target index: {INDEX_PATH}")

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"[vector_retriever] Missing corpus CSV at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    _documents = (
        df["Title"].fillna("") + "\n\n" + df["scraped_text"].fillna("")
    ).tolist()
    print(f"[vector_retriever] Loaded {len(_documents)} documents.")

    model = SentenceTransformer(MODEL_NAME)
    print(f"[vector_retriever] Loaded embedding model '{MODEL_NAME}'.")

    embeddings = model.encode(_documents, show_progress_bar=True)
    print(f"[vector_retriever] Computed embeddings with shape {embeddings.shape}.")

    index = faiss.IndexFlatL2(EMBED_DIM)
    index.add(embeddings)
    faiss.write_index(index, str(INDEX_PATH))

    print(
        f"[vector_retriever] Index build complete. "
        f"Stored {index.ntotal} vectors to {INDEX_PATH}"
    )


def _load_documents_and_index():
    """Load documents and FAISS index (no document embedding is done here)."""
    global _documents, _index

    if _index is not None and _documents is not None:
        return

    with _lock:
        if _index is not None and _documents is not None:
            return

        if not DATA_PATH.exists():
            raise FileNotFoundError(f"[vector_retriever] Missing corpus CSV at {DATA_PATH}")

        df = pd.read_csv(DATA_PATH)
        _documents = (
            df["Title"].fillna("") + "\n\n" + df["scraped_text"].fillna("")
        ).tolist()

        if not INDEX_PATH.exists():
            raise FileNotFoundError(
                f"[vector_retriever] Missing FAISS index at {INDEX_PATH}. "
                f"Run `python {__file__}` once to build it."
            )

        _index = faiss.read_index(str(INDEX_PATH))


def _load_model():
    """Lazily load the sentence-transformer model for query encoding."""
    global _embed_model
    if _embed_model is not None:
        return

    with _lock:
        if _embed_model is not None:
            return
        _embed_model = SentenceTransformer(MODEL_NAME)


def retrieve_relevant_docs(query: str, k: int = 2) -> str:
    """
    Return the top-k documents stitched into a single context block.

    Document embeddings are **not** recomputed here — they should be built once
    by running this module as a script:

        python backend/Response/vector_retriever.py
    """
    if not query:
        print("[vector_retriever] Empty query string received; skipping retrieval.")
        return ""

    print("[vector_retriever] Loading documents and FAISS index (if not already loaded)...")
    _load_documents_and_index()
    if _index is None or _documents is None:
        print("[vector_retriever] ERROR: Index or documents not loaded.")
        return ""
    print(f"[vector_retriever] Documents loaded: {len(_documents)}")
    print(f"[vector_retriever] Index size (ntotal): {_index.ntotal}")

    print("[vector_retriever] Loading embedding model (if not already loaded)...")
    _load_model()
    if _embed_model is None:
        print("[vector_retriever] ERROR: Embedding model not loaded.")
        return ""

    print("[vector_retriever] Encoding query to embedding...")
    q_emb = _embed_model.encode([query])
    print(f"[vector_retriever] Query embedding shape: {getattr(q_emb, 'shape', 'unknown')}")

    print(f"[vector_retriever] Searching top-{k} nearest documents in FAISS index...")
    _, hit_indices = _index.search(q_emb, k)

    selected = []
    for idx in hit_indices[0]:
        if 0 <= idx < len(_documents):
            selected.append(_documents[idx])

    print(f"[vector_retriever] Retrieved {len(selected)} article(s) from index.")
    return "\n\n".join(selected)


if __name__ == "__main__":
    # One-off embedding + index build entrypoint.
    # Run this from the project root:
    #   python backend/Response/vector_retriever.py
    build_index_once()
```

### Frontend

#### `frontend/src/lib/api.ts`

```ts
export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  endpoints: {
    chat: "/chat",
  },
} as const;

export type ChatProvider = "llama" | "openai";

export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.baseURL}${endpoint}`;
};

export const sendChatMessage = async (
  message: string,
  provider: ChatProvider = "llama",
): Promise<string> => {
  const response = await fetch(getApiUrl(API_CONFIG.endpoints.chat), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message, provider }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  return data.response;
};
```

#### `frontend/src/pages/Index.tsx`

```tsx
const Index = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! I'm your Climate Assistant. I'm here to help you understand climate change, explore sustainable solutions, and answer your environmental questions. What would you like to know?",
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [provider, setProvider] = useState<ChatProvider>("llama");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: await sendChatMessage(content, provider),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error calling API:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Sorry, I encountered an error while processing your request using ${provider === "openai" ? "ChatGPT" : "Llama"}. Please make sure the backend server is running on http://localhost:8000`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  // In the header:
  // Powered by {provider === "openai" ? "ChatGPT" : "Llama"}.
  // And the two toggle buttons:
  // - Local Llama (sets provider to "llama")
  // - ChatGPT (sets provider to "openai")
};
```

### How to restore after hard reset

1. Recreate `response_generator.py`, `api.py`, and `vector_retriever.py` in `backend/Response` using the code above.
2. Ensure your `.env` (or environment) contains `OPEN_AI_KEY` and optionally `OPENAI_MODEL` (defaults to `gpt-4o-mini`).
3. In the frontend, restore the `ChatProvider` type, `provider` state, and toggle buttons in `Index.tsx`, and keep `sendChatMessage` sending `{ message, provider }` to `/chat`.


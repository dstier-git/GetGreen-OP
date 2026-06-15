# GetGreen-OP

GetGreen is a sustainability coaching assistant (“GiGi”) that combines **retrieval over an article corpus**, **personalized user context**, and **large language models** to answer questions and suggest realistic environmental actions.

This repository holds the **core application**: a **FastAPI** backend (`core/backend`) and a **Vite + React + TypeScript** frontend (`core/frontend`). The backend can use **OpenAI** (`chatgpt` / `auto`) with a **local Llama** fallback via **Ollama**, or **Llama** only.

---

## What it does

- **Semantic search** over sustainability articles (FAISS or a NumPy embedding store, using `sentence-transformers`).
- **User-aware replies** using profile and recommendation data from CSVs under `core/core_data/`.
- **Intent handling** (e.g. general Q&A vs. recommendations / weekly planning) with structured response formatting.
- **HTTP API**: `POST /chat` for conversations and `POST /welcome` for an opening message.

---

## Repository layout

| Path | Role |
|------|------|
| `core/backend/` | FastAPI app (`response.py`), retrieval, LLM adapters, user logic |
| `core/frontend/` | Web UI (dev server on port **8080**) |
| `core/core_data/` | **Required** CSV assets (see below); not all bundles ship every file in public clones |
| `core/.env` | Local secrets and overrides (create from `core/.env.example`) |
| `data/` | Optional notebooks / legacy notes; the **running app** expects data under `core/core_data/` |

---

## Prerequisites

- **Python** 3.10+ (3.12 works with the pinned stack in `core/backend/requirements.txt`)
- **Node.js** 18+ and npm
- **Optional:** [OpenAI API key](https://platform.openai.com/) for the `chatgpt` / `auto` providers
- **Optional:** [Ollama](https://ollama.com/) running locally if you use the `llama` provider or need fallback when ChatGPT fails. Default model name is set in `core/backend/llama.py` (`MODEL_NAME`); adjust it to match a model you have pulled in Ollama.

---

## Data files (`core/core_data/`)

The backend expects these **filenames** (paths are wired in `vector_retriever.py`, `user_retriever.py`, and `data_retriever.py`):

| File | Purpose |
|------|---------|
| `articles_with_actions.csv` | Article corpus for embeddings and RAG (columns such as `Title`, `action_ids`, `action_names`, `scraped_text`, `URL`) |
| `Data-Sample.csv` | Event log + action catalog: maps action IDs to names, categories, and effort, and holds each user's `CompleteAction` history and `leaf_value`s |
| `User Info.csv` | Per-user profile rows (keyed by `scrambled_id`) for personalization |
| `data_with_stats-copy.csv` | Per-user stats source. **Required at startup** — `data_retriever.py` loads it into SQLite the moment the backend is imported |
| `data_with_stats.db` | SQLite database, **auto-created/overwritten** from `data_with_stats-copy.csv` by `data_retriever.py`. Do not edit by hand; it is rebuilt on every launch |

If your team distributes different CSV names, rename or convert them to match what the code loads, or update the path constants in the backend.

> **Heads up:** `data_retriever.py` runs `pandas.read_csv(...).to_sql(...)` at **module import**, so `data_with_stats-copy.csv` must exist under `core/core_data/` before you start `uvicorn` — otherwise the backend raises on startup, not on first request.

**Public checkouts** may omit large CSVs; obtain them from the project maintainer or your internal data bundle.

---

## One-time setup

### 1. Python environment and dependencies

```bash
cd core/backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

The first embedding build downloads the sentence-transformer model (`all-MiniLM-L6-v2`); ensure you have disk and network available.

### 2. Environment variables

```bash
cp core/.env.example core/.env
```

Edit `core/.env`. Typical entries:

- `OPENAI_API_KEY` — required for ChatGPT-backed generation (also accepts legacy `OPEN_AI_KEY`).
- `OPENAI_MODEL` — optional override (default `gpt-4o-mini`).
- `VITE_API_BASE_URL` — optional; frontend defaults to `http://localhost:8000`.

### 3. Build the retrieval index

From the **repository root**:

```bash
python core/backend/vector_retriever.py
```

This reads `core/core_data/articles_with_actions.csv` and writes `faiss_index.bin` (if FAISS is installed) and/or `article_embeddings.npy` under `core/backend/`. The API can also trigger a build on first request if files are missing, but running the script once is the clearest workflow.

### 4. Frontend dependencies

```bash
cd core/frontend
npm install
```

---

## Run the app

**Terminal 1 — backend** (from `core/backend` so imports resolve as in development):

```bash
cd core/backend
source .venv/bin/activate   # if you use a venv
uvicorn response:app --reload --port 8000
```

API base URL: `http://localhost:8000`.

**Terminal 2 — frontend:**

```bash
cd core/frontend
npm run dev
```

UI: `http://localhost:8080` (see `core/frontend/vite.config.ts`). CORS is enabled for `localhost:8080`, `5173`, and `3000`.

**Production build (frontend only):**

```bash
cd core/frontend
npm run build
npm run preview   # optional local static preview
```

---

## API (quick reference)

| Method | Path | Body (JSON) | Response |
|--------|------|-------------|----------|
| `POST` | `/chat` | `message`, optional `provider` (`chatgpt`, `llama`, `auto`), `user_id`, `history` | `response`, `meta` (`intent`, `used_provider`, `fallback_used`) |
| `POST` | `/welcome` | optional `user_id`, `provider` | `message`, `meta` |

The active default user ID when `user_id` is omitted is defined in `core/backend/user_retriever.py` (`CURRENT_USER_ID`).

---

## Troubleshooting

- **Missing corpus / index errors:** Confirm `articles_with_actions.csv` is under `core/core_data/` and rerun `python core/backend/vector_retriever.py`.
- **Backend fails on startup (`data_with_stats-copy.csv` not found):** `data_retriever.py` rebuilds the SQLite store at import time, so this CSV must be present under `core/core_data/` before you launch `uvicorn`.
- **ChatGPT errors / empty replies:** Check `OPENAI_API_KEY` in `core/.env`. With `auto`, the backend falls back to Ollama if ChatGPT fails—ensure Ollama is running and the model name in `llama.py` exists locally.
- **Llama-only mode:** Start Ollama, pull or create the configured model, then send `provider: "llama"` from the client.
- **Frontend cannot reach API:** Confirm the backend is on port 8000 or set `VITE_API_BASE_URL` in `core/.env` and restart Vite.

---

## Git workflow (short)

```bash
git pull origin main
git add <paths>
git commit -m "Describe the change"
git push origin main
```

Do not commit `core/.env` or other secrets.

---

## Further docs

- `core/README.md` — older step-by-step notes (prefer this root README + paths above if they differ).
- `core/frontend/README.md` — Vite/React-specific notes from the template.

# GetGreen app & bot runtime

This folder contains only the code and data paths used when running the **app** (frontend + backend API) and **bot**. All other repo content (notebooks, tutorials, analysis, misc) stays in the repo root.

## Run the app

### 1. Backend (API)

From the repo root, in one terminal:

```bash
cd core/backend
uvicorn response:app --reload --port 8000
```

Use your current Python (conda base, system, or a venv). If you have a venv at the repo root:

```bash
cd core/backend && source ../../venv/bin/activate && uvicorn response:app --reload --port 8000
```

### 2. Frontend

In a second terminal:

```bash
cd core/frontend
npm install   # first time only
npm run dev
```

Frontend runs on port 8080 and talks to the backend at `http://localhost:8000`.

### 3. Environment

- Copy `core/.env.example` to `core/.env`.
- Fill in `SUPABASE_URL` and `SUPABASE_KEY` if you use Supabase.

### 4. Data files (required at runtime)

Place these in **`core/data/`** (they are gitignored; do not commit):

- `articles_cleaned_filtered.csv` – article corpus for the chat retriever.
- `data_with_stats-copy.csv` and `data_with_stats.db` – user/stats data for the backend.

**FAISS index:** After putting `articles.csv` in `core/data/`, build the index once:

```bash
cd core/backend
python vector_retriever.py
```

This creates `faiss_index.bin` in `core/backend/`.

## Layout

- `core/frontend/` – Vite/React UI.
- `core/backend/` – FastAPI app (`response.py`) and its dependencies (llama, chatgpt, vector_retriever, data_retriever).
- `core/data/` – Runtime data files (csv, db; FAISS index in `core/backend/`).

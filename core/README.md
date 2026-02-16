# GetGreen app & bot runtime

This folder contains only the code and data paths used when running the **app** (frontend + backend API) and **bot**. All other repo content (notebooks, tutorials, analysis, misc) stays in the repo root.

## Run the app

### 1. Backend (API)

From the **project root** (so `core/` is visible) or from `core/backend/Response`:

```bash
cd core/backend/Response
uvicorn mainTry:app --reload --port 8000
```

Or from repo root:

```bash
uvicorn mainTry:app --reload --port 8000 --app-dir core/backend/Response
```

### 2. Frontend

```bash
cd core/frontend
npm install   # first time only
npm run dev
```

Frontend runs on port 8080 and talks to the backend at `http://localhost:8000`.

### 3. Environment

- Copy `core/.env.example` to `core/.env` (or put `.env` in `core/backend/Response`).
- Fill in `SUPABASE_URL` and `SUPABASE_KEY` if you use Supabase.

### 4. Data files (required at runtime)

Place these in **`core/data/`** (they are gitignored; do not commit):

- `articles_cleaned_filtered.csv` – article corpus for the chat retriever.
- `data_with_stats-copy.csv` and `data_with_stats.db` – user/stats data for the backend.

**FAISS index:** After putting `articles_cleaned_filtered.csv` in `core/data/`, build the index once:

```bash
cd core/backend/Response
python vector_retriever.py
```

This creates `faiss_index.bin` in `core/backend/Response/`.

## Layout

- `core/frontend/` – Vite/React UI.
- `core/backend/Response/` – FastAPI app (`mainTry.py`) and its dependencies (response generator, vector retriever, DB helpers).
- `core/data/` – Runtime data files (csv, db, and the built FAISS index lives in `Response/`).
